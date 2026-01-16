# backend/routes/wardrobe.py
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status, Query
from typing import Dict, Any, List, Optional
from bson import ObjectId
from datetime import datetime
import numpy as np
import traceback
from services.gamification import award_wear_points, get_user_rewards_summary
# Models & utils
from models import WardrobeItem
from ai_utils import classify_image, extract_features, search_user_closet, safe_convert
from cloudinary_utils import upload_to_cloudinary
from middleware.auth import get_current_user
from services.analytics import get_analytics_summary
from services.social_scouting import get_current_trends, match_trends_to_user_closet

router = APIRouter(tags=["Wardrobe"])

def get_db(request: Request):
    return request.app.state.db

def generate_mitumba_upcycle_ideas(
    category: str,
    material: str,
    color: str,
    style: str = "casual"
) -> List[str]:
    """
    Simple rule-based upcycling suggestions tailored for Kenyan mitumba context
    """
    ideas: List[str] = []

    material_lower = material.lower()
    if "cotton" in material_lower or "kitenge" in material_lower or "ankara" in material_lower:
        ideas.extend([
            "Add contrasting kitenge or ankara patches for cultural flair",
            "Tie-dye or re-dye to refresh faded areas",
            "Turn into a tote bag, headwrap or cushion cover if heavily worn"
        ])
    if "denim" in material_lower or "jeans" in category.lower():
        ideas.extend([
            "Distress knees and hems for modern streetwear vibe",
            "Patch with colorful African fabric prints",
            "Cut into high-waist shorts, denim skirt or bag"
        ])
    if "wool" in material_lower or "sweater" in category.lower():
        ideas.append("Felt and reshape into warm slippers, hat or bag")

    color_lower = color.lower()
    if "faded" in color_lower or "worn" in color_lower or "discolored" in color_lower:
        ideas.append("Re-dye with vibrant kitenge-inspired colors")

    if "traditional" in style.lower() or any(x in category.lower() for x in ["kitenge", "kanga", "shuka"]):
        ideas.extend([
            "Layer with modern accessories for fusion look",
            "Add beads, cowrie shells or Maasai-inspired embroidery"
        ])
    if category in ["shirt", "blouse", "dress"]:
        ideas.extend([
            "Shorten into crop top or tunic style",
            "Add decorative buttons, zips or lace details"
        ])

    ideas.extend([
        "Take to local fundi for resizing, zipper replacement or reinforcement",
        "Combine with other mitumba pieces for a unique layered outfit",
        "Sell or donate if upcycling isn't viable"
    ])

    unique_ideas = []
    seen = set()
    for idea in ideas:
        if idea not in seen:
            unique_ideas.append(idea)
            seen.add(idea)
        if len(unique_ideas) >= 6:
            break

    return unique_ideas

@router.post("/upload")

