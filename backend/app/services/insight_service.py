# backend/app/services/insight_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import json
import re

from app.models.insight import Insight
from app.models.user import User
from app.services.ai_service import gemini_service


class InsightService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_insights_for_user(
        self, 
        user: User, 
        region: Optional[str] = None,
        limit: int = 20
    ) -> List[Insight]:
        """Получить инсайты по направлению пользователя"""
        query = select(Insight)
        
        # Фильтр по направлению
        if user.field_of_study:
            query = query.where(Insight.field_of_study == user.field_of_study)
        
        # Фильтр по региону
        if region == 'uz':
            query = query.where(Insight.region == 'uz')
        
        query = query.order_by(
            desc(Insight.importance), 
            desc(Insight.published_at)
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_insight_by_id(self, insight_id: str) -> Optional[Insight]:
        """Получить инсайт по ID"""
        result = await self.db.execute(
            select(Insight).where(Insight.id == insight_id)
        )
        return result.scalar_one_or_none()
    
    async def generate_detailed_content(self, insight: Insight) -> str:
        """Генерация детального конспекта по инсайту"""
        if insight.detailed_content:
            return insight.detailed_content
        
        prompt = f"""Создай детальный академический конспект по следующей новости.

Заголовок: {insight.title}
Краткое содержание: {insight.summary}
Связь с учебной темой: {insight.academic_link}

Оригинальный текст:
{insight.original_content[:5000]}

Структура конспекта:
1. **Ключевые факты** (bullet points)
2. **Анализ последствий** (что это значит)
3. **Связь с теорией** (какие темы из курса затрагивает)
4. **Вопросы для размышления** (2-3 вопроса)
5. **Термины для изучения** (3-5 терминов)

Пиши на русском языке. Формат: Markdown."""

        content = await gemini_service._generate_async(prompt)
        
        # Кэшируем
        insight.detailed_content = content
        await self.db.commit()
        
        return content
    
    async def process_news_item(
        self,
        title: str,
        content: str,
        source_url: str,
        source_name: str,
        field: str,
        region: str
    ) -> Insight:
        """Обработка новой новости через AI"""
        
        prompt = f"""Ты — академический аналитик. Проанализируй новость для студентов направления "{field}".

Новость: {title}

Содержание: {content[:3000]}

Ответь в JSON формате:
{{
    "title": "Краткий академический заголовок (макс 100 символов)",
    "summary": "Суть за 2-3 предложения",
    "importance": число от 1 до 10,
    "importance_reason": "Почему это важно для студента (1 предложение)",
    "academic_link": "Связь с учебной темой (например: Макроэкономика, Глава 5)"
}}

Верни ТОЛЬКО валидный JSON."""

        try:
            response = await gemini_service._generate_async(prompt)
            response = response.strip()
            response = re.sub(r'^```json\s*', '', response)
            response = re.sub(r'^```\s*', '', response)
            response = re.sub(r'\s*```$', '', response)
            
            analysis = json.loads(response)
        except:
            analysis = {
                "title": title[:100],
                "summary": content[:200],
                "importance": 5,
                "importance_reason": "Актуальная новость",
                "academic_link": "Общая тема"
            }
        
        insight = Insight(
            source_url=source_url,
            source_name=source_name,
            original_title=title,
            original_content=content,
            title=analysis['title'],
            summary=analysis['summary'],
            importance=analysis['importance'],
            importance_reason=analysis['importance_reason'],
            academic_link=analysis['academic_link'],
            field_of_study=field,
            region=region
        )
        
        self.db.add(insight)
        await self.db.commit()
        await self.db.refresh(insight)
        
        return insight