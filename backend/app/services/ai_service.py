# backend/app/services/ai_service.py
import google.generativeai as genai
from typing import Optional
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

# Thread pool для CPU-bound операций (Gemini SDK синхронный!)
_executor = ThreadPoolExecutor(max_workers=4)


class GeminiService:
    """Сервис для работы с Gemini AI — НЕ БЛОКИРУЕТ event loop!"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            print(f"🤖 Gemini configured with model: {self.model_name}")
        else:
            print("⚠️ GEMINI_API_KEY not set!")
    
    def _get_model(self):
        """Получить модель Gemini"""
        return genai.GenerativeModel(self.model_name)
    
    def _generate_sync(self, prompt: str) -> str:
        """Синхронный вызов Gemini — выполняется в thread pool"""
        model = self._get_model()
        response = model.generate_content(prompt)
        return response.text
    
    async def _generate_async(self, prompt: str) -> str:
        """Асинхронная обёртка — НЕ блокирует event loop!"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._generate_sync, prompt)
    
    async def generate_content_from_topic(self, topic: str) -> str:
        """Генерация учебного материала по теме"""
        prompt = f"""Ты - эксперт-преподаватель. Создай подробный учебный материал по теме: "{topic}"

Структура материала:
1. Введение (что это, почему важно)
2. Основные понятия и определения
3. Ключевые аспекты темы (3-5 разделов)
4. Примеры и применение
5. Интересные факты
6. Заключение

Требования:
- Материал должен быть информативным и структурированным
- Используй понятный язык
- Добавь конкретные примеры
- Объём: 2000-3000 слов

Напиши материал:"""

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ Generate from topic error: {e}")
            raise
    
    async def generate_smart_notes(self, content: str, title: str = "") -> str:
        """Генерация умного конспекта"""
        prompt = f"""Создай структурированный конспект по материалу.

Название: {title}

Материал:
{content[:30000]}

Требования:
1. Выдели основные темы и подтемы
2. Используй маркированные списки
3. Выдели ключевые определения
4. Добавь примеры где уместно
5. Сохрани логическую структуру

Формат: Markdown с заголовками ##, списками -, выделением **жирным**."""

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ Smart notes error: {e}")
            raise
    
    async def generate_tldr(self, content: str) -> str:
        """Генерация краткого содержания"""
        prompt = f"""Напиши краткое содержание (TL;DR) этого материала в 3-5 предложениях.

Материал:
{content[:20000]}

Выдели самое важное. Будь конкретен."""

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ TLDR error: {e}")
            raise
    
    async def generate_quiz(self, content: str, num_questions: int = 15) -> str:
        """Генерация теста"""
        prompt = f"""Создай тест из {num_questions} вопросов по материалу.

Материал:
{content[:25000]}

Требования:
1. Разные типы: определения, понимание, применение
2. 30% лёгкие, 50% средние, 20% сложные
3. Правдоподобные варианты ответов

Формат JSON:
{{
  "questions": [
    {{
      "question": "Вопрос?",
      "options": ["A) вариант", "B) вариант", "C) вариант", "D) вариант"],
      "correct": 0,
      "explanation": "Пояснение",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

Создай ровно {num_questions} вопросов!
Верни ТОЛЬКО валидный JSON."""

        try:
            text = await self._generate_async(prompt)
            text = text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            parsed = json.loads(text)
            if len(parsed.get("questions", [])) < num_questions:
                print(f"⚠️ Only {len(parsed['questions'])} questions generated")
            
            return text
        except json.JSONDecodeError:
            return json.dumps({
                "questions": [{
                    "question": "Тест не удалось сгенерировать",
                    "options": ["Попробуйте снова"],
                    "correct": 0,
                    "explanation": "",
                    "difficulty": "easy"
                }]
            }, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Quiz error: {e}")
            raise
    
    async def generate_glossary(self, content: str) -> str:
        """Генерация глоссария"""
        prompt = f"""Создай глоссарий ключевых терминов.

Материал:
{content[:25000]}

Формат JSON:
{{
  "terms": [
    {{
      "term": "Термин",
      "definition": "Определение с примером"
    }}
  ]
}}

Найди 10-20 важных терминов. Верни ТОЛЬКО JSON."""

        try:
            text = await self._generate_async(prompt)
            text = text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            json.loads(text)  # Проверка
            return text
        except json.JSONDecodeError:
            return json.dumps({"terms": []}, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Glossary error: {e}")
            raise
    
    async def generate_flashcards(self, content: str, num_cards: int = 15) -> str:
        """Генерация флэш-карточек"""
        prompt = f"""Создай {num_cards} флэш-карточек.

Материал:
{content[:25000]}

Формат JSON:
{{
  "cards": [
    {{
      "front": "Вопрос или термин",
      "back": "Ответ или определение"
    }}
  ]
}}

Создай МИНИМУМ {num_cards} карточек! Верни ТОЛЬКО JSON."""

        try:
            text = await self._generate_async(prompt)
            text = text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            parsed = json.loads(text)
            if not parsed.get("cards"):
                raise ValueError("No cards")
            
            return text
        except json.JSONDecodeError as e:
            print(f"❌ Flashcards JSON error: {e}")
            return json.dumps({
                "cards": [{"front": "Ошибка", "back": "Попробуйте снова"}]
            }, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Flashcards error: {e}")
            raise


gemini_service = GeminiService()