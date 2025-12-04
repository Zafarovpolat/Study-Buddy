# backend/app/bot/handlers.py - ЗАМЕНИ ПОЛНОСТЬЮ
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import ContextTypes

from app.models import AsyncSessionLocal
from app.services import UserService
from app.services.payment_service import PaymentService, PRICES
from app.core.config import settings


WELCOME_TEXT = """
🎓 *Добро пожаловать в EduAI!*

📝 *Smart Notes* — умные конспекты
⚡ *TL;DR* — краткое содержание
❓ *Тесты* — проверь знания
🃏 *Карточки* — запоминание

🆓 Бесплатно: 3 материала/день
⭐ Pro: безлимит

Нажми кнопку ниже 👇
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, is_new = await user_service.get_or_create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        status = "🆕 Добро пожаловать!" if is_new else "👋 С возвращением!"
        tier = "⭐ Pro" if db_user.is_pro else "🆓 Free"
    
    webapp_url = settings.FRONTEND_URL or "https://eduai-api-tlyf.onrender.com"
    
    keyboard = [
        [InlineKeyboardButton("📱 Открыть", web_app=WebAppInfo(url=webapp_url))],
        [
            InlineKeyboardButton("⭐ Pro", callback_data="show_pro"),
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        ]
    ]
    
    await update.message.reply_text(
        f"{status}, {user.first_name}! ({tier})\n{WELCOME_TEXT}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = """
📖 *Как пользоваться:*

1️⃣ Открой приложение
2️⃣ Загрузи материал
3️⃣ Получи конспект!

/start — меню
/pro — подписка
/stats — статистика
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /pro - показать тарифы"""
    await show_pro_plans(update, context)


async def show_pro_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать планы подписки"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        payment_service = PaymentService(db)
        status = await payment_service.check_subscription_status(db_user)
    
    if status["is_pro"]:
        text = f"""
⭐ *У тебя Pro подписка!*

✅ Безлимитные материалы
✅ Приоритетная обработка

📅 Осталось дней: {status['days_left'] if status['days_left'] >= 0 else '∞'}
"""
        keyboard = [[InlineKeyboardButton("🔄 Продлить", callback_data="buy_pro_monthly")]]
    else:
        text = f"""
⭐ *Pro подписка*

✅ Безлимитные материалы
✅ Приоритетная обработка  
✅ Аудио-подкасты (скоро)
✅ AI-дебаты (скоро)

💰 *Цены:*
• 1 месяц: {PRICES['pro_monthly']} ⭐
• 1 год: {PRICES['pro_yearly']} ⭐ (скидка 33%!)
"""
        keyboard = [
            [InlineKeyboardButton(f"1 месяц — {PRICES['pro_monthly']} ⭐", callback_data="buy_pro_monthly")],
            [InlineKeyboardButton(f"1 год — {PRICES['pro_yearly']} ⭐ (выгодно!)", callback_data="buy_pro_yearly")],
        ]
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        streak = await user_service.get_streak_info(db_user)
        can_proceed, remaining = await user_service.check_rate_limit(db_user)
    
    tier = "Pro ⭐" if db_user.is_pro else "Free 🆓"
    
    text = f"""
📊 *Статистика*

👤 {user.first_name}
📱 Тариф: {tier}
🔥 Streak: {streak['current_streak']} дней
🏆 Рекорд: {streak['longest_streak']} дней

Сегодня: {'✅' if can_proceed else '❌'} ({remaining if remaining >= 0 else '∞'} осталось)
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.message.reply_text("Используй /help")
    
    elif query.data == "show_pro":
        await show_pro_plans(update, context)
    
    elif query.data == "buy_pro_monthly":
        await send_invoice(update, context, "pro_monthly")
    
    elif query.data == "buy_pro_yearly":
        await send_invoice(update, context, "pro_yearly")


async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str):
    """Отправить invoice для оплаты"""
    query = update.callback_query
    
    async with AsyncSessionLocal() as db:
        payment_service = PaymentService(db)
        invoice_data = await payment_service.create_invoice_data(plan)
    
    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=invoice_data["title"],
        description=invoice_data["description"],
        payload=invoice_data["payload"],
        provider_token="",  # Пустой для Telegram Stars
        currency=invoice_data["currency"],
        prices=[LabeledPrice(p["label"], p["amount"]) for p in invoice_data["prices"]],
    )


async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение перед оплатой"""
    query = update.pre_checkout_query
    # Всегда подтверждаем (можно добавить проверки)
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Успешная оплата"""
    payment = update.message.successful_payment
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        
        payment_service = PaymentService(db)
        await payment_service.process_successful_payment(
            user=db_user,
            payload=payment.invoice_payload,
            telegram_payment_charge_id=payment.telegram_payment_charge_id
        )
    
    await update.message.reply_text(
        "🎉 *Спасибо за покупку!*\n\n"
        "✅ Pro подписка активирована!\n"
        "Теперь у тебя безлимитный доступ.",
        parse_mode="Markdown"
    )