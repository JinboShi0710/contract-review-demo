# -*- coding: utf-8 -*-
"""
合同相关 SQLAlchemy 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Contract(Base):
    """合同模型"""
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="created")  # created/processing/completed/failed
    contract_type = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    created_by = Column(String(36), nullable=True)  # 上传用户 ID，null = 历史数据

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    elements = relationship("ContractElement", back_populates="contract", lazy="dynamic")
    risks = relationship("ContractRisk", back_populates="contract", lazy="dynamic")
    reports = relationship("ContractReport", back_populates="contract", lazy="dynamic")


class ContractElement(Base):
    """合同要素模型"""
    __tablename__ = "contract_elements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False)
    element_type = Column(String(50), nullable=False)
    element_value = Column(Text, nullable=False)
    location = Column(JSON, nullable=True)  # {x, y, width, height}
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联
    contract = relationship("Contract", back_populates="elements")


class ContractRisk(Base):
    """合同风险标注模型"""
    __tablename__ = "contract_risks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False)
    risk_type = Column(String(50), nullable=False)  # 风险类型/规则名称
    risk_level = Column(String(10), nullable=False)  # low/medium/high
    location = Column(JSON, nullable=False)  # {x, y, width, height}
    description = Column(Text, nullable=True)

    # 扩展字段：完整规则执行信息
    rule_id = Column(String(36), nullable=True)  # 关联的规则ID
    rule_name = Column(String(100), nullable=True)  # 规则名称
    rule_type = Column(String(50), nullable=True)  # keyword/regex/llm_risk等
    rule_params = Column(JSON, nullable=True)  # 规则参数
    matched = Column(Integer, nullable=True, default=0)  # 0=无法确定 1=有证据通过 2=风险
    matched_items = Column(JSON, nullable=True)  # 命中的内容列表
    execution_result = Column(Text, nullable=True)  # LLM 分析结果或执行说明

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联
    contract = relationship("Contract", back_populates="risks")


class ContractComparison(Base):
    """合同比对记录模型"""
    __tablename__ = "contract_comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    differences = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    similarity = Column(Float, nullable=True)  # 相似度百分比
    template_pages = Column(Integer, nullable=True)  # 模板页数
    contract_pages = Column(Integer, nullable=True)  # 合同页数
    template_file_path = Column(String(512), nullable=True)  # 模板文件路径（不上传审核）
    contract_file_path = Column(String(512), nullable=True)  # 合同文件路径（不上传审核）

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ContractReport(Base):
    """审核报告模型"""
    __tablename__ = "contract_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False)
    report_path = Column(String(512), nullable=False)
    report_type = Column(String(10), nullable=False, default="pdf")
    conclusion = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联
    contract = relationship("Contract", back_populates="reports")