async def upload_wardrobe_item(
    file: UploadFile = File(...),
    is_mitumba: bool = Query(default=False, description="Mark this item as second-hand / mitumba"),
    purchase_price_kes: Optional[float] = Query(default=None, ge=0, description="Optional purchase price in KES"),
    source_platform: Optional[str] = Query(default=None, description="Where was it bought? e.g. Gikomba, Toi Market, Jumia, Instagram shop, Kilimall"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only image files allowed")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file uploaded")

    try:
        image_url = await upload_to_cloudinary(image_bytes)
        classification = await classify_image(image_bytes)
        features = await extract_features(image_bytes)

        classification_clean = safe_convert(classification)
        features_clean = safe_convert(features)

        upcycle_suggestions = []
        if is_mitumba:
            upcycle_suggestions = generate_mitumba_upcycle_ideas(
                classification_clean["category"],
                classification_clean["material"],
                classification_clean["color"],
                classification_clean["style"]
            )

        item_data = {
            "user_id": current_user["_id"],
            "image_url": image_url,
            "category": classification_clean["category"],
            "color": classification_clean["color"],
            "colors_palette": classification_clean.get("colors_palette", []),
            "style": classification_clean["style"],
            "material": classification_clean["material"],
            "seasonality": classification_clean["seasonality"],
            "features": features_clean,
            "wear_count": 0,
            "last_worn": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_mitumba": is_mitumba,
            "purchase_price_kes": purchase_price_kes,
            "purchase_date": datetime.utcnow() if is_mitumba and purchase_price_kes else None,
            "source_platform": source_platform,
            "upcycle_suggestions": upcycle_suggestions,
            "times_suggested": 0,
        }

        result = await db.wardrobe_items.insert_one(item_data)
        item_id = str(result.inserted_id)

        safe_response = {
            "success": True,
            "message": f"{classification_clean['category'].capitalize()} item uploaded and classified!",
            "item_id": item_id,
            "image_url": image_url,
            "category": classification_clean["category"],
            "color": classification_clean["color"],
            "style": classification_clean["style"],
            "confidence": classification_clean.get("confidence", 0.0),
            "is_mitumba": is_mitumba,
            "upcycle_suggestions": upcycle_suggestions if is_mitumba else []
        }

        return safe_convert(safe_response)

    except Exception as e:
        print("Upload error:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")


@router.post("/visual-search")
async def visual_search_inspiration(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload an inspiration image → find similar items in user's own closet
    Returns ranked similar wardrobe items + basic hints if nothing close found
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only image files allowed")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    try:
        # Extract features from the uploaded inspiration image
        query_features_np = await extract_features(image_bytes)

        # Search the user's closet using FAISS similarity
        similar_items = await search_user_closet(
            query_features_np,
            current_user["_id"],
            db,
            top_k=10
        )

        # Basic "what might be missing" hint
        missing_hint = None
        if len(similar_items) < 3:
            missing_hint = (
                "Few close matches in your wardrobe. "
                "Try searching Jumia or Kilimall for similar styles, "
                "or check local mitumba markets for affordable options."
            )

        response = {
            "success": True,
            "message": f"Found {len(similar_items)} similar items in your wardrobe",
            "similar_items": similar_items,
            "missing_hint": missing_hint,
            "query_processed": True
        }

        return safe_convert(response)

    except Exception as e:
        print("Visual search error:\n", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")
    
@router.post("/{item_id}/mark-worn")
async def mark_item_as_worn(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Mark an item as worn today → award points & check badges
    """
    item = await db.wardrobe_items.find_one_and_update(
        {"_id": ObjectId(item_id), "user_id": current_user["_id"]},
        {
            "$inc": {"wear_count": 1},
            "$set": {"last_worn": datetime.utcnow()}
        },
        return_document=True
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found or not owned by user")

    # Award points via gamification service
    reward_result = await award_wear_points(
        db,
        current_user["_id"],
        item_id,
        current_wear_count=item["wear_count"]
    )

    return {
        "success": True,
        "message": reward_result["message"],
        "points_awarded": reward_result["points_awarded"],
        "total_points": reward_result["total_points"],
        "new_badges": reward_result["new_badges"]
    }

@router.get("/rewards")
async def get_rewards_summary(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get user's current points, badges, and gamification stats
    """
    summary = await get_user_rewards_summary(db, current_user["_id"])
    return {
        "success": True,
        **summary
    }

@router.get("/analytics")
async def get_analytics_dashboard(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get comprehensive wardrobe analytics:
    - Most/least worn items
    - Cost-per-wear
    - Seasonal patterns
    - Carbon footprint estimate of unused clothes
    """
    try:
        summary = await get_analytics_summary(db, current_user["_id"])
        return {
            "success": True,
            "analytics": summary
        }
    except Exception as e:
        print("Analytics error:\n", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )
    
@router.get("/trends")
async def get_fashion_trends(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current Kenyan fashion trends scouted from social media (X/Twitter)
    + how they match your wardrobe + suggestions for missing pieces
    """
    try:
        trends = await get_current_trends(db)
        wardrobe_matches = await match_trends_to_user_closet(db, current_user["_id"], trends)

        return {
            "success": True,
            "current_trends": trends,
            "wardrobe_matches": wardrobe_matches,
            "last_updated": datetime.utcnow().isoformat(),
            "source_note": "Trends from recent public X (Twitter) posts with #KenyanFashion, #NairobiStyle, #Kitenge, etc. Refreshes daily."
        }

    except Exception as e:
        print("Trends endpoint error:\n", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trends: {str(e)}"
        )