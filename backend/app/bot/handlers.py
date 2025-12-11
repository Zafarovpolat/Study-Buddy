# backend/app/bot/handlers.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import ContextTypes

from app.models import AsyncSessionLocal
from app.services import UserService
from app.services.payment_service import PaymentService, PRICES
from app.services.group_service import GroupService
from app.core.config import settings


WELCOME_TEXT = """
🎓 *Добро пожаловать в Lecto!*

📝 *Smart Notes* — умные конспекты
⚡ *TL;DR* — краткое содержание  
❓ *Тесты* — проверь знания
🃏 *Карточки* — запоминание

🆓 Бесплатно: {daily_limit} материалов/день
⭐ Pro: безлимит + AI Debate + Vector Search

Нажми кнопку ниже 👇
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с поддержкой deep link"""
    user = update.effective_user
    args = context.args
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, is_new = await user_service.get_or_create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        referrer_name = None
        group_name = None
        
        if args and len(args) > 0:
            param = args[0]
            
            if param.startswith('ref_'):
                ref_code = param[4:]
                group_service = GroupService(db)
                success, referrer = await group_service.process_referral(db_user, ref_code)
                if success and referrer:
                    referrer_name = referrer.first_name or referrer.telegram_username or "друг"
                    print(f"✅ Referral: {user.id} invited by {referrer.telegram_id}")
            
            elif param.startswith('group_'):
                invite_code = param[6:]
                group_service = GroupService(db)
                success, message, group = await group_service.join_group(db_user, invite_code)
                if success and group:
                    group_name = group.name
                    print(f"✅ User {user.id} joined group {group.id}")
        
        if is_new:
            if referrer_name:
                status = f"🎉 Добро пожаловать! Вас пригласил {referrer_name}"
            else:
                status = "🆕 Добро пожаловать!"
        else:
            status = "👋 С возвращением!"
        
        if group_name:
            status += f"\n✅ Вы вступили в группу «{group_name}»"
        
        tier = "⭐ Pro" if db_user.is_pro else "🆓 Free"
        daily_limit = 5
    
    webapp_url = settings.FRONTEND_URL or "https://eduai-api-tlyf.onrender.com"
    
    keyboard = [
        [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url=webapp_url))],
        [
            InlineKeyboardButton("⭐ Тарифы", callback_data="show_plans"),
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        ]
    ]
    
    welcome = WELCOME_TEXT.format(daily_limit=daily_limit)
    
    await update.message.reply_text(
        f"{status} ({tier})\n{welcome}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    text = """
📖 *Как пользоваться:*

1️⃣ Открой приложение
2️⃣ Загрузи материал (PDF, фото, текст)
3️⃣ Получи конспект, тесты, карточки!

*Команды:*
/start — главное меню
/pro — тарифы и подписка
/stats — твоя статистика
/invite — пригласить друзей

*Поддержка:* @zafarovpolat
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /invite"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        
        group_service = GroupService(db)
        stats = await group_service.get_referral_stats(db_user)
    
    remaining = stats['referrals_needed']
    count = stats['referral_count']
    threshold = stats['threshold']
    link = stats['referral_link']
    
    if stats['pro_granted']:
        text = f"""
🎉 *Ты уже получил Pro за приглашения!*

Продолжай приглашать друзей:
👥 Приглашено: {count} человек

🔗 Твоя ссылка:
`{link}`
"""
    else:
        progress_bar = '🟩' * count + '⬜' * remaining
        text = f"""
🎁 *Пригласи друзей — получи Pro бесплатно!*

📊 Прогресс: {count}/{threshold}
{progress_bar}

Осталось пригласить: {remaining}

🔗 Твоя ссылка:
`{link}`

Отправь эту ссылку друзьям!
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться", 
            url=f"https://t.me/share/url?url={link}&text=📚 Присоединяйся к Lecto — ИИ-помощник для учёбы!")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /pro"""
    await show_plans(update, context, is_callback=False)


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Показать все тарифы"""
    user = update.callback_query.from_user if is_callback else update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        payment_service = PaymentService(db)
        status = await payment_service.check_subscription_status(db_user)
    
    if status["is_pro"]:
        tier_name = "Pro ⭐" if status["tier"] == "pro" else "SOS 🔥"
        if status["days_left"] > 0:
            expires_text = f"{status['days_left']} дней"
        elif status["hours_left"] > 0:
            expires_text = f"{status['hours_left']} часов"
        else:
            expires_text = "∞"
        
        text = f"""
✅ *У тебя {tier_name} подписка!*

*Доступно:*
• Безлимитные генерации
• 🎧 Audio-Dialog (скоро)
• 💬 AI-Debate (скоро)
• 📊 Презентации (скоро)
• 🔍 Vector Search

📅 Осталось: {expires_text}
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Продлить Pro", callback_data="buy_pro_monthly")],
        ]
    else:
        text = f"""
📋 *Тарифы Lecto*

━━━━━━━━━━━━━━━━
🆓 *STARTER* (Бесплатно)
• 5 генераций в день
• Smart Notes, Тесты, Карточки
• Группы

━━━━━━━━━━━━━━━━
⭐ *PRO* ({PRICES['pro_monthly']} Stars/мес)
• Безлимитные генерации  
• 🎧 Audio-Dialog
• 💬 AI-Debate
• 📊 Презентации
• 🔍 Vector Search

━━━━━━━━━━━━━━━━
🔥 *SOS* ({PRICES['sos_24h']} Stars/24ч)
• Экзамен завтра?
• Безлимит на 24 часа
• Все Pro функции

━━━━━━━━━━━━━━━━
💡 Или пригласи 5 друзей → 30 дней Pro бесплатно!
"""
        keyboard = [
            [InlineKeyboardButton(f"🔥 SOS 24ч — {PRICES['sos_24h']} ⭐", callback_data="buy_sos")],
            [InlineKeyboardButton(f"⭐ Pro 1 мес — {PRICES['pro_monthly']} ⭐", callback_data="buy_pro_monthly")],
            [InlineKeyboardButton(f"💎 Pro 1 год — {PRICES['pro_yearly']} ⭐ (-33%)", callback_data="buy_pro_yearly")],
            [InlineKeyboardButton("🎁 Пригласить друзей", callback_data="show_invite")],
        ]
    
    if is_callback:
        await update.callback_query.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        streak = await user_service.get_streak_info(db_user)
        can_proceed, remaining = await user_service.check_rate_limit(db_user)
        
        group_service = GroupService(db)
        ref_stats = await group_service.get_referral_stats(db_user)
        
        payment_service = PaymentService(db)
        sub_status = await payment_service.check_subscription_status(db_user)
    
    if sub_status["is_pro"]:
        tier = "Pro ⭐" if sub_status["tier"] == "pro" else "SOS 🔥"
        limit_text = "∞"
    else:
        tier = "Free 🆓"
        limit_text = f"{remaining}/5"
    
    text = f"""
📊 *Твоя статистика*

👤 {user.first_name}
📱 Тариф: {tier}
📝 Сегодня: {limit_text}

🔥 Streak: {streak['current_streak']} дней
🏆 Рекорд: {streak['longest_streak']} дней

👥 Приглашено: {ref_stats['referral_count']}/{ref_stats['threshold']}
"""
    
    keyboard = [[InlineKeyboardButton("📋 Тарифы", callback_data="show_plans")]]
    
    await update.message.reply_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.message.reply_text("Используй /help для справки")
    
    elif query.data == "show_plans":
        await show_plans(update, context, is_callback=True)
    
    elif query.data == "show_invite":
        user = query.from_user
        async with AsyncSessionLocal() as db:
            user_service = UserService(db)
            db_user, _ = await user_service.get_or_create(telegram_id=user.id)
            group_service = GroupService(db)
            stats = await group_service.get_referral_stats(db_user)
        
        link = stats['referral_link']
        remaining = stats['referrals_needed']
        count = stats['referral_count']
        
        if stats['pro_granted']:
            text = f"🎉 Ты уже получил Pro!\n\n🔗 Твоя ссылка:\n`{link}`"
        else:
            text = f"🎁 Пригласи ещё {remaining} друзей для Pro!\n\n📊 Прогресс: {count}/5\n\n🔗 Твоя ссылка:\n`{link}`"
        
        keyboard = [[InlineKeyboardButton("📤 Поделиться", 
            url=f"https://t.me/share/url?url={link}&text=📚 Присоединяйся к Lecto!")]]
        
        await query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "buy_sos":
        await send_invoice(update, context, "sos_24h")
    
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
        provider_token="",
        currency=invoice_data["currency"],
        prices=[LabeledPrice(p["label"], p["amount"]) for p in invoice_data["prices"]],
    )


async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение перед оплатой"""
    query = update.pre_checkout_query
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
    
    # Разные сообщения для разных тарифов
    if payment.invoice_payload == "sos_24h":
        text = """
🔥 *SOS активирован!*

✅ Безлимит на 24 часа
✅ Все Pro функции доступны

Удачи на экзамене! 💪
"""
    else:
        text = """
🎉 *Спасибо за покупку!*

✅ Pro подписка активирована!

*Теперь тебе доступно:*
• Безлимитные генерации
• 🎧 Audio-Dialog
• 💬 AI-Debate  
• 📊 Презентации
• 🔍 Vector Search
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")