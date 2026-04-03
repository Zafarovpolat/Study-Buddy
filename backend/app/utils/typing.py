# backend/app/utils/typing.py
"""Утилиты для работы с типами"""


def get_val(v):
    """Безопасное извлечение значения — работает и с Enum, и со строками"""
    return v.value if hasattr(v, "value") else v
