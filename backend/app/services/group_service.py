# backend/app/services/group_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from app.models import User, Folder, GroupMember, SubscriptionTier
from app.core.config import settings


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
    
    async def create_group(
        self,
        owner: User,
        name: str,
        description: Optional[str] = None
    ) -> Folder:
        group = Folder(
            user_id=owner.id,
            name=name,
            description=description,
            is_group=True,
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
        
        return group
    
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
        
        existing = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group.id,
                GroupMember.user_id == user.id
            )
        )
        if existing.scalar_one_or_none():
            return False, "Вы уже состоите в этой группе", group
        
        member_count = await self.db.execute(
            select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
        )
        if member_count.scalar() >= group.max_members:
            return False, "Группа заполнена", group
        
        membership = GroupMember(
            group_id=group.id,
            user_id=user.id,
            role=GroupRole.MEMBER
        )
        self.db.add(membership)
        await self.db.commit()
        
        return True, "Вы успешно присоединились к группе", group
    
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
            
            role = get_val(membership.role)
            
            groups.append({
                "id": str(folder.id),
                "name": folder.name,
                "description": folder.description,
                "invite_code": folder.invite_code,
                "role": role,
                "member_count": member_count,
                "max_members": folder.max_members,
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
        
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'lectoaibot')
        
        return {
            "referral_code": user.referral_code,
            "referral_link": f"https://t.me/{bot_username}?start=ref_{user.referral_code}",
            "referral_count": user.referral_count or 0,
            "referrals_needed": max(0, self.REFERRAL_PRO_THRESHOLD - (user.referral_count or 0)),
            "pro_granted": user.referral_pro_granted or False,
            "threshold": self.REFERRAL_PRO_THRESHOLD
        }