# backend/app/api/routes/materials.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.models import get_db, User, Material, Folder, AIOutput, ProcessingStatus, MaterialType, AsyncSessionLocal
from app.services import UserService, MaterialService
from app.api.schemas import MaterialResponse, MaterialDetailResponse, SuccessResponse
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/materials", tags=["materials"])


# ==================== Schemas ====================

class UpdateMaterialRequest(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[UUID] = None

class GenerateFromTopicRequest(BaseModel):
    topic: str
    folder_id: Optional[str] = None
    group_id: Optional[str] = None


# ==================== Upload Endpoints ====================

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
    """Загрузить материал — обработка в фоне"""
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
    await db.commit()  # Сразу коммитим!
    
    # Запускаем обработку В ФОНЕ — не блокируем ответ
    if auto_process:
        import asyncio
        asyncio.create_task(
            process_material_background(
                material_id=material.id,
                group_id=group_id,
                user_telegram_id=current_user.telegram_id,
                user_first_name=current_user.first_name
            )
        )
    
    # Возвращаем сразу! Статус будет "pending"
    return material

async def process_material_background(
    material_id: UUID,
    group_id: Optional[UUID],
    user_telegram_id: int,
    user_first_name: Optional[str]
):
    """Фоновая обработка материала"""
    from app.models import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Material).where(Material.id == material_id)
            )
            material = result.scalar_one_or_none()
            
            if not material:
                print(f"❌ Material {material_id} not found")
                return
            
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService(db)
            await processing_service.process_material(material)
            await db.commit()
            
            print(f"✅ Background processing complete: {material_id}")
            
            # Уведомления
            if group_id and material.status == ProcessingStatus.COMPLETED:
                await send_group_notification(
                    db, group_id, material.title, 
                    user_first_name, user_telegram_id
                )
                
        except Exception as e:
            print(f"❌ Background processing error: {e}")
            import traceback
            traceback.print_exc()
            
            # Помечаем как failed
            try:
                result = await db.execute(
                    select(Material).where(Material.id == material_id)
                )
                material = result.scalar_one_or_none()
                if material:
                    material.status = ProcessingStatus.FAILED
                    await db.commit()
            except:
                pass

async def generate_topic_background(
    material_id: UUID,
    topic: str,
    group_id: Optional[UUID],
    user_telegram_id: int,
    user_first_name: Optional[str]
):
    """Фоновая генерация по теме"""
    from app.models import AsyncSessionLocal
    from app.services.ai_service import gemini_service
    from app.services.text_extractor import clean_text_for_db
    
    async with AsyncSessionLocal() as db:
        try:
            print(f"🎯 Background generating: {topic}")
            
            # Генерируем контент
            generated_content = await gemini_service.generate_content_from_topic(topic)
            generated_content = clean_text_for_db(generated_content)
            
            # Обновляем материал
            result = await db.execute(
                select(Material).where(Material.id == material_id)
            )
            material = result.scalar_one_or_none()
            
            if not material:
                print(f"❌ Material {material_id} not found")
                return
            
            material.raw_content = generated_content
            await db.commit()
            
            # Обрабатываем (генерируем конспекты, тесты и тд)
            from app.services.processing_service import ProcessingService
            processing_service = ProcessingService(db)
            await processing_service.process_material(material)
            await db.commit()
            
            print(f"✅ Background generation complete: {material_id}")
            
            # Уведомления
            if group_id and material.status == ProcessingStatus.COMPLETED:
                await send_group_notification(
                    db, group_id, material.title,
                    user_first_name, user_telegram_id
                )
                
        except Exception as e:
            print(f"❌ Background generation error: {e}")
            import traceback
            traceback.print_exc()
            
            # Помечаем как failed
            try:
                result = await db.execute(
                    select(Material).where(Material.id == material_id)
                )
                material = result.scalar_one_or_none()
                if material:
                    material.status = ProcessingStatus.FAILED
                    await db.commit()
            except:
                pass

async def send_group_notification(
    db: AsyncSession,
    group_id: UUID,
    material_title: str,
    user_first_name: Optional[str],
    user_telegram_id: int
):
    """Отправка уведомлений группе"""
    try:
        from app.services.notification_service import NotificationService
        from app.services.group_service import GroupService
        from app.main import bot_app
        
        if not bot_app:
            return
        
        group_service = GroupService(db)
        members = await group_service.get_group_members(group_id)
        member_ids = [m.get("telegram_id") for m in members if m.get("telegram_id")]
        
        group = await group_service.get_group_by_id(group_id)
        group_name = group.name if group else "Группа"
        
        notification_service = NotificationService(db)
        sent = await notification_service.send_group_material_notification(
            group_name=group_name,
            material_title=material_title,
            uploader_name=user_first_name or "Участник",
            member_telegram_ids=member_ids,
            exclude_user_id=user_telegram_id,
            bot=bot_app.bot
        )
        print(f"📨 Notified {sent} members")
    except Exception as e:
        print(f"⚠️ Notification error: {e}")

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
    
    try:
        from app.services.processing_service import ProcessingService
        processing_service = ProcessingService(db)
        await processing_service.process_material(material)
        await db.refresh(material)
    except Exception as e:
        print(f"Processing error: {e}")
    
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


