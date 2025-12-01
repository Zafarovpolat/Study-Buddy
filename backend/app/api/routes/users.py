# backend/app/api/routes/users.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_db, User
from app.services import UserService
from app.api.schemas import UserResponse, SuccessResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/test")
async def test_endpoint():
    """Тестовый endpoint без авторизации"""
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