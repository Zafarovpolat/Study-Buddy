# backend/app/bot/bot.py - ЗАМЕНИ ПОЛНОСТЬЮ
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters

from app.core.config import settings
from app.bot.handlers import (
    start_command,
    help_command,
    premium_command,
    stats_command,
    button_callback,
    pre_checkout_callback,
    successful_payment_callback
)


def create_bot_application() -> Application:
    """Создание бота"""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("pro", premium_command))
    app.add_handler(CommandHandler("premium", premium_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Кнопки
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Платежи
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    return app