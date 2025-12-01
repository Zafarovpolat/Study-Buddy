# backend/app/api/routes/outputs.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.models import get_db, User, AIOutput, Material, OutputFormat
from app.api.deps import get_current_user

router = APIRouter(prefix="/outputs", tags=["outputs"])


@router.get("/material/{material_id}")
async def get_material_outputs(
    material_id: UUID,
    format: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все AI-выводы для материала"""
    material_result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.user_id == current_user.id
        )
    )
    material = material_result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    query = select(AIOutput).where(AIOutput.material_id == material_id)
    
    if format:
        try:
            format_enum = OutputFormat(format)
            query = query.where(AIOutput.format == format_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid format")
    
    result = await db.execute(query)
    outputs = result.scalars().all()
    
    return {
        "material_id": str(material_id),
        "material_title": material.title,
        "outputs": [
            {
                "id": str(o.id),
                "format": o.format.value,
                "content": o.content,
                "created_at": o.created_at.isoformat()
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
    result = await db.execute(
        select(AIOutput)
        .join(Material)
        .where(
            AIOutput.id == output_id,
            Material.user_id == current_user.id
        )
    )
    output = result.scalar_one_or_none()
    
    if not output:
        raise HTTPException(status_code=404, detail="Output not found")
    
    return {
        "id": str(output.id),
        "material_id": str(output.material_id),
        "format": output.format.value,
        "content": output.content,
        "created_at": output.created_at.isoformat()
    }