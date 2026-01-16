import tensorflow as tf
import numpy as np
import faiss
import cv2

import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as tf_image
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ========== CONFIGURATION ==========
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your-api-key-here")  # ← Put in .env !
IMAGE_STORAGE_DIR = "wardrobe_images"
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FashionAI")



# ========== ENUMS AND DATA CLASSES ==========
class WeatherCondition(Enum):
    SUNNY = "sunny"
    RAINY = "rainy"
    CLOUDY = "cloudy"
    HUMID = "humid"
    COLD = "cold"

class Seasonality(Enum):
    WARM = "warm"
    LIGHT = "light"
    WATERPROOF = "waterproof"
    COOL = "cool"

class Style(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    SMART_CASUAL = "smart_casual"
    SPORTY = "sporty"
    TRADITIONAL = "traditional"

class Occasion(Enum):
    DAILY = "daily"
    OFFICE = "office"
    CHURCH = "church"
    CAMPUS = "campus"
    WEDDING = "wedding"
    TRAVEL = "travel"

@dataclass
class WardrobeItem:
    id: str
    user_id: str
    category: str
    color: str              # dominant hex
    
    style: str
    material: str
    seasonality: str
    features: np.ndarray
    image_path: str
    last_worn: Optional[datetime] = None
    faiss_id: int = -1
    colors_palette: List[str] = field(default_factory=list)

@dataclass
class OutfitRecommendation:
    top: Optional[WardrobeItem] = None
    bottom: Optional[WardrobeItem] = None
    footwear: Optional[WardrobeItem] = None
    outerwear: Optional[WardrobeItem] = None
    accessories: List[WardrobeItem] = field(default_factory=list)
    occasion: str = "daily"
    confidence_score: float = 0.0
    weather_appropriate: bool = False

# ========== GLOBAL STORAGE & MODELS ==========
base_model = MobileNetV2(weights='imagenet', include_top=False)
classification_model = MobileNetV2(weights='imagenet')  # For inference
feature_model = tf.keras.Model(
    inputs=classification_model.input,
    outputs=classification_model.layers[-2].output
)

dimension = 1280
faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))  # Proper removable index

# user_id → {item_id → WardrobeItem}
wardrobe_db: Dict[str, Dict[str, WardrobeItem]] = {}

# ========== FINE-TUNING ON AFRICAN FASHION DATASET ==========
def fine_tune_model(dataset_path: str, epochs: int = 10, batch_size: int = 32):
    """
    Fine-tune MobileNetV2 on AFRIFASHION1600 or similar African fashion dataset.
    Assume dataset is organized in folders: dataset_path/train/class1, dataset_path/val/class1, etc.
    Download AFRIFASHION1600 from: https://github.com/DataScienceNigeria/Research-Papers-by-Data-Science-Nigeria (contact authors if needed) or use similar like inuwamobarak/african-atire from HF.
    """
    # Data generators
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )

    train_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )

    val_generator = train_datagen.flow_from_directory(
        dataset_path,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )

    num_classes = len(train_generator.class_indices)

    # Build fine-tuned model
    global base_model
    base_model.trainable = True  # Unfreeze for fine-tuning

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(1024, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Train
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=val_generator
    )

    # Save and update global models
    model.save('fine_tuned_mobilenetv2.h5')
    global classification_model, feature_model
    classification_model = model
    feature_model = tf.keras.Model(inputs=model.input, outputs=model.layers[-3].output)  # Update feature extractor

    logger.info("Model fine-tuned successfully.")
    return history

