# backend/app/api/routes/insights.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import get_db, User
from app.services.insight_service import InsightService
from app.api.deps import get_current_user

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/")
async def get_insights(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить инсайты для пользователя"""
    if not current_user.field_of_study:
        return []  # Пустой список если не настроен профиль
    
    service = InsightService(db)
    insights = await service.get_insights_for_user(current_user, region=region)
    
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "summary": i.summary,
            "importance": i.importance,
            "importance_reason": i.importance_reason,
            "academic_link": i.academic_link,
            "region": i.region,
            "source_name": i.source_name,
            "published_at": i.published_at.isoformat() if i.published_at else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in insights
    ]


@router.get("/{insight_id}")
async def get_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить инсайт по ID"""
    service = InsightService(db)
    insight = await service.get_insight_by_id(insight_id)
    
    if not insight:
        raise HTTPException(404, "Инсайт не найден")
    
    return {
        "id": str(insight.id),
        "title": insight.title,
        "summary": insight.summary,
        "importance": insight.importance,
        "importance_reason": insight.importance_reason,
        "academic_link": insight.academic_link,
        "original_content": insight.original_content,
        "source_url": insight.source_url,
        "source_name": insight.source_name,
    }


@router.get("/{insight_id}/detailed")
async def get_detailed_insight(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить детальный конспект по инсайту (Pro only)"""
    if current_user.subscription_tier == 'free':
        raise HTTPException(403, "Детальные инсайты доступны только в Pro")
    
    service = InsightService(db)
    insight = await service.get_insight_by_id(insight_id)
    
    if not insight:
        raise HTTPException(404, "Инсайт не найден")
    
    content = await service.generate_detailed_content(insight)
    
    return {"content": content}