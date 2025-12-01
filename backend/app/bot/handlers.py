from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AsyncSessionLocal
from app.services import UserService
from app.core.config import settings

# Текст приветствия
WELCOME_TEXT = """
🎓 **Добро пожаловать в EduAI Assistant!**

Я помогу тебе учиться эффективнее:

📝 **Smart Notes** — умные конспекты из любых материалов
⚡ **TL;DR** — краткое содержание за 30 секунд  
❓ **Тесты** — проверь свои знания
📚 **Глоссарий** — ключевые термины

🆓 **Бесплатно:** 3 материала в день
⭐ **Pro:** безлимит + аудио-подкасты

Нажми кнопку ниже, чтобы начать! 👇
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Регистрируем пользователя в БД
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, is_new = await user_service.get_or_create(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        user_status = "🆕 Новый" if is_new else "👋 С возвращением"
        tier_emoji = "⭐" if db_user.subscription_tier != "free" else "🆓"
    
    # Кнопка для открытия Mini App
    webapp_url = settings.TELEGRAM_WEBAPP_URL or "https://your-app-url.com"
    
    keyboard = [
        [InlineKeyboardButton(
            "📱 Открыть приложение", 
            web_app=WebAppInfo(url=webapp_url)
        )],
        [InlineKeyboardButton("⭐ Pro подписка", callback_data="subscribe_pro")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"{user_status}, {user.first_name}! {tier_emoji}\n\n{WELCOME_TEXT}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 **Как пользоваться EduAI:**

1️⃣ Открой приложение по кнопке
2️⃣ Загрузи материал (PDF, фото, текст)
3️⃣ Подожди пока AI обработает
4️⃣ Получи конспекты, тесты и карточки!

**Форматы материалов:**
• PDF документы
• Word файлы (.docx)
• Фотографии текста
• Скопированный текст
• Аудио лекции (Pro)

**Команды:**
/start — главное меню
/help — эта справка
/premium — информация о Pro
/stats — твоя статистика

❓ Вопросы: @your_support_username
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о премиум подписке"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
    
    if db_user.subscription_tier != "free":
        text = f"⭐ У тебя уже активна **{db_user.subscription_tier.upper()}** подписка!"
    else:
        text = """
⭐ **Pro подписка — 150 Stars/месяц**

Что включено:
✅ Безлимитные материалы
✅ Аудио-подкасты из конспектов
✅ Приоритетная обработка
✅ Расширенные тесты
✅ Экспорт в PDF

🎁 **Первые 7 дней бесплатно!**
"""
    
    keyboard = [[InlineKeyboardButton("💫 Оформить Pro", callback_data="buy_pro")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика пользователя"""
    user = update.effective_user
    
    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        db_user, _ = await user_service.get_or_create(telegram_id=user.id)
        can_proceed, remaining = await user_service.check_rate_limit(db_user)
    
    tier_name = "Pro ⭐" if db_user.subscription_tier != "free" else "Free 🆓"
    
    text = f"""
📊 **Твоя статистика**

👤 Аккаунт: {user.first_name}
📱 Тариф: {tier_name}
📅 С нами с: {db_user.created_at.strftime('%d.%m.%Y')}

**Сегодня:**
{'✅ Можно загружать' if can_proceed else '❌ Лимит исчерпан'}
Осталось запросов: {remaining if remaining >= 0 else '∞'}
"""
    await update.message.reply_text(text, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.message.reply_text("Используй /help для справки")
    
    elif query.data == "subscribe_pro" or query.data == "buy_pro":
        # TODO: Интеграция с оплатой
        await query.message.reply_text(
            "💫 Оплата Pro подписки будет доступна в следующем обновлении!\n\n"
            "А пока пользуйся бесплатным тарифом (3 материала в день)."
        )