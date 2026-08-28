# -*- coding: utf-8 -*-
"""
审核点配置 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import success_response, error_response, ErrorCode
from app.services.audit_rule_service import audit_rule_service

router = APIRouter(prefix="/audit-rules", tags=["审核点配置"])


@router.get("")
async def list_audit_rules(
    global_only: bool = Query(False),
    include_deleted: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取配置列表
    GET /api/v1/audit-rules?global_only=false&include_deleted=false
    """
    try:
        if global_only:
            rules = audit_rule_service.list_rules(
                db, include_deleted=include_deleted, global_only=True
            )
        else:
            rules = audit_rule_service.list_rules(db, include_deleted=include_deleted)

        return success_response(data={"items": rules, "total": len(rules)})
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))


@router.post("")
async def create_audit_rule(
    name: str,
    rule_type: str,
    params: dict,
    severity: str,
    description: Optional[str] = None,
    is_global: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建配置
    POST /api/v1/audit-rules
    """
    if is_global and current_user.role != "admin":
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="只有管理员能创建全局配置",
        )

    try:
        rule = audit_rule_service.create_rule(
            db=db,
            name=name,
            rule_type=rule_type,
            params=params,
            severity=severity,
            description=description,
            is_global=is_global,
            created_by=current_user.id,
        )
        return success_response(data=rule, message="创建成功")
    except ValueError as e:
        return error_response(code=ErrorCode.BAD_REQUEST, message=str(e))
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))


@router.post("/import")
async def import_default_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导入默认规则
    POST /api/v1/audit-rules/import
    """
    if current_user.role != "admin":
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="只有管理员能导入规则",
        )

    try:
        count = audit_rule_service.import_default_rules(db, current_user.id)
        return success_response(data={"imported": count}, message=f"成功导入 {count} 个规则")
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))


@router.get("/{rule_id}")
async def get_audit_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """
    获取配置详情
    GET /api/v1/audit-rules/{rule_id}
    """
    rule = audit_rule_service.get_rule(db, rule_id)
    if not rule:
        return error_response(code=ErrorCode.NOT_FOUND, message="配置不存在")

    return success_response(data=rule)


@router.put("/{rule_id}")
async def update_audit_rule(
    rule_id: str,
    name: Optional[str] = None,
    params: Optional[dict] = None,
    severity: Optional[str] = None,
    description: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    修改配置
    PUT /api/v1/audit-rules/{rule_id}
    """
    try:
        existing = audit_rule_service.get_rule(db, rule_id)
        if not existing:
            return error_response(code=ErrorCode.NOT_FOUND, message="配置不存在")

        if existing["is_global"] and current_user.role != "admin":
            return error_response(
                code=ErrorCode.FORBIDDEN,
                message="普通用户不能修改全局配置",
            )

        rule = audit_rule_service.update_rule(
            db=db,
            rule_id=rule_id,
            name=name,
            params=params,
            severity=severity,
            description=description,
            enabled=enabled,
            updated_by=current_user.id,
        )
        return success_response(data=rule, message="更新成功")
    except PermissionError as e:
        return error_response(code=ErrorCode.FORBIDDEN, message=str(e))
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))


@router.delete("/{rule_id}")
async def delete_audit_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除配置
    DELETE /api/v1/audit-rules/{rule_id}
    """
    try:
        success = audit_rule_service.delete_rule(db, rule_id, current_user.id)
        if not success:
            return error_response(code=ErrorCode.NOT_FOUND, message="配置不存在")
        return success_response(message="删除成功")
    except PermissionError as e:
        return error_response(code=ErrorCode.FORBIDDEN, message=str(e))
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))


@router.get("/{rule_id}/versions")
async def list_audit_rule_versions(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """
    获取版本历史
    GET /api/v1/audit-rules/{rule_id}/versions
    """
    versions = audit_rule_service.list_versions(db, rule_id)
    return success_response(data={"items": versions, "total": len(versions)})


@router.post("/{rule_id}/rollback/{version}")
async def rollback_audit_rule(
    rule_id: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    回滚到指定版本
    POST /api/v1/audit-rules/{rule_id}/rollback/{version}
    """
    if current_user.role != "admin":
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="只有管理员能回滚配置",
        )

    try:
        rule = audit_rule_service.rollback(db, rule_id, version, current_user.id)
        if not rule:
            return error_response(code=ErrorCode.NOT_FOUND, message="版本不存在")
        return success_response(data=rule, message="回滚成功")
    except Exception as e:
        return error_response(code=ErrorCode.INTERNAL_ERROR, message=str(e))
