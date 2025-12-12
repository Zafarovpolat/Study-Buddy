# backend/app/api/routes/debate.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from app.api.deps import get_current_user, get_db
from app.models import User, Material
from app.services.debate_service import debate_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/debate", tags=["debate"])


class StartDebateRequest(BaseModel):
    topic: str = Field(..., min_length=5, max_length=500)
    user_position: Literal["ЗА", "ПРОТИВ"] = "ЗА"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    material_id: Optional[str] = None


class ContinueDebateRequest(BaseModel):
    topic: str
    ai_position: str
    difficulty: Literal["easy", "medium", "hard"]
    history: List[dict]
    user_message: str = Field(..., min_length=1, max_length=2000)
    material_id: Optional[str] = None


class JudgeDebateRequest(BaseModel):
    topic: str
    history: List[dict]


@router.post("/start")
async def start_debate(
    request: StartDebateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Начать дебаты"""
    
    # Проверка Pro для hard режима
    if request.difficulty == "hard" and not current_user.is_pro:
        raise HTTPException(
            status_code=403,
            detail="Сложный режим доступен только для Pro"
        )
    
    # Получаем контент материала если указан
    material_content = ""
    if request.material_id:
        result = await db.execute(
            select(Material).where(Material.id == request.material_id)
        )
        material = result.scalar_one_or_none()
        if material and material.raw_content:
            material_content = material.raw_content
    
    result = await debate_service.start_debate(
        topic=request.topic,
        user_position=request.user_position,
        difficulty=request.difficulty,
        material_content=material_content
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ошибка"))
    
    return result


@router.post("/continue")
async def continue_debate(
    request: ContinueDebateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Продолжить дебаты"""
    
    # Получаем контент материала если указан
    material_content = ""
    if request.material_id:
        result = await db.execute(
            select(Material).where(Material.id == request.material_id)
        )
        material = result.scalar_one_or_none()
        if material and material.raw_content:
            material_content = material.raw_content
    
    result = await debate_service.continue_debate(
        topic=request.topic,
        ai_position=request.ai_position,
        difficulty=request.difficulty,
        history=request.history,
        user_message=request.user_message,
        material_content=material_content
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ошибка"))
    
    return result


@router.post("/judge")
async def judge_debate(
    request: JudgeDebateRequest,
    current_user: User = Depends(get_current_user)
):
    """Судья оценивает дебаты"""
    
    if len(request.history) < 4:
        raise HTTPException(
            status_code=400,
            detail="Нужно минимум 2 раунда для оценки"
        )
    
    result = await debate_service.judge_debate(
        topic=request.topic,
        history=request.history
    )
    
    return result