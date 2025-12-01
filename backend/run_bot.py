import asyncio
from app.bot.bot import run_bot_polling

if __name__ == "__main__":
    print("🤖 Starting Telegram Bot...")
    asyncio.run(run_bot_polling())