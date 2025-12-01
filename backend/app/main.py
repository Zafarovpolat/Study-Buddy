# backend/app/main.py - ЗАМЕНИ ПОЛНОСТЬЮ
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import traceback
from pathlib import Path

from app.api.routes import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting EduAI Backend...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    print("👋 Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered educational assistant",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

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
    
    # Раздаём assets (JS, CSS, картинки)
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    
    # Для других статических файлов в корне (favicon, etc)
    @app.get("/vite.svg")
    async def serve_vite_svg():
        svg_path = STATIC_DIR / "vite.svg"
        if svg_path.exists():
            return FileResponse(svg_path)
        return JSONResponse({"error": "not found"}, status_code=404)
    
    # Все остальные роуты -> index.html (SPA)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Пропускаем API роуты
        if full_path.startswith("api/"):
            return JSONResponse({"error": "not found"}, status_code=404)
        
        # Если файл существует - отдаём его
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Иначе отдаём index.html (для SPA роутинга)
        return FileResponse(INDEX_FILE)
else:
    print("⚠️ Static files not found, running API only mode")
    print(f"   To serve frontend, copy build files to: {STATIC_DIR}")
    
    @app.get("/")
    async def root():
        return {
            "message": "EduAI API is running", 
            "docs": "/docs",
            "note": "Frontend not configured. Copy frontend build to 'static' folder."
        }