# -*- coding: utf-8 -*-
"""
凭证处理服务（合并分类+要素提取）
使用 OCR + LLM 进行凭证分类和要素提取
"""
import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models.voucher import VoucherClassification
from app.utils.ocr.engine import ocr_engine
from app.utils.file_validator import validate_file, FileValidationError


# 凭证分类类型枚举
VOUCHER_CLASSIFICATIONS = {
    # 证件类
    "ID_CARD": "身份证",
    "HOUSEHOLD_REGISTER": "户口簿",
    "TEMPORARY_ID_CARD": "临时身份证",
    "OTHER_ID": "其他证件",
    # 凭证类
    "BIRTH_CERTIFICATE": "出生证明",
    "REGULAR_CERTIFICATE": "普通存单",
    "LARGE_SPECIAL_CERTIFICATE": "大额特种存单",
    "PERSONAL_LARGE_CERTIFICATE": "个人大额存单",
    "GOVERNMENT_BOND": "凭证式国债",
    "TRANSFER_CHECK": "转账支票",
    "DEPOSIT_SLIP": "进账单",
    "SPECIAL_DEBIT_VOUCHER": "特种转账借方凭证",
    "SPECIAL_CREDIT_VOUCHER": "特种转账贷方凭证",
    "OTHER_VOUCHER": "其他凭证",
}

# LLM 分类提示词
CLASSIFICATION_PROMPT = """你是一个凭证分类专家。请根据以下 OCR 识别的凭证文本内容，判断该凭证属于以下哪种类型：

证件类型：
- ID_CARD: 身份证
- HOUSEHOLD_REGISTER: 户口簿
- TEMPORARY_ID_CARD: 临时身份证
- OTHER_ID: 其他证件

凭证类型：
- BIRTH_CERTIFICATE: 出生证明
- REGULAR_CERTIFICATE: 普通存单
- LARGE_SPECIAL_CERTIFICATE: 大额特种存单
- PERSONAL_LARGE_CERTIFICATE: 个人大额存单
- GOVERNMENT_BOND: 凭证式国债
- TRANSFER_CHECK: 转账支票
- DEPOSIT_SLIP: 进账单
- SPECIAL_DEBIT_VOUCHER: 特种转账借方凭证
- SPECIAL_CREDIT_VOUCHER: 特种转账贷方凭证
- OTHER_VOUCHER: 其他凭证

OCR 识别内容：
{ocr_text}

请只返回一个分类代码，不要返回其他内容。如果无法确定，返回 OTHER_VOUCHER。
"""

# LLM 要素提取提示词
ELEMENT_EXTRACTION_PROMPT = """你是一个凭证要素提取专家。请根据以下 OCR 识别的凭证文本内容，提取所有你认为有价值的要素。

OCR 识别内容：
{ocr_text}

请以 JSON 格式返回提取到的要素列表，每项包含 label（要素名称）和 value（要素值）。
只返回你确定的内容，不要猜测。

返回格式：
{{"elements": [
  {{"label": "金额", "value": "10000元"}},
  {{"label": "日期", "value": "2024年1月1日"}}
]}}

只返回 JSON，不要返回其他内容。
"""


class VoucherProcessService:
    """凭证处理服务（合并分类+要素提取）"""

    def process_voucher(
        self,
        file: UploadFile,
        db: Session
    ) -> dict:
        """
        处理凭证（分类+要素提取）

        Args:
            file: 上传的凭证文件
            db: 数据库会话

        Returns:
            处理结果（分类+要素）
        """
        voucher_id = str(uuid.uuid4())

        try:
            # 1. 保存文件
            file_path, file_size, file_ext = self._save_file(file)

            # 2. OCR 识别
            ocr_results, page_count = self._ocr_recognize(file_path)
            full_text = "\n".join([item["text"] for item in ocr_results])

            # 3. LLM 分类 + 要素提取（并行调用）
            classification = self._classify_with_llm(full_text)
            elements = self._extract_with_llm(ocr_results)

            # 4. 存储分类记录
            classification_record = VoucherClassification(
                id=str(uuid.uuid4()),
                file_name=file.filename,
                file_path=file_path,
                file_type=file_ext,
                file_size=file_size,
                classification_type=classification,
            )
            db.add(classification_record)
            db.commit()

            return {
                "voucher_id": voucher_id,
                "file_name": file.filename,
                "classification_type": classification,
                "classification_name": VOUCHER_CLASSIFICATIONS.get(classification, "未知"),
                "elements": elements,
            }

        except Exception as e:
            db.rollback()
            raise e

    def _save_file(self, file: UploadFile) -> Tuple[str, int, str]:
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

        return str(file_path), file_path.stat().st_size, file_ext

    def _get_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        from pathlib import Path
        return Path(filename).suffix.lower().lstrip(".")

    def _ocr_recognize(self, file_path: str) -> Tuple[List[dict], int]:
        """OCR 识别"""
        results, _, page_count = ocr_engine.recognize(file_path)
        return results, page_count

    def _classify_with_llm(self, full_text: str) -> str:
        """使用 LLM 进行分类判断"""
        from app.utils.llm.client import llm_client

        if not full_text.strip() or len(full_text.strip()) < 10:
            return "OTHER_VOUCHER"

        prompt = CLASSIFICATION_PROMPT.format(ocr_text=full_text[:2000])

        try:
            response = llm_client.chat([{"role": "user", "content": prompt}])
            classification_code = response.strip()

            if classification_code in VOUCHER_CLASSIFICATIONS:
                return classification_code
            else:
                return "OTHER_VOUCHER"
        except Exception as e:
            print(f"LLM 分类失败: {e}")
            return "OTHER_VOUCHER"

    def _extract_with_llm(self, ocr_results: List[dict]) -> List[dict]:
        """使用 LLM 进行要素提取"""
        from app.utils.llm.client import llm_client
        import json

        full_text = "\n".join([item["text"] for item in ocr_results])

        if not full_text.strip() or len(full_text.strip()) < 10:
            return []

        prompt = ELEMENT_EXTRACTION_PROMPT.format(ocr_text=full_text[:2000])

        try:
            response = llm_client.chat([{"role": "user", "content": prompt}])

            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            elements = result.get("elements", [])

            valid_elements = []
            for elem in elements:
                label = elem.get("label", "").strip()
                value = elem.get("value", "").strip()
                if label and value:
                    valid_elements.append({
                        "label": label[:50],
                        "value": str(value)[:512],
                    })

            return valid_elements

        except Exception as e:
            print(f"LLM 要素提取失败: {e}")
            return []


# 单例
voucher_process_service = VoucherProcessService()
