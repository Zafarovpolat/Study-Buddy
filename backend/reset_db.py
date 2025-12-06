# backend/reset_db.py - СОЗДАЙ ЭТОТ ФАЙЛ
"""Reset database for fresh migration"""
import os

def reset_alembic():
    database_url = os.environ.get('DATABASE_URL', '')
    
    if not database_url:
        print("⚠️ No DATABASE_URL, skipping reset")
        return
    
    # Преобразуем URL для psycopg2
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Удаляем все таблицы и типы
        cur.execute("""
            DROP TABLE IF EXISTS alembic_version CASCADE;
            DROP TABLE IF EXISTS ai_outputs CASCADE;
            DROP TABLE IF EXISTS materials CASCADE;
            DROP TABLE IF EXISTS group_members CASCADE;
            DROP TABLE IF EXISTS folders CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
            DROP TYPE IF EXISTS outputformat CASCADE;
            DROP TYPE IF EXISTS processingstatus CASCADE;
            DROP TYPE IF EXISTS materialtype CASCADE;
            DROP TYPE IF EXISTS grouprole CASCADE;
            DROP TYPE IF EXISTS subscriptiontier CASCADE;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database reset complete")
        
    except ImportError:
        print("⚠️ psycopg2 not installed, skipping reset")
    except Exception as e:
        print(f"⚠️ Reset error (may be OK on first run): {e}")


if __name__ == "__main__":
    reset_alembic()