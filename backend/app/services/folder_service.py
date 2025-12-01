# backend/app/services/folder_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from app.models import Folder, User

class FolderService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_folder(
        self,
        user: User,
        name: str,
        parent_id: Optional[UUID] = None
    ) -> Folder:
        """Создать папку"""
        folder = Folder(
            user_id=user.id,
            name=name,
            parent_id=parent_id
        )
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder
    
    async def get_by_id(self, folder_id: UUID, user_id: UUID) -> Optional[Folder]:
        """Получить папку по ID"""
        result = await self.db.execute(
            select(Folder).where(
                Folder.id == folder_id,
                Folder.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_folders(
        self,
        user_id: UUID,
        parent_id: Optional[UUID] = None
    ) -> List[Folder]:
        """Получить папки пользователя"""
        query = select(Folder).where(Folder.user_id == user_id)
        
        if parent_id:
            query = query.where(Folder.parent_id == parent_id)
        else:
            query = query.where(Folder.parent_id.is_(None))
        
        query = query.order_by(Folder.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def rename_folder(self, folder: Folder, new_name: str) -> Folder:
        """Переименовать папку"""
        folder.name = new_name
        await self.db.commit()
        await self.db.refresh(folder)
        return folder
    
    async def delete_folder(self, folder: Folder) -> None:
        """Удалить папку (без вложенных материалов)"""
        await self.db.delete(folder)
        await self.db.commit()