# -*- coding: utf-8 -*-
"""大模型配置 API（仅管理员）。"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.response import success_response, error_response
from app.utils.llm.client import llm_client

router = APIRouter(prefix="/model-settings", tags=["模型配置"])
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class ModelSettingsRequest(BaseModel):
    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1)
    timeout: int = Field(default=60, ge=5, le=600)
    api_key: Optional[str] = None


def _public_settings() -> dict:
    return {
        "base_url": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
        "timeout": settings.LLM_TIMEOUT,
        "api_key_configured": bool(settings.LLM_API_KEY),
    }


def _save_env(values: dict[str, str]) -> None:
    """保留 .env 中其他配置，仅更新 LLM 相关字段。"""
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    pending = dict(values)
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in pending:
            output.append(f"{key}={pending.pop(key)}")
        else:
            output.append(line)
    if pending and output and output[-1] != "":
        output.append("")
    output.extend(f"{key}={value}" for key, value in pending.items())
    ENV_FILE.write_text("\n".join(output) + "\n", encoding="utf-8")


@router.get("")
def get_model_settings(_: User = Depends(require_admin)):
    """获取非敏感模型配置；API Key 永不返回前端。"""
    return success_response(data=_public_settings())


@router.put("")
def update_model_settings(
    body: ModelSettingsRequest,
    _: User = Depends(require_admin),
):
    api_key = (body.api_key or "").strip() or settings.LLM_API_KEY
    if not api_key:
        return error_response(code=400, message="请填写 API Key")

    base_url = body.base_url.strip().rstrip("/")
    model = body.model.strip()
    values = {
        "LLM_BASE_URL": base_url,
        "LLM_MODEL": model,
        "LLM_TIMEOUT": str(body.timeout),
    }
    if body.api_key and body.api_key.strip():
        values["LLM_API_KEY"] = body.api_key.strip()

    try:
        _save_env(values)
        llm_client.reconfigure(api_key, base_url, model, body.timeout)
        return success_response(data=_public_settings(), message="模型配置已保存并生效")
    except Exception as exc:
        return error_response(code=500, message=f"保存失败：{exc}")


@router.post("/test")
def test_model_settings(
    body: ModelSettingsRequest,
    _: User = Depends(require_admin),
):
    """使用当前表单参数发起一次最小请求，不保存配置。"""
    api_key = (body.api_key or "").strip() or settings.LLM_API_KEY
    if not api_key:
        return error_response(code=400, message="请填写 API Key")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=body.base_url.strip().rstrip("/"),
            timeout=body.timeout,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=body.model.strip(),
            messages=[{"role": "user", "content": "只回复：连接成功"}],
            temperature=0,
            max_tokens=16,
        )
        reply = response.choices[0].message.content or "连接成功"
        return success_response(data={"reply": reply}, message="模型连接成功")
    except Exception as exc:
        return error_response(code=500, message=f"连接失败：{exc}")
