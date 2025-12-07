# backend/app/api/routes/outputs.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from app.models import get_db, User, AIOutput, Material, OutputFormat
from app.api.deps import get_current_user

router = APIRouter(prefix="/outputs", tags=["outputs"])


async def check_material_access(
    material: Material, 
    current_user: User, 
    db: AsyncSession
) -> bool:
    """Проверить доступ к материалу (владелец или участник группы)"""
    # Владелец
    if material.user_id == current_user.id:
        return True
    
    # Участник группы
    if material.folder_id:
        from app.services.group_service import GroupService
        group_service = GroupService(db)
        groups = await group_service.get_user_groups(current_user)
        if any(g["id"] == str(material.folder_id) for g in groups):
            return True
    
    return False


@router.get("/material/{material_id}")
async def get_material_outputs(
    material_id: UUID,
    format: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все AI-выводы для материала"""
    
    # Загружаем материал без фильтра по user_id
    material_result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    material = material_result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    # Проверяем доступ
    has_access = await check_material_access(material, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к материалу")
    
    # Загружаем outputs
    query = select(AIOutput).where(AIOutput.material_id == material_id)
    
    if format:
        try:
            format_enum = OutputFormat(format)
            query = query.where(AIOutput.format == format_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат")
    
    result = await db.execute(query.order_by(AIOutput.created_at))
    outputs = result.scalars().all()
    
    return {
        "material_id": str(material_id),
        "material_title": material.title,
        "outputs": [
            {
                "id": str(o.id),
                "format": o.format.value,
                "content": o.content,
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in outputs
        ]
    }


@router.get("/{output_id}")
async def get_output(
    output_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить конкретный AI-вывод"""
    
    # Загружаем output с материалом
    result = await db.execute(
        select(AIOutput)
        .options(selectinload(AIOutput.material))
        .where(AIOutput.id == output_id)
    )
    output = result.scalar_one_or_none()
    
    if not output:
        raise HTTPException(status_code=404, detail="Не найдено")
    
    # Проверяем доступ через материал
    has_access = await check_material_access(output.material, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    return {
        "id": str(output.id),
        "material_id": str(output.material_id),
        "format": output.format.value,
        "content": output.content,
        "created_at": output.created_at.isoformat() if output.created_at else None
    }