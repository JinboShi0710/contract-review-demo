# -*- coding: utf-8 -*-
"""
FastAPI 依赖项：认证与权限
"""
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


class AuthError(Exception):
    """认证/权限错误，使用统一响应格式"""
    def __init__(self, status_code: int, code: int, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    从 Authorization: Bearer <token> 中提取并验证当前用户。
    Token 缺失或无效抛 AuthError(401)，用户被禁用抛 AuthError(403)。
    """
    if not credentials:
        raise AuthError(401, 401, "未授权")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise AuthError(401, 401, "登录已过期，请重新登录")

    user = db.query(User).filter(
        User.id == payload.get("sub"),
        User.is_deleted == 0,
    ).first()

    if not user:
        raise AuthError(401, 401, "未授权")

    if not user.is_active:
        raise AuthError(403, 403, "账号已被禁用")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """仅 admin 角色可通过"""
    if current_user.role != "admin":
        raise AuthError(403, 403, "权限不足")
    return current_user