@router.post("/generate-from-topic", response_model=MaterialResponse)
async def generate_from_topic(
    request: GenerateFromTopicRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация по теме — в фоне"""
    user_service = UserService(db)
    can_proceed, _ = await user_service.check_rate_limit(current_user)
    
    if not can_proceed:
        raise HTTPException(status_code=429, detail="Дневной лимит исчерпан")
    
    if len(request.topic.strip()) < 3:
        raise HTTPException(status_code=400, detail="Название темы слишком короткое")
    
    target_folder_id = None
    if request.folder_id:
        target_folder_id = UUID(request.folder_id)
    
    if request.group_id:
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if not any(g["id"] == request.group_id for g in groups):
            raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
        target_folder_id = UUID(request.group_id)
    
    # Создаём материал со статусом processing
    material_service = MaterialService(db)
    material = Material(
        user_id=current_user.id,
        title=request.topic,
        material_type=MaterialType.TXT,
        folder_id=target_folder_id,
        status=ProcessingStatus.PROCESSING,
        raw_content=""  # Пока пустой
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    
    await user_service.increment_request_count(current_user)
    await db.commit()
    
    # Запускаем генерацию В ФОНЕ
    import asyncio
    asyncio.create_task(
        generate_topic_background(
            material_id=material.id,
            topic=request.topic,
            group_id=UUID(request.group_id) if request.group_id else None,
            user_telegram_id=current_user.telegram_id,
            user_first_name=current_user.first_name
        )
    )
    
    # Возвращаем сразу! Статус "processing"
    return material

# ==================== Get Endpoints ====================

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


@router.get("/search/all")
async def search_materials(
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск по всем доступным материалам"""
    if not q or len(q.strip()) < 2:
        return []
    
    search_query = f"%{q.strip().lower()}%"
    
    from app.services.group_service import GroupService
    group_service = GroupService(db)
    user_groups = await group_service.get_user_groups(current_user)
    group_ids = [UUID(g["id"]) for g in user_groups]
    
    conditions = [Material.user_id == current_user.id]
    
    if group_ids:
        conditions.append(Material.folder_id.in_(group_ids))
    
    result = await db.execute(
        select(Material)
        .where(
            or_(*conditions),
            func.lower(Material.title).like(search_query)
        )
        .order_by(Material.created_at.desc())
        .limit(limit)
    )
    
    materials = result.scalars().all()
    
    return [
        {
            "id": str(m.id),
            "title": m.title,
            "material_type": m.material_type.value,
            "status": m.status.value,
            "folder_id": str(m.folder_id) if m.folder_id else None,
            "created_at": m.created_at.isoformat(),
            "is_own": m.user_id == current_user.id
        }
        for m in materials
    ]


@router.get("/debug/groups-check")
async def debug_groups_check(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Временный endpoint для отладки"""
    from sqlalchemy import text
    
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


# ==================== Get Material by ID (должен быть ПОСЛЕ /search/all) ====================

@router.get("/{material_id}")
async def get_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить материал с AI-выводами"""
    result = await db.execute(
        select(Material)
        .options(
            selectinload(Material.outputs),
            selectinload(Material.folder)
        )
        .where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    has_access = False
    group_id = None
    
    if material.user_id == current_user.id:
        has_access = True
    
    if material.folder_id:
        if material.folder and material.folder.is_group:
            group_id = material.folder_id
        
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if any(g["id"] == str(material.folder_id) for g in groups):
            has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к материалу")
    
    return {
        "id": str(material.id),
        "user_id": str(material.user_id),
        "title": material.title,
        "material_type": material.material_type.value,
        "status": material.status.value,
        "folder_id": str(material.folder_id) if material.folder_id else None,
        "group_id": str(group_id) if group_id else None,
        "raw_content": material.raw_content,
        "original_filename": material.original_filename,
        "created_at": material.created_at.isoformat(),
        "updated_at": material.updated_at.isoformat() if material.updated_at else None,
        "outputs": [
            {
                "id": str(o.id),
                "format": o.format.value,
                "content": o.content,
                "created_at": o.created_at.isoformat()
            }
            for o in material.outputs
        ]
    }


# ==================== Update/Delete Endpoints ====================

@router.patch("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: UUID,
    request: UpdateMaterialRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить материал"""
    result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.user_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    if request.title is not None:
        material.title = request.title.strip()
    
    if request.folder_id is not None:
        folder_result = await db.execute(
            select(Folder).where(
                Folder.id == request.folder_id,
                Folder.user_id == current_user.id
            )
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            raise HTTPException(status_code=404, detail="Папка не найдена")
        material.folder_id = request.folder_id
    
    await db.commit()
    await db.refresh(material)
    
    return material


@router.patch("/{material_id}/move-to-root", response_model=MaterialResponse)
async def move_material_to_root(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Переместить материал в корень"""
    result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.user_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    material.folder_id = None
    await db.commit()
    await db.refresh(material)
    
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
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    await material_service.delete_material(material)
    
    return SuccessResponse(message="Удалено")


# ==================== Debug/Test Endpoints ====================

@router.post("/debug/test-notification")
async def test_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Тестовая отправка уведомления себе"""
    from app.main import bot_app
    
    if not bot_app:
        return {"error": "Bot not initialized"}
    
    try:
        await bot_app.bot.send_message(
            chat_id=current_user.telegram_id,
            text=(
                f"🧪 *Тестовое уведомление!*\n\n"
                f"Привет, {current_user.first_name or 'друг'}!\n"
                f"Твой telegram\\_id: `{current_user.telegram_id}`\n\n"
                f"✅ Уведомления работают!"
            ),
            parse_mode="Markdown"
        )
        return {"success": True, "sent_to": current_user.telegram_id}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}