def safe_convert(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON/Pydantic serialization.
    Handles arrays, scalars, dicts, lists, etc.
    """
    if isinstance(obj, np.ndarray):
        return [safe_convert(x) for x in obj.tolist()]
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: safe_convert(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_convert(item) for item in obj]
    if obj is None:
        return None
    return obj

# Example: fine_tune_model('/path/to/afrifashion1600')

# ========== HELPER FUNCTIONS ==========
def save_image(image_bytes: bytes, item_id: str) -> str:
    path = os.path.join(IMAGE_STORAGE_DIR, f"{item_id}.jpg")
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


async def build_user_faiss_index(user_id: str, db) -> Tuple[faiss.IndexFlatIP, List[str]]:
    """
    Build FAISS index from user's wardrobe items on demand (MVP approach)
    Returns: (index, list_of_item_ids_in_order)
    """
    items = await db.wardrobe_items.find(
        {"user_id": user_id},
        {"_id": 1, "features": 1}
    ).to_list(1000)  # limit for safety

    if not items:
        return None, []

    vectors = []
    item_ids = []

    for item in items:
        if "features" in item and len(item["features"]) > 0:
            vec = np.array(item["features"], dtype=np.float32)
            vectors.append(vec)
            item_ids.append(str(item["_id"]))

    if not vectors:
        return None, []

    dimension = len(vectors[0])
    index = faiss.IndexFlatIP(dimension)  # Inner Product = cosine after normalization
    vectors_np = np.array(vectors).astype('float32')
    faiss.normalize_L2(vectors_np)        # very important for cosine similarity
    index.add(vectors_np)

    return index, item_ids


async def search_user_closet(
    query_features: np.ndarray,
    user_id: str,
    db,
    top_k: int = 8
) -> List[Dict]:
    """
    Find most similar items in user's wardrobe
    """
    index, item_ids = await build_user_faiss_index(user_id, db)
    if index is None:
        return []

    # Normalize query vector
    query_vec = query_features.astype('float32').reshape(1, -1)
    faiss.normalize_L2(query_vec)

    distances, indices = index.search(query_vec, top_k)

    results = []
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx == -1:
            continue
        item_id = item_ids[idx]
        similarity = float(dist)  # cosine similarity (higher = better)

        item = await db.wardrobe_items.find_one({"_id": ObjectId(item_id)})
        if item:
            results.append({
                "item_id": item_id,
                "image_url": item["image_url"],
                "category": item["category"],
                "color": item["color"],
                "style": item["style"],
                "similarity_score": round(similarity, 4),
                "rank": rank + 1
            })

    return sorted(results, key=lambda x: x["similarity_score"], reverse=True)

# ========== WEATHER SERVICE (REAL API) ==========
class WeatherService:
    def __init__(self):
        self.cache: Dict[str, Tuple[datetime, Dict]] = {}
        self.cache_duration = timedelta(minutes=30)
        self.kenyan_cities = {
            "nairobi": {"lat": -1.286389, "lon": 36.817223},
            "mombasa": {"lat": -4.0435, "lon": 39.6682},
            "kisumu": {"lat": -0.1022, "lon": 34.7617},
            "eldoret": {"lat": 0.5143, "lon": 35.2698}
        }

    async def get_weather(self, city: str) -> Dict[str, Any]:
        city = city.lower()
        now = datetime.now()

        if city in self.cache:
            cached_time, data = self.cache[city]
            if now - cached_time < self.cache_duration:
                return data

        if city not in self.kenyan_cities:
            return self._fallback_weather(city)

        coords = self.kenyan_cities[city]

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}&units=metric"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning(f"Weather API failed for {city}: {resp.status}")
                        return self._fallback_weather(city)
                    data = await resp.json()

            weather = {
                "temperature": data["main"]["temp"],
                "condition": data["weather"][0]["main"].lower(),
                "humidity": data["main"]["humidity"],
                "rain_probability": data.get("rain", {}).get("1h", 0) * 4,  # rough estimate
                "city": city.title()
            }
            self.cache[city] = (now, weather)
            return weather

        except Exception as e:
            logger.error(f"Weather fetch error for {city}: {e}")
            return self._fallback_weather(city)

    def _fallback_weather(self, city: str) -> Dict:
        ranges = {"nairobi": (18, 25), "mombasa": (26, 32), "kisumu": (22, 28), "eldoret": (15, 22)}
        temp_range = ranges.get(city, (20, 25))
        return {
            "temperature": round(np.random.uniform(*temp_range), 1),
            "condition": np.random.choice(["sunny", "rainy", "cloudy", "humid"]),
            "humidity": np.random.randint(40, 90),
            "rain_probability": np.random.randint(0, 100),
            "city": city.title()
        }

    def get_seasonality_recommendation(self, weather: Dict) -> List[str]:
        temp = weather.get("temperature", 25)
        cond = weather.get("condition", "sunny")
        recs = []

        if temp < 17:
            recs.append("warm")
        elif temp > 26:
            recs.append("light")

        if cond == "rainy" or weather.get("rain_probability", 0) > 40:
            recs.append("waterproof")

        return recs or ["cool"]

weather_service = WeatherService()

# ========== CLASSIFICATION & FEATURE EXTRACTION ==========
FASHION_CATEGORIES = {
    'shirt': ['jersey', 't-shirt', 'shirt', 'polo', 'blouse', 'sweatshirt'],
    'trousers': ['trousers', 'jeans', 'pants', 'slacks', 'leggings', 'cargo'],
    'dress': ['dress', 'gown', 'frock', 'sundress', 'maxi'],
    'jacket': ['jacket', 'coat', 'blazer', 'overcoat'],
    'shoes': ['sneaker', 'shoe', 'boot', 'sandal', 'loafer', 'heel'],
    'jewellery': ['necklace', 'earring', 'bracelet', 'ring', 'bangle', 'anklet'],
    'traditional': ['kitenge', 'kanga', 'shuka', 'ankara', 'maasai']  # added
}

async def classify_image(image_bytes: bytes) -> Dict[str, Any]:
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img_resized = img.resize((224, 224))
    img_array = tf_image.img_to_array(img_resized)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = classification_model.predict(img_array, verbose=0)
    decoded = decode_predictions(preds, top=10)[0]

    # Fashion classification
    best_cat = "other"
    best_sub = ""
    conf = 0.0

    for _, label, prob in decoded:
        label = label.lower()
        for cat, keys in FASHION_CATEGORIES.items():
            if any(k in label for k in keys):
                if prob > conf:
                    conf = prob
                    best_cat = cat
                    best_sub = label

    # Color extraction
    img_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img_cv is not None:
        img_cv = cv2.resize(img_cv, (120, 120))
        pixels = img_cv.reshape(-1, 3).astype(np.float32)
        _, _, centers = cv2.kmeans(pixels, 5, None,
                                 (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
                                 10, cv2.KMEANS_RANDOM_CENTERS)
        colors_hex = ['#%02x%02x%02x' % (c[2], c[1], c[0]) for c in centers.astype(int)]
        dominant = colors_hex[0]
    else:
        dominant = "#95a5a6"
        colors_hex = [dominant]

    # Improved Kenyan/African pattern detection (post-fine-tuning enhancement)
    if best_cat == "other" and len(set(colors_hex)) > 3:  # Colorful patterns
        best_cat = "traditional"
        best_sub = "kitenge or similar"

    material = _guess_material(best_cat)
    style = _guess_style(best_cat, dominant)
    seasonality = _guess_seasonality(best_cat, material, dominant)

    return {
        "category": best_cat,
        "subcategory": best_sub,
        "color": dominant,
        "colors_palette": colors_hex,
        "style": style,
        "material": material,
        "seasonality": seasonality,
        "confidence": round(float(conf), 3)
    }

def _guess_material(cat: str) -> str:
    opts = {
        "shirt": "cotton", "trousers": "denim", "dress": "cotton",
        "jacket": "polyester", "shoes": "leather", "traditional": "cotton",
        "jewellery": "metal"
    }
    return opts.get(cat, "unknown")

def _guess_style(cat: str, dominant_color: str) -> str:
    if cat in ["jacket", "dress"] and dominant_color in ["#000000", "#1a1a1a", "#333333"]:
        return "formal"
    if cat == "traditional":
        return "traditional"
    return "casual"

def _guess_seasonality(cat: str, material: str, color: str) -> str:
    if cat in ["jacket"] or material in ["wool", "leather"]:
        return "warm"
    if "light" in color.lower() or material == "linen":
        return "light"
    if np.random.random() < 0.15:  # small chance of waterproof (raincoats etc)
        return "waterproof"
    return "cool"

async def extract_features(image_bytes: bytes) -> np.ndarray:
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    arr = tf_image.img_to_array(img)
    arr = np.expand_dims(arr, 0)
    arr = preprocess_input(arr)
    return feature_model.predict(arr, verbose=0).flatten()

# ========== WARDROBE MANAGEMENT ==========
async def add_to_wardrobe(user_id: str, image_bytes: bytes) -> Dict:
    item_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    classification = await classify_image(image_bytes)
    features = await extract_features(image_bytes)
    
    faiss.normalize_L2(features.reshape(1, -1))
    
    # Add to FAISS with ID
    faiss_id = len(wardrobe_db.get(user_id, {}))  # simple incremental
    faiss_index.add_with_ids(features.reshape(1, -1), np.array([faiss_id], dtype=np.int64))
    
    image_path = save_image(image_bytes, item_id)
    
    item = WardrobeItem(
        id=item_id,
        user_id=user_id,
        category=classification["category"],
        color=classification["color"],
        colors_palette=classification["colors_palette"],
        style=classification["style"],
        material=classification["material"],
        seasonality=classification["seasonality"],
        features=features,
        image_path=image_path,
        faiss_id=faiss_id
    )
    
    if user_id not in wardrobe_db:
        wardrobe_db[user_id] = {}
    wardrobe_db[user_id][item_id] = item
    
    return {
        "success": True,
        "item_id": item_id,
        "classification": classification,
        "path": image_path
    }

# ========== MAIN FASHION AI CLASS ==========
class FashionAIAssistant:
    def __init__(self):
        pass  # can add more services later

    async def upload_item(self, user_id: str, image_bytes: bytes) -> Dict:
        return await add_to_wardrobe(user_id, image_bytes)

    async def get_recommendations(self,
                                 user_id: str,
                                 occasion: str,
                                 city: str = "nairobi",
                                 preferences: Optional[Dict] = None) -> List[Dict]:
        if user_id not in wardrobe_db or not wardrobe_db[user_id]:
            return []

        items = list(wardrobe_db[user_id].values())
        weather = await weather_service.get_weather(city)
        seasonality_req = weather_service.get_seasonality_recommendation(weather)

        # Very simple outfit generator (expand in production)
        recommendations = []

        for item in items[:6]:  # limit for demo
            rec = {
                "occasion": occasion,
                "confidence_score": 0.72,
                "weather_appropriate": "warm" in item.seasonality or "light" in item.seasonality,
                "items": {
                    "main": {
                        "category": item.category,
                        "color": item.color,
                        "style": item.style,
                        "material": item.material,
                        "seasonality": item.seasonality
                    }
                }
            }
            recommendations.append(rec)

        return recommendations[:3]

# ========== Quick Test ==========
async def test():
    assistant = FashionAIAssistant()
    
    # Fake upload example
    fake_image = b"fake"  # in real → read from file
    result = await assistant.upload_item("user123", fake_image)
    print("Added:", result)

if __name__ == "__main__":
    # asyncio.run(test())
    print("Fashion AI Assistant ready. Remember to set OPENWEATHER_API_KEY!")
    # To fine-tune: fine_tune_model('/path/to/downloaded/afrifashion1600')