# backend/app/api/routes/search.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.models import get_db, User
from app.services.vector_service import VectorService
from app.api.deps import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


class AskLibraryRequest(BaseModel):
    question: str
    material_id: Optional[str] = None  # Если указан — ищем только в этом материале


class SearchResult(BaseModel):
    material_id: str
    material_title: str
    content: str
    similarity: float


class AskLibraryResponse(BaseModel):
    answer: str
    sources: List[dict]


@router.post("/ask", response_model=AskLibraryResponse)
async def ask_library(
    request: AskLibraryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Спроси свою библиотеку — RAG поиск"""
    
    # Проверяем доступ к фиче
    if not current_user.can_use_feature('vector_search'):
        raise HTTPException(
            status_code=403, 
            detail="Vector Search доступен только в Pro подписке"
        )
    
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Вопрос слишком короткий")
    
    vector_service = VectorService(db)
    result = await vector_service.ask_library(current_user.id, request.question)
    
    return result


@router.get("/semantic")
async def semantic_search(
    q: str,
    limit: int = 10,
    material_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Семантический поиск по материалам"""
    
    if not current_user.can_use_feature('vector_search'):
        raise HTTPException(
            status_code=403,
            detail="Семантический поиск доступен только в Pro подписке"
        )
    
    if not q or len(q.strip()) < 2:
        return []
    
    vector_service = VectorService(db)
    
    material_uuid = UUID(material_id) if material_id else None
    
    results = await vector_service.search(
        user_id=current_user.id,
        query=q,
        limit=limit,
        material_id=material_uuid
    )
    
    return results


@router.post("/index/{material_id}")
async def index_material(
    material_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Проиндексировать материал для vector search"""
    from sqlalchemy import select
    from app.models import Material
    
    # Проверяем доступ
    result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.user_id == current_user.id
        )
    )
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    if not material.raw_content:
        raise HTTPException(status_code=400, detail="Материал не содержит текста")
    
    vector_service = VectorService(db)
    chunks_count = await vector_service.index_material(
        material_id=material.id,
        user_id=current_user.id,
        content=material.raw_content
    )
    
    return {"success": True, "chunks_indexed": chunks_count}