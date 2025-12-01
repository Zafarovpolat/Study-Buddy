from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from app.core.config import settings
from app.bot.handlers import (
    start_command,
    help_command,
    premium_command,
    stats_command,
    button_callback
)

def create_bot_application() -> Application:
    """Создание и настройка Telegram бота"""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Обработчик callback кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    return application

# Для запуска бота отдельно (polling mode - для разработки)
async def run_bot_polling():
    """Запуск бота в режиме polling (для разработки)"""
    application = create_bot_application()
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Держим бота запущенным
    import asyncio
    while True:
        await asyncio.sleep(1)