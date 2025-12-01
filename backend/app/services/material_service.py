# backend/app/services/material_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
import aiofiles
import os
from pathlib import Path

from app.models import Material, MaterialType, ProcessingStatus, User, Folder
from app.core.config import settings

class MaterialService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_material(
        self,
        user: User,
        title: str,
        material_type: MaterialType,
        file_path: Optional[str] = None,
        original_filename: Optional[str] = None,
        folder_id: Optional[UUID] = None,
        raw_content: Optional[str] = None
    ) -> Material:
        """Создать новый материал"""
        material = Material(
            user_id=user.id,
            title=title,
            material_type=material_type,
            file_path=file_path,
            original_filename=original_filename,
            folder_id=folder_id,
            raw_content=raw_content,
            status=ProcessingStatus.PENDING
        )
        self.db.add(material)
        await self.db.commit()
        await self.db.refresh(material)
        return material
    
    async def get_by_id(self, material_id: UUID, user_id: UUID) -> Optional[Material]:
        """Получить материал по ID (с проверкой владельца)"""
        result = await self.db.execute(
            select(Material)
            .options(selectinload(Material.outputs))
            .where(Material.id == material_id, Material.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_materials(
        self, 
        user_id: UUID, 
        folder_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Material]:
        """Получить материалы пользователя"""
        query = select(Material).where(Material.user_id == user_id)
        
        if folder_id:
            query = query.where(Material.folder_id == folder_id)
        else:
            query = query.where(Material.folder_id.is_(None))
        
        query = query.order_by(Material.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_status(
        self, 
        material: Material, 
        status: ProcessingStatus,
        raw_content: Optional[str] = None
    ) -> Material:
        """Обновить статус материала"""
        material.status = status
        if raw_content:
            material.raw_content = raw_content
        await self.db.commit()
        await self.db.refresh(material)
        return material
    
    async def delete_material(self, material: Material) -> None:
        """Удалить материал"""
        # Удаляем файл если есть
        if material.file_path and os.path.exists(material.file_path):
            os.remove(material.file_path)
        
        await self.db.delete(material)
        await self.db.commit()
    
    @staticmethod
    async def save_uploaded_file(
        file_content: bytes,
        filename: str,
        user_id: UUID
    ) -> str:
        """Сохранить загруженный файл"""
        # Создаём директорию пользователя
        user_dir = Path(settings.UPLOAD_DIR) / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        import uuid
        ext = Path(filename).suffix
        safe_filename = f"{uuid.uuid4()}{ext}"
        file_path = user_dir / safe_filename
        
        # Сохраняем файл
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        return str(file_path)
    
    @staticmethod
    def detect_material_type(filename: str) -> MaterialType:
        """Определить тип материала по расширению"""
        ext = Path(filename).suffix.lower()
        type_map = {
            '.pdf': MaterialType.PDF,
            '.docx': MaterialType.DOCX,
            '.doc': MaterialType.DOCX,
            '.txt': MaterialType.TXT,
            '.png': MaterialType.IMAGE,
            '.jpg': MaterialType.IMAGE,
            '.jpeg': MaterialType.IMAGE,
            '.mp3': MaterialType.AUDIO,
            '.wav': MaterialType.AUDIO,
            '.m4a': MaterialType.AUDIO,
        }
        return type_map.get(ext, MaterialType.TXT)