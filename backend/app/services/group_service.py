# backend/app/services/group_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from app.models import User, Folder, GroupMember, Material, SubscriptionTier


def get_val(v):
    """Безопасно получить value из enum или вернуть строку"""
    return v.value if hasattr(v, 'value') else v


class GroupRole:
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class GroupService:
    REFERRAL_PRO_THRESHOLD = 5
    REFERRAL_PRO_DAYS = 30
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _count_user_groups(self, user: User) -> int:
        """Подсчёт групп, созданных пользователем"""
        result = await self.db.execute(
            select(func.count(Folder.id)).where(
                Folder.user_id == user.id,
                Folder.is_group == True
            )
        )
        return result.scalar() or 0
    
    async def _count_group_materials(self, group_id: UUID) -> int:
    """Подсчёт материалов в группе (группа = folder с is_group=True)"""
    result = await self.db.execute(
        select(func.count(Material.id)).where(Material.folder_id == group_id)
    )
    return result.scalar() or 0
    
    async def create_group(
        self,
        owner: User,
        name: str,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Folder]]:
        """Создать группу с проверкой лимитов"""
        
        # Проверка лимита групп
        current_groups = await self._count_user_groups(owner)
        max_groups = owner.max_groups
        
        if current_groups >= max_groups:
            if owner.effective_tier == SubscriptionTier.SOS:
                return False, "SOS тариф не позволяет создавать группы", None
            elif owner.effective_tier == SubscriptionTier.FREE:
                return False, f"Лимит групп исчерпан ({max_groups}). Оформите Pro для создания до 30 групп.", None
            else:
                return False, f"Достигнут лимит групп ({max_groups})", None
        
        group = Folder(
            user_id=owner.id,
            name=name,
            description=description,
            is_group=True,
            max_members=owner.max_members_per_group if owner.max_members_per_group < 999999 else 9999
        )
        group.generate_invite_code()
        
        self.db.add(group)
        await self.db.flush()
        
        membership = GroupMember(
            group_id=group.id,
            user_id=owner.id,
            role=GroupRole.OWNER
        )
        self.db.add(membership)
        
        await self.db.commit()
        await self.db.refresh(group)
        
        return True, "Группа создана", group
    
    async def get_group_by_id(self, group_id: UUID) -> Optional[Folder]:
        result = await self.db.execute(
            select(Folder)
            .options(selectinload(Folder.members).selectinload(GroupMember.user))
            .where(Folder.id == group_id, Folder.is_group == True)
        )
        return result.scalar_one_or_none()
    
    async def get_group_by_invite_code(self, invite_code: str) -> Optional[Folder]:
        result = await self.db.execute(
            select(Folder)
            .options(selectinload(Folder.members))
            .where(Folder.invite_code == invite_code.upper(), Folder.is_group == True)
        )
        return result.scalar_one_or_none()
    
    async def join_group(self, user: User, invite_code: str) -> Tuple[bool, str, Optional[Folder]]:
        group = await self.get_group_by_invite_code(invite_code)
        
        if not group:
            return False, "Группа не найдена", None
        
        # Проверка: уже в группе?
        existing = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group.id,
                GroupMember.user_id == user.id
            )
        )
        if existing.scalar_one_or_none():
            return False, "Вы уже состоите в этой группе", group
        
        # Получаем владельца группы для проверки его лимитов
        owner_result = await self.db.execute(
            select(User).where(User.id == group.user_id)
        )
        owner = owner_result.scalar_one_or_none()
        
        # Проверка лимита участников (лимит владельца!)
        member_count = await self.db.execute(
            select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
        )
        current_members = member_count.scalar() or 0
        
        max_members = owner.max_members_per_group if owner else 5
        if current_members >= max_members:
            if max_members <= 5:
                return False, f"Группа заполнена (макс. {max_members} участников в Free)", group
            return False, "Группа заполнена", group
        
        membership = GroupMember(
            group_id=group.id,
            user_id=user.id,
            role=GroupRole.MEMBER
        )
        self.db.add(membership)
        await self.db.commit()
        
        return True, "Вы успешно присоединились к группе", group
    
    async def can_add_material_to_group(self, user: User, group_id: UUID) -> Tuple[bool, str]:
        """Проверка возможности добавить материал в группу"""
        group = await self.get_group_by_id(group_id)
        if not group:
            return False, "Группа не найдена"
        
        # Получаем владельца группы
        owner_result = await self.db.execute(
            select(User).where(User.id == group.user_id)
        )
        owner = owner_result.scalar_one_or_none()
        
        # Проверка лимита материалов (лимит владельца!)
        materials_count = await self._count_group_materials(group_id)
        max_materials = owner.max_materials_per_group if owner else 10
        
        if materials_count >= max_materials:
            if max_materials <= 10:
                return False, f"Лимит материалов в группе ({max_materials}). Владельцу нужен Pro."
            return False, f"Достигнут лимит материалов в группе ({max_materials})"
        
        return True, "OK"
    
    async def leave_group(self, user: User, group_id: UUID) -> Tuple[bool, str]:
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user.id
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            return False, "Вы не состоите в этой группе"
        
        role = get_val(membership.role)
        if role == GroupRole.OWNER:
            return False, "Владелец не может покинуть группу"
        
        await self.db.delete(membership)
        await self.db.commit()
        
        return True, "Вы покинули группу"
    
    async def get_user_groups(self, user: User) -> List[dict]:
        result = await self.db.execute(
            select(GroupMember, Folder)
            .join(Folder, GroupMember.group_id == Folder.id)
            .where(GroupMember.user_id == user.id)
            .order_by(GroupMember.joined_at.desc())
        )
        
        groups = []
        for membership, folder in result.all():
            count_result = await self.db.execute(
                select(func.count(GroupMember.id)).where(GroupMember.group_id == folder.id)
            )
            member_count = count_result.scalar()
            
            materials_count = await self._count_group_materials(folder.id)
            
            role = get_val(membership.role)
            
            groups.append({
                "id": str(folder.id),
                "name": folder.name,
                "description": folder.description,
                "invite_code": folder.invite_code,
                "role": role,
                "member_count": member_count,
                "max_members": folder.max_members,
                "materials_count": materials_count,
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
                "is_owner": role == GroupRole.OWNER
            })
        
        return groups
    
    async def get_group_members(self, group_id: UUID) -> List[dict]:
        result = await self.db.execute(
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id)
            .order_by(GroupMember.role, GroupMember.joined_at)
        )
        
        members = []
        for membership, user in result.all():
            members.append({
                "id": str(user.id),
                "telegram_id": user.telegram_id,
                "telegram_username": user.telegram_username,
                "first_name": user.first_name,
                "role": get_val(membership.role),
                "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
            })
        
        return members
    
    async def delete_group(self, user: User, group_id: UUID) -> Tuple[bool, str]:
        group = await self.get_group_by_id(group_id)
        
        if not group:
            return False, "Группа не найдена"
        
        if group.user_id != user.id:
            return False, "Только владелец может удалить группу"
        
        await self.db.delete(group)
        await self.db.commit()
        
        return True, "Группа удалена"
    
    async def get_or_create_referral_code(self, user: User) -> str:
        if not user.referral_code:
            user.generate_referral_code()
            await self.db.commit()
        return user.referral_code
    
    async def process_referral(self, new_user: User, referral_code: str) -> Tuple[bool, Optional[User]]:
        if not referral_code:
            return False, None
        
        result = await self.db.execute(
            select(User).where(User.referral_code == referral_code.upper())
        )
        referrer = result.scalar_one_or_none()
        
        if not referrer or referrer.id == new_user.id:
            return False, None
        
        new_user.referred_by_id = referrer.id
        referrer.referral_count = (referrer.referral_count or 0) + 1
        
        if referrer.referral_count >= self.REFERRAL_PRO_THRESHOLD and not referrer.referral_pro_granted:
            await self._grant_referral_pro(referrer)
        
        await self.db.commit()
        return True, referrer
    
    async def _grant_referral_pro(self, user: User) -> None:
        user.subscription_tier = SubscriptionTier.PRO
        user.subscription_expires_at = datetime.now() + timedelta(days=self.REFERRAL_PRO_DAYS)
        user.referral_pro_granted = True
    
    async def get_referral_stats(self, user: User) -> dict:
        await self.get_or_create_referral_code(user)
        
        from app.core.config import settings
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'lectoaibot')
        
        return {
            "referral_code": user.referral_code,
            "referral_link": f"https://t.me/{bot_username}?start=ref_{user.referral_code}",
            "referral_count": user.referral_count or 0,
            "referrals_needed": max(0, self.REFERRAL_PRO_THRESHOLD - (user.referral_count or 0)),
            "pro_granted": user.referral_pro_granted or False,
            "threshold": self.REFERRAL_PRO_THRESHOLD
        }