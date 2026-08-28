# -*- coding: utf-8 -*-
"""
合同审核 API 路由
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import success_response, error_response, ErrorCode
from app.schemas.contract import (
    ContractSchema,
    ContractListItemSchema,
    ContractUploadResponse,
    ContractCreateRequest,
    CompareRequest,
    CompareResponse,
    ReportResponse,
)
from app.services.contract_service import contract_service
from app.services.report_generator import report_generator
from app.services.comparison_service import comparison_service
from app.utils.file_validator import FileValidationError

router = APIRouter(prefix="/contracts", tags=["合同审核"])


@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传合同文件
    POST /api/v1/contracts/upload
    """
    try:
        result = contract_service.upload_contract(file, db, created_by=current_user.id)
        return success_response(data=result, message="上传成功")
    except FileValidationError as e:
        return error_response(code=e.code, message=e.message)
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=f"上传失败: {str(e)}")


@router.post("/{contract_id}/process")
async def process_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理合同（OCR + 要素提取 + 风险检测）
    POST /api/v1/contracts/{contract_id}/process
    """
    try:
        result = contract_service.process_contract(contract_id, db)
        if result.get("code") == 40003:
            return error_response(code=40003, message=result["message"])
        return success_response(data=result, message="处理完成")
    except ValueError as e:
        return error_response(code=ErrorCode.NOT_FOUND, message=str(e))
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=f"处理失败: {str(e)}")


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取合同详情
    GET /api/v1/contracts/{contract_id}
    """
    contract = contract_service.get_contract(
        contract_id, db,
        current_user_id=current_user.id,
        role=current_user.role,
    )
    if not contract:
        if current_user.role == "manager":
            return error_response(code=403, message="权限不足")
        return error_response(code=ErrorCode.NOT_FOUND, message="合同不存在")

    elements = []
    for elem in contract.elements:
        elements.append({
            "id": elem.id,
            "element_type": elem.element_type,
            "element_value": elem.element_value,
            "location": elem.location,
            "confidence": elem.confidence,
        })

    risks = []
    for risk in contract.risks:
        risks.append({
            "id": risk.id,
            "risk_type": risk.risk_type,
            "risk_level": risk.risk_level,
            "location": risk.location,
            "description": risk.description,
            "rule_id": risk.rule_id,
            "rule_name": risk.rule_name,
            "rule_type": risk.rule_type,
            "rule_params": risk.rule_params,
            "matched": risk.matched,
            "matched_items": risk.matched_items,
            "execution_result": risk.execution_result,
        })

    data = {
        "id": contract.id,
        "file_name": contract.file_name,
        "file_type": contract.file_type,
        "file_size": contract.file_size,
        "page_count": contract.page_count,
        "status": contract.status,
        "contract_type": contract.contract_type,
        "confidence": contract.confidence,
        "elements": elements,
        "risks": risks,
        "created_at": contract.created_at.isoformat(),
    }

    return success_response(data=data, message="成功")


@router.get("/")
async def list_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取合同列表
    GET /api/v1/contracts?page=1&page_size=20
    """
    contracts, total = contract_service.list_contracts(
        db, page, page_size,
        current_user_id=current_user.id,
        role=current_user.role,
    )

    items = []
    for contract in contracts:
        items.append({
            "id": contract.id,
            "file_name": contract.file_name,
            "file_type": contract.file_type,
            "status": contract.status,
            "contract_type": contract.contract_type,
            "confidence": contract.confidence,
            "created_at": contract.created_at.isoformat(),
        })

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }, message="成功")


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除合同（软删除）
    DELETE /api/v1/contracts/{contract_id}
    """
    success = contract_service.delete_contract(contract_id, db)
    if not success:
        return error_response(code=ErrorCode.NOT_FOUND, message="合同不存在")

    return success_response(message="删除成功")


@router.get("/{contract_id}/report/export")
async def export_report(
    contract_id: str,
    format: str = Query("pdf", pattern="^(pdf|word)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导出审核报告（PDF 或 Word）
    GET /api/v1/contracts/{contract_id}/report/export?format=pdf|word
    """
    from app.models.contract import ContractReport

    contract = contract_service.get_contract(
        contract_id, db,
        current_user_id=current_user.id,
        role=current_user.role,
    )
    if not contract:
        return error_response(code=ErrorCode.NOT_FOUND, message="合同不存在")

    if contract.status != "completed":
        return error_response(code=40005, message="合同审核未完成，无法导出报告")

    risks = list(contract.risks)

    try:
        report = report_generator.generate(
            contract=contract,
            risks=risks,
            fmt=format,
        )
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message="报告生成失败，请重试")

    existing = (
        db.query(ContractReport)
        .filter(
            ContractReport.contract_id == contract_id,
            ContractReport.report_type == format,
        )
        .first()
    )
    if existing:
        existing.report_path = report.report_path
        existing.conclusion = report.conclusion
        db.commit()
    else:
        db.add(report)
        db.commit()

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "word"
        else "application/pdf"
    )
    suffix = "docx" if format == "word" else "pdf"
    filename = f"audit_report_{contract_id[:8]}.{suffix}"

    return FileResponse(
        path=report.report_path,
        media_type=media_type,
        filename=filename,
    )


@router.post("/compare")
async def compare_contracts(
    template_file: UploadFile = File(...),
    contract_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    合同模板比对
    POST /api/v1/contracts/compare
    """
    try:
        result = comparison_service.compare_contracts(
            template_file=template_file,
            contract_file=contract_file,
            db=db,
        )
        return success_response(data=result, message="比对完成")
    except FileValidationError as e:
        return error_response(code=e.code, message=e.message)
    except Exception as e:
        return error_response(code=50001, message=f"比对失败: {str(e)}")


@router.get("/comparisons/{comparison_id}")
async def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取比对结果
    GET /api/v1/contracts/comparisons/{comparison_id}
    """
    result = comparison_service.get_comparison(comparison_id, db)
    if not result:
        return error_response(code=ErrorCode.NOT_FOUND, message="比对记录不存在")

    return success_response(data=result, message="成功")
