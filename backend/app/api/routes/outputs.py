# backend/app/api/routes/outputs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from app.models import get_db, User, AIOutput, Material
from app.api.deps import get_current_user

router = APIRouter(prefix="/outputs", tags=["outputs"])


def get_val(v):
    """Безопасно получить value из enum или вернуть строку"""
    return v.value if hasattr(v, 'value') else v


async def check_material_access(
    material: Material, 
    current_user: User, 
    db: AsyncSession
) -> bool:
    if material.user_id == current_user.id:
        return True
    
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
    material_result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    material = material_result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    has_access = await check_material_access(material, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к материалу")
    
    query = select(AIOutput).where(AIOutput.material_id == material_id)
    
    if format:
        query = query.where(AIOutput.format == format)
    
    result = await db.execute(query.order_by(AIOutput.created_at))
    outputs = result.scalars().all()
    
    return {
        "material_id": str(material_id),
        "material_title": material.title,
        "outputs": [
            {
                "id": str(o.id),
                "format": get_val(o.format),
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
    result = await db.execute(
        select(AIOutput)
        .options(selectinload(AIOutput.material))
        .where(AIOutput.id == output_id)
    )
    output = result.scalar_one_or_none()
    
    if not output:
        raise HTTPException(status_code=404, detail="Не найдено")
    
    has_access = await check_material_access(output.material, current_user, db)
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    return {
        "id": str(output.id),
        "material_id": str(output.material_id),
        "format": get_val(output.format),
        "content": output.content,
        "created_at": output.created_at.isoformat() if output.created_at else None
    }