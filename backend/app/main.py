# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import traceback
import asyncio
from pathlib import Path

from app.api.routes import api_router
from app.core.config import settings
from app.bot.bot import create_bot_application

# Глобальная переменная для бота
bot_app = None
# Глобальный список фоновых задач для graceful shutdown
_background_tasks: set[asyncio.Task] = set()


def schedule_background_task(coro):
    """Создать фоновую задачу с отслеживанием для graceful shutdown"""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    print("🚀 Starting Lecto Backend...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Инициализируем бота
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            bot_app = create_bot_application()
            await bot_app.initialize()

            # Устанавливаем webhook
            webhook_url = f"{settings.FRONTEND_URL}/api/v1/webhook"
            await bot_app.bot.set_webhook(url=webhook_url)
            print(f"✅ Telegram webhook set: {webhook_url}")
        except Exception as e:
            print(f"❌ Failed to setup bot: {e}")
            traceback.print_exc()
    else:
        print("⚠️ TELEGRAM_BOT_TOKEN not set, bot disabled")

    # ===== ЗАПУСК ПЛАНИРОВЩИКА =====
    try:
        from app.services.scheduler import start_scheduler

        start_scheduler()
    except Exception as e:
        print(f"⚠️ Scheduler failed to start: {e}")
        traceback.print_exc()

    yield

    # Shutdown
    # ===== ОЖИДАНИЕ ФОНОВЫХ ЗАДАЧ =====
    if _background_tasks:
        print(f"⏳ Waiting for {_background_tasks.__len__()} background tasks...")
        await asyncio.gather(*_background_tasks, return_exceptions=True)
        print("✅ All background tasks completed")

    # ===== ОСТАНОВКА ПЛАНИРОВЩИКА =====
    try:
        from app.services.scheduler import stop_scheduler

        stop_scheduler()
    except Exception as e:
        print(f"⚠️ Scheduler failed to stop: {e}")

    # ===== ОСТАНОВКА THREAD POOL EXECUTORS =====
    try:
        from app.services.ai_service import _executor as ai_executor

        ai_executor.shutdown(wait=True)
        print("✅ AI ThreadPoolExecutor shutdown")
    except Exception as e:
        print(f"⚠️ AI executor shutdown failed: {e}")

    try:
        from app.services.text_extractor import _executor as text_executor

        text_executor.shutdown(wait=True)
        print("✅ Text extractor ThreadPoolExecutor shutdown")
    except Exception as e:
        print(f"⚠️ Text executor shutdown failed: {e}")

    if bot_app:
        await bot_app.shutdown()
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered educational assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — whitelist origins
allowed_origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL else []
if settings.DEBUG:
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Глобальный обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Error: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# API роуты
app.include_router(api_router, prefix="/api/v1")


# Telegram Webhook endpoint
@app.post("/api/v1/webhook")
async def telegram_webhook(request: Request):
    """Обработчик webhook от Telegram"""
    global bot_app
    if bot_app is None:
        return JSONResponse({"error": "Bot not initialized"}, status_code=500)

    try:
        data = await request.json()
        from telegram import Update

        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return JSONResponse({"ok": True})
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/health")
async def health_check():
    from app.services.scheduler import scheduler

    return {
        "status": "healthy",
        "bot": bot_app is not None,
        "scheduler": scheduler.running if scheduler else False,
    }


# Путь к статическим файлам frontend
STATIC_DIR = Path(__file__).parent.parent / "static"
ASSETS_DIR = STATIC_DIR / "assets"
INDEX_FILE = STATIC_DIR / "index.html"

print(f"📁 Static dir: {STATIC_DIR}")
print(f"📁 Static dir exists: {STATIC_DIR.exists()}")
print(f"📁 Assets dir exists: {ASSETS_DIR.exists()}")
print(f"📁 Index file exists: {INDEX_FILE.exists()}")

# Раздаём статику frontend (если папки существуют)
if STATIC_DIR.exists() and ASSETS_DIR.exists() and INDEX_FILE.exists():
    print("✅ Serving static files from:", STATIC_DIR)

    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    @app.get("/vite.svg")
    async def serve_vite_svg():
        svg_path = STATIC_DIR / "vite.svg"
        if svg_path.exists():
            return FileResponse(svg_path)
        return JSONResponse({"error": "not found"}, status_code=404)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"error": "not found"}, status_code=404)

        file_path = (STATIC_DIR / full_path).resolve()

        # Path traversal защита
        if not file_path.is_relative_to(STATIC_DIR.resolve()):
            return JSONResponse({"error": "not found"}, status_code=404)

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(INDEX_FILE)
else:
    print("⚠️ Static files not found, running API only mode")
    print(f"   To serve frontend, copy build files to: {STATIC_DIR}")

    @app.get("/")
    async def root():
        return {
            "message": "Lecto API is running",
            "docs": "/docs",
            "note": "Frontend not configured. Copy frontend build to 'static' folder.",
        }
