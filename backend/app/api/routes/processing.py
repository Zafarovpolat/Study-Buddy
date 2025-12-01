# backend/app/api/routes/processing.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models import get_db, User, ProcessingStatus, OutputFormat
from app.services import MaterialService
from app.services.processing_service import ProcessingService
from app.api.deps import get_current_user
from app.api.schemas import SuccessResponse

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/material/{material_id}")
async def process_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Запустить обработку материала"""
    material_service = MaterialService(db)
    material = await material_service.get_by_id(material_id, current_user.id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if material.status == ProcessingStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Already processing")
    
    processing_service = ProcessingService(db)
    result = await processing_service.process_material(material)
    
    return result


@router.post("/material/{material_id}/regenerate/{output_format}")
async def regenerate_output(
    material_id: UUID,
    output_format: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Перегенерировать конкретный формат"""
    material_service = MaterialService(db)
    material = await material_service.get_by_id(material_id, current_user.id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    try:
        format_enum = OutputFormat(output_format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Available: {[f.value for f in OutputFormat]}"
        )
    
    processing_service = ProcessingService(db)
    output = await processing_service.regenerate_output(material, format_enum)
    
    return {
        "success": True,
        "output_id": str(output.id),
        "format": output.format.value
    }


@router.get("/material/{material_id}/status")
async def get_processing_status(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статус обработки"""
    material_service = MaterialService(db)
    material = await material_service.get_by_id(material_id, current_user.id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    outputs_info = [
        {"format": o.format.value, "id": str(o.id)}
        for o in material.outputs
    ]
    
    return {
        "material_id": str(material.id),
        "status": material.status.value,
        "outputs": outputs_info,
        "has_content": bool(material.raw_content)
    }