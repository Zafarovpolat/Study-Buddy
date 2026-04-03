# backend/app/utils/text.py
"""Утилиты для обработки текста"""

import re


def clean_text_for_db(text: str) -> str:
    """Очищает текст от символов, несовместимых с PostgreSQL UTF-8"""
    if not text:
        return ""

    # Удаляем null-байты
    text = text.replace("\x00", "")

    # Удаляем другие проблемные control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Заменяем невалидные UTF-8 символы
    text = text.encode("utf-8", errors="replace").decode("utf-8")

    return text
