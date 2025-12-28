# backend/app/api/routes/__init__.py
from fastapi import APIRouter
from app.api.routes.users import router as users_router
from app.api.routes.materials import router as materials_router
from app.api.routes.folders import router as folders_router
from app.api.routes.processing import router as processing_router
from app.api.routes.outputs import router as outputs_router
from app.api.routes.groups import router as groups_router
from app.api.routes.search import router as search_router
from app.api.routes.presentations import router as presentations_router
from app.api.routes.debate import router as debate_router  # Добавить
from app.api.routes.insights import router as insights_router


api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(materials_router)
api_router.include_router(folders_router)
api_router.include_router(processing_router)
api_router.include_router(outputs_router)
api_router.include_router(groups_router)
api_router.include_router(search_router)
api_router.include_router(presentations_router)
api_router.include_router(debate_router)  # Добавить
api_router.include_router(insights_router)
