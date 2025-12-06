# backend/app/api/routes/groups.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.models import get_db, User
from app.services.group_service import GroupService
from app.api.deps import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


# ==================== Schemas ====================

class CreateGroupRequest(BaseModel):
    name: str
    description: Optional[str] = None


class JoinGroupRequest(BaseModel):
    invite_code: str


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    invite_code: str
    role: str
    member_count: int
    max_members: int
    joined_at: str
    is_owner: bool


class GroupMemberResponse(BaseModel):
    id: str
    telegram_username: Optional[str]
    first_name: Optional[str]
    role: str
    joined_at: str


class ReferralStatsResponse(BaseModel):
    referral_code: str
    referral_link: str
    referral_count: int
    referrals_needed: int
    pro_granted: bool
    threshold: int


# ==================== Group Endpoints ====================

@router.post("/", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новую группу"""
    service = GroupService(db)
    group = await service.create_group(
        owner=current_user,
        name=request.name,
        description=request.description
    )
    
    groups = await service.get_user_groups(current_user)
    return next(g for g in groups if g["id"] == str(group.id))


@router.get("/", response_model=List[GroupResponse])
async def get_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все мои группы"""
    service = GroupService(db)
    return await service.get_user_groups(current_user)


@router.get("/{group_id}")
async def get_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить информацию о группе"""
    service = GroupService(db)
    group = await service.get_group_by_id(group_id)
    
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    # Проверяем, состоит ли пользователь в группе
    groups = await service.get_user_groups(current_user)
    user_group = next((g for g in groups if g["id"] == str(group_id)), None)
    
    if not user_group:
        raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
    
    # Добавляем список участников
    members = await service.get_group_members(group_id)
    user_group["members"] = members
    
    return user_group


@router.post("/join")
async def join_group(
    request: JoinGroupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Присоединиться к группе по коду"""
    service = GroupService(db)
    success, message, group = await service.join_group(current_user, request.invite_code)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "group": {
            "id": str(group.id),
            "name": group.name
        }
    }


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Покинуть группу"""
    service = GroupService(db)
    success, message = await service.leave_group(current_user, group_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить группу"""
    service = GroupService(db)
    success, message = await service.delete_group(current_user, group_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить участников группы"""
    service = GroupService(db)
    
    # Проверяем членство
    groups = await service.get_user_groups(current_user)
    if not any(g["id"] == str(group_id) for g in groups):
        raise HTTPException(status_code=403, detail="Вы не состоите в этой группе")
    
    return await service.get_group_members(group_id)


# ==================== Referral Endpoints ====================

@router.get("/referral/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику рефералов"""
    service = GroupService(db)
    return await service.get_referral_stats(current_user)


@router.post("/referral/generate")
async def generate_referral_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Сгенерировать реферальный код"""
    service = GroupService(db)
    code = await service.get_or_create_referral_code(current_user)
    stats = await service.get_referral_stats(current_user)
    return stats