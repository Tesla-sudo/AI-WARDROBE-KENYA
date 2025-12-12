# backend/routes/wardrobe.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from models import WardrobeItem
from ai_utils import classify_image, extract_features, add_to_index
from cloudinary_utils import upload_to_cloudinary
from middleware.auth import get_current_user
import numpy as np

router = APIRouter()

def get_db():
    from main import app
    return app.state.db

@router.post("/upload")
async def upload_wardrobe_item(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files allowed")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(400, "Empty file")

    try:
        # 1. Upload to Cloudinary
        image_url = await upload_to_cloudinary(image_bytes)

        # 2. AI Classification + Features
        classification = await classify_image(image_bytes)
        features = await extract_features(image_bytes)

        # 3. Create item — LET MongoDB generate _id automatically
        item = WardrobeItem(
            user_id=current_user["_id"],
            image_url=image_url,
            category=classification["category"],
            color=classification["color"],
            style=classification["style"],
            material=classification["material"],
            seasonality=classification["seasonality"],
            features=features.tolist()
        )

        # 4. Insert and capture real _id
        result = await db.wardrobe_items.insert_one(item.model_dump(by_alias=True, exclude={"id"}))
        item_id = str(result.inserted_id)  # ← This will NEVER be empty now

        # 5. Add to FAISS
        await add_to_index(item_id, features)

        return {
            "message": f"{classification['category'].capitalize()} uploaded & classified!",
            "item_id": item_id,
            "category": classification["category"],
            "color": classification["color"],
            "image_url": image_url
        }

    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")