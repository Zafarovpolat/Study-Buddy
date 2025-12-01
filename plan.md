# План реализации образовательного AI-ассистента (Telegram Mini App)

## 🎯 Стратегия реализации

---

## Фаза 0: Подготовка (1-2 недели)

### Архитектура и инфраструктура

- Настроить репозиторий (monorepo: frontend + backend)
- Развернуть dev-окружение (Docker Compose)
- Создать Telegram Bot через BotFather
- Настроить PostgreSQL + Redis для кеширования
- Подключить S3-совместимое хранилище
- Настроить CI/CD pipeline

### API ключи и сервисы

- OpenAI (GPT-4o-mini + Whisper)
- Векторная БД (рекомендую Qdrant вместо Pinecone - дешевле, self-hosted)
- Payment provider (Telegram Stars + резервный Stripe)

---

## Фаза 1: Core MVP (4-6 недель)

### Неделя 1-2: Backend Foundation

#### Приоритет 1: Базовая инфраструктура

**Основные компоненты:**
- User management (регистрация через Telegram)
- File upload API (PDF, DOCX, TXT)
- Database schema:
  - `users` (id, telegram_id, subscription_tier, created_at)
  - `materials` (id, user_id, type, status, raw_content)
  - `folders` (id, user_id, name, is_group)
  - `ai_outputs` (id, material_id, format, content)

#### Приоритет 2: AI Processing Pipeline

**Базовая архитектура обработки:**

```python
async def process_material(file_id: str):
    # 1. Извлечение текста
    text = await extract_text(file_id)
    
    # 2. Параллельная генерация
    tasks = [
        generate_smart_notes(text),
        generate_tldr(text),
        generate_quiz(text),
        generate_glossary(text)
    ]
    results = await asyncio.gather(*tasks)
    
    # 3. Сохранение
    await save_outputs(file_id, results)
```

**Критичные функции:**
- OCR для изображений (Tesseract + GPT-4 Vision для проверки качества)
- Парсинг PDF/DOCX (PyMuPDF, python-docx)
- Chunking текста для LLM (max 8k tokens на запрос)
- Rate limiting (3 запроса/день для Free)

---

### Неделя 3-4: Telegram Mini App UI

#### Структура экранов (приоритет)

**1. Dashboard (главный экран)**
- Компонент: Welcome card + Quick actions
- Стек: React + Telegram WebApp SDK
- Интеграция с Telegram.WebApp.BackButton

**2. Library (80% времени пользователя)**
- Folder tree (рекурсивная структура)
- Material cards с preview
- Bottom sheet для выбора формата просмотра

**3. Viewer (читалка контента)**
- Markdown renderer для Smart Notes
- Audio player для подкастов
- Quiz interface с прогресс-баром

#### UI Kit

```javascript
// Используйте Telegram цвета
const theme = {
  bg_color: Telegram.WebApp.backgroundColor,
  button_color: Telegram.WebApp.themeParams.button_color,
  text_color: Telegram.WebApp.themeParams.text_color
}
```

---

### Неделя 5-6: Integration & Testing

- Интеграция Frontend ↔ Backend
- Telegram Bot команды (/start, /help, /premium)
- Push-уведомления через Telegram
- Beta-тестирование с 10-20 студентами

---

## Фаза 2: Premium Features (3-4 недели)

### Неделя 7-8: Audio Pipeline

#### Speech-to-Text

```python
# Whisper integration
async def transcribe_audio(audio_path: str):
    # Разбить аудио на чанки по 10 мин (Whisper limit)
    chunks = split_audio(audio_path, chunk_size=600)
    
    transcriptions = []
    for chunk in chunks:
        result = await openai.Audio.transcribe(
            model="whisper-1",
            file=chunk,
            language="ru"  # или auto-detect
        )
        transcriptions.append(result.text)
    
    return merge_transcriptions(transcriptions)
```

#### Text-to-Speech (подкасты)

**Варианты:**
- Вариант 1 (дорогой): ElevenLabs - качественные голоса
- Вариант 2 (экономный): OpenAI TTS - хорошо для русского
- Формат: Монолог (проще) → Диалог (требует промпт-инженерии)

---

### Неделя 9: Presentation Generator

```python
# Генерация PDF-слайдов
async def create_presentation(notes: str):
    # 1. LLM извлекает ключевые тезисы
    slides_content = await gpt_extract_key_points(notes, max_slides=10)
    
    # 2. Генерация PDF (ReportLab или Pillow)
    pdf = create_pdf_slides(slides_content, template="academic")
    
    return pdf
```

---

### Неделя 10: RAG Search

#### Векторное хранилище

```python
from qdrant_client import QdrantClient

# Индексация материалов
async def index_material(material_id: str, text: str):
    # 1. Эмбеддинги через OpenAI
    embedding = await openai.Embedding.create(
        model="text-embedding-3-small",
        input=text
    )
    
    # 2. Сохранение в Qdrant
    qdrant.upsert(
        collection_name="materials",
        points=[{
            "id": material_id,
            "vector": embedding.data[0].embedding,
            "payload": {"text": text, "user_id": user_id}
        }]
    )

# Контекстный чат
async def ai_chat(user_id: str, question: str):
    # 1. Поиск релевантных материалов
    results = qdrant.search(
        collection_name="materials",
        query_vector=get_embedding(question),
        filter={"user_id": user_id},
        limit=5
    )
    
    # 2. Формирование контекста
    context = "\n".join([r.payload["text"] for r in results])
    
    # 3. Ответ с контекстом
    response = await openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": question}
        ]
    )
    
    return response.choices[0].message.content
```

---

## Фаза 3: Group Features (2-3 недели)

