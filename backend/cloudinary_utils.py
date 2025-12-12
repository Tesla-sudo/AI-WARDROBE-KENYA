# backend/cloudinary_utils.py
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def upload_to_cloudinary(image_bytes: bytes) -> str:
    response = cloudinary.uploader.upload(image_bytes, folder="wardrobe-items")
    return response["secure_url"]