# -*- coding: utf-8 -*-
"""
合同模板比对服务
"""
import uuid
import difflib
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models.contract import ContractComparison
from app.utils.ocr.engine import ocr_engine
from app.utils.file_validator import validate_file, FileValidationError


class ComparisonService:
    """合同模板比对服务"""

    def compare_contracts(
        self,
        template_file: UploadFile,
        contract_file: UploadFile,
        db: Session
    ) -> dict:
        """
        比对两份合同

        Args:
            template_file: 模板文件
            contract_file: 待审合同文件
            db: 数据库会话

        Returns:
            比对结果
        """
        comparison_id = str(uuid.uuid4())

        try:
            # 1. 保存文件（不上传到contracts表，直接存文件路径）
            template_path, contract_path = self._save_files(
                template_file, contract_file
            )

            # 2. OCR 识别（返回带页码的识别结果）
            template_results, template_pages = self._ocr_recognize(template_path)
            contract_results, contract_pages = self._ocr_recognize(contract_path)

            # 3. 文本比对
            differences = self._compare_text(template_results, contract_results)

            # 4. 计算相似度
            template_text = "\n".join([item["text"] for item in template_results])
            contract_text = "\n".join([item["text"] for item in contract_results])
            similarity = self._calculate_similarity(template_text, contract_text)

            # 5. 保存比对记录（仅存储文件路径，不走contracts表）
            comparison = ContractComparison(
                id=comparison_id,
                differences=differences,
                summary=f"发现 {len(differences)} 处差异，相似度 {similarity:.1f}%",
                similarity=similarity,
                template_pages=template_pages,
                contract_pages=contract_pages,
                template_file_path=template_path,
                contract_file_path=contract_path,
            )
            db.add(comparison)
            db.commit()

            return {
                "comparison_id": comparison_id,
                "similarity": similarity,
                "template_pages": template_pages,
                "contract_pages": contract_pages,
                "differences_count": len(differences),
                "status": "completed",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _save_files(
        self,
        template_file: UploadFile,
        contract_file: UploadFile
    ) -> Tuple[str, str]:
        """保存上传的文件，返回文件路径元组"""
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # 保存模板文件
        template_id = str(uuid.uuid4())
        template_ext = self._get_extension(template_file.filename)
        template_filename = f"{template_id}.{template_ext}"
        template_path = settings.UPLOAD_DIR / template_filename

        with open(template_path, "wb") as f:
            f.write(template_file.file.read())

        validate_file(str(template_path), template_path.stat().st_size)

        # 保存合同文件
        contract_id = str(uuid.uuid4())
        contract_ext = self._get_extension(contract_file.filename)
        contract_filename = f"{contract_id}.{contract_ext}"
        contract_path = settings.UPLOAD_DIR / contract_filename

        with open(contract_path, "wb") as f:
            f.write(contract_file.file.read())

        validate_file(str(contract_path), contract_path.stat().st_size)

        return str(template_path), str(contract_path)

    def _get_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        from pathlib import Path
        return Path(filename).suffix.lower().lstrip(".")

    def _ocr_recognize(self, file_path: str) -> Tuple[List[dict], int]:
        """OCR 识别，返回每项结果及页码信息"""
        results, _, page_count = ocr_engine.recognize(file_path)
        return results, page_count

    def _compare_text(self, template_results: List[dict], contract_results: List[dict]) -> List[dict]:
        """
        比对两份文档的文本差异，使用 OCR 返回的页码信息

        Returns:
            差异列表
        """
        # 按行拆分文本，保留页码信息
        def expand_with_pages(results: List[dict]) -> List[Tuple[str, int]]:
            items = []
            for item in results:
                lines = item["text"].split("\n")
                page = item.get("page", 1)
                for line in lines:
                    if line.strip():
                        items.append((line, page))
            return items

        template_items = expand_with_pages(template_results)
        contract_items = expand_with_pages(contract_results)

        template_lines = [item[0] for item in template_items]
        contract_lines = [item[0] for item in contract_items]

        differ = difflib.SequenceMatcher(None, template_lines, contract_lines)

        differences = []

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            # 使用第一行的页码作为参考
            template_page = template_items[i1][1] if i1 < len(template_items) else 1
            contract_page = contract_items[j1][1] if j1 < len(contract_items) else 1

            if tag == "replace":
                differences.append({
                    "type": "modified",
                    "template_text": "\n".join(template_lines[i1:i2]),
                    "contract_text": "\n".join(contract_lines[j1:j2]),
                    "location": {"page": template_page},
                })
            elif tag == "delete":
                differences.append({
                    "type": "deleted",
                    "template_text": "\n".join(template_lines[i1:i2]),
                    "contract_text": "",
                    "location": {"page": template_page},
                })
            elif tag == "insert":
                differences.append({
                    "type": "added",
                    "template_text": "",
                    "contract_text": "\n".join(contract_lines[j1:j2]),
                    "location": {"page": contract_page},
                })

        return differences

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算相似度"""
        if not text1 and not text2:
            return 100.0
        if not text1 or not text2:
            return 0.0

        # 使用 SequenceMatcher 计算相似度
        return difflib.SequenceMatcher(None, text1, text2).ratio() * 100

    def get_comparison(self, comparison_id: str, db: Session) -> dict:
        """获取比对结果"""
        comparison = db.query(ContractComparison).filter(
            ContractComparison.id == comparison_id
        ).first()

        if not comparison:
            return None

        return {
            "comparison_id": comparison.id,
            "similarity": comparison.similarity,
            "template_pages": comparison.template_pages,
            "contract_pages": comparison.contract_pages,
            "differences": comparison.differences,
            "summary": comparison.summary,
        }


# 单例
comparison_service = ComparisonService()
