# backend/app/services/gamification_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


class GamificationService:
    """Сервис геймификации — Intellect Points"""
    
    REWARDS = {
        'debate_term_used': 10,      # Использовал 2+ термина из глоссария
        'debate_strong_argument': 5,  # Сильный аргумент
        'debate_win': 50,             # Выиграл дебаты
        'debate_draw': 20,            # Ничья
        'quiz_completed': 10,         # Прошёл тест
        'quiz_perfect': 50,           # 100% на тесте
        'quiz_good': 25,              # 80%+ на тесте
        'streak_3_days': 30,          # 3 дня подряд
        'streak_7_days': 100,         # 7 дней подряд
        'streak_30_days': 500,        # 30 дней подряд
        'first_material': 20,         # Первый материал
        'first_group': 30,            # Первая группа
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def award_points(
        self, 
        user: User, 
        reason: str, 
        custom_amount: int = None
    ) -> dict:
        """Начислить очки пользователю"""
        amount = custom_amount or self.REWARDS.get(reason, 0)
        
        if amount > 0:
            old_points = user.intellect_points or 0
            user.intellect_points = old_points + amount
            await self.db.commit()
            
            return {
                "awarded": True,
                "amount": amount,
                "reason": reason,
                "old_total": old_points,
                "new_total": user.intellect_points
            }
        
        return {"awarded": False, "amount": 0}
    
    async def update_debate_stats(
        self, 
        user: User, 
        won: bool, 
        draw: bool = False
    ):
        """Обновить статистику дебатов"""
        user.total_debates = (user.total_debates or 0) + 1
        
        if won:
            user.debates_won = (user.debates_won or 0) + 1
            await self.award_points(user, 'debate_win')
        elif draw:
            await self.award_points(user, 'debate_draw')
        
        await self.db.commit()
    
    async def update_quiz_stats(
        self, 
        user: User, 
        score: int, 
        max_score: int
    ):
        """Обновить статистику тестов"""
        user.quizzes_completed = (user.quizzes_completed or 0) + 1
        
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        if percentage == 100:
            user.perfect_quizzes = (user.perfect_quizzes or 0) + 1
            await self.award_points(user, 'quiz_perfect')
        elif percentage >= 80:
            await self.award_points(user, 'quiz_good')
        else:
            await self.award_points(user, 'quiz_completed')
        
        await self.db.commit()
    
    async def check_debate_terms(
        self, 
        user: User, 
        message: str, 
        glossary: list
    ) -> dict:
        """Проверить использование терминов в дебатах"""
        terms_used = 0
        message_lower = message.lower()
        
        for term in glossary:
            term_text = term.get('term', term) if isinstance(term, dict) else term
            if term_text.lower() in message_lower:
                terms_used += 1
        
        if terms_used >= 2:
            result = await self.award_points(user, 'debate_term_used')
            return {
                "terms_found": terms_used,
                "points_awarded": result.get('amount', 0),
                "total_points": user.intellect_points
            }
        
        return {
            "terms_found": terms_used,
            "points_awarded": 0,
            "total_points": user.intellect_points
        }