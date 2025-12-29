# 🎓 Lecto — AI-помощник для учёбы

<div align="center">

![Lecto](https://img.shields.io/badge/Lecto-AI%20Study%20Buddy-blueviolet?style=for-the-badge&logo=telegram)
![Version](https://img.shields.io/badge/version-1.1.0-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/status-Production-green?style=for-the-badge)

**Telegram Mini App для эффективной учёбы с искусственным интеллектом**

[Открыть бота](https://t.me/lectoaibot) · [Документация](PROJECT_REVIEW.md) · [План развития](plan.md)

</div>

---

## ✨ Возможности

### 📤 Загрузка материалов
- **PDF, DOCX, TXT** — извлечение текста
- **Изображения** — OCR через Gemini Vision
- **Камера** — сканирование конспектов
- **Тема** — генерация материала по названию

### 🤖 AI обработка (Gemini 2.0 Flash)
| Формат | Описание |
|--------|----------|
| 📝 **Smart Notes** | Структурированный конспект |
| ⚡ **TL;DR** | Краткое содержание за 30 сек |
| ❓ **Тесты** | 15-20 вопросов с объяснениями |
| 📚 **Глоссарий** | Ключевые термины и определения |
| 🃏 **Flashcards** | Карточки для запоминания |

### ⚔️ AI Дебаты
- Выбери тезис — AI займёт противоположную позицию
- 3 уровня сложности: Новичок, Опытный, Эксперт
- Судья оценивает аргументы и выносит вердикт
- Получай советы по улучшению навыков

### 📊 Генератор презентаций
- AI создаёт структуру слайдов
- 4 стиля: деловой, учебный, креативный, минималистичный
- 4 цветовые темы
- Скачивание готового PPTX

### 🔍 Умный поиск (RAG)
- Семантический поиск по всем материалам
- "Спроси свою библиотеку" — ответы на вопросы
- Автоматическая индексация при загрузке

### 👥 Групповая учёба
- Создание учебных групп
- Вступление по коду приглашения
- Общие материалы и тесты
- 🏆 Leaderboard с рейтингом участников
- Результаты тестов для владельца группы

### 💰 Монетизация
| | Free | Pro (150⭐/мес) |
|---|:---:|:---:|
| Материалов в день | 5 | ∞ |
| AI обработка | ✅ | ✅ |
| Группы | ✅ | ✅ |
| AI Дебаты (сложный) | ❌ | ✅ |
| Генератор презентаций | ❌ | ✅ |
| RAG поиск | ❌ | ✅ |

---

## 🛠️ Технологии

### Backend
```
Python 3.11 · FastAPI · SQLAlchemy 2.0 (async)
PostgreSQL (Supabase) · APScheduler
Google Gemini 2.0 Flash · python-telegram-bot
python-pptx
```

### Frontend
```
React 18 · TypeScript · Vite
Tailwind CSS · Zustand
Telegram WebApp SDK
```

### Инфраструктура
```
Render.com (Backend + Static)
Supabase (PostgreSQL)
Alembic (Миграции)
```

---

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL (или Supabase)
- Telegram Bot Token
- Gemini API Key

### Установка

```bash
# 1. Клонируем репозиторий
git clone https://github.com/zafarovpolat/lecto.git
cd lecto

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Заполни переменные
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd ../frontend
npm install
npm run build             # Сборка в backend/static

# 4. Запуск
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Переменные окружения (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
WEBAPP_URL=https://your-app.onrender.com

# AI
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash-exp

# Settings
DEBUG=false
FREE_DAILY_LIMIT=5
MAX_FILE_SIZE_MB=20
```

---

## 📁 Структура проекта

```
lecto/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── bot/              # Telegram bot
│   │   ├── core/             # Config
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # DB migrations
│   ├── static/               # Frontend build
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Pages
│   │   ├── lib/              # API, Telegram SDK
│   │   └── store/            # Zustand
│   └── package.json
│
├── plan.md                   # План развития
├── PROJECT_REVIEW.md         # Техническая документация
└── README.md
```

---

## 🔐 API Endpoints

### Основные
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/users/me` | Текущий пользователь |
| POST | `/api/v1/materials/upload` | Загрузить материал |
| POST | `/api/v1/processing/material/{id}` | Обработать AI |
| GET | `/api/v1/outputs/material/{id}` | Получить результаты |

### Группы
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/groups/` | Создать группу |
| POST | `/api/v1/groups/join` | Вступить по коду |
| GET | `/api/v1/groups/{id}/leaderboard` | Рейтинг |

### AI функции
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/search/ask` | RAG поиск |
| POST | `/api/v1/debate/start` | Начать дебаты |
| POST | `/api/v1/presentations/download` | Скачать PPTX |

---

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────┐
│                 Telegram Client                      │
│                   (Mini App)                         │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              React Frontend (Vite)                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐   │
│  │ HomePage │ │ Material │ │ PresentationGen   │   │
│  │ Groups   │ │ Outputs  │ │ DebateTab         │   │
│  └──────────┘ └──────────┘ └───────────────────┘   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                         │
│  ┌────────────────────────────────────────────────┐ │
│  │ Services: AI, Vector, Debate, Presentation     │ │
│  │ Routes: users, materials, groups, search...    │ │
│  └────────────────────────────────────────────────┘ │
│                        │                             │
│            ┌───────────┴───────────┐                │
│            ▼                       ▼                │
│   ┌─────────────────┐   ┌─────────────────┐        │
│   │   Gemini AI     │   │   PostgreSQL    │        │
│   │   (2.0 Flash)   │   │   (Supabase)    │        │
│   └─────────────────┘   └─────────────────┘        │
└─────────────────────────────────────────────────────┘
```

---

## 📈 Статус проекта

```
MVP Progress: ████████████████████ 100%

✅ Загрузка материалов (PDF, DOCX, изображения, OCR)
✅ AI обработка (5 форматов)
✅ Telegram авторизация и Stars
✅ Группы и Leaderboard
✅ Реферальная система
✅ Push уведомления
✅ Vector Search (RAG)
✅ AI Дебаты
✅ Генератор презентаций
✅ Онбординг
✅ UI компоненты (Badge, Skeleton, ProgressBar, SliderTabs)
✅ Персонализация онбординга (направление, регион)
✅ Инсайты модуль
✅ Геймификация (Intellect Points)
✅ ProWall (Premium paywall)
✅ Белая/фиолетовая тема UI
```

---

## 📞 Контакты

- **Telegram Bot**: [@lectoaibot](https://t.me/lectoaibot)
- **Разработчик**: [@zafarovpolat](https://t.me/zafarovpolat)
- **GitHub**: [zafarovpolat](https://github.com/zafarovpolat)

---

## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE)

---

<div align="center">

**Сделано с ❤️ для студентов всего мира**

</div>