# Lecto - Полный обзор проекта и технический статус

> **Обновлено**: 2025-12-29  
> **Статус**: MVP 100% готов + Новые модули 🎉  
> **Версия**: 1.1.0

---

## 📊 Общая информация

**Lecto** — Telegram Mini App для эффективной учёбы с искусственным интеллектом. Загружай материалы (PDF, DOCX, изображения) — получай умные конспекты, тесты, карточки, глоссарий, презентации и участвуй в AI дебатах!

### Ключевые технологии
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.0 (async)
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Database**: PostgreSQL (Supabase) - Session Pooler
- **AI**: Google Gemini 2.0 Flash + text-embedding-004
- **Bot**: python-telegram-bot
- **Deploy**: Render.com

---

## 📂 Детальная структура проекта

### Backend (`/backend`)

```
backend/
├── alembic/                          # Миграции БД
│   ├── env.py                        # Конфигурация Alembic
│   └── versions/
│       └── 001_initial.py            # Миграция (VARCHAR, без ENUM)
│
├── app/
│   ├── main.py                       # 🚀 Entry point: FastAPI, WebHook, Scheduler
│   │
│   ├── core/
│   │   └── config.py                 # Переменные окружения
│   │
│   ├── models/                       # SQLAlchemy модели (async)
│   │   ├── __init__.py               # Экспорт всех моделей
│   │   ├── base.py                   # AsyncEngine, SessionLocal, Base
│   │   ├── user.py                   # User: подписка, streak, рефералы
│   │   ├── material.py               # Material: файлы, OCR, статус
│   │   ├── folder.py                 # Folder: папки + группы (is_group=True)
│   │   ├── group_member.py           # GroupMember: участники групп
│   │   ├── ai_output.py              # AIOutput: результаты AI обработки
│   │   ├── quiz_result.py            # QuizResult: результаты тестов
│   │   └── text_chunk.py             # TextChunk: chunks для vector search
│   │
│   ├── api/
│   │   ├── deps.py                   # Зависимости: get_db, get_current_user
│   │   ├── schemas.py                # Pydantic схемы
│   │   └── routes/
│   │       ├── __init__.py           # api_router
│   │       ├── users.py              # /users/*
│   │       ├── materials.py          # /materials/*
│   │       ├── folders.py            # /folders/*
│   │       ├── groups.py             # /groups/*
│   │       ├── processing.py         # /processing/*
│   │       ├── outputs.py            # /outputs/*
│   │       ├── search.py             # /search/* (RAG, semantic)
│   │       ├── presentations.py      # /presentations/* 🆕
│   │       └── debate.py             # /debate/* 🆕
│   │
│   ├── services/
│   │   ├── user_service.py           # Авторизация, streak, лимиты
│   │   ├── material_service.py       # CRUD материалов
│   │   ├── folder_service.py         # CRUD папок
│   │   ├── group_service.py          # Группы, рефералы, leaderboard
│   │   ├── ai_service.py             # Gemini API: 5 форматов
│   │   ├── processing_service.py     # Обработка материалов
│   │   ├── text_extractor.py         # PDF, DOCX, OCR
│   │   ├── payment_service.py        # Telegram Stars
│   │   ├── notification_service.py   # Push уведомления
│   │   ├── scheduler.py              # APScheduler
│   │   ├── vector_service.py         # RAG: embeddings, semantic search
│   │   ├── presentation_service.py   # PPTX генерация 🆕
│   │   └── debate_service.py         # AI дебаты 🆕
│   │
│   └── bot/
│       ├── bot.py                    # Telegram bot app
│       └── handlers.py               # /start, /pro, /stats, /invite
│
├── requirements.txt
├── reset_db.py                       # Сброс БД
└── run_bot.py                        # Polling режим (dev)
```

### Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── main.tsx                      # React entry
│   ├── App.tsx                       # Router
│   ├── index.css                     # Global + Tailwind
│   │
│   ├── pages/
│   │   ├── HomePage.tsx              # Вкладки, поиск, breadcrumbs
│   │   ├── MaterialPage.tsx          # Деталь + AI outputs + Debate
│   │   └── GroupResultsPage.tsx      # Результаты тестов (owner)
│   │
│   ├── components/
│   │   ├── Header.tsx                # Streak, баланс, поиск
│   │   ├── MaterialCard.tsx          # Карточка материала
│   │   ├── MaterialActions.tsx       # Редактировать, удалить
│   │   ├── UploadModal.tsx           # 5 способов загрузки
│   │   ├── OutputViewer.tsx          # AI outputs: тест, карточки, дебаты
│   │   ├── GroupsTab.tsx             # Группы: создание, вступление
│   │   ├── LeaderboardTab.tsx        # Рейтинг участников
│   │   ├── AskLibrary.tsx            # "Спроси библиотеку" (RAG)
│   │   ├── PresentationGenerator.tsx # Генератор презентаций 🆕
│   │   ├── DebateTab.tsx             # AI Дебаты 🆕
│   │   └── ui/                       # Button, Card, Input...
│   │
│   ├── lib/
│   │   ├── api.ts                    # Axios: все API методы
│   │   └── telegram.ts               # WebApp SDK
│   │
│   └── store/
│       └── useStore.ts               # Zustand
│
├── package.json
│   ├── vite.config.ts
└── tailwind.config.js
```

---

## ✅ Реализованные функции

### 1. Загрузка и обработка материалов ✅

| Функция | Endpoint | Статус |
|---------|----------|--------|
| Загрузка PDF/DOCX/TXT | `POST /materials/upload` | ✅ |
| Загрузка изображений (OCR) | `POST /materials/upload` | ✅ |
| Сканирование камерой | `POST /materials/scan` | ✅ |
| Создание из текста | `POST /materials/text` | ✅ |
| Генерация по теме | `POST /materials/generate-from-topic` | ✅ |

### 2. AI Обработка (Gemini 2.0 Flash) ✅

| Формат | Описание | Статус |
|--------|----------|--------|
| `smart_notes` | Структурированный конспект | ✅ |
| `tldr` | Краткое содержание | ✅ |
| `quiz` | 15-20 вопросов (3 уровня) | ✅ |
| `glossary` | Глоссарий терминов | ✅ |
| `flashcards` | Карточки "вопрос-ответ" | ✅ |

### 3. AI Дебаты 🆕 ✅

| Функция | Endpoint | Статус |
|---------|----------|--------|
| Начать дебаты | `POST /debate/start` | ✅ |
| Продолжить дебаты | `POST /debate/continue` | ✅ |
| Оценка судьи | `POST /debate/judge` | ✅ |

**Особенности:**
- 3 уровня сложности: easy, medium, hard (Pro only)
- AI автоматически занимает противоположную позицию
- Судья оценивает аргументы и выносит вердикт
- Советы по улучшению навыков аргументации

### 4. Генератор презентаций 🆕 ✅

| Функция | Endpoint | Статус |
|---------|----------|--------|
| Превью структуры | `POST /presentations/generate` | ✅ |
| Скачать PPTX | `POST /presentations/download` | ✅ |

**Особенности:**
- 4 стиля: professional, educational, creative, minimal
- 4 цветовые темы: blue, green, purple, orange
- 5 типов слайдов: title, content, two_columns, quote, conclusion
- Заметки докладчика
- Только для Pro пользователей

### 5. Vector Search (RAG) ✅

| Компонент | Реализация | Статус |
|-----------|------------|--------|
| Chunking | `VectorService._split_into_chunks()` | ✅ |
| Embeddings | Gemini `text-embedding-004` | ✅ |
| Storage | `text_chunks` таблица | ✅ |
| RAG endpoint | `POST /search/ask` | ✅ |
| Semantic search | `GET /search/semantic` | ✅ |
| UI | `AskLibrary.tsx` | ✅ |
| Pro-only | `user.can_use_feature('vector_search')` | ✅ |

### 6. Социальные функции — Группы ✅

| Функция | Endpoint | Статус |
|---------|----------|--------|
| Создание группы | `POST /groups/` | ✅ |
| Вступление по коду | `POST /groups/join` | ✅ |
| Материалы группы | `GET /materials/group/{id}` | ✅ |
| Результаты тестов | `GET /groups/{id}/quiz-results` | ✅ |
| Leaderboard | `GET /groups/{id}/leaderboard` | ✅ |

### 7. Монетизация ✅

| Функция | Реализация | Статус |
|---------|------------|--------|
| Free тариф (3/день) | `user_service.check_rate_limit()` | ✅ |
| Pro подписка | Telegram Stars | ✅ |
| SOS тариф (24 часа) | Telegram Stars | ✅ |
| Pro за 5 рефералов | `group_service._grant_referral_pro()` | ✅ |

**Цены**: 
- Pro: 1 мес = 150⭐, 1 год = 1200⭐
- SOS: 24 часа безлимита

#### Тарифы и лимиты

| Параметр | Free | Pro | SOS |
|----------|------|-----|-----|
| Запросов в день | 3 | ∞ | ∞ |
| Макс. групп | 3 | 30 | 0 |
| Участников в группе | 5 | ∞ | — |
| Материалов в группе | 10 | ∞ | ∞ |
| Аудио (минут) | 15 | 120 | 120 |
| Функции | Базовые | Все | Все |
| Длительность | — | 1 мес/год | 24 часа |

**Особенности SOS тарифа:**
- Все Pro-функции на 24 часа
- Нельзя создавать группы
- Идеально для экзаменов и дедлайнов

---

## 📊 Статус по модулям

```
Backend ████████████████ 100%
├── Users              ████████████ 100%
├── Materials          ████████████ 100%
├── Folders            ████████████ 100%
├── Groups             ████████████ 100%
├── AI Processing      ████████████ 100%
├── Vector Search      ████████████ 100%
├── Presentations      ████████████ 100% 🆕
├── Debate             ████████████ 100% 🆕
├── Payments           ████████████ 100%
├── Notifications      ████████████ 100%
└── Scheduler          ████████████ 100%

