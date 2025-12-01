from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# === User Schemas ===
class UserBase(BaseModel):
    telegram_id: int
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    subscription_tier: str
    daily_requests_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Folder Schemas ===
class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None

class FolderResponse(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Material Schemas ===
class MaterialCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    folder_id: Optional[UUID] = None

class MaterialResponse(BaseModel):
    id: UUID
    title: str
    material_type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# === AI Output Schemas ===
class AIOutputResponse(BaseModel):
    id: UUID
    format: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MaterialDetailResponse(MaterialResponse):
    raw_content: Optional[str] = None
    outputs: List["AIOutputResponse"] = []

# === API Responses ===
class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None