# backend/app/models/__init__.py - ОБНОВИ
from app.models.base import Base
from app.models.database import get_db, engine, async_session
from app.models.user import User, SubscriptionTier
from app.models.material import Material, MaterialType, ProcessingStatus
from app.models.folder import Folder
from app.models.group_member import GroupMember, GroupRole
from app.models.ai_output import AIOutput, OutputFormat

__all__ = [
    "Base",
    "get_db",
    "engine", 
    "async_session",
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
]