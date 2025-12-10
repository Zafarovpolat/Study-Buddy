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

class UserResponse(BaseModel):
    id: UUID
    telegram_id: int
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    subscription_tier: str
    daily_requests_count: int
    current_streak: Optional[int] = 0
    longest_streak: Optional[int] = 0
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
    user_id: Optional[UUID] = None  # ← ДОБАВЬ
    title: str
    material_type: str
    status: str
    folder_id: Optional[UUID] = None  # ← ДОБАВЬ
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

class MaterialDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    material_type: str
    status: str
    folder_id: Optional[UUID] = None
    group_id: Optional[UUID] = None  # ← ДОБАВЬ ЭТО!
    raw_content: Optional[str] = None
    original_filename: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    outputs: List[AIOutputResponse] = []
    
    class Config:
        from_attributes = True

# === API Responses ===
class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None