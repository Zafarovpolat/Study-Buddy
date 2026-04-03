# backend/app/api/deps.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import asyncio
import hmac
import hashlib
from urllib.parse import parse_qsl, urlencode

from app.models import get_db, User
from app.services import UserService
from app.core.config import settings


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """HMAC-SHA256 валидация Telegram initData"""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise ValueError("No hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(
        b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
    ).digest()

    computed_hash = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid HMAC signature")

    return parsed


async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Получение текущего пользователя с HMAC-валидацией Telegram initData.
    """

    telegram_id = None

    # Dev режим: используем X-User-ID (без HMAC)
    if settings.DEBUG and x_user_id:
        try:
            telegram_id = int(x_user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid X-User-ID")

    # Production: парсим и ВАЛИДИРУЕМ Telegram initData
    elif x_telegram_init_data:
        try:
            import json

            parsed_data = verify_telegram_init_data(
                x_telegram_init_data, settings.TELEGRAM_BOT_TOKEN
            )
            user_data = json.loads(parsed_data.get("user", "{}"))
            telegram_id = user_data.get("id")

            if not telegram_id:
                raise ValueError("No user ID in initData")
        except ValueError as e:
            raise HTTPException(
                status_code=401, detail=f"Invalid Telegram init data: {e}"
            )
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
                await asyncio.sleep(0.5)
                continue
            raise HTTPException(
                status_code=503, detail="Сервис временно недоступен. Попробуйте снова."
            )
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка")


get_current_user_dev = get_current_user
