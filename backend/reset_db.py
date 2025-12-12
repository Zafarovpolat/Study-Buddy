# backend/reset_db.py
"""Reset database for fresh migration"""
import os
import sys


def reset_database():
    database_url = os.environ.get('DATABASE_URL', '')
    
    if not database_url:
        print("⚠️ No DATABASE_URL set, skipping reset")
        return False
    
    # Sync URL
    sync_url = database_url
    if sync_url.startswith('postgres://'):
        sync_url = sync_url.replace('postgres://', 'postgresql://', 1)
    if '+asyncpg' in sync_url:
        sync_url = sync_url.replace('+asyncpg', '')
    
    # SSL для Supabase
    if "supabase" in sync_url and "sslmode" not in sync_url:
        sync_url += "?sslmode=require" if "?" not in sync_url else "&sslmode=require"
    
    try:
        import psycopg2
        print(f"🔌 Connecting to database...")
        conn = psycopg2.connect(sync_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("🗑️ Dropping all tables...")
        cur.execute("""
            DROP TABLE IF EXISTS alembic_version CASCADE;
            DROP TABLE IF EXISTS text_chunks CASCADE;
            DROP TABLE IF EXISTS quiz_results CASCADE;
            DROP TABLE IF EXISTS ai_outputs CASCADE;
            DROP TABLE IF EXISTS materials CASCADE;
            DROP TABLE IF EXISTS group_members CASCADE;
            DROP TABLE IF EXISTS folders CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        """)
        
        print("🗑️ Dropping all ENUM types...")
        cur.execute("""
            DROP TYPE IF EXISTS outputformat CASCADE;
            DROP TYPE IF EXISTS processingstatus CASCADE;
            DROP TYPE IF EXISTS materialtype CASCADE;
            DROP TYPE IF EXISTS grouprole CASCADE;
            DROP TYPE IF EXISTS subscriptiontier CASCADE;
        """)
        
        cur.close()
        conn.close()
        print("✅ Database reset complete!")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    reset_database()