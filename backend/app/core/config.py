# -*- coding: utf-8 -*-
"""
应用配置
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "ContractLens"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/contract_review.db"

    # 文件上传
    UPLOAD_DIR: Path = Path("./uploads")
    EXPORT_DIR: Path = Path("./exports")
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS: set = {
        "pdf", "jpg", "jpeg", "png",
        "docx", "txt", "md",
    }

    # OCR 配置
    OCR_API_TOKEN: str = ""  # 通过 .env 配置，不提交真实令牌
    OCR_USE_GPU: bool = False  # Demo 环境不使用 GPU
    OCR_LANG: str = "ch"  # 中文
    OCR_CONF_THRESHOLD: float = 0.6  # 置信度阈值

    # LLM 配置（通过环境变量或 .env 文件配置，不可硬编码）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 60  # 秒

    # JWT 认证
    JWT_SECRET: str = "change-me-in-production-use-env-var"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # 风险关键词（可配置）
    RISK_KEYWORDS: list = [
        "免责声明",
        "免责条款",
        "违约金过高",
        "不承担",
        "不负责",
        "损失赔偿",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
