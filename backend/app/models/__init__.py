# backend/app/models/__init__.py
from app.models.base import Base, get_db, engine, AsyncSessionLocal
from app.models.user import User, SubscriptionTier
from app.models.material import Material, MaterialType, ProcessingStatus
from app.models.folder import Folder
from app.models.group_member import GroupMember, GroupRole
from app.models.ai_output import AIOutput, OutputFormat
from app.models.quiz_result import QuizResult

async_session = AsyncSessionLocal

__all__ = [
    "Base",
    "get_db",
    "engine", 
    "async_session",
    "AsyncSessionLocal",
    "User",
    "SubscriptionTier",
    "Material",
    "MaterialType",
    "ProcessingStatus",
    "Folder",
    "GroupMember",
    "GroupRole",
    "AIOutput",
    "OutputFormat",
    "QuizResult",
]