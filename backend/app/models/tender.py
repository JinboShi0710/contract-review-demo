# -*- coding: utf-8 -*-
"""招投标文件审查数据模型。"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class TenderReviewTask(Base):
    __tablename__ = "tender_review_tasks"

    id = Column(String(36), primary_key=True, default=_uuid)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="created")
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    line_count = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("TenderReviewItem", back_populates="task", cascade="all, delete-orphan")


class TenderReviewItem(Base):
    __tablename__ = "tender_review_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("tender_review_tasks.id"), nullable=False)
    category = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    requirement = Column(Text, nullable=False)
    evidence_quote = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_line = Column(Integer, nullable=True)
    importance = Column(String(20), nullable=False, default="attention")
    action = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="keyword")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    task = relationship("TenderReviewTask", back_populates="items")
