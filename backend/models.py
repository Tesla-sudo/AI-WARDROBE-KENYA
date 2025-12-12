# backend/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: any, _handler: any):
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

class WardrobeItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")  # ← CHANGED: default_factory
    user_id: str
    image_url: str
    category: str
    color: str
    style: Optional[str] = "casual"
    material: Optional[str] = "unknown"
    seasonality: Optional[str] = "all-season"
    wear_count: int = 0
    last_worn: Optional[datetime] = None
    is_mitumba: bool = False
    upcycle_suggestions: List[str] = Field(default_factory=list)
    features: List[float]

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        arbitrary_types_allowed = True