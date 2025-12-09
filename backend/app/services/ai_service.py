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
        self.model_name = settings.GEMINI_MODEL
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            print(f"🤖 Gemini configured with model: {self.model_name}")
        else:
            print("⚠️ GEMINI_API_KEY not set!")
    
    def _get_model(self):
        """Получить модель Gemini"""
        return genai.GenerativeModel(self.model_name)
    
    async def generate_content_from_topic(self, topic: str) -> str:
        """Генерация полного учебного материала по названию темы"""
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
            model = self._get_model()
            response = model.generate_content(prompt)
            return response.text
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
    
    async def generate_quiz(self, content: str, num_questions: int = 15) -> str:
        """Генерация теста с 15-20 вопросами"""
        prompt = f"""Создай сложный тест из {num_questions} вопросов по материалу.

Материал:
{content[:25000]}

Требования к вопросам:
1. Разные типы: определения, понимание, применение, анализ
2. Разный уровень сложности: 30% лёгкие, 50% средние, 20% сложные
3. Варианты ответов должны быть правдоподобными
4. Пояснения должны быть информативными

Формат JSON:
{{
  "questions": [
    {{
      "question": "Вопрос?",
      "options": ["A) вариант", "B) вариант", "C) вариант", "D) вариант"],
      "correct": 0,
      "explanation": "Подробное пояснение почему это правильный ответ",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

ВАЖНО: Создай ровно {num_questions} вопросов!
Верни ТОЛЬКО валидный JSON без markdown."""

        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            # Проверяем JSON
            parsed = json.loads(text)
            
            # Проверяем количество вопросов
            if len(parsed.get("questions", [])) < 10:
                print(f"⚠️ Only {len(parsed['questions'])} questions generated, expected {num_questions}")
            
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
        prompt = f"""Создай подробный глоссарий ключевых терминов из материала.

Материал:
{content[:25000]}

Формат JSON:
{{
  "terms": [
    {{
      "term": "Термин",
      "definition": "Подробное определение с примером использования"
    }}
  ]
}}

Найди 10-20 важных терминов. Определения должны быть понятными и информативными.
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
            return json.dumps({"terms": []}, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Glossary error: {e}")
            raise
    
    async def generate_flashcards(self, content: str, num_cards: int = 15) -> str:
        """Генерация флэш-карточек"""
        prompt = f"""Создай {num_cards} флэш-карточек для запоминания ключевых понятий.

Материал:
{content[:25000]}

ВАЖНО: Создай МИНИМУМ {num_cards} карточек!

Типы карточек:
- Определения терминов
- Вопрос-ответ
- Факты и даты
- Причина-следствие

Формат JSON:
{{
  "cards": [
    {{
      "front": "Вопрос или термин",
      "back": "Ответ или определение"
    }}
  ]
}}

Создай разнообразные карточки для эффективного запоминания.
Верни ТОЛЬКО валидный JSON."""

        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'^```\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            
            parsed = json.loads(text)
            
            if not parsed.get("cards") or len(parsed["cards"]) == 0:
                raise ValueError("No cards generated")
            
            return text
        except json.JSONDecodeError as e:
            print(f"❌ Flashcards JSON error: {e}")
            return json.dumps({
                "cards": [{"front": "Ошибка генерации", "back": "Попробуйте снова"}]
            }, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Flashcards error: {e}")
            raise


gemini_service = GeminiService()