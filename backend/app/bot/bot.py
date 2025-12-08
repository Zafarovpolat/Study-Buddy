from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from app.bot.handlers import (
    start_command,
    help_command,
    premium_command,
    stats_command,
    invite_command,  # ДОБАВЬ
    button_callback,
    pre_checkout_callback,
    successful_payment_callback,
)
from app.core.config import settings


def create_bot_application() -> Application:
    """Создать приложение бота"""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pro", premium_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("invite", invite_command))  # ДОБАВЬ
    
    # Кнопки
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Платежи
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    return application