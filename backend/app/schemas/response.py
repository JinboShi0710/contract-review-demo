# -*- coding: utf-8 -*-
"""
统一响应格式定义
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    {
        "code": 0,        // 0=成功，非0=失败
        "message": "",    // 提示信息
        "data": {}        // 数据体，可为 null
    }
    """
    code: int = 0
    message: str = ""
    data: Optional[T] = None


class PageData(BaseModel):
    """分页数据"""
    items: list
    total: int
    page: int
    page_size: int


# 预定义错误码
class ErrorCode:
    # 客户端错误 4xxxx
    INVALID_FORMAT = 40001
    FILE_TOO_LARGE = 40002
    LOW_QUALITY = 40003
    FILE_CORRUPTED = 40004
    INVALID_PARAMETER = 40005
    FORBIDDEN = 40301

    # 服务器错误 5xxxx
    INTERNAL_ERROR = 50001
    LLM_TIMEOUT = 50002
    OCR_FAILED = 50003
    NOT_FOUND = 50004


def success_response(data: T = None, message: str = "成功") -> Response[T]:
    """成功响应"""
    return Response(code=0, message=message, data=data)


def error_response(code: int, message: str) -> Response:
    """错误响应"""
    return Response(code=code, message=message, data=None)