Frontend ████████████████ 100%
├── HomePage           ████████████ 100%
├── MaterialPage       ████████████ 100%
├── OutputViewer       ████████████ 100%
├── DebateTab          ████████████ 100% 🆕
├── PresentationGen    ████████████ 100% 🆕
├── GroupsTab          ████████████ 100%
├── LeaderboardTab     ████████████ 100%
├── OnboardingModal    ████████████ 100%
├── AskLibrary         ████████████ 100%
└── InviteBanner       ████████████ 100%

Общий прогресс: 100% 🎉
```

---

## 🔐 API Endpoints

### Users
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/users/me` | Текущий пользователь |
| GET | `/api/v1/users/me/limits` | Лимиты и подписка |
| GET | `/api/v1/users/me/streak` | Streak информация |

### Materials
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/materials/` | Список материалов |
| POST | `/api/v1/materials/upload` | Загрузить файл |
| POST | `/api/v1/materials/text` | Создать из текста |
| POST | `/api/v1/materials/scan` | OCR сканирование |
| POST | `/api/v1/materials/generate-from-topic` | Генерация по теме |
| GET | `/api/v1/materials/search/all` | Глобальный поиск |

### Groups
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/groups/` | Мои группы |
| POST | `/api/v1/groups/` | Создать группу |
| POST | `/api/v1/groups/join` | Вступить по коду |
| GET | `/api/v1/groups/{id}/leaderboard` | Рейтинг участников |
| GET | `/api/v1/groups/{id}/quiz-results` | Результаты тестов |

### Search (RAG)
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/search/ask` | "Спроси библиотеку" |
| GET | `/api/v1/search/semantic` | Семантический поиск |
| POST | `/api/v1/search/index/{id}` | Проиндексировать материал |

### Presentations 🆕
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/presentations/generate` | Генерация превью |
| POST | `/api/v1/presentations/download` | Скачать PPTX |

### Debate 🆕
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/debate/start` | Начать дебаты |
| POST | `/api/v1/debate/continue` | Продолжить дебаты |
| POST | `/api/v1/debate/judge` | Оценка судьи |

---

## 🛠 Технический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| **Backend** | FastAPI | 0.111+ |
| **ORM** | SQLAlchemy (async) | 2.0+ |
| **Database** | PostgreSQL (Supabase) | 15+ |
| **AI** | Gemini 2.0 Flash | API |
| **Embeddings** | text-embedding-004 | API |
| **Bot** | python-telegram-bot | 21+ |
| **Scheduler** | APScheduler | 3.10+ |
| **PPTX** | python-pptx | 0.6+ |
| **Frontend** | React | 18 |
| **State** | Zustand | 4+ |
| **Styling** | Tailwind CSS | 3+ |

---

## 🔄 Changelog

### 2025-12-12 (вечер)
- ✅ **AI Дебаты** — 3 уровня сложности, судья, советы
- ✅ **Генератор презентаций** — PPTX с 4 темами и стилями
- ✅ DebateTab интегрирован в OutputViewer
- ✅ PresentationGenerator добавлен на HomePage
- 🎉 **MVP 100% готов!**

### 2025-12-29
- ✅ **UI компоненты** — ProgressBar (Badge, Skeleton, SliderTabs удалены как неиспользуемые)
- ✅ **Онбординг v2** — Персонализация (выбор направления и региона)
- ✅ **User модель** — Новые поля: field_of_study, region, intellect_points, debates_won
- ✅ **Инсайты модуль** — Backend + Frontend (без контента)
- ✅ **UI тема** — Обновление на белую/фиолетовую цветовую схему

### 2026-04-03 — Оптимизация и рефакторинг
- ✅ **Безопасность** — HMAC-валидация Telegram Init Data, admin-only debug endpoints, CORS whitelist, SSL fix, path traversal
- ✅ **Runtime баги** — Исправлены `.value` на строковых колонках, XSS через DOMPurify, `onKeyPress` → `onKeyDown`
- ✅ **Мёртвый код** — Удалены 7 файлов (OnboardingModal, ProWall, InviteBanner, SliderTabs, Badge, Skeleton, App.css), 8 зависимостей
- ✅ **Дублирование** — Созданы `utils/text.py`, `utils/typing.py`, `utils/json.py`
- ✅ **Backend perf** — N+1 → GROUP BY, `asyncio.gather()` для AI, graceful shutdown
- ✅ **Frontend perf** — Code splitting (-49% initial load), manualChunks, polling fix, поиск работает
- ✅ **Типизация** — Экспортированы интерфейсы, `any` → `unknown` в catch
- ✅ **UI палитра** — Убраны все `dark:` классы, только белая/фиолетовая тема
- ✅ **Эмодзи → SVG** — Все эмодзи заменены на Lucide иконки
- ✅ **UX** — Escape key для модалок, результаты поиска отображаются

### 2025-12-12 (утро)
- ✅ Vector Search (RAG) — VectorService
- ✅ Leaderboard в группах
- ✅ Онбординг для новых пользователей
- ✅ AskLibrary UI

### 2025-12-11
- ✅ Глобальный поиск по материалам
- ✅ Push уведомления
- ✅ Миграция БД на Supabase PostgreSQL

---

## 📞 Связь и поддержка

- **Telegram Bot**: [@lectoaibot](https://t.me/lectoaibot)
- **Support**: @zafarovpolat
- **Repository**: [GitHub](https://github.com/zafarovpolat)

---

**Сделано с ❤️ для студентов всего мира**