# backend/app/api/routes/folders.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.models import get_db, User
from app.services import FolderService
from app.api.schemas import FolderCreate, FolderResponse, SuccessResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("/", response_model=FolderResponse)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать папку"""
    folder_service = FolderService(db)
    
    if folder_data.parent_id:
        parent = await folder_service.get_by_id(folder_data.parent_id, current_user.id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    
    folder = await folder_service.create_folder(
        user=current_user,
        name=folder_data.name,
        parent_id=folder_data.parent_id
    )
    
    return folder


@router.get("/", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список папок"""
    folder_service = FolderService(db)
    folders = await folder_service.get_user_folders(
        user_id=current_user.id,
        parent_id=parent_id
    )
    return folders


@router.delete("/{folder_id}", response_model=SuccessResponse)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить папку"""
    folder_service = FolderService(db)
    folder = await folder_service.get_by_id(folder_id, current_user.id)
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    await folder_service.delete_folder(folder)
    
    return SuccessResponse(message="Folder deleted successfully")