# -*- coding: utf-8 -*-
"""
认证服务：密码哈希、JWT 生成与验证
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str, role: str) -> str:
    """生成 JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT Token，返回 payload 或 None"""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """验证用户名和密码，返回用户对象或 None"""
    user = db.query(User).filter(
        User.username == username,
        User.is_deleted == 0,
    ).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def init_admin(db: Session) -> None:
    """首次启动时创建默认管理员账号（FC-01）"""
    exists = db.query(User).filter(User.is_deleted == 0).first()
    if exists:
        return
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("✅ 已创建默认管理员账号：admin / admin123")
