# -*- coding: utf-8 -*-
"""
文件校验工具
"""
from pathlib import Path
from app.core.config import settings


class FileValidationError(Exception):
    """文件校验异常"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def validate_file(file_path: str, file_size: int) -> dict:
    """
    校验文件

    Args:
        file_path: 文件路径
        file_size: 文件大小（字节）

    Returns:
        校验结果字典

    Raises:
        FileValidationError: 校验失败
    """
    # 1. 检查文件大小
    if file_size > settings.MAX_FILE_SIZE:
        raise FileValidationError(
            code=40002,
            message=f"文件大小超出限制（最大 {settings.MAX_FILE_SIZE // (1024*1024)}MB）"
        )

    # 2. 检查文件大小为0
    if file_size == 0:
        raise FileValidationError(
            code=40005,
            message="文件为空"
        )

    # 3. 检查文件扩展名
    ext = Path(file_path).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            code=40001,
            message="仅支持 PDF、DOCX、TXT、MD、JPG、PNG 格式"
        )

    # 4. 检查文件是否存在
    if not Path(file_path).exists():
        raise FileValidationError(
            code=40005,
            message="文件不存在"
        )

    return {
        "valid": True,
        "extension": ext,
        "size": file_size,
    }


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower().lstrip(".")


def is_pdf(file_path: str) -> bool:
    """判断是否为 PDF 文件"""
    return get_file_extension(file_path) == "pdf"


def is_image(file_path: str) -> bool:
    """判断是否为图片文件"""
    ext = get_file_extension(file_path)
    return ext in {"jpg", "jpeg", "png"}
