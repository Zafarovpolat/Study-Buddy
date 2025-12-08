# backend/app/api/routes/users.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db, User
from app.services import UserService
from app.api.schemas import UserResponse
from app.api.deps import get_current_user
from app.core.config import settings  # ДОБАВЛЕНО

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
    
    is_free = current_user.subscription_tier.value == "free"
    
    return {
        "subscription_tier": current_user.subscription_tier.value,
        "can_make_request": can_proceed,
        "remaining_today": remaining if is_free else "unlimited",
        "daily_limit": settings.FREE_DAILY_LIMIT if is_free else "unlimited"  # ИСПРАВЛЕНО
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
# ⚠️ УДАЛИТЬ В ПРОДАКШЕНЕ!

@router.post("/debug/grant-pro")
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


@router.post("/debug/reset-referral")
async def debug_reset_referral(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сбросить реферальные данные (только для тестов!)"""
    current_user.referred_by_id = None
    current_user.referral_count = 0
    current_user.referral_pro_granted = False
    await db.commit()
    
    return {"success": True, "message": "Реферальные данные сброшены"}


@router.post("/debug/reset-limits")
async def debug_reset_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сбросить дневной счётчик запросов"""
    current_user.daily_requests_count = 0
    await db.commit()
    
    return {"success": True, "message": "Лимиты сброшены", "remaining": settings.FREE_DAILY_LIMIT}


@router.delete("/debug/delete-me")
async def debug_delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить свой аккаунт (только для тестов!)"""
    user_id = str(current_user.id)
    await db.delete(current_user)
    await db.commit()
    
    return {"success": True, "message": f"Аккаунт {user_id} удалён"}

@router.delete("/debug/delete-all-users")
async def debug_delete_all_users(
    db: AsyncSession = Depends(get_db)
):
    """Удалить ВСЕХ пользователей (ТОЛЬКО ДЛЯ ТЕСТОВ!)"""
    from sqlalchemy import text
    
    # Получаем количество до удаления
    result = await db.execute(text("SELECT COUNT(*) FROM users"))
    count_before = result.scalar()
    
    # Удаляем всё каскадно
    await db.execute(text("TRUNCATE TABLE users CASCADE"))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Удалено {count_before} пользователей",
        "warning": "Все данные очищены!"
    }