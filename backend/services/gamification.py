# backend/services/gamification.py
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bson import ObjectId
import asyncio

# Constants
POINTS_BASE = 5               # points for any wear
POINTS_LEAST_WORN_BONUS = 10  # extra if item worn < 3 times
POINTS_MILESTONE = 50         # points needed for a basic badge

BADGES = {
    "consistent_user": {
        "name": "Consistent User",
        "description": "Worn at least 10 different items in the last 30 days",
        "icon": "🔄"
    },
    "sustainability_star": {
        "name": "Sustainability Star",
        "description": "Revived 5+ least-worn items (≤2 wears before revival)",
        "icon": "🌱"
    },
    "wardrobe_master": {
        "name": "Wardrobe Master",
        "description": "Reached 500 total points",
        "icon": "👑"
    }
}

async def award_wear_points(
    db,
    user_id: str,
    item_id: str,
    current_wear_count: int
) -> Dict[str, Any]:
    """
    Award points when user marks an item as worn.
    Gives bonus for least-worn items.
    Returns: points awarded + any new badges
    """
    points = POINTS_BASE
    if current_wear_count < 3:
        points += POINTS_LEAST_WORN_BONUS

    # Update user rewards document
    reward_doc = await db.user_rewards.find_one_and_update(
        {"user_id": user_id},
        {
            "$inc": {
                "total_points": points,
                "wear_events": 1,
                "least_worn_revived": 1 if current_wear_count < 3 else 0
            },
            "$set": {"updated_at": datetime.utcnow()},
            "$addToSet": {"worn_item_ids": item_id}
        },
        upsert=True,
        return_document=True
    )

    new_badges = await check_and_award_badges(db, user_id, reward_doc)

    return {
        "points_awarded": points,
        "total_points": reward_doc.get("total_points", points),
        "new_badges": new_badges,
        "message": f"+{points} points awarded! {'Bonus for reviving a least-worn item!' if current_wear_count < 3 else ''}"
    }


async def check_and_award_badges(
    db,
    user_id: str,
    reward_doc: Dict
) -> List[Dict]:
    """
    Check badge conditions and award new ones if earned
    """
    current_badges = set(reward_doc.get("badges", []))
    new_badges = []

    # Badge 1: Consistent User
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_wears = await db.wardrobe_items.count_documents({
        "user_id": user_id,
        "last_worn": {"$gte": thirty_days_ago}
    })

    if recent_wears >= 10 and "consistent_user" not in current_badges:
        new_badges.append(BADGES["consistent_user"])
        current_badges.add("consistent_user")

    # Badge 2: Sustainability Star
    if reward_doc.get("least_worn_revived", 0) >= 5 and "sustainability_star" not in current_badges:
        new_badges.append(BADGES["sustainability_star"])
        current_badges.add("sustainability_star")

    # Badge 3: Wardrobe Master
    if reward_doc.get("total_points", 0) >= 500 and "wardrobe_master" not in current_badges:
        new_badges.append(BADGES["wardrobe_master"])
        current_badges.add("wardrobe_master")

    if new_badges:
        await db.user_rewards.update_one(
            {"user_id": user_id},
            {"$set": {"badges": list(current_badges)}}
        )

    return new_badges


async def get_user_rewards_summary(
    db,
    user_id: str
) -> Dict[str, Any]:
    """
    Get user's current points, badges, and stats
    """
    reward = await db.user_rewards.find_one({"user_id": user_id})
    if not reward:
        return {
            "total_points": 0,
            "badges": [],
            "wear_events": 0,
            "least_worn_revived": 0
        }

    return {
        "total_points": reward.get("total_points", 0),
        "badges": reward.get("badges", []),
        "wear_events": reward.get("wear_events", 0),
        "least_worn_revived": reward.get("least_worn_revived", 0)
    }