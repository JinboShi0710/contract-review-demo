# -*- coding: utf-8 -*-
"""
认证 API 路由
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import success_response, error_response
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录，返回 JWT Token
    POST /api/v1/auth/login
    """
    user = authenticate_user(body.username, body.password, db)
    if not user:
        return error_response(code=401, message="用户名或密码错误")
    if not user.is_active:
        return error_response(code=403, message="账号已被禁用")

    token = create_access_token(user.id, user.username, user.role)
    return success_response(data={"access_token": token, "token_type": "bearer"})


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    GET /api/v1/auth/me
    """
    return success_response(data={
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    })


@router.put("/password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户验证原密码后修改自己的密码。"""
    if not verify_password(body.current_password, current_user.hashed_password):
        return error_response(code=400, message="当前密码不正确")
    if len(body.new_password) < 8:
        return error_response(code=422, message="新密码至少需要8个字符")
    if body.new_password == body.current_password:
        return error_response(code=400, message="新密码不能与当前密码相同")

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return success_response(data=None, message="密码修改成功，请重新登录")
