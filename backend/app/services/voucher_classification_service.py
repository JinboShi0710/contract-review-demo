# -*- coding: utf-8 -*-
"""
凭证分类服务
使用 OCR + LLM 进行凭证分类
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


class VoucherClassificationService:
    """凭证分类服务"""

    def classify_voucher(
        self,
        file: UploadFile,
        db: Session
    ) -> dict:
        """
        凭证分类

        Args:
            file: 上传的凭证文件
            db: 数据库会话

        Returns:
            分类结果
        """
        classification_id = str(uuid.uuid4())

        try:
            # 1. 保存文件
            file_path, file_size, file_ext = self._save_file(file)

            # 2. OCR 识别
            ocr_results, page_count = self._ocr_recognize(file_path)

            # 3. LLM 分类
            classification_type = self._classify_with_llm(ocr_results)

            # 4. 保存分类记录
            classification = VoucherClassification(
                id=classification_id,
                file_name=file.filename,
                file_path=file_path,
                file_type=file_ext,
                file_size=file_size,
                classification_type=classification_type,
            )
            db.add(classification)
            db.commit()

            return {
                "classification_id": classification_id,
                "classification_type": classification_type,
                "classification_name": VOUCHER_CLASSIFICATIONS.get(classification_type, "未知"),
                "confidence_level": "high",  # Demo 级别固定为 high
            }

        except Exception as e:
            db.rollback()
            raise e

    def list_classifications(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """
        获取分类历史列表

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            (分类列表, 总数)
        """
        query = db.query(VoucherClassification).order_by(
            VoucherClassification.created_at.desc()
        )

        total = query.count()
        offset = (page - 1) * page_size
        classifications = query.offset(offset).limit(page_size).all()

        items = []
        for c in classifications:
            items.append({
                "classification_id": c.id,
                "file_name": c.file_name,
                "classification_type": c.classification_type,
                "classification_name": VOUCHER_CLASSIFICATIONS.get(c.classification_type, "未知"),
                "created_at": c.created_at.isoformat(),
            })

        return items, total

    def get_classification(
        self,
        classification_id: str,
        db: Session
    ) -> dict:
        """获取分类详情"""
        classification = db.query(VoucherClassification).filter(
            VoucherClassification.id == classification_id
        ).first()

        if not classification:
            return None

        return {
            "classification_id": classification.id,
            "file_name": classification.file_name,
            "file_path": classification.file_path,
            "file_type": classification.file_type,
            "classification_type": classification.classification_type,
            "classification_name": VOUCHER_CLASSIFICATIONS.get(classification.classification_type, "未知"),
            "created_at": classification.created_at.isoformat(),
        }

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

    def _classify_with_llm(self, ocr_results: List[dict]) -> str:
        """使用 LLM 进行分类判断"""
        from app.utils.llm.client import llm_client

        # 合并 OCR 文本
        full_text = "\n".join([item["text"] for item in ocr_results])

        # 如果文本为空或太短，返回默认分类
        if not full_text.strip() or len(full_text.strip()) < 10:
            return "OTHER_VOUCHER"

        # 调用 LLM
        prompt = CLASSIFICATION_PROMPT.format(ocr_text=full_text[:2000])

        try:
            response = llm_client.chat([{"role": "user", "content": prompt}])
            classification_code = response.strip()

            # 验证返回的分类代码是否有效
            if classification_code in VOUCHER_CLASSIFICATIONS:
                return classification_code
            else:
                return "OTHER_VOUCHER"
        except Exception as e:
            print(f"LLM 分类失败: {e}")
            return "OTHER_VOUCHER"


# 单例
voucher_classification_service = VoucherClassificationService()
