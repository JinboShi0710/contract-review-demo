# -*- coding: utf-8 -*-
"""
凭证相关 SQLAlchemy 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class VoucherClassification(Base):
    """凭证分类模型"""
    __tablename__ = "voucher_classifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    classification_type = Column(String(50), nullable=False)  # 分类类型枚举
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class VoucherElement(Base):
    """凭证要素模型"""
    __tablename__ = "voucher_elements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    voucher_id = Column(String(36), nullable=False)  # 关联凭证ID（可为分类ID或独立凭证ID）
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    element_type = Column(String(50), nullable=False)  # 要素类型枚举
    element_value = Column(String(512), nullable=True)  # 要素值
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
