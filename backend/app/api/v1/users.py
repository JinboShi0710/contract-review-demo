# -*- coding: utf-8 -*-
"""
用户管理 API 路由（仅 admin）
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.response import success_response, error_response
from app.services.auth_service import hash_password

router = APIRouter(prefix="/users", tags=["用户管理"])

VALID_ROLES = {"admin", "reviewer", "manager"}


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str


class UpdateUserRequest(BaseModel):
    is_active: Optional[bool] = None


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
    }


@router.post("")
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    创建用户（仅 admin）
    POST /api/v1/users
    """
    if body.role not in VALID_ROLES:
        return error_response(code=422, message="角色值无效")

    exists = db.query(User).filter(
        User.username == body.username,
        User.is_deleted == 0,
    ).first()
    if exists:
        return error_response(code=400, message="用户名已存在")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(data=_user_to_dict(user))


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    用户列表（仅 admin）
    GET /api/v1/users
    """
    users = db.query(User).filter(User.is_deleted == 0).all()
    return success_response(data=[_user_to_dict(u) for u in users])


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    更新用户（禁用/启用），仅 admin
    PATCH /api/v1/users/{user_id}
    """
    if body.is_active is False and user_id == current_admin.id:
        return error_response(code=400, message="不能禁用当前登录账号")

    user = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == 0,
    ).first()
    if not user:
        return error_response(code=404, message="用户不存在")

    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return success_response(data=_user_to_dict(user))
