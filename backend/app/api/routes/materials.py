# backend/app/api/routes/materials.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID

from app.models import get_db, User, Material, AIOutput, ProcessingStatus, MaterialType
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
    group_id: Optional[UUID] = Form(None),
    auto_process: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Загрузить и обработать материал"""
    user_service = UserService(db)
    can_proceed, remaining = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(status_code=429, detail="Дневной лимит исчерпан")
    
    target_folder_id = folder_id
    if group_id:
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if not any(g["id"] == str(group_id) for g in groups):
            raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
        target_folder_id = group_id
    
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"Файл слишком большой. Макс: {settings.MAX_FILE_SIZE_MB}MB")
    
    material_service = MaterialService(db)
    material_type = material_service.detect_material_type(file.filename)
    
    file_path = await material_service.save_uploaded_file(content, file.filename, current_user.id)
    
    material = await material_service.create_material(
        user=current_user,
        title=title or file.filename,
        material_type=material_type,
        file_path=file_path,
        original_filename=file.filename,
        folder_id=target_folder_id
    )
    
    await user_service.increment_request_count(current_user)
    
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
    group_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать материал из текста"""
    user_service = UserService(db)
    can_proceed, _ = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(status_code=429, detail="Дневной лимит исчерпан")
    
    # Проверяем минимальную длину текста
    if len(content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Текст слишком короткий (минимум 10 символов)")
    
    target_folder_id = folder_id
    if group_id:
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if not any(g["id"] == str(group_id) for g in groups):
            raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
        target_folder_id = group_id
    
    material_service = MaterialService(db)
    
    material = await material_service.create_material(
        user=current_user,
        title=title,
        material_type=MaterialType.TXT,
        folder_id=target_folder_id,
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
        # Не падаем - материал создан, можно сгенерировать вручную
    
    return material


@router.post("/scan", response_model=MaterialResponse)
async def scan_image(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    folder_id: Optional[UUID] = Form(None),
    group_id: Optional[UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сканировать изображение"""
    user_service = UserService(db)
    can_proceed, _ = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(status_code=429, detail="Дневной лимит исчерпан")
    
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Только изображения: JPG, PNG, WebP")
    
    target_folder_id = folder_id
    if group_id:
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if not any(g["id"] == str(group_id) for g in groups):
            raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
        target_folder_id = group_id
    
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"Файл слишком большой")
    
    material_service = MaterialService(db)
    file_path = await material_service.save_uploaded_file(content, file.filename, current_user.id)
    
    material = await material_service.create_material(
        user=current_user,
        title=title or "Скан",
        material_type=MaterialType.IMAGE,
        file_path=file_path,
        original_filename=file.filename,
        folder_id=target_folder_id
    )
    
    await user_service.increment_request_count(current_user)
    
    try:
        from app.services.processing_service import ProcessingService
        processing_service = ProcessingService(db)
        await processing_service.process_material(material)
        await db.refresh(material)
    except Exception as e:
        print(f"Scan processing error: {e}")
        material.status = ProcessingStatus.FAILED
        await db.commit()
    
    return material


@router.get("/", response_model=List[MaterialResponse])
async def list_materials(
    folder_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить материалы пользователя"""
    material_service = MaterialService(db)
    materials = await material_service.get_user_materials(
        user_id=current_user.id,
        folder_id=folder_id,
        limit=limit,
        offset=offset
    )
    return materials


@router.get("/group/{group_id}", response_model=List[MaterialResponse])
async def get_group_materials(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить материалы группы"""
    from app.services.group_service import GroupService
    
    group_service = GroupService(db)
    groups = await group_service.get_user_groups(current_user)
    
    if not any(g["id"] == str(group_id) for g in groups):
        raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
    
    result = await db.execute(
        select(Material)
        .where(Material.folder_id == group_id)
        .order_by(Material.created_at.desc())
    )
    materials = result.scalars().all()
    
    return materials


@router.get("/{material_id}", response_model=MaterialDetailResponse)
async def get_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить материал с AI-выводами"""
    
    # Загружаем материал С outputs через selectinload
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.outputs))
        .where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    # Проверяем доступ - владелец или участник группы
    has_access = False
    
    if material.user_id == current_user.id:
        has_access = True
    elif material.folder_id:
        # Проверяем членство в группе
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if any(g["id"] == str(material.folder_id) for g in groups):
            has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к материалу")
    
    return material


# backend/app/api/routes/materials.py - ДОБАВЬ временно

@router.get("/debug/groups-check")
async def debug_groups_check(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Временный endpoint для отладки"""
    from sqlalchemy import text
    
    # Проверяем группы пользователя
    result = await db.execute(text("""
        SELECT 
            f.id as group_id,
            f.name as group_name,
            f.is_group,
            gm.user_id as member_id,
            gm.role
        FROM folders f
        LEFT JOIN group_members gm ON f.id = gm.group_id
        WHERE f.is_group = true
    """))
    groups_data = [dict(row._mapping) for row in result.fetchall()]
    
    # Проверяем материалы в группах
    result2 = await db.execute(text("""
        SELECT 
            m.id as material_id,
            m.title,
            m.folder_id,
            m.user_id as owner_id,
            f.name as folder_name,
            f.is_group
        FROM materials m
        LEFT JOIN folders f ON m.folder_id = f.id
        WHERE m.folder_id IS NOT NULL
    """))
    materials_data = [dict(row._mapping) for row in result2.fetchall()]
    
    return {
        "current_user_id": str(current_user.id),
        "groups_and_members": groups_data,
        "materials_in_folders": materials_data
    }

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
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    await material_service.delete_material(material)
    
    return SuccessResponse(message="Удалено")