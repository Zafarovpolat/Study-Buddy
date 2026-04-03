# backend/app/utils/json.py
"""Утилиты для парсинга JSON из AI ответов"""

import re
import json


def parse_ai_json_response(text: str) -> dict:
    """
    Извлекает JSON из ответа AI, удаляя markdown code fences.
    AI часто оборачивает JSON в ```json ... ```
    """
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
