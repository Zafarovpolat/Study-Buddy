from fastapi import APIRouter
from app.api.routes import users, materials, folders, processing, outputs

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(materials.router)
api_router.include_router(folders.router)
api_router.include_router(processing.router)
api_router.include_router(outputs.router)