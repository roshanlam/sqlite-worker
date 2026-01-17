"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ItemCreate(BaseModel):
    """Model for creating an item"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    value: float = Field(default=0.0, ge=0)


class ItemUpdate(BaseModel):
    """Model for updating an item"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    value: Optional[float] = Field(None, ge=0)


class Item(BaseModel):
    """Model for item response"""
    id: int
    name: str
    description: Optional[str]
    value: float
    created_at: datetime
