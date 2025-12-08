# backend/scripts/reset_db.py
"""
Скрипт для полного сброса базы данных.
Запуск: python -m scripts.reset_db
"""

import asyncio
import sys
import os

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models.base import async_session_maker, engine


async def reset_database():
    """Полный сброс всех данных"""
    
    print("=" * 50)
    print("⚠️  СБРОС БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    async with async_session_maker() as db:
        try:
            # Показываем что есть до удаления
            print("\n📊 Текущее состояние:")
            
            tables = ['users', 'materials', 'folders', 'group_members', 'ai_outputs']
            
            for table in tables:
                try:
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   {table}: {count} записей")
                except:
                    print(f"   {table}: таблица не существует")
            
            # Удаляем все данные
            print("\n🗑️  Удаление данных...")
            
            await db.execute(text("""
                TRUNCATE TABLE 
                    users,
                    materials, 
                    folders,
                    group_members,
                    ai_outputs
                CASCADE
            """))
            
            await db.commit()
            
            # Проверяем результат
            print("\n✅ После очистки:")
            for table in tables:
                try:
                    result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   {table}: {count} записей")
                except:
                    pass
            
            print("\n" + "=" * 50)
            print("✅ БАЗА ДАННЫХ ОЧИЩЕНА!")
            print("=" * 50)
            
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            await db.rollback()
            raise


async def reset_users_only():
    """Сброс только пользователей"""
    
    print("🗑️  Удаление всех пользователей...")
    
    async with async_session_maker() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"   Найдено: {count} пользователей")
        
        await db.execute(text("TRUNCATE TABLE users CASCADE"))
        await db.commit()
        
        print(f"   ✅ Удалено: {count} пользователей")


async def reset_referrals_only():
    """Сброс только реферальных данных"""
    
    print("🔄 Сброс реферальных данных...")
    
    async with async_session_maker() as db:
        await db.execute(text("""
            UPDATE users SET 
                referred_by_id = NULL,
                referral_count = 0,
                referral_pro_granted = false
        """))
        await db.commit()
        
        print("   ✅ Реферальные данные сброшены")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Сброс базы данных')
    parser.add_argument('--users', action='store_true', help='Удалить только пользователей')
    parser.add_argument('--referrals', action='store_true', help='Сбросить только рефералы')
    parser.add_argument('--all', action='store_true', help='Полный сброс всего')
    
    args = parser.parse_args()
    
    if args.users:
        asyncio.run(reset_users_only())
    elif args.referrals:
        asyncio.run(reset_referrals_only())
    elif args.all:
        asyncio.run(reset_database())
    else:
        print("Использование:")
        print("  python -m scripts.reset_db --all        # Полный сброс")
        print("  python -m scripts.reset_db --users      # Только пользователи")
        print("  python -m scripts.reset_db --referrals  # Только рефералы")