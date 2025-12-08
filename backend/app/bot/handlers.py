# backend/app/bot/handlers.py - ЗАМЕНИ ПОЛНОСТЬЮ
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import ContextTypes

from app.models import AsyncSessionLocal
from app.services import UserService
from app.services.payment_service import PaymentService, PRICES
from app.services.group_service import GroupService
from app.core.config import settings


WELCOME_TEXT = """
🎓 *Добро пожаловать в Study Buddy!*

📝 *Smart Notes* — умные конспекты
⚡ *TL;DR* — краткое содержание
❓ *Тесты* — проверь знания
🃏 *Карточки* — запоминание

🆓 Бесплатно: {daily_limit} материалов/день
⭐ Pro: безлимит

Нажми кнопку ниже 👇
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start с поддержкой deep link"""
    user = update.effective_user
    args = context.args  # Аргументы после /start
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, is_new = await user_service.get_or_create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        # Обработка deep link
        referrer_name = None
        group_name = None
        
        if args and len(args) > 0:
            param = args[0]
            
            # Реферальная ссылка: ref_XXXXXX
            if param.startswith('ref_'):
                ref_code = param[4:]  # Убираем "ref_"
                group_service = GroupService(db)
                success, referrer = await group_service.process_referral(db_user, ref_code)
                if success and referrer:
                    referrer_name = referrer.first_name or referrer.telegram_username or "друг"
                    print(f"✅ Referral: {user.id} invited by {referrer.telegram_id}")
            
            # Приглашение в группу: group_XXXXXX
            elif param.startswith('group_'):
                invite_code = param[6:]  # Убираем "group_"
                group_service = GroupService(db)
                success, message, group = await group_service.join_group(db_user, invite_code)
                if success and group:
                    group_name = group.name
                    print(f"✅ User {user.id} joined group {group.id}")
        
        # Формируем приветствие
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
        daily_limit = settings.FREE_DAILY_LIMIT
    
    webapp_url = settings.FRONTEND_URL or "https://studybuddyai-qd2m.onrender.com"
    
    keyboard = [
        [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url=webapp_url))],
        [
            InlineKeyboardButton("⭐ Pro подписка", callback_data="show_pro"),
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
/pro — подписка Pro
/stats — твоя статистика
/invite — пригласить друзей

*Поддержка:* @studybuddy_support
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /invite — показать реферальную ссылку"""
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
        text = f"""
🎁 *Пригласи друзей — получи Pro бесплатно!*

📊 Прогресс: {count}/{threshold}
{'🟩' * count}{'⬜' * remaining}

Осталось пригласить: {remaining}

🔗 Твоя ссылка:
`{link}`

Отправь эту ссылку друзьям!
"""
    
    keyboard = [
        [InlineKeyboardButton("📤 Поделиться", 
            url=f"https://t.me/share/url?url={link}&text=📚 Присоединяйся к Study Buddy — ИИ-помощник для учёбы!")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /pro — показать тарифы"""
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
✅ Доступ к новым функциям

💰 *Цены:*
• 1 месяц: {PRICES['pro_monthly']} ⭐
• 1 год: {PRICES['pro_yearly']} ⭐ (-33%)

Или пригласи 5 друзей → Pro бесплатно!
"""
        keyboard = [
            [InlineKeyboardButton(f"1 месяц — {PRICES['pro_monthly']} ⭐", callback_data="buy_pro_monthly")],
            [InlineKeyboardButton(f"1 год — {PRICES['pro_yearly']} ⭐ 🔥", callback_data="buy_pro_yearly")],
            [InlineKeyboardButton("🎁 Пригласить друзей", callback_data="show_invite")],
        ]
    
    if update.callback_query:
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
    
    tier = "Pro ⭐" if db_user.is_pro else "Free 🆓"
    limit_text = "∞" if db_user.is_pro else f"{remaining}/{settings.FREE_DAILY_LIMIT}"
    
    text = f"""
📊 *Твоя статистика*

👤 {user.first_name}
📱 Тариф: {tier}
📝 Сегодня: {limit_text}

🔥 Streak: {streak['current_streak']} дней
🏆 Рекорд: {streak['longest_streak']} дней

👥 Приглашено: {ref_stats['referral_count']}/{ref_stats['threshold']}
"""
    await update.message.reply_text(text, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.message.reply_text("Используй /help для справки")
    
    elif query.data == "show_pro":
        await show_pro_plans(update, context)
    
    elif query.data == "show_invite":
        # Показываем реферальную информацию
        user = query.from_user
        async with AsyncSessionLocal() as db:
            user_service = UserService(db)
            db_user, _ = await user_service.get_or_create(telegram_id=user.id)
            group_service = GroupService(db)
            stats = await group_service.get_referral_stats(db_user)
        
        link = stats['referral_link']
        await query.message.reply_text(
            f"🔗 Твоя ссылка:\n`{link}`\n\nОтправь друзьям!",
            parse_mode="Markdown"
        )
    
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