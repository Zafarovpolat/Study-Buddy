# backend/app/services/ai_service.py - ПОЛНАЯ ВЕРСИЯ
import google.generativeai as genai
from typing import Optional
import json
import asyncio
from functools import partial
from pathlib import Path

from app.core.config import settings

# Настройка Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiService:
    """Сервис для работы с Gemini AI"""
    
    def __init__(self):
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=4096,
        )
    
    async def _generate(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Асинхронная генерация текста (с опциональным изображением)"""
        loop = asyncio.get_event_loop()
        
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
                    self.vision_model.generate_content,
                    [prompt, image_part],
                    generation_config=self.generation_config
                )
            )
        else:
            response = await loop.run_in_executor(
                None,
                partial(
                    self.text_model.generate_content,
                    prompt,
                    generation_config=self.generation_config
                )
            )
        
        return response.text
    
    async def extract_text_from_image(self, image_path: str) -> str:
        """OCR: Извлечение текста из изображения"""
        prompt = """Извлеки весь текст с этого изображения.

ИНСТРУКЦИИ:
1. Извлеки ВЕСЬ видимый текст, включая рукописный
2. Сохрани структуру (заголовки, списки, абзацы)
3. Исправь очевидные опечатки
4. Если текст на доске/в тетради - структурируй логически
5. Формулы запиши в понятном виде

Если изображение нечёткое или текста мало - извлеки что возможно.
Верни ТОЛЬКО извлечённый текст без комментариев."""

        return await self._generate(prompt, image_path)
    
    async def generate_smart_notes(self, content: str, title: str = "") -> str:
        """Генерация умных конспектов"""
        max_content = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Ты — эксперт по созданию учебных конспектов. 
Проанализируй материал и создай структурированный конспект.

МАТЕРИАЛ:
{title}
{content[:max_content]}

ИНСТРУКЦИИ:
1. Выдели 5-7 ключевых разделов
2. Для каждого раздела:
   - Заголовок (## Название)
   - 3-5 ключевых пунктов
   - Важные определения в **жирном**
   - Примеры где уместно
3. В конце добавь раздел "🎯 Главное" с 3-5 пунктами

Формат: Markdown
Язык: тот же, что в материале"""
        
        return await self._generate(prompt)
    
    async def generate_tldr(self, content: str) -> str:
        """Генерация краткого содержания"""
        max_content = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай краткое содержание (TL;DR) для этого материала.

МАТЕРИАЛ:
{content[:max_content]}

ИНСТРУКЦИИ:
1. Максимум 5-7 предложений
2. Только самое важное
3. Начни с "📌 **Суть:**"
4. Используй простой язык

Формат: короткий текст с эмодзи"""
        
        return await self._generate(prompt)
    
    async def generate_quiz(self, content: str, num_questions: int = 5) -> str:
        """Генерация теста"""
        max_content = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай тест для проверки понимания материала.

МАТЕРИАЛ:
{content[:max_content]}

ИНСТРУКЦИИ:
1. Создай ровно {num_questions} вопросов
2. Каждый вопрос с 4 вариантами ответа (A, B, C, D)
3. Только один правильный ответ
4. Разная сложность вопросов

ФОРМАТ (строго JSON):
```json
{{
  "questions": [
    {{
      "id": 1,
      "question": "Текст вопроса?",
      "options": {{
        "A": "Вариант А",
        "B": "Вариант Б",
        "C": "Вариант В",
        "D": "Вариант Г"
      }},
      "correct": "A",
      "explanation": "Почему это правильный ответ"
    }}
  ]
}}
```
Верни ТОЛЬКО валидный JSON без дополнительного текста."""

        response = await self._generate(prompt)
        return self._extract_json(response)

    async def generate_glossary(self, content: str) -> str:
        """Генерация глоссария терминов"""
        max_content = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай глоссарий ключевых терминов из материала.

МАТЕРИАЛ:
{content[:max_content]}

ИНСТРУКЦИИ:
1. Выдели 10-15 ключевых терминов
2. Дай краткое определение каждому (1-2 предложения)
3. Отсортируй по алфавиту

ФОРМАТ:
**Термин** — определение.

Пример:
**Алгоритм** — последовательность действий для решения задачи."""

        return await self._generate(prompt)

    async def generate_flashcards(self, content: str, num_cards: int = 10) -> str:
        """Генерация карточек для запоминания"""
        max_content = getattr(settings, 'MAX_CONTENT_LENGTH', 30000)
        
        prompt = f"""Создай карточки для запоминания (flashcards).

МАТЕРИАЛ:
{content[:max_content]}

ИНСТРУКЦИИ:
1. Создай {num_cards} карточек
2. Вопрос на лицевой стороне, ответ на обратной
3. Вопросы должны проверять понимание, не просто память

ФОРМАТ (строго JSON):
```json
{{
  "flashcards": [
    {{
      "id": 1,
      "front": "Что такое X?",
      "back": "X — это определение"
    }}
  ]
}}
```
Верни ТОЛЬКО валидный JSON."""

        response = await self._generate(prompt)
        return self._extract_json(response)

    async def generate_lexicon_definition(self, term: str, context: str) -> str:
        """Генерация определения термина в контексте (для Neuro-Lexicon)"""
        prompt = f"""Дай определение термину в контексте материала.

ТЕРМИН: {term}

КОНТЕКСТ:
{context[:5000]}

ИНСТРУКЦИИ:
1. Определение из контекста (не из общих знаний)
2. Простым языком
3. 2-3 предложения максимум
4. Если есть пример в контексте - приведи его

Формат: Только определение, без заголовков."""

        return await self._generate(prompt)

    def _extract_json(self, response: str) -> str:
        """Извлечение JSON из ответа"""
        try:
            json_str = response
            
            # Убираем markdown блоки если есть
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            # Валидируем JSON
            parsed = json.loads(json_str.strip())
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            # Если не получилось — возвращаем как есть
            return response


# Singleton instance
gemini_service = GeminiService()