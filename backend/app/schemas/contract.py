# -*- coding: utf-8 -*-
"""
合同相关 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ContractElementSchema(BaseModel):
    """合同要素"""
    id: str
    element_type: str  # party_a/party_b/amount/signing_date...
    element_value: str
    location: Optional[dict] = None  # {x, y, width, height}
    confidence: Optional[float] = None

    class Config:
        from_attributes = True


class ContractRiskSchema(BaseModel):
    """合同风险"""
    id: str
    risk_type: str  # disclaimer/high_penalty/missing_clause...
    risk_level: str  # low/medium/high
    location: dict  # {x, y, width, height}
    description: Optional[str] = None
    # 规则执行详情
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    rule_params: Optional[dict] = None
    matched: Optional[int] = None  # 0=无法确定 1=有证据通过 2=风险
    matched_items: Optional[List[str]] = None
    execution_result: Optional[str] = None

    class Config:
        from_attributes = True


class ContractComparisonSchema(BaseModel):
    """合同比对结果"""
    id: str
    template_id: Optional[str] = None
    differences: list
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class ContractSchema(BaseModel):
    """合同详情"""
    id: str
    file_name: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    status: str  # created/processing/completed/failed
    contract_type: Optional[str] = None
    confidence: Optional[float] = None
    elements: List[ContractElementSchema] = []
    risks: List[ContractRiskSchema] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ContractListItemSchema(BaseModel):
    """合同列表项"""
    id: str
    file_name: str
    file_type: str
    status: str
    contract_type: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ContractUploadResponse(BaseModel):
    """合同上传响应"""
    contract_id: str
    status: str
    file_name: str


class ContractCreateRequest(BaseModel):
    """合同创建请求（内部使用）"""
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None


class ContractUpdateRequest(BaseModel):
    """合同更新请求"""
    status: Optional[str] = None
    contract_type: Optional[str] = None
    confidence: Optional[float] = None
    page_count: Optional[int] = None


class CompareRequest(BaseModel):
    """合同比对请求"""
    template_contract_id: Optional[str] = None  # 可选：使用已有模板


class CompareResponse(BaseModel):
    """合同比对响应"""
    comparison_id: str
    differences: list
    summary: str


class ReportResponse(BaseModel):
    """报告生成响应"""
    report_id: str
    download_url: str