### Неделя 11-12: Групповая логика

#### Database schema

```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    owner_id UUID REFERENCES users(id),
    invite_code VARCHAR(10) UNIQUE,
    created_at TIMESTAMP
);

CREATE TABLE group_members (
    group_id UUID REFERENCES groups(id),
    user_id UUID REFERENCES users(id),
    role ENUM('admin', 'member'),
    joined_at TIMESTAMP
);

CREATE TABLE group_materials (
    id UUID PRIMARY KEY,
    group_id UUID REFERENCES groups(id),
    material_id UUID REFERENCES materials(id),
    uploaded_by UUID REFERENCES users(id)
);
```

#### Механика

1. Админ создает группу → генерируется `t.me/bot?start=group_abc123`
2. Участник переходит по ссылке → автоматически вступает
3. При загрузке материала → webhook отправляет Telegram-уведомления всем участникам
4. Leaderboard: агрегация статистики по `quiz_results` таблице

---

### Неделя 13: Gamification

```python
# Таблица лидеров
async def get_leaderboard(group_id: str):
    stats = await db.query("""
        SELECT 
            u.telegram_username,
            COUNT(DISTINCT qr.material_id) as materials_completed,
            AVG(qr.score) as avg_score,
            SUM(qr.score) as total_points
        FROM quiz_results qr
        JOIN users u ON qr.user_id = u.id
        WHERE qr.group_id = $1
        GROUP BY u.id
        ORDER BY total_points DESC
        LIMIT 10
    """, group_id)
    
    return stats
```

---

## Фаза 4: Polish & Launch (2 недели)

### Неделя 14: Payment Integration

#### Telegram Stars (рекомендую)

```python
# Создание invoice
await bot.send_invoice(
    chat_id=user_id,
    title="Pro подписка",
    description="Безлимит + Аудио",
    payload="pro_subscription_monthly",
    provider_token="",  # Пусто для Stars
    currency="XTR",
    prices=[{"label": "Pro", "amount": 150}]  # 150 Stars
)

# Webhook для успешной оплаты
@bot.pre_checkout_query_handler(func=lambda query: True)
async def process_payment(pre_checkout_query):
    await bot.answer_pre_checkout_query(
        pre_checkout_query.id, 
        ok=True
    )

@bot.message_handler(content_types=['successful_payment'])
async def upgrade_subscription(message):
    await db.update_user_tier(message.from_user.id, "pro")
```

---

### Неделя 15: Marketing & Analytics

#### Метрики для отслеживания

- DAU/MAU (Daily/Monthly Active Users)
- Retention Day 1, 7, 30
- Conversion Free → Pro (цель: 5-10%)
- Group creation rate
- Viral coefficient (сколько юзеров приглашает 1 админ группы)

#### Аналитика

```python
# Mixpanel или PostHog
analytics.track(user_id, "Material Uploaded", {
    "type": file_type,
    "size_mb": file_size,
    "tier": user_tier
})
```

---

## 🚀 Приоритеты для запуска

### Must-Have для MVP

1. ✅ Загрузка текста/PDF
2. ✅ Генерация Smart Notes + TL;DR
3. ✅ Тесты с оценкой
4. ✅ Базовая библиотека (папки)
5. ✅ Оплата подписки

### Can Wait

- ❌ Видео (Slides) - сложно, низкая ценность на старте
- ❌ Диалоговые подкасты - требуют prompt engineering
- ❌ Перевод на другие языки (Use-Case 2) - niche фича

---

## 💰 Бюджет (примерный)

### Разработка
- 3-4 месяца × 1-2 разработчика

### Инфраструктура (месяц)
- Сервер: $50 (AWS Lightsail / DigitalOcean)
- OpenAI API: $200-500 (зависит от объема)
- Storage: $20 (S3)
- Qdrant: Self-hosted = $0

**Total MVP:** ~$300-600/месяц на старте

---

## ⚠️ Риски и рекомендации

1. **Качество конспектов** - ваша главная метрика. Сделайте A/B тест промптов.
2. **Rate limits OpenAI** - добавьте очередь (Celery + Redis) для обработки.
3. **Spam в группах** - админ должен иметь модерацию участников.
4. **GDPR/данные** - храните минимум личной информации, удаляйте контент по запросу.

---

## 📊 Таймлайн

| Фаза | Длительность | Ключевые результаты |
|------|--------------|---------------------|
| Фаза 0: Подготовка | 1-2 недели | Инфраструктура готова |
| Фаза 1: Core MVP | 4-6 недель | Базовые функции работают |
| Фаза 2: Premium | 3-4 недели | Аудио + RAG + презентации |
| Фаза 3: Groups | 2-3 недели | Групповые функции |
| Фаза 4: Launch | 2 недели | Оплата + аналитика |

**Total:** 12-17 недель (3-4 месяца)

---

## 🎯 Следующие шаги

1. Определить команду (frontend dev, backend dev, devops)
2. Создать детальное техническое задание для каждой фазы
3. Настроить project management (Jira, Linear, GitHub Projects)
4. Начать с Фазы 0 параллельно с дизайном UI/UX
5. Запланировать еженедельные демо для валидации фич

---

## 📝 Дополнительные материалы

### Рекомендуемый tech stack

**Frontend:**
- React 18+
- TypeScript
- Vite
- TanStack Query (для API)
- Zustand (state management)

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- Alembic (миграции)
- Celery + Redis (очереди)

**Infrastructure:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- PostgreSQL 15+
- Redis 7+
- Qdrant (векторная БД)

**Monitoring:**
- Sentry (error tracking)
- PostHog / Mixpanel (analytics)
- Prometheus + Grafana (metrics)