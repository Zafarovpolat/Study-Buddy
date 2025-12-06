# Study Buddy - Project Review & Implementation Plan

## 📂 Project Structure Overview

### Backend (`/backend`)
Built with **FastAPI** and **PostgreSQL**.

*   **`app/main.py`**: Entry point. Initializes FastAPI app, database, and Telegram bot webhook.
*   **`app/api/`**: API routes.
    *   `routes/users.py`: User management, subscription, limits.
    *   `routes/materials.py`: Material management (CRUD).
    *   `routes/processing.py`: Triggering AI processing.
*   **`app/bot/`**: Telegram Bot logic (using `python-telegram-bot`).
    *   `bot.py`: Bot application setup.
    *   `handlers.py`: Command handlers (`/start`, `/pro`) and payment logic.
*   **`app/core/`**: Configuration.
    *   `config.py`: Environment variables (Database URL, API Keys).
*   **`app/models/`**: SQLAlchemy models.
    *   `user.py`: User schema, subscription tier, streaks.
    *   `material.py`: Material schema, processing status.
    *   `ai_output.py`: Generated content (notes, quizzes).
*   **`app/services/`**: Business logic.
    *   `ai_service.py`: Integration with **Gemini 2.0 Flash** (Text generation, OCR).
    *   `payment_service.py`: Telegram Stars payment processing.
    *   `processing_service.py`: Orchestrates material processing pipeline.
    *   `text_extractor.py`: Extracts text from PDF, DOCX, Images.
    *   `user_service.py`: User management, streaks, rate limits.
*   **`alembic/`**: Database migrations.

### Frontend (`/frontend`)
Built with **React**, **Vite**, and **Tailwind CSS**.

*   **`src/App.tsx`**: Main router and layout.
*   **`src/pages/`**: Application screens.
    *   `HomePage.tsx`: Dashboard with Quick Actions, Daily Plan.
    *   `MaterialPage.tsx`: Detailed view of a material with AI outputs.
*   **`src/components/`**: Reusable UI components.
    *   `ui/`: Base components (Button, Card, Input).
    *   `MaterialCard.tsx`: Card component for material list.
    *   `UploadModal.tsx`: File upload interface.
*   **`src/lib/`**: Utilities.
    *   `api.ts`: Axios client for backend API.
    *   `telegram.ts`: Telegram WebApp integration (Theme, Haptic, MainButton).
*   **`src/store/`**: State management (Zustand).
    *   `useStore.ts`: Global state for user, materials, folders.

---

## 📊 Project Status Review

### ✅ Implemented Features (Ready)

**1. Business Logic & Monetization**
*   **Free Tier**: Daily limit of 3 uploads implemented (`UserService`).
*   **Pro Subscription**: $4.99/month via Telegram Stars. Logic for removing limits is active.
*   **Micro-transactions**: Infrastructure for one-time payments exists.

**2. User Journey**
*   **Dashboard**: Header with Streak Counter, Quick Actions (Scan, Upload), Daily Plan (basic list).
*   **Knowledge Base**: "Personal" tab, Folder navigation, Material list.
*   **Material View**: Display of Smart Notes, Quizzes, Glossaries.

**3. Technical Pipeline**
*   **Ingestion**: File upload (PDF, DOCX, Images) works.
*   **Processing**:
    *   **OCR**: Gemini Vision used for images.
    *   **Text Extraction**: `pypdf` and `python-docx` for documents.
*   **AI Structuring**: Gemini 2.0 Flash generates structured notes, TL;DR.
*   **Generation**: Quizzes, Glossaries, and Flashcards are generated.

**4. Tech Stack**
*   **Frontend**: React + Telegram UI Kit.
*   **Backend**: FastAPI + PostgreSQL + SQLAlchemy.
*   **AI**: Gemini 2.0 Flash (Efficient and cost-effective).

---

## 🚀 Implementation Plan (Next Steps)

This plan focuses on filling the gaps identified in the "Missing / To Do" section, excluding Audio/Whisper features as requested.

### Phase 1: Viral Loop & Social Mechanics (High Priority)
*Goal: Implement the "Group" mechanics to drive user growth.*

1.  **Backend: Group Folders**
    *   Update `Folder` model to support `is_group=True` and `share_link`.
    *   Create `UserGroup` association table (User <-> Folder).
    *   Add API endpoints for creating groups and joining via link.
2.  **Backend: Referral System**
    *   Add `referred_by` field to `User` model.
    *   Implement logic: When 5 users join via a user's link -> Grant free PRO.
    *   Generate unique referral links (`t.me/bot?start=ref_123`).
3.  **Frontend: Group Interface**
    *   Add "Groups" tab to `HomePage`.
    *   Create "Create Group" modal.
    *   Display "Invite Friends" banner with progress bar (e.g., "2/5 friends invited").

### Phase 2: Advanced AI Tools (Differentiation)
*Goal: Add unique value that separates the app from simple file readers.*

1.  **AI Debate (Text-based)**
    *   *Note: Implementing text-based debate since audio is excluded.*
    *   **Backend**: Create `DebateSession` model.
    *   **AI**: Implement `DebateService` using Gemini to act as a "Skeptic Professor".
    *   **Frontend**: Chat interface for debating specific topics from a material.
2.  **Neuro-Lexicon (Spaced Repetition)**
    *   **Backend**: Create `UserVocabulary` table (term, definition, next_review_date).
    *   **AI**: "Auto-Linking" - Detect terms in notes and link them to the lexicon.
    *   **Frontend**: "Swipe" interface (Tinder-style) for learning terms: "Know" / "Don't Know".
    *   **Scheduler**: Background job to send push notifications for terms due for review.

### Phase 3: Search & Personalization (Retention)
*Goal: Make the app smarter as more content is added.*

1.  **Vector Search (Pinecone/PGVector)**
    *   *Recommendation: Use `pgvector` (PostgreSQL extension) to keep stack simple instead of adding Pinecone.*
    *   **Backend**: Generate embeddings for all materials using Gemini.
    *   **Feature**: "Ask your Library" - Chat with all your materials at once.
2.  **Smart Daily Plan**
    *   Improve `Daily Plan` algorithm to recommend materials based on Spaced Repetition (not just random/recent).

### Phase 4: Polish & Optimization
1.  **Performance**: Optimize large file processing.
2.  **UX**: Add onboarding tutorial for new users.
3.  **Notifications**: Reminders to keep the streak alive.

---

## 📝 Immediate Action Items (Next 2 Weeks)

1.  **Database Migration**: Add `is_group` to Folders and create `UserGroup` table.
2.  **API**: Implement `POST /api/groups` and `POST /api/groups/join`.
3.  **Frontend**: Add "Groups" tab and "Invite" UI.
