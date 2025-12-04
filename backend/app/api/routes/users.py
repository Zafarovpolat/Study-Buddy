# backend/app/api/routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db, User
from app.services import UserService
from app.api.schemas import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/test")
async def test_endpoint():
    """Тестовый endpoint"""
    return {"status": "ok", "message": "API работает!"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.get("/me/limits")
async def get_my_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о лимитах"""
    user_service = UserService(db)
    can_proceed, remaining = await user_service.check_rate_limit(current_user)
    
    return {
        "subscription_tier": current_user.subscription_tier.value,
        "can_make_request": can_proceed,
        "remaining_today": remaining if remaining >= 0 else "unlimited",
        "daily_limit": 3 if current_user.subscription_tier.value == "free" else "unlimited"
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


# ⚠️ ТЕСТОВЫЙ ENDPOINT - УДАЛИТЬ В ПРОДАКШЕНЕ!
@router.post("/me/grant-pro")
async def grant_pro_for_testing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Временно выдать Pro подписку для тестирования"""
    from datetime import datetime, timedelta
    from app.models import SubscriptionTier
    
    current_user.subscription_tier = SubscriptionTier.PRO
    current_user.subscription_expires_at = datetime.now() + timedelta(days=7)
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Pro подписка выдана на 7 дней",
        "expires_at": current_user.subscription_expires_at.isoformat()
    }