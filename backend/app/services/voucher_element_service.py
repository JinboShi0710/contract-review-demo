# -*- coding: utf-8 -*-
"""
凭证要素提取服务
使用 OCR + LLM 进行凭证要素提取
不存储数据，直接返回提取结果
"""
import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.utils.ocr.engine import ocr_engine
from app.utils.file_validator import validate_file, FileValidationError


# LLM 要素提取提示词（动态提取，不约束类型）
ELEMENT_EXTRACTION_PROMPT = """你是一个凭证要素提取专家。请根据以下 OCR 识别的凭证文本内容，提取所有你认为有价值的要素。

OCR 识别内容：
{ocr_text}

请以 JSON 格式返回提取到的要素列表，每项包含 label（要素名称）和 value（要素值）。
只返回你确定的内容，不要猜测。

返回格式：
{{"elements": [
  {{"label": "金额", "value": "10000元"}},
  {{"label": "日期", "value": "2024年1月1日"}},
  {{"label": "收款人", "value": "张三"}}
]}}

只返回 JSON，不要返回其他内容。
"""


class VoucherElementService:
    """凭证要素提取服务（不存储，直接返回）"""

    def extract_elements(
        self,
        file: UploadFile,
        db: Session
    ) -> dict:
        """
        提取凭证要素（不存储，直接返回）

        Args:
            file: 上传的凭证文件
            db: 数据库会话（不使用）

        Returns:
            要素提取结果
        """
        voucher_id = str(uuid.uuid4())

        # 1. 保存临时文件
        file_path, file_ext = self._save_file(file)

        # 2. OCR 识别
        ocr_results, page_count = self._ocr_recognize(file_path)

        # 3. LLM 提取要素
        elements = self._extract_with_llm(ocr_results)

        return {
            "voucher_id": voucher_id,
            "file_name": file.filename,
            "elements": elements,
        }

    def _save_file(self, file: UploadFile) -> Tuple[str, str]:
        """保存上传的文件"""
        from pathlib import Path

        file_id = str(uuid.uuid4())
        file_ext = self._get_extension(file.filename)
        filename = f"{file_id}.{file_ext}"
        file_path = settings.UPLOAD_DIR / filename

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        validate_file(str(file_path), file_path.stat().st_size)

        return str(file_path), file_ext

    def _get_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        from pathlib import Path
        return Path(filename).suffix.lower().lstrip(".")

    def _ocr_recognize(self, file_path: str) -> Tuple[List[dict], int]:
        """OCR 识别"""
        results, _, page_count = ocr_engine.recognize(file_path)
        return results, page_count

    def _extract_with_llm(self, ocr_results: List[dict]) -> List[dict]:
        """使用 LLM 进行要素提取（动态类型）"""
        from app.utils.llm.client import llm_client
        import json

        # 合并 OCR 文本
        full_text = "\n".join([item["text"] for item in ocr_results])

        # 如果文本为空或太短，返回空列表
        if not full_text.strip() or len(full_text.strip()) < 10:
            return []

        # 调用 LLM
        prompt = ELEMENT_EXTRACTION_PROMPT.format(ocr_text=full_text[:2000])

        try:
            response = llm_client.chat([{"role": "user", "content": prompt}])

            # 解析 JSON 响应
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            elements = result.get("elements", [])

            # 验证并清理要素
            valid_elements = []
            for elem in elements:
                label = elem.get("label", "").strip()
                value = elem.get("value", "").strip()
                if label and value:
                    valid_elements.append({
                        "label": label[:50],  # 限制长度
                        "value": str(value)[:512],  # 截断过长值
                    })

            return valid_elements

        except Exception as e:
            print(f"LLM 要素提取失败: {e}")
            return []


# 单例
voucher_element_service = VoucherElementService()
