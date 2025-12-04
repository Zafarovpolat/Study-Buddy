# backend/app/services/ai_service.py - ЗАМЕНИ ПОЛНОСТЬЮ
import google.generativeai as genai
from typing import Optional
import json
import asyncio
from functools import partial
from pathlib import Path
import traceback

from app.core.config import settings

# Настройка Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:
    """Сервис для работы с Gemini AI"""
    
    def __init__(self):
        # Gemini 2.0 Flash
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        print(f"🤖 Initializing Gemini model: {model_name}")
        
        self.model = genai.GenerativeModel(model_name)
        
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=8192,  # Gemini 2.0 поддерживает больше
        )
    
    async def _generate(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Асинхронная генерация текста (с опциональным изображением)"""
        loop = asyncio.get_event_loop()
        
        try:
            if image_path:
                # Читаем изображение
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Определяем MIME тип
                ext = Path(image_path).suffix.lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                }
                mime_type = mime_types.get(ext, 'image/jpeg')
                
                # Создаём контент с изображением
                image_part = {
                    "mime_type": mime_type,
                    "data": image_data
                }
                
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self.model.generate_content,
                        [prompt, image_part],
                        generation_config=self.generation_config
                    )
                )
            else:
                response = await loop.run_in_executor(
                    None,
                    partial(
                        self.model.generate_content,
                        prompt,
                        generation_config=self.generation_config
                    )
                )
            
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            print(traceback.format_exc())
            raise
    
    async def extract_text_from_image(self, image_path: str) -> str:
        """OCR: Извлечение текста из изображения"""
        prompt = """Извлеки весь текст с этого изображения.

ИНСТРУКЦИИ:
1. Извлеки ВЕСЬ видимый текст, включая рукописный
2. Сохрани структуру (заголовки, списки, абзацы)
3. Исправь очевидные опечатки
4. Если текст на доске/в тетради - структурируй логически
5. Формулы запиши в понятном виде

Верни ТОЛЬКО извлечённый текст без комментариев."""

        return await self._generate(prompt, image_path)
    
    async def generate_smart_notes(self, content: str, title: str = "") -> str:
        """Генерация умных конспектов"""
        max_len = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Ты — эксперт по созданию учебных конспектов.

МАТЕРИАЛ:
{title}
{content[:max_len]}

Создай структурированный конспект:
1. 5-7 ключевых разделов (## Заголовок)
2. Для каждого: 3-5 пунктов, термины **жирным**
3. В конце: "🎯 Главное" с 3-5 выводами

Формат: Markdown"""
        
        return await self._generate(prompt)
    
    async def generate_tldr(self, content: str) -> str:
        """Генерация краткого содержания"""
        max_len = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай TL;DR (краткое содержание):

{content[:max_len]}

Требования:
- Максимум 5-7 предложений
- Начни с "📌 **Суть:**"
- Простой язык"""
        
        return await self._generate(prompt)
    
    async def generate_quiz(self, content: str, num_questions: int = 5) -> str:
        """Генерация теста"""
        max_len = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай тест из {num_questions} вопросов:

{content[:max_len]}

ФОРМАТ JSON:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Вопрос?",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct": "A",
      "explanation": "Почему"
    }}
  ]
}}

Верни ТОЛЬКО JSON."""
        
        response = await self._generate(prompt)
        return self._extract_json(response)
    
    async def generate_glossary(self, content: str) -> str:
        """Генерация глоссария"""
        max_len = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай глоссарий из материала:

{content[:max_len]}

Формат: **Термин** — определение (1-2 предложения).
Отсортируй по алфавиту. 10-15 терминов."""
        
        return await self._generate(prompt)
    
    async def generate_flashcards(self, content: str, num_cards: int = 10) -> str:
        """Генерация карточек"""
        max_len = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай {num_cards} flashcards:

{content[:max_len]}

ФОРМАТ JSON:
{{
  "flashcards": [
    {{"id": 1, "front": "Вопрос", "back": "Ответ"}}
  ]
}}

Верни ТОЛЬКО JSON."""
        
        response = await self._generate(prompt)
        return self._extract_json(response)
    
    def _extract_json(self, response: str) -> str:
        """Извлечение JSON из ответа"""
        try:
            json_str = response
            
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            parsed = json.loads(json_str.strip())
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            return response


# Singleton
gemini_service = GeminiService()