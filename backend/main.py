# backend/main.py
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Import routes
from routes.auth import router as auth_router
from routes.wardrobe import router as wardrobe_router

load_dotenv()

app = FastAPI(
    title="AI Wardrobe Kenya API",
    description="Smart wardrobe management with AI classification, visual search, trend matching, and sustainable fashion insights.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS Configuration ───────────────────────────────────────────────────────
# In production: replace with your actual frontend domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # "https://your-production-frontend.com",  # ← add real domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global MongoDB Client ────────────────────────────────────────────────────
client: Optional[AsyncIOMotorClient] = None
DATABASE_NAME = "wardrobe_ai_kenya"

@app.on_event("startup")
async def startup_db_client():
    global client
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not set in .env file!")

    try:
        print("Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongo_uri)
        # Test connection
        await client.admin.command("ping")
        app.state.db = client[DATABASE_NAME]
        print(f"✓ Successfully connected to MongoDB - Database: {DATABASE_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        print("MongoDB connection closed gracefully.")


# ── Include Routers ──────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(wardrobe_router, prefix="/api/wardrobe", tags=["Wardrobe"])


# ── Root & Health Check ──────────────────────────────────────────────────────
@app.get("/", tags=["General"])
async def root():
    """API root endpoint"""
    return {
        "message": "AI Wardrobe Kenya API is running!",
        "docs": "/docs",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint (used for monitoring/load balancers)"""
    db_status = "connected" if app.state.db else "disconnected"
    return JSONResponse(
        content={
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        },
        status_code=status.HTTP_200_OK
    )


# ── Global Exception Handler (optional – nice for production) ────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if os.getenv("ENV") == "development" else None
        },
    )