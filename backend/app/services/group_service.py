# backend/app/services/group_service.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from app.models import User, Folder, GroupMember, GroupRole, SubscriptionTier
from app.core.config import settings


class GroupService:
    REFERRAL_PRO_THRESHOLD = 5  # Сколько рефералов нужно для Pro
    REFERRAL_PRO_DAYS = 30  # На сколько дней давать Pro
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== ГРУППЫ ====================
    
    async def create_group(
        self,
        owner: User,
        name: str,
        description: Optional[str] = None
    ) -> Folder:
        """Создать новую группу"""
        group = Folder(
            user_id=owner.id,
            name=name,
            description=description,
            is_group=True,
        )
        group.generate_invite_code()
        
        self.db.add(group)
        await self.db.flush()
        
        # Добавляем создателя как owner
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
        """Получить группу по ID"""
        result = await self.db.execute(
            select(Folder)
            .options(selectinload(Folder.members).selectinload(GroupMember.user))
            .where(Folder.id == group_id, Folder.is_group == True)
        )
        return result.scalar_one_or_none()
    
    async def get_group_by_invite_code(self, invite_code: str) -> Optional[Folder]:
        """Получить группу по коду приглашения"""
        result = await self.db.execute(
            select(Folder)
            .options(selectinload(Folder.members))
            .where(Folder.invite_code == invite_code.upper(), Folder.is_group == True)
        )
        return result.scalar_one_or_none()
    
    # backend/app/services/group_service.py

async def join_group(self, user: User, invite_code: str) -> Tuple[bool, str, Optional[Folder]]:
    """Присоединиться к группе по коду"""
    print(f"🔍 join_group: user={user.id}, code={invite_code}")
    
    group = await self.get_group_by_invite_code(invite_code)
    
    if not group:
        print(f"❌ Group not found for code: {invite_code}")
        return False, "Группа не найдена", None
    
    print(f"✅ Found group: {group.id} - {group.name}")
    
    # Проверяем, не состоит ли уже
    existing = await self.db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id,
            GroupMember.user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        print(f"⚠️ User already in group")
        return False, "Вы уже состоите в этой группе", group
    
    # Добавляем участника
    membership = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role=GroupRole.MEMBER
    )
    self.db.add(membership)
    await self.db.commit()
    
    print(f"✅ Added membership: group={group.id}, user={user.id}")
    
    # Проверяем что добавилось
    check = await self.db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id,
            GroupMember.user_id == user.id
        )
    )
    if check.scalar_one_or_none():
        print(f"✅ Membership confirmed in DB")
    else:
        print(f"❌ Membership NOT found after commit!")
    
    return True, "Вы успешно присоединились к группе", group

    async def leave_group(self, user: User, group_id: UUID) -> Tuple[bool, str]:
        """Покинуть группу"""
        result = await self.db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user.id
            )
        )
        membership = result.scalar_one_or_none()
        
        if not membership:
            return False, "Вы не состоите в этой группе"
        
        if membership.role == GroupRole.OWNER:
            return False, "Владелец не может покинуть группу. Удалите её или передайте права."
        
        await self.db.delete(membership)
        await self.db.commit()
        
        return True, "Вы покинули группу"
    
    async def get_user_groups(self, user: User) -> List[dict]:
        """Получить все группы пользователя"""
        result = await self.db.execute(
            select(GroupMember, Folder)
            .join(Folder, GroupMember.group_id == Folder.id)
            .where(GroupMember.user_id == user.id)
            .order_by(GroupMember.joined_at.desc())
        )
        
        groups = []
        for membership, folder in result.all():
            # Считаем участников
            count_result = await self.db.execute(
                select(func.count(GroupMember.id)).where(GroupMember.group_id == folder.id)
            )
            member_count = count_result.scalar()
            
            groups.append({
                "id": str(folder.id),
                "name": folder.name,
                "description": folder.description,
                "invite_code": folder.invite_code,
                "role": membership.role.value,
                "member_count": member_count,
                "max_members": folder.max_members,
                "joined_at": membership.joined_at.isoformat(),
                "is_owner": membership.role == GroupRole.OWNER
            })
        
        return groups
    
    async def get_group_members(self, group_id: UUID) -> List[dict]:
        """Получить участников группы"""
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
                "telegram_username": user.telegram_username,
                "first_name": user.first_name,
                "role": membership.role.value,
                "joined_at": membership.joined_at.isoformat()
            })
        
        return members
    
    async def delete_group(self, user: User, group_id: UUID) -> Tuple[bool, str]:
        """Удалить группу (только owner)"""
        group = await self.get_group_by_id(group_id)
        
        if not group:
            return False, "Группа не найдена"
        
        if group.user_id != user.id:
            return False, "Только владелец может удалить группу"
        
        await self.db.delete(group)
        await self.db.commit()
        
        return True, "Группа удалена"
    
    # ==================== РЕФЕРАЛЫ ====================
    
    async def get_or_create_referral_code(self, user: User) -> str:
        """Получить или создать реферальный код"""
        if not user.referral_code:
            user.generate_referral_code()
            await self.db.commit()
        return user.referral_code
    
    async def process_referral(self, new_user: User, referral_code: str) -> Tuple[bool, Optional[User]]:
        """Обработать реферальный код при регистрации"""
        if not referral_code:
            return False, None
        
        # Ищем пригласившего
        result = await self.db.execute(
            select(User).where(User.referral_code == referral_code.upper())
        )
        referrer = result.scalar_one_or_none()
        
        if not referrer:
            return False, None
        
        if referrer.id == new_user.id:
            return False, None  # Нельзя пригласить себя
        
        # Устанавливаем связь
        new_user.referred_by_id = referrer.id
        
        # Увеличиваем счётчик рефералов
        referrer.referral_count = (referrer.referral_count or 0) + 1
        
        # Проверяем, достиг ли порога для Pro
        if referrer.referral_count >= self.REFERRAL_PRO_THRESHOLD and not referrer.referral_pro_granted:
            await self._grant_referral_pro(referrer)
        
        await self.db.commit()
        
        return True, referrer
    
    async def _grant_referral_pro(self, user: User) -> None:
        """Выдать Pro подписку за рефералов"""
        user.subscription_tier = SubscriptionTier.PRO
        user.subscription_expires_at = datetime.now() + timedelta(days=self.REFERRAL_PRO_DAYS)
        user.referral_pro_granted = True
    
    async def get_referral_stats(self, user: User) -> dict:
        """Получить статистику рефералов"""
        from app.core.config import settings
        
        await self.get_or_create_referral_code(user)
        
        # Используем username бота из настроек
        bot_username = settings.TELEGRAM_BOT_USERNAME
        
        return {
            "referral_code": user.referral_code,
            "referral_link": f"https://t.me/{bot_username}?start=ref_{user.referral_code}",
            "referral_count": user.referral_count or 0,
            "referrals_needed": max(0, self.REFERRAL_PRO_THRESHOLD - (user.referral_count or 0)),
            "pro_granted": user.referral_pro_granted,
            "threshold": self.REFERRAL_PRO_THRESHOLD
        }
    
    async def _get_bot_username(self) -> str:
        """Получить username бота"""
        from app.core.config import settings
        
        # Если есть сохранённый username - используем его
        # Иначе пробуем получить через API
        try:
            from telegram import Bot
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            me = await bot.get_me()
            return me.username
        except Exception:
            # Fallback - используем известный username
            return "studybuddy_uzbot"
    