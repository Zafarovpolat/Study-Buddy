# backend/app/api/routes/presentations.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
import urllib.parse
import re

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


def sanitize_filename(filename: str) -> str:
    """Очищает имя файла от проблемных символов"""
    # Транслитерация кириллицы
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
    
    result = ""
    for char in filename:
        if char in translit_map:
            result += translit_map[char]
        elif char.isalnum() or char in ' ._-':
            result += char
        else:
            result += '_'
    
    # Убираем множественные пробелы/подчеркивания
    result = re.sub(r'[_\s]+', '_', result)
    result = result.strip('_')
    
    return result[:50] if result else "presentation"


@router.post("/generate", response_model=PresentationPreviewResponse)
async def generate_presentation_structure(
    request: GeneratePresentationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерирует структуру презентации (превью)"""
    
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
        print(f"Presentation generation error: {e}")
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
        
        # Безопасное имя файла (ASCII only)
        safe_filename = sanitize_filename(request.topic) + ".pptx"
        
        # URL-encoded имя для UTF-8 поддержки в современных браузерах
        encoded_filename = urllib.parse.quote(request.topic[:50] + ".pptx")
        
        return StreamingResponse(
            pptx_file,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                # ASCII fallback + UTF-8 encoded version
                "Content-Disposition": f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except Exception as e:
        print(f"Presentation download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))