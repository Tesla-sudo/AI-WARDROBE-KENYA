
### Project Documentation 

# Project Overview: AI Wardrobe Kenya

## Introduction
This app helps Kenyans manage wardrobes, reduce impulse buys, promote sustainability, and leverage mitumba. Built with FastAPI (backend), React (frontend), MongoDB, TensorFlow, FAISS, Cloudinary.

## Features (Up to Week 3)
- **Auth**: JWT for user sessions (dummy login).
- **Wardrobe Upload**: Upload clothes → AI auto-tags category/color/style → save to MongoDB/Cloudinary.
- **Visual Search**: Upload image → find similar in wardrobe via FAISS.
- **Get Items**: List user's wardrobe.

## Architecture
- **Frontend**: React with AuthContext, React Query for API, Dropzone for uploads. Routes: /login, /wardrobe, /visual-search.
- **Backend**: FastAPI endpoints (/api/wardrobe/upload, /visual-search, /my-items). Async MongoDB. AI in ai_utils.py.
- **DB Schema** (models.py):
  - User: email, password, location, points.
  - WardrobeItem: user_id, image_url, category, color, features (vector).
- **AI Flow**: MobileNetV2 predicts labels → map to fashion categories → extract color with OpenCV → feature vector for FAISS.
- **Security**: JWT validation, CORS.
- **Storage**: Cloudinary for images.

## How It Works
1. User logs in → gets JWT.
2. Upload: Frontend sends file → backend validates token → uploads to Cloudinary → AI processes → saves to DB → indexes in FAISS → returns ID.
3. Visual Search: Upload → extract features → FAISS search → fetch DB items → return.
4. Future: Add weather, trends, outfits (Week 4).

## Extension Ideas
- Add real login/register.
- Integrate weather API for seasonality.
- Trend scraper for Instagram.
- Outfit generator using rules/ML.

## Known Issues
- Category "other" for uncommon items — improve with custom model.
- FAISS resets on restart — persist to file.

