# backend/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema()
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

class WardrobeItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    image_url: str                    # Cloud storage URL (Cloudinary, S3, etc.)
    category: str
    color: str
    colors_palette: List[str] = Field(default_factory=list)
    style: str = "casual"
    material: str = "unknown"
    seasonality: str = "all-season"
    features: List[float] = Field(default_factory=list)  # FAISS vector as list
    wear_count: int = 0
    last_worn: Optional[datetime] = None

    # ── Mitumba & upcycling fields ──
    is_mitumba: bool = Field(
        default=False,
        description="Item is second-hand / from mitumba market"
    )
    purchase_price_kes: Optional[float] = Field(
        None,
        ge=0,
        description="Purchase price in KES if known"
    )
    purchase_date: Optional[datetime] = Field(
        None,
        description="Date when the item was purchased"
    )
    source_platform: Optional[str] = Field(
        None,
        description="Where it was bought, e.g. 'Gikomba', 'Toi Market', 'Jumia', 'Instagram shop', 'Kilimall'"
    )
    upcycle_suggestions: List[str] = Field(
        default_factory=list,
        description="AI or rule-based upcycling/repair ideas"
    )
    repair_cost_estimate_kes: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated repair/upcycle cost in KES"
    )
    fundi_recommended: Optional[str] = Field(
        None,
        description="Name/contact of recommended local tailor/fundi"
    )

    # Analytics helper fields
    times_suggested: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True