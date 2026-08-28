# -*- coding: utf-8 -*-
"""
凭证分类 API 路由
"""
from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import success_response, error_response, ErrorCode
from app.services.voucher_classification_service import voucher_classification_service
from app.services.voucher_element_service import voucher_element_service
from app.services.voucher_process_service import voucher_process_service
from app.utils.file_validator import FileValidationError

router = APIRouter(prefix="/vouchers", tags=["凭证分类"])


@router.post("/classify")
async def classify_voucher(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    凭证分类
    POST /api/v1/vouchers/classify
    Content-Type: multipart/form-data
    """
    try:
        result = voucher_classification_service.classify_voucher(file, db)
        return success_response(data=result, message="分类成功")
    except FileValidationError as e:
        return error_response(code=e.code, message=e.message)
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=f"分类失败: {str(e)}")


@router.get("/classifications")
async def list_classifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取分类历史列表
    GET /api/v1/vouchers/classifications?page=1&page_size=20
    """
    items, total = voucher_classification_service.list_classifications(db, page, page_size)

    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }, message="成功")


@router.get("/classifications/{classification_id}")
async def get_classification(
    classification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取分类详情
    GET /api/v1/vouchers/classifications/{classification_id}
    """
    result = voucher_classification_service.get_classification(classification_id, db)
    if not result:
        return error_response(code=ErrorCode.NOT_FOUND, message="分类记录不存在")

    return success_response(data=result, message="成功")


# ========== 凭证要素提取 API ==========

@router.post("/elements/extract")
async def extract_elements(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提取凭证要素
    POST /api/v1/vouchers/elements/extract
    Content-Type: multipart/form-data
    """
    try:
        result = voucher_element_service.extract_elements(file, db)
        return success_response(data=result, message="提取成功")
    except FileValidationError as e:
        return error_response(code=e.code, message=e.message)
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=f"提取失败: {str(e)}")


# ========== 凭证处理（合并分类+要素提取） ==========

@router.post("/process")
async def process_voucher(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    凭证处理（分类+要素提取）
    POST /api/v1/vouchers/process
    Content-Type: multipart/form-data
    """
    try:
        result = voucher_process_service.process_voucher(file, db)
        return success_response(data=result, message="处理成功")
    except FileValidationError as e:
        return error_response(code=e.code, message=e.message)
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=f"处理失败: {str(e)}")
