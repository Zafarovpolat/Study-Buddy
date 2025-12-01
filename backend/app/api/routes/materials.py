# backend/app/api/routes/materials.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.models import get_db, User, ProcessingStatus, MaterialType
from app.services import UserService, MaterialService
from app.api.schemas import MaterialResponse, MaterialDetailResponse, SuccessResponse
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/materials", tags=["materials"])


@router.post("/upload", response_model=MaterialResponse)
async def upload_material(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    folder_id: Optional[UUID] = Form(None),
    auto_process: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузить и обработать материал"""
    # Проверяем лимиты
    user_service = UserService(db)
    can_proceed, remaining = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(
            status_code=429,
            detail="Daily limit reached. Upgrade to Pro for unlimited access."
        )
    
    # Проверяем размер файла
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Определяем тип и сохраняем
    material_service = MaterialService(db)
    material_type = material_service.detect_material_type(file.filename)
    
    file_path = await material_service.save_uploaded_file(
        content, file.filename, current_user.id
    )
    
    # Создаём материал
    material = await material_service.create_material(
        user=current_user,
        title=title or file.filename,
        material_type=material_type,
        file_path=file_path,
        original_filename=file.filename,
        folder_id=folder_id
    )
    
    # Увеличиваем счётчик
    await user_service.increment_request_count(current_user)
    
    # Автоматическая обработка
    if auto_process:
        try:
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService(db)
            await processing_service.process_material(material)
            await db.refresh(material)
        except Exception as e:
            print(f"Processing error: {e}")
    
    return material


@router.post("/text", response_model=MaterialResponse)
async def create_text_material(
    title: str = Form(...),
    content: str = Form(...),
    folder_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать материал из текста"""
    user_service = UserService(db)
    can_proceed, _ = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(status_code=429, detail="Daily limit reached")
    
    material_service = MaterialService(db)
    
    material = await material_service.create_material(
        user=current_user,
        title=title,
        material_type=MaterialType.TXT,
        folder_id=folder_id,
        raw_content=content
    )
    
    await user_service.increment_request_count(current_user)
    
    # Автоматическая обработка
    try:
        from app.services.processing_service import ProcessingService
        processing_service = ProcessingService(db)
        await processing_service.process_material(material)
        await db.refresh(material)
    except Exception as e:
        print(f"Processing error: {e}")
    
    return material


@router.get("/", response_model=List[MaterialResponse])
async def list_materials(
    folder_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список материалов"""
    material_service = MaterialService(db)
    materials = await material_service.get_user_materials(
        user_id=current_user.id,
        folder_id=folder_id,
        limit=limit,
        offset=offset
    )
    return materials


@router.get("/{material_id}", response_model=MaterialDetailResponse)
async def get_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить материал с AI-выводами"""
    material_service = MaterialService(db)
    material = await material_service.get_by_id(material_id, current_user.id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return material


@router.delete("/{material_id}", response_model=SuccessResponse)
async def delete_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить материал"""
    material_service = MaterialService(db)
    material = await material_service.get_by_id(material_id, current_user.id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    await material_service.delete_material(material)
    
    return SuccessResponse(message="Material deleted successfully")