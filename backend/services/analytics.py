# backend/services/analytics.py
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
import asyncio

# Basic carbon footprint constants (grams CO₂e)
# These are rough averages – in real app you'd want better data/sources
CO2_PER_ITEM_PER_YEAR_UNUSED = 5000      # ~5 kg CO₂e/year per unused garment (textile production + waste)
CO2_PER_WEAR_SAVED = 20                  # rough savings per time an item is worn instead of buying new

async def get_analytics_summary(
    db,
    user_id: str,
    days: int = 365  # default: last year
) -> Dict[str, Any]:
    """
    Generate comprehensive analytics summary for the user
    """
    since_date = datetime.utcnow() - timedelta(days=days)

    # 1. Most worn & least worn items
    most_worn_pipeline = [
        {"$match": {"user_id": user_id, "wear_count": {"$gt": 0}}},
        {"$sort": {"wear_count": -1}},
        {"$limit": 5},
        {"$project": {
            "item_id": {"$toString": "$_id"},
            "category": 1,
            "color": 1,
            "style": 1,
            "wear_count": 1
        }}
    ]

    least_worn_pipeline = [
        {"$match": {"user_id": user_id, "wear_count": {"$gt": 0}}},
        {"$sort": {"wear_count": 1}},
        {"$limit": 5},
        {"$project": {
            "item_id": {"$toString": "$_id"},
            "category": 1,
            "color": 1,
            "style": 1,
            "wear_count": 1
        }}
    ]

    most_worn = await db.wardrobe_items.aggregate(most_worn_pipeline).to_list(5)
    least_worn = await db.wardrobe_items.aggregate(least_worn_pipeline).to_list(5)

    # 2. Cost-per-wear (only for items with known purchase price)
    cost_per_wear_pipeline = [
        {"$match": {
            "user_id": user_id,
            "purchase_price_kes": {"$exists": True, "$ne": None},
            "wear_count": {"$gt": 0}
        }},
        {"$project": {
            "item_id": {"$toString": "$_id"},
            "category": 1,
            "purchase_price_kes": 1,
            "wear_count": 1,
            "cost_per_wear": {
                "$divide": ["$purchase_price_kes", "$wear_count"]
            }
        }},
        {"$sort": {"cost_per_wear": 1}},
        {"$limit": 5}
    ]

    cost_per_wear_items = await db.wardrobe_items.aggregate(cost_per_wear_pipeline).to_list(5)

    # Average cost per wear across all tracked items
    total_cost = 0
    total_wears = 0
    async for item in db.wardrobe_items.find({
        "user_id": user_id,
        "purchase_price_kes": {"$exists": True, "$ne": None},
        "wear_count": {"$gt": 0}
    }, {"purchase_price_kes": 1, "wear_count": 1}):
        total_cost += item["purchase_price_kes"]
        total_wears += item["wear_count"]

    avg_cost_per_wear = round(total_cost / total_wears, 2) if total_wears > 0 else None

    # 3. Seasonal patterns (simple count of wears per month in last year)
    seasonal_pipeline = [
        {"$match": {"user_id": user_id, "last_worn": {"$gte": since_date}}},
        {"$group": {
            "_id": {"$month": "$last_worn"},
            "wear_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    seasonal_data = await db.wardrobe_items.aggregate(seasonal_pipeline).to_list(12)
    seasonal_patterns = {str(doc["_id"]): doc["wear_count"] for doc in seasonal_data}

    # 4. Carbon footprint of unused clothes (very rough estimate)
    unused_items = await db.wardrobe_items.count_documents({
        "user_id": user_id,
        "wear_count": 0
    })

    estimated_unused_co2 = unused_items * CO2_PER_ITEM_PER_YEAR_UNUSED

    # Items that were worn at least once → saved emissions (very approximate)
    worn_at_least_once = await db.wardrobe_items.count_documents({
        "user_id": user_id,
        "wear_count": {"$gte": 1}
    })
    estimated_saved_co2 = worn_at_least_once * CO2_PER_WEAR_SAVED * 10  # assume avg 10 wears

    return {
        "most_worn_items": most_worn,
        "least_worn_items": least_worn,
        "cost_per_wear_items": cost_per_wear_items,
        "average_cost_per_wear_kes": avg_cost_per_wear,
        "seasonal_patterns_by_month": seasonal_patterns,
        "carbon_footprint_estimate": {
            "unused_items_count": unused_items,
            "estimated_annual_co2_grams_unused": estimated_unused_co2,
            "estimated_co2_saved_grams": estimated_saved_co2,
            "note": "Rough estimates based on industry averages"
        },
        "total_items": await db.wardrobe_items.count_documents({"user_id": user_id}),
        "total_wears": await db.wardrobe_items.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$wear_count"}}}
        ]).to_list(1) | (lambda r: r[0]["total"] if r else 0)
    }