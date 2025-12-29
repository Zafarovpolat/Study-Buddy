# backend/app/api/routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.models import get_db, User, SubscriptionTier
from app.services import UserService
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "API работает!"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "id": str(current_user.id),
        "telegram_id": current_user.telegram_id,
        "telegram_username": current_user.telegram_username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "subscription_tier": current_user.subscription_tier,  # Уже строка!
        "is_pro": current_user.is_pro,
        "daily_requests": current_user.daily_requests or 0,
        "current_streak": current_user.current_streak or 0,
        "longest_streak": current_user.longest_streak or 0,
        "referral_code": current_user.referral_code,
        "referral_count": current_user.referral_count or 0,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.get("/me/limits")
async def get_my_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о лимитах"""
    user_service = UserService(db)
    can_proceed, remaining = await user_service.check_rate_limit(current_user)
    
    # subscription_tier — это строка, не enum!
    is_free = current_user.subscription_tier == SubscriptionTier.FREE
    
    return {
        "subscription_tier": current_user.subscription_tier,
        "is_pro": current_user.is_pro,
        "can_make_request": can_proceed,
        "remaining_today": remaining if is_free else -1,
        "daily_limit": current_user.daily_limit if is_free else -1,
        "daily_used": current_user.daily_requests or 0,
    }


@router.get("/me/subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статус подписки"""
    from app.services.payment_service import PaymentService
    
    payment_service = PaymentService(db)
    status = await payment_service.check_subscription_status(current_user)
    
    return status


@router.get("/me/streak")
async def get_my_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о streak"""
    user_service = UserService(db)
    streak_info = await user_service.get_streak_info(current_user)
    
    return streak_info


# ==================== DEBUG ENDPOINTS ====================

@router.post("/debug/grant-pro")
async def grant_pro_for_testing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime, timedelta
    
    current_user.subscription_tier = SubscriptionTier.PRO
    current_user.subscription_expires_at = datetime.now() + timedelta(days=7)
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Pro подписка выдана на 7 дней",
        "expires_at": current_user.subscription_expires_at.isoformat()
    }


@router.post("/debug/reset-limits")
async def debug_reset_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.daily_requests = 0  # ← Правильное имя!
    await db.commit()
    
    return {"success": True, "message": "Лимиты сброшены", "remaining": settings.FREE_DAILY_LIMIT}

class UpdatePreferencesRequest(BaseModel):
    field_of_study: Optional[str] = None
    region: Optional[str] = None
    preferred_language: Optional[str] = None

@router.patch("/me/preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить персонализацию пользователя"""
    if request.field_of_study:
        current_user.field_of_study = request.field_of_study
    if request.region:
        current_user.region = request.region
    if request.preferred_language:
        current_user.preferred_language = request.preferred_language
    
    current_user.onboarding_completed = True
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "user": {
            "field_of_study": current_user.field_of_study,
            "region": current_user.region,
            "onboarding_completed": current_user.onboarding_completed
        }
    }

@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user)
):
    """Получить статистику пользователя"""
    return {
        "intellect_points": current_user.intellect_points or 0,
        "total_debates": current_user.total_debates or 0,
        "debates_won": current_user.debates_won or 0,
        "quizzes_completed": current_user.quizzes_completed or 0,
        "perfect_quizzes": current_user.perfect_quizzes or 0,
        "current_streak": current_user.current_streak or 0,
        "longest_streak": current_user.longest_streak or 0,
    }