# backend/app/services/ai_service.py
import google.generativeai as genai
from typing import Optional
import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.config.prompts import (
    TOPIC_GENERATION_PROMPT,
    SMART_NOTES_PROMPT,
    TLDR_PROMPT,
    QUIZ_PROMPT,
    GLOSSARY_PROMPT,
    FLASHCARDS_PROMPT
)

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
        prompt = TOPIC_GENERATION_PROMPT.format(topic=topic)

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ Generate from topic error: {e}")
            raise
    
    async def generate_smart_notes(self, content: str, title: str = "") -> str:
        """Генерация умного конспекта"""
        prompt = SMART_NOTES_PROMPT.format(title=title, content=content[:30000])

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ Smart notes error: {e}")
            raise
    
    async def generate_tldr(self, content: str) -> str:
        """Генерация краткого содержания"""
        prompt = TLDR_PROMPT.format(content=content[:20000])

        try:
            return await self._generate_async(prompt)
        except Exception as e:
            print(f"❌ TLDR error: {e}")
            raise
    
    async def generate_quiz(self, content: str, num_questions: int = 15) -> str:
        """Генерация теста"""
        prompt = QUIZ_PROMPT.format(num_questions=num_questions, content=content[:25000])

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
        prompt = GLOSSARY_PROMPT.format(content=content[:25000])

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
        prompt = FLASHCARDS_PROMPT.format(num_cards=num_cards, content=content[:25000])

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