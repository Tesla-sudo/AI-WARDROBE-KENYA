# backend/ai_utils.py
import tensorflow as tf
import numpy as np
import faiss
import cv2
from PIL import Image
from io import BytesIO
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as tf_image
from typing import List

# Load models once
classification_model = MobileNetV2(weights='imagenet')
feature_model = tf.keras.Model(
    inputs=classification_model.input,
    outputs=classification_model.layers[-2].output
)

# Global FAISS index
dimension = 1280
index = faiss.IndexFlatIP(dimension)

def map_to_fashion_category(pred_class: str) -> str:
    pred_class = pred_class.lower()
    if any(x in pred_class for x in ['shirt', 't-shirt', 'jersey']):
        return 'shirt'
    if any(x in pred_class for x in ['trousers', 'pants', 'jeans']):
        return 'trousers'
    if 'dress' in pred_class:
        return 'dress'
    if any(x in pred_class for x in ['jacket', 'coat', 'blazer']):
        return 'jacket'
    if any(x in pred_class for x in ['shoe', 'sneaker', 'boot']):
        return 'shoes'
    if any(x in pred_class for x in ['necklace', 'ring', 'bracelet']):
        return 'jewellery'
    return 'other'


async def classify_image(image_bytes: bytes):
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    img_array = tf_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    preds = classification_model.predict(img_array, verbose=0)
    decoded = decode_predictions(preds, top=10)[0]

    best_category = "other"
    confidence = 0.0
    labels = [label.lower() for _, label, prob in decoded]
    probs = [prob for _, _, prob in decoded]

    for label, prob in zip(labels, probs):
        if prob > confidence:
            if any(k in label for k in ["jersey", "t-shirt", "shirt", "polo", "blouse", "sweatshirt"]):
                best_category = "shirt"; confidence = prob
            elif any(k in label for k in ["trousers", "jeans", "pants", "slacks", "leggings", "cargo"]):
                best_category = "trousers"; confidence = prob
            elif any(k in label for k in ["dress", "gown", "frock", "sundress", "maxi"]):
                best_category = "dress"; confidence = prob
            elif any(k in label for k in ["suit", "blazer", "jacket", "coat", "tuxedo", "military uniform"]):
                best_category = "suit" if "suit" in label or "tuxedo" in label else "jacket"
                confidence = prob
            elif any(k in label for k in ["sneaker", "shoe", "boot", "sandal", "loafer", "heel"]):
                best_category = "shoes"; confidence = prob
            elif any(k in label for k in ["necklace", "earring", "bracelet", "ring", "bangle", "anklet"]):
                best_category = "jewellery"; confidence = prob
            elif any(k in label for k in ["handbag", "purse", "backpack", "clutch"]):
                best_category = "bag"; confidence = prob

    # Fallback
    # if confidence < 0.25:
    #     best_category = "shirt"  # most common

    # DOMINANT COLOR — FIXED LINE BELOW
    img_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img_cv is not None and img_cv.size > 0:
        pixels = img_cv.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, _, centers = cv2.kmeans(pixels, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        dominant = centers[0].astype(int)
        color = '#%02x%02x%02x' % (dominant[2], dominant[1], dominant[0])  # BGR→RGB
    else:
        color = "#95a5a6"

    style = "formal" if best_category in ["suit", "jacket"] else "casual"
    material = "wool" if best_category in ["suit", "jacket"] else "cotton"

    return {
        "category": best_category,
        "color": color,
        "style": style,
        "material": material,
        "seasonality": "warm" if any(c in color.lower() for c in ["red", "orange", "brown"]) else "cool",
        "confidence": round(confidence, 3)
    }

async def extract_features(image_bytes: bytes) -> np.ndarray:
    img = Image.open(BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    img_array = tf_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    
    features = feature_model.predict(img_array, verbose=0)
    return features.flatten()

async def add_to_index(item_id: str, features: np.ndarray):
    faiss.normalize_L2(features.reshape(1, -1))
    index.add(features.reshape(1, -1))

async def search_index(query_features: np.ndarray, k: int = 5) -> List[str]:
    faiss.normalize_L2(query_features.reshape(1, -1))
    distances, indices = index.search(query_features.reshape(1, -1), k)
    return [str(i) for i in indices[0] if i != -1]