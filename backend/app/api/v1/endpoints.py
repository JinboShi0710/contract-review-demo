# -*- coding: utf-8 -*-
"""
API 路由汇总
"""
from fastapi import APIRouter
from . import contract
from . import voucher
from . import audit_rule
from . import auth
from . import users
from . import model_settings
from . import tender

api_router = APIRouter(prefix="/api/v1")

# 注册子路由
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(contract.router)
api_router.include_router(voucher.router)
api_router.include_router(audit_rule.router)
api_router.include_router(model_settings.router)
api_router.include_router(tender.router)
