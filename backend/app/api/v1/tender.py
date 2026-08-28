# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import ErrorCode, error_response, success_response
from app.services.tender_review_service import tender_review_service

router = APIRouter(prefix="/tenders", tags=["招投标审核"])


@router.post("/upload")
def upload_tender(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return success_response(tender_review_service.upload(file, db, current_user.id), "上传成功")
    except ValueError as exc:
        return error_response(ErrorCode.INVALID_FORMAT, str(exc))
    except Exception as exc:
        return error_response(ErrorCode.INTERNAL_ERROR, f"上传失败：{exc}")


@router.post("/{task_id}/process")
def process_tender(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return success_response(tender_review_service.process(task_id, db), "审查完成")
    except ValueError as exc:
        return error_response(ErrorCode.INVALID_PARAMETER, str(exc))
    except Exception as exc:
        return error_response(ErrorCode.INTERNAL_ERROR, f"处理失败：{exc}")


@router.get("")
def list_tenders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response(tender_review_service.list(db, current_user.id, current_user.role))


@router.get("/{task_id}")
def get_tender(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return success_response(tender_review_service.detail(task_id, db))
    except ValueError as exc:
        return error_response(ErrorCode.NOT_FOUND, str(exc))


@router.get("/{task_id}/export")
def export_tender(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        path = tender_review_service.export(task_id, db)
        return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=path.name)
    except ValueError as exc:
        return error_response(ErrorCode.NOT_FOUND, str(exc))
