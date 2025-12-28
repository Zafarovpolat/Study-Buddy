# backend/app/services/debate_service.py
from typing import List, Dict, Any, Literal
from app.services.ai_service import gemini_service

DifficultyLevel = Literal["easy", "medium", "hard"]


class DebateService:
    """Сервис для AI дебатов"""
    
    DIFFICULTY_PROMPTS = {
        "easy": """Ты — начинающий дебатёр. 
- Приводи простые аргументы
- Легко соглашайся с хорошими контраргументами
- Иногда делай логические ошибки, которые пользователь может заметить
- Будь вежливым и конструктивным""",
        
        "medium": """Ты — опытный дебатёр.
- Приводи убедительные аргументы с примерами
- Находи слабые места в аргументах оппонента
- Используй риторические приёмы
- Требуй доказательств и уточнений
- Признавай сильные аргументы, но ищи контраргументы""",
        
        "hard": """Ты — профессиональный дебатёр и эксперт.
- Используй сложные логические конструкции
- Применяй метод Сократа — задавай наводящие вопросы
- Находи логические ошибки и fallacies в аргументах
- Приводи статистику, исследования, цитаты экспертов
- Меняй тактику: иногда атакуй, иногда защищайся
- Не сдавайся легко, но признай поражение если аргументы неопровержимы"""
    }
    
    def _build_system_prompt(
        self, 
        topic: str, 
        position: str,
        difficulty: DifficultyLevel,
        material_context: str = ""
    ) -> str:
        """Создаёт системный промпт для дебатов"""
        
        difficulty_instructions = self.DIFFICULTY_PROMPTS[difficulty]
        
        context_part = ""
        if material_context:
            context_part = f"""

КОНТЕКСТ ИЗ МАТЕРИАЛА:
{material_context[:5000]}

Используй факты из контекста для усиления своих аргументов."""
        
        return f"""Ты участвуешь в дебатах на тему: "{topic}"

ТВОЯ ПОЗИЦИЯ: {position}

{difficulty_instructions}

ПРАВИЛА ДЕБАТОВ:
1. Отвечай кратко — 2-4 предложения максимум
2. Каждый ответ должен содержать:
   - Ответ на аргумент оппонента (если есть)
   - Твой новый аргумент или вопрос
3. Не повторяй одни и те же аргументы
4. В конце каждого ответа можешь задать вопрос оппоненту
5. Пиши на русском языке
{context_part}

ФОРМАТ ОТВЕТА:
Просто текст твоего аргумента, без лишних пояснений."""
    
    async def start_debate(
        self,
        topic: str,
        user_position: str,
        difficulty: DifficultyLevel = "medium",
        material_content: str = ""
    ) -> Dict[str, Any]:
        """Начинает дебаты — AI делает первый ход"""
        
        # AI занимает противоположную позицию
        ai_position = "ПРОТИВ" if user_position.upper() == "ЗА" else "ЗА"
        
        system_prompt = self._build_system_prompt(
            topic=topic,
            position=ai_position,
            difficulty=difficulty,
            material_context=material_content
        )
        
        opening_prompt = f"""{system_prompt}

Начни дебаты. Представь свою позицию и приведи первый аргумент {ai_position} темы "{topic}"."""
        
        try:
            ai_response = await gemini_service._generate_async(opening_prompt)
            
            return {
                "success": True,
                "topic": topic,
                "user_position": user_position,
                "ai_position": ai_position,
                "difficulty": difficulty,
                "ai_message": ai_response.strip(),
                "turn": 1
            }
        except Exception as e:
            print(f"Debate start error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def continue_debate(
        self,
        topic: str,
        ai_position: str,
        difficulty: DifficultyLevel,
        history: List[Dict[str, str]],
        user_message: str,
        material_content: str = ""
    ) -> Dict[str, Any]:
        """Продолжает дебаты — обрабатывает ход пользователя"""
        
        system_prompt = self._build_system_prompt(
            topic=topic,
            position=ai_position,
            difficulty=difficulty,
            material_context=material_content
        )
        
        # Формируем историю диалога
        history_text = ""
        for msg in history[-10:]:  # Последние 10 сообщений
            role = "Оппонент" if msg["role"] == "user" else "Ты"
            history_text += f"{role}: {msg['content']}\n\n"
        
        prompt = f"""{system_prompt}

ИСТОРИЯ ДЕБАТОВ:
{history_text}

Оппонент сейчас сказал: "{user_message}"

Ответь на этот аргумент и продолжи дебаты."""
        
        try:
            ai_response = await gemini_service._generate_async(prompt)
            
            return {
                "success": True,
                "ai_message": ai_response.strip(),
                "turn": len(history) // 2 + 1
            }
        except Exception as e:
            print(f"Debate continue error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def judge_debate(
        self,
        topic: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Судья оценивает дебаты"""
        
        history_text = ""
        for msg in history:
            role = "Участник 1" if msg["role"] == "user" else "Участник 2 (AI)"
            history_text += f"{role}: {msg['content']}\n\n"
        
        prompt = f"""Ты — беспристрастный судья дебатов.

ТЕМА: {topic}

ДЕБАТЫ:
{history_text}

Оцени дебаты по критериям:
1. Качество аргументов (кто привёл более убедительные доводы)
2. Логика (кто был последовательнее)
3. Ответы на контраргументы (кто лучше парировал)
4. Риторика (кто был убедительнее)

ФОРМАТ ОТВЕТА (JSON):
{{
    "winner": "user" или "ai" или "draw",
    "user_score": число от 1 до 10,
    "ai_score": число от 1 до 10,
    "user_strengths": ["сильная сторона 1", "сильная сторона 2"],
    "user_weaknesses": ["слабая сторона 1"],
    "ai_strengths": ["сильная сторона 1"],
    "ai_weaknesses": ["слабая сторона 1"],
    "summary": "Краткий итог дебатов в 2-3 предложения",
    "tip": "Совет пользователю как улучшить навыки дебатов"
}}

Верни ТОЛЬКО JSON."""
        
        try:
            import json
            import re
            
            response = await gemini_service._generate_async(prompt)
            response = response.strip()
            response = re.sub(r'^```json\s*', '', response)
            response = re.sub(r'^```\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
            
            result = json.loads(response)
            result["success"] = True
            return result
            
        except Exception as e:
            print(f"Judge error: {e}")
            return {
                "success": False,
                "error": str(e),
                "winner": "draw",
                "summary": "Не удалось оценить дебаты"
            }
    # Добавить в класс DebateService после judge_debate:

    async def continue_with_gamification(
        self,
        db: AsyncSession,
        user,
        topic: str,
        ai_position: str,
        difficulty: str,
        history: list,
        user_message: str,
        glossary: list = None,
        material_content: str = ""
    ) -> dict:
        """Продолжить дебаты с геймификацией"""
        from app.services.gamification_service import GamificationService
        
        # Проверяем термины
        gamification = GamificationService(db)
        terms_result = {"terms_found": 0, "points_awarded": 0}
        
        if glossary:
            terms_result = await gamification.check_debate_terms(
                user, user_message, glossary
            )
        
        # Генерируем ответ AI
        response = await self.continue_debate(
            topic=topic,
            ai_position=ai_position,
            difficulty=difficulty,
            history=history,
            user_message=user_message,
            material_content=material_content
        )
        
        # Добавляем инфо о геймификации
        response["terms_used"] = terms_result["terms_found"]
        response["points_earned"] = terms_result["points_awarded"]
        response["total_points"] = user.intellect_points
        
        # Генерируем подсказку если мало терминов
        if terms_result["terms_found"] < 2 and glossary and len(history) > 2:
            hint = await self._generate_term_hint(topic, glossary[:5])
            response["hint"] = hint
        
        return response
    
    async def _generate_term_hint(self, topic: str, glossary: list) -> str:
        """Генерация подсказки для использования терминов"""
        terms = [t.get('term', t) if isinstance(t, dict) else t for t in glossary]
        
        prompt = f"""Тема дебатов: {topic}
Доступные термины: {', '.join(terms)}

Дай короткую подсказку (1 предложение), как использовать один из этих терминов для усиления аргументации. Не называй термин напрямую, просто намекни."""

        try:
            return await gemini_service._generate_async(prompt)
        except:
            return None


debate_service = DebateService()