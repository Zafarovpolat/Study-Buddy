# backend/app/utils/tasks.py
"""Утилиты для фоновых задач — без импорта из main.py (избегаем circular import)"""

import asyncio

_background_tasks: set[asyncio.Task] = set()


def schedule_background_task(coro):
    """Создать фоновую задачу с отслеживанием для graceful shutdown"""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def get_background_tasks():
    """Получить набор фоновых задач (для graceful shutdown в main.py)"""
    return _background_tasks
