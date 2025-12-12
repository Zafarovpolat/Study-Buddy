# backend/app/api/routes/presentations.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.api.deps import get_current_user, get_db
from app.models import User
from app.services.presentation_service import presentation_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/presentations", tags=["presentations"])


class GeneratePresentationRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    num_slides: int = Field(default=10, ge=5, le=20)
    style: Literal["professional", "educational", "creative", "minimal"] = "professional"
    theme: Literal["blue", "green", "purple", "orange"] = "blue"


class PresentationPreviewResponse(BaseModel):
    title: str
    subtitle: Optional[str]
    slides_count: int
    slides: list


@router.post("/generate", response_model=PresentationPreviewResponse)
async def generate_presentation_structure(
    request: GeneratePresentationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерирует структуру презентации (превью)"""
    
    # Проверка Pro
    if not current_user.is_pro:
        raise HTTPException(
            status_code=403,
            detail="Генератор презентаций доступен только для Pro пользователей"
        )
    
    try:
        structure = await presentation_service.generate_presentation_structure(
            topic=request.topic,
            num_slides=request.num_slides,
            style=request.style
        )
        
        return PresentationPreviewResponse(
            title=structure.get("title", request.topic),
            subtitle=structure.get("subtitle"),
            slides_count=len(structure.get("slides", [])),
            slides=structure.get("slides", [])
        )
        
    except Exception as e:
        print(f"❌ Presentation generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_presentation(
    request: GeneratePresentationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерирует и скачивает PPTX файл"""
    
    if not current_user.is_pro:
        raise HTTPException(
            status_code=403,
            detail="Генератор презентаций доступен только для Pro пользователей"
        )
    
    try:
        # Генерируем структуру
        structure = await presentation_service.generate_presentation_structure(
            topic=request.topic,
            num_slides=request.num_slides,
            style=request.style
        )
        
        # Создаём PPTX
        pptx_file = presentation_service.create_pptx(structure, theme=request.theme)
        
        # Формируем имя файла
        filename = f"{request.topic[:50].replace(' ', '_')}.pptx"
        
        return StreamingResponse(
            pptx_file,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        print(f"❌ Presentation download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))