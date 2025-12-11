# backend/app/api/deps.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import asyncio

from app.models import get_db, User
from app.services import UserService
from app.core.config import settings


async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя.
    """
    
    telegram_id = None
    
    # Dev режим: используем X-User-ID
    if settings.DEBUG and x_user_id:
        try:
            telegram_id = int(x_user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid X-User-ID")
    
    # Production: парсим Telegram initData
    elif x_telegram_init_data:
        try:
            from urllib.parse import parse_qsl
            import json
            
            parsed_data = dict(parse_qsl(x_telegram_init_data, keep_blank_values=True))
            user_data = json.loads(parsed_data.get('user', '{}'))
            telegram_id = user_data.get('id')
        except Exception as e:
            print(f"Error parsing Telegram data: {e}")
            raise HTTPException(status_code=401, detail="Invalid Telegram init data")
    
    # Fallback для dev
    if not telegram_id:
        if settings.DEBUG:
            telegram_id = 123456789
        else:
            raise HTTPException(status_code=401, detail="Authentication required")
    
    # Получаем или создаём пользователя с retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            user_service = UserService(db)
            user, is_new = await user_service.get_or_create(telegram_id=telegram_id)
            
            if is_new:
                print(f"✅ Created new user: {telegram_id}")
            
            return user
            
        except SQLAlchemyError as e:
            print(f"⚠️ DB error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)  # Ждём перед retry
                continue
            raise HTTPException(
                status_code=503, 
                detail="Сервис временно недоступен. Попробуйте снова."
            )
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка")


get_current_user_dev = get_current_user