# backend/services/social_scouting.py
from datetime import datetime, timedelta
from typing import List, Dict, Any
import traceback

# Cache key in MongoDB
TREND_CACHE_KEY = "kenyan_fashion_trends_current"

# Hardcoded fallback trends (used if X fetch fails or rate-limited)
FALLBACK_TRENDS = [
    {
        "trend": "Kitenge fusion streetwear",
        "description": "Traditional prints mixed with hoodies, sneakers, oversized jackets",
        "colors": ["multicolor", "orange", "blue", "yellow"],
        "hashtags": ["#KitengeModern", "#NairobiStreetStyle"],
        "source": "Recent X conversation",
        "example_categories": ["jacket", "hoodie", "sneakers", "trousers"]
    },
    {
        "trend": "Bold color blocking",
        "description": "Large blocks of primary/bright colors in outfits",
        "colors": ["red", "yellow", "blue", "green"],
        "hashtags": ["#KenyanFashion2026", "#ColorBlockKE"],
        "source": "Nairobi fashion buzz",
        "example_categories": ["dress", "shirt", "jacket"]
    },
    {
        "trend": "Upcycled mitumba looks",
        "description": "Revamped second-hand pieces with patches, dye, resizing",
        "colors": ["earthy tones", "vibrant accents"],
        "hashtags": ["#MitumbaRevival", "#SustainableKE"],
        "source": "Local creators & markets",
        "example_categories": ["denim", "shirt", "jacket", "dress"]
    }
]

async def fetch_kenyan_fashion_trends_from_x() -> List[Dict]:
    """
    MVP placeholder: In real production, replace with actual X search.
    For now returns fallback data.
    
    Real version example (using x_keyword_search tool or client):
    query = '(#KenyanFashion OR #NairobiStyle OR #Kitenge OR #MitumbaFashion OR #AnkaraKE) lang:en since:2026-01-01 min_faves:3 filter:has_engagement'
    mode = "Latest"
    limit = 20
    """
    # Placeholder – in real app, call X search here
    return FALLBACK_TRENDS


async def refresh_trends_cache(db):
    """
    Refresh cache with latest trends from X (or fallback)
    """
    try:
        trends = await fetch_kenyan_fashion_trends_from_x()
        if not trends:
            trends = FALLBACK_TRENDS

        await db.trend_cache.update_one(
            {"key": TREND_CACHE_KEY},
            {
                "$set": {
                    "data": trends,
                    "updated_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24)
                }
            },
            upsert=True
        )
        return trends

    except Exception as e:
        print("Trends refresh error:\n", traceback.format_exc())
        # Fallback to cached or sample
        cache = await db.trend_cache.find_one({"key": TREND_CACHE_KEY})
        return cache["data"] if cache else FALLBACK_TRENDS


async def get_current_trends(db) -> List[Dict]:
    """
    Get latest cached trends (refresh if expired)
    """
    cache = await db.trend_cache.find_one({"key": TREND_CACHE_KEY})
    if cache and cache.get("expires_at", datetime.min) > datetime.utcnow():
        return cache["data"]

    return await refresh_trends_cache(db)


async def match_trends_to_user_closet(
    db,
    user_id: str,
    trends: List[Dict]
) -> List[Dict]:
    """
    Simple matching: user's items that align with trends (color + category)
    """
    user_items = await db.wardrobe_items.find(
        {"user_id": user_id},
        {"category": 1, "color": 1, "style": 1, "is_mitumba": 1}
    ).to_list(300)

    matches = []

    for trend in trends:
        matching_items = []
        missing_pieces = set(trend.get("example_categories", []))

        for item in user_items:
            score = 0

            item_cat = item.get("category", "").lower()
            for ex_cat in trend.get("example_categories", []):
                if ex_cat.lower() in item_cat:
                    score += 3
                    missing_pieces.discard(ex_cat)

            item_color = item.get("color", "").lower()
            for trend_color in trend.get("colors", []):
                if trend_color.lower() in item_color:
                    score += 2

            if "upcycle" in trend["description"].lower() and item.get("is_mitumba", False):
                score += 1

            if score >= 3:
                matching_items.append({
                    "item_id": str(item["_id"]),
                    "category": item["category"],
                    "color": item["color"],
                    "style": item.get("style", "casual"),
                    "match_score": score,
                    "is_mitumba": item.get("is_mitumba", False)
                })

        matches.append({
            "trend": trend["trend"],
            "description": trend["description"],
            "matching_items": sorted(matching_items, key=lambda x: x["match_score"], reverse=True)[:4],
            "missing_pieces": list(missing_pieces),
            "suggested_action": "Search Jumia or Kilimall for these" if missing_pieces else "You have good pieces for this trend!"
        })

    return matches