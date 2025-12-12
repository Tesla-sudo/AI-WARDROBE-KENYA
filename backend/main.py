# backend/main.py
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from fastapi import HTTPException, status
import jwt

# Import your wardrobe routes
from routes.wardrobe import router as wardrobe_router

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="AI Wardrobe Kenya API",
    description="Smart wardrobe management with AI classification, visual search & outfit recommendations",
    version="1.0.0"
)

# CORS setup — adjust origins when deploying
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # Add your production domain later, e.g.:
        # "https://wardrobe-ai-kenya.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MongoDB client
client: AsyncIOMotorClient | None = None
DATABASE_NAME = "wardrobe_ai_kenya"  # Change only change this if you want a different DB name


@app.on_event("startup")
async def startup_db_client():
    global client
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        print("ERROR: MONGO_URI is not set in .env file!")
        raise RuntimeError("Missing MONGO_URI in environment variables")

    try:
        print("Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongo_uri)

        # Test the connection with a ping
        await client.admin.command("ping")
        
        # Set default database
        app.state.db = client[DATABASE_NAME]
        
        print("SUCCESS: Connected to MongoDB!")
        print(f"   Database: {DATABASE_NAME}")
        print(f"   URI: {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}")

    except Exception as e:
        print("FAILED: Could not connect to MongoDB")
        print(f"   Error: {e}")
        raise  # This stops the server if DB fails


@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")


# Include API routes
app.include_router(wardrobe_router, prefix="/api/wardrobe")

# In main.py — you can add this if you want zero warnings
import warnings
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Wardrobe Kenya API is running!",
        "docs": "/docs",
        "status": "healthy"
    }

# Temporary secret (same as in .env)
# TEMP_SECRET = "V+k9ewA5Xyr0HGIVvUJnQdGE5ThtafCYqi4Ya4blR/A="  # ← Must match JWT_SECRET in .env

@app.post("/api/auth/login-dummy")
async def login_dummy():
    # This gives you a valid token instantly (no password needed)
    payload = {
        "_id": "6709fb7cd0f4d6003d1fb7cdc",
        "email": "test@kenya.com",
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    return {"token": token, "user_id": payload["_id"]}