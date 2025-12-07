# backend/app/services/ai_service.py - ЗАМЕНИ ПОЛНОСТЬЮ
import google.generativeai as genai
from typing import Optional
import json
import re

from app.core.config import settings


class GeminiService:
    """Сервис для работы с Gemini AI"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL  # Читаем из настроек!
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            print(f"🤖 Gemini configured with model: {self.model_name}")
        else:
            print("⚠️ GEMINI_API_KEY not set!")
    
    def _get_model(self):
        """Получить модель Gemini"""
        return genai.GenerativeModel(self.model_name)
    
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
            model = self._get_model()
            response = model.generate_content(prompt)
            return response.text
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
            model = self._get_model()
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ TLDR error: {e}")
            raise
    
    async def generate_quiz(self, content: str, num_questions: int = 5) -> str:
        """Генерация теста"""
        prompt = f"""Создай тест из {num_questions} вопросов по материалу.

Материал:
{content[:25000]}

Формат JSON:
{{
  "questions": [
    {{
      "question": "Вопрос?",
      "options": ["A) вариант", "B) вариант", "C) вариант", "D) вариант"],
      "correct": 0,
      "explanation": "Пояснение"
    }}
  ]
}}

Верни ТОЛЬКО валидный JSON без markdown."""

        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            
            # Очищаем от markdown
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            # Проверяем валидность JSON
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # Возвращаем базовый тест
            return json.dumps({
                "questions": [{
                    "question": "Тест не удалось сгенерировать",
                    "options": ["Попробуйте снова"],
                    "correct": 0,
                    "explanation": ""
                }]
            }, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Quiz error: {e}")
            raise
    
    async def generate_glossary(self, content: str) -> str:
        """Генерация глоссария"""
        prompt = f"""Создай глоссарий ключевых терминов из материала.

Материал:
{content[:25000]}

Формат JSON:
{{
  "terms": [
    {{
      "term": "Термин",
      "definition": "Определение"
    }}
  ]
}}

Найди 5-15 важных терминов. Верни ТОЛЬКО JSON."""

        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return json.dumps({"terms": []}, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Glossary error: {e}")
            raise
    
    async def generate_flashcards(self, content: str, num_cards: int = 10) -> str:
        """Генерация флэш-карточек"""
        prompt = f"""Создай {num_cards} флэш-карточек для запоминания.

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

Верни ТОЛЬКО JSON."""

        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return json.dumps({"cards": []}, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Flashcards error: {e}")
            raise


# Создаём глобальный экземпляр
gemini_service = GeminiService()