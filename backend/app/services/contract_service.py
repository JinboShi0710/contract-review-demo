# -*- coding: utf-8 -*-
"""
合同服务（核心业务逻辑）
"""
import os
import time
import uuid
import json
from pathlib import Path
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models.contract import Contract, ContractElement, ContractRisk
from app.utils.file_validator import validate_file, FileValidationError
from app.utils.ocr.engine import ocr_engine
from app.utils.llm.client import llm_client
from app.services.rule_engine import RuleEngine
from app.services.audit_engine import audit_engine
from app.services.audit_rule_service import audit_rule_service
from app.services.element_extractor import element_extractor


LOAN_RULE_TERMS = (
    "贷款", "借款", "信贷", "银行", "利率", "LPR", "还款", "贷后",
    "银保监", "网贷", "借款人", "担保物", "抵押", "质押",
)


def _is_loan_contract(contract_type: Optional[str], text: str) -> bool:
    label = contract_type or ""
    strong_terms = ("贷款合同", "借款合同", "信贷合同", "融资合同")
    return any(term in label or term in text[:1200] for term in strong_terms)


def _rule_is_applicable(rule: dict, contract_type: Optional[str], text: str) -> bool:
    """按合同类型过滤明显不适用规则，避免贷款规则污染采购合同。"""
    generic_rule_names = {
        "霸王条款识别", "签章一致性审核", "合同条款前后一致性检查",
        "合同页码完整性检查", "授权文件完整性检查",
        "合同条款编号与结构连续性检查", "合同履约能力条款检查",
        "付款节点清晰度检查", "违约责任对等性检查",
    }
    if rule.get("name") in generic_rule_names:
        return True

    combined = " ".join([
        rule.get("name", ""),
        rule.get("description", ""),
        json.dumps(rule.get("params", {}), ensure_ascii=False),
    ])
    if any(term in combined for term in LOAN_RULE_TERMS):
        return _is_loan_contract(contract_type, text)

    if "电子合同" in combined or "电子签名" in combined:
        electronic_markers = ("电子合同", "电子签名", "电子签章", "数字证书", "哈希值")
        return any(marker in text for marker in electronic_markers)

    if any(term in combined for term in ("担保人", "担保物", "抵押物", "质押物")):
        guarantee_markers = ("担保合同", "保证合同", "抵押合同", "质押合同")
        return any(marker in (contract_type or "") or marker in text[:1200] for marker in guarantee_markers)

    return True


def _assess_contract_document(text: str, extracted_type: Optional[str]) -> Tuple[bool, str, str]:
    """判断输入是否具备合同基本特征，避免把会议纪要等文件审核为全部通过。"""
    normalized = "".join(text.split())
    non_contract_markers = ("会议纪要", "会议记录", "退休职工", "工作简报", "新闻稿", "通知公告")
    contract_markers = (
        "甲方", "乙方", "本合同", "本协议", "双方", "合同金额",
        "付款方式", "违约责任", "争议解决", "签字盖章", "签订日期",
    )
    found_contract_markers = [marker for marker in contract_markers if marker in normalized]
    found_non_contract = next((marker for marker in non_contract_markers if marker in normalized[:1500]), None)

    if found_non_contract and len(found_contract_markers) < 3:
        return False, f"检测到“{found_non_contract}”，且缺少合同主体、权利义务等基本结构", found_non_contract
    if len(found_contract_markers) < 2 and extracted_type in (None, "", "其他", "未知", "未提及"):
        evidence = found_contract_markers[0] if found_contract_markers else ""
        return False, "未找到足够的合同主体、权利义务或签署结构，无法按合同出具通过结论", evidence
    return True, "具备合同基本结构", "、".join(found_contract_markers[:3])


class ContractService:
    """合同服务"""

    def upload_contract(self, file: UploadFile, db: Session, created_by: str = None) -> dict:
        """
        上传并处理合同
        """
        contract_id = str(uuid.uuid4())

        file_ext = Path(file.filename).suffix.lower().lstrip(".")
        saved_filename = f"{contract_id}.{file_ext}"
        file_path = settings.UPLOAD_DIR / saved_filename

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        content = file.file.read()
        file_size = len(content)
        with open(file_path, "wb") as f:
            f.write(content)

        validate_file(str(file_path), file_size)

        contract = Contract(
            id=contract_id,
            file_name=file.filename,
            file_path=str(file_path),
            file_type=file_ext,
            file_size=file_size,
            status="created",
            created_by=created_by,
        )
        db.add(contract)
        db.commit()

        return {
            "contract_id": contract_id,
            "status": "created",
            "file_name": file.filename,
        }

    def process_contract(self, contract_id: str, db: Session) -> dict:
        """
        处理合同：OCR + LLM 提取要素和风险 + 审核规则引擎
        """
        contract = db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.is_deleted == 0
        ).first()

        if not contract:
            raise ValueError("合同不存在")

        contract.status = "processing"
        db.commit()

        try:
            file_path = contract.file_path

            # 1. OCR 识别
            ocr_results, avg_confidence, page_count = ocr_engine.recognize(file_path)
            contract.confidence = avg_confidence
            contract.page_count = page_count

            # 拼接完整文本
            full_text = "\n\n".join([
                f"[第{item.get('page', index)}页]\n{item['text']}"
                for index, item in enumerate(ocr_results, start=1)
            ])

            # 2. LLM 提取要素
            elements_data = {}
            try:
                elements_data = llm_client.extract_contract_elements(full_text) or {}
                contract_type = elements_data.pop("contract_type", None)
                # 这些字段用于文档分类，不属于需要展示的合同业务要素。
                elements_data.pop("document_category", None)
                elements_data.pop("is_contract", None)
                elements_data.pop("document_type_reason", None)
                if contract_type:
                    contract.contract_type = str(contract_type)
            except Exception as e:
                print(f"LLM 要素提取失败: {e}")

            # 无论模型是否可用，都用本地规则补齐未提取的常见要素。
            # 这样遇到429、网络故障或模型漏项时，合同要素区不会整块消失。
            local_elements = element_extractor._extract_by_rules(full_text, ocr_results)
            for item in local_elements:
                elements_data.setdefault(item["element_type"], item["element_value"])

            for elem_type, elem_value in elements_data.items():
                if elem_value and elem_value not in ["未知", "未提及", ""]:
                    contract_element = ContractElement(
                        contract_id=contract_id,
                        element_type=elem_type,
                        element_value=str(elem_value),
                        confidence=None,
                    )
                    db.add(contract_element)

            # 非合同或证据不足的文件不能继续套用合同规则，更不能显示“全部通过”。
            is_contract_document, document_reason, document_evidence = _assess_contract_document(
                full_text, contract.contract_type
            )
            if not is_contract_document:
                db.add(ContractRisk(
                    contract_id=contract_id,
                    risk_type="文档类型校验",
                    risk_level="medium",
                    location={"x": 0, "y": 0, "width": 100, "height": 20},
                    description=document_reason,
                    rule_name="合同文档有效性校验",
                    rule_type="document_validation",
                    rule_params={
                        "disposition": "需核验",
                        "evidence_verified": bool(document_evidence),
                    },
                    matched=0,
                    matched_items=[document_evidence] if document_evidence else [],
                    execution_result="无法确认该文件属于可审核合同，已停止后续合同规则执行",
                ))
                contract.status = "completed"
                db.commit()
                return {
                    "status": "completed",
                    "contract_id": contract_id,
                    "confidence": avg_confidence,
                    "elements_count": len(elements_data),
                    "risks_count": 0,
                    "rule_matches_count": 0,
                    "document_validation": "uncertain",
                }

            # 3. 执行审核规则引擎 (FC-08, FC-11)
            all_enabled_rules = audit_rule_service.get_enabled_rules(db)
            enabled_rules = [
                rule for rule in all_enabled_rules
                if _rule_is_applicable(rule, contract.contract_type, full_text)
            ]
            skipped_count = len(all_enabled_rules) - len(enabled_rules)
            if skipped_count:
                print(
                    f"按合同类型 {contract.contract_type or '未识别'} 跳过 "
                    f"{skipped_count} 条不适用规则",
                    flush=True,
                )
            rule_engine = RuleEngine(enabled_rules) if enabled_rules else None

            rule_results = []
            llm_rules = []
            if rule_engine:
                rule_results = rule_engine.execute_all(full_text)
                # 分离需要LLM处理的规则
                llm_rule_types = ["llm_risk", "llm_compliance", "llm_completeness"]
                for rule in enabled_rules:
                    if rule["rule_type"] in llm_rule_types:
                        llm_rules.append(rule)

            # 4. 执行LLM语义审核 (FC-09, FC-11)
            audit_result = audit_engine.execute_audit(
                db, full_text, rule_results, llm_rules,
                contract_type=contract.contract_type,
            )

            # 5. 保存所有规则执行结果（FC-06: 未命中显示"通过"，FC-11: 完整规则信息）
            # 先按 rule_id 建立 lookup
            rule_lookup = {r.rule_id: r for r in rule_results}

            # 保存规则引擎的执行结果
            for rule_result in rule_results:
                # 获取对应的规则配置
                rule_config = next((r for r in enabled_rules if r["id"] == rule_result.rule_id), None)

                contract_risk = ContractRisk(
                    contract_id=contract_id,
                    risk_type=rule_result.rule_name,  # 使用规则名称作为风险类型
                    risk_level=rule_result.severity,
                    location={"x": 0, "y": 0, "width": 100, "height": 20},
                    description=rule_result.details or (f"命中规则: {rule_result.rule_name}" if rule_result.matched else f"规则执行: {rule_result.rule_name}"),
                    rule_id=rule_result.rule_id,
                    rule_name=rule_result.rule_name,
                    rule_type=rule_result.rule_type,
                    rule_params=rule_config.get("params", {}) if rule_config else {},
                    # 风险=2；有原文证据支持的通过=1；没有证据只能是无法确定=0。
                    matched=2 if rule_result.matched else (1 if rule_result.matched_items else 0),
                    matched_items=rule_result.matched_items or [],
                    execution_result=(rule_result.details if rule_result.matched else
                                      "执行通过，已有原文证据" if rule_result.matched_items else
                                      "未发现风险，但缺少可反查的通过证据，结论为无法确定"),
                )
                db.add(contract_risk)

            # 保存全部LLM规则执行结果：命中的显示风险，未命中的明确显示通过。
            # 这样前端不会只看到本地规则，也能核对AI实际执行了哪些规则。
            llm_risks_by_rule = {}
            for risk in audit_result.get("risks", []):
                if risk.get("source") == "llm" and risk.get("rule_id"):
                    llm_risks_by_rule.setdefault(risk["rule_id"], []).append(risk)
            llm_assessed_rule_ids = set(audit_result.get("llm_assessed_rule_ids", []))
            llm_passes_by_rule = {
                passed["rule_id"]: passed
                for passed in audit_result.get("llm_passes", [])
                if passed.get("rule_id") and passed.get("evidence_verified")
            }
            for rule_config in llm_rules:
                matched_risks = llm_risks_by_rule.get(rule_config["id"], [])
                rows = matched_risks or [None]
                for risk in rows:
                    is_risk = risk is not None
                    was_assessed = rule_config["id"] in llm_assessed_rule_ids
                    passed = llm_passes_by_rule.get(rule_config["id"])
                    has_verified_pass = passed is not None
                    description = (
                        risk.get("description", "") if is_risk
                        else "已找到可反查的合同原文，未发现该规则所述风险" if has_verified_pass
                        else "AI未识别到可反查的通过证据，结论为无法确定" if was_assessed
                        else "AI未确认完成该规则的审查，结论为无法确定"
                    )
                    contract_risk = ContractRisk(
                        contract_id=contract_id,
                        risk_type=risk.get("risk_type", rule_config["name"]) if is_risk else rule_config["name"],
                        risk_level=risk.get("severity", rule_config.get("severity", "low")) if is_risk else rule_config.get("severity", "low"),
                        location={"x": 0, "y": 0, "width": 100, "height": 20},
                        description=description,
                        rule_id=rule_config["id"],
                        rule_name=rule_config["name"],
                        rule_type=rule_config["rule_type"],
                        rule_params={
                            **rule_config.get("params", {}),
                            "audit_framework": "ArchSight AIOS Contract Audit",
                            "evidence_page": risk.get("evidence_page") if is_risk else passed.get("evidence_page") if has_verified_pass else None,
                            "evidence_clause": risk.get("evidence_clause") if is_risk else passed.get("evidence_clause") if has_verified_pass else None,
                            "review_role": risk.get("review_role") if is_risk else passed.get("review_role") if has_verified_pass else None,
                            "disposition": risk.get("disposition") if is_risk else "无需处理" if has_verified_pass else "需核验",
                            "evidence_verified": risk.get("evidence_verified") if is_risk else has_verified_pass,
                            "independent_issue_key": risk.get("independent_issue_key") if is_risk else None,
                            "evidence_scope": None if is_risk else (f"第{passed.get('evidence_page')}页" if has_verified_pass and passed.get("evidence_page") else None),
                            "assessment_completed": True if was_assessed else False,
                        },
                        matched=2 if is_risk else (1 if has_verified_pass else 0),
                        matched_items=(
                            [risk.get("evidence_quote", "")] if is_risk and risk.get("evidence_quote")
                            else [passed.get("evidence_quote", "")] if has_verified_pass
                            else []
                        ),
                        execution_result=json.dumps(risk, ensure_ascii=False) if is_risk else description,
                    )
                    db.add(contract_risk)

            contract.status = "completed"
            db.commit()

            return {
                "status": "completed",
                "contract_id": contract_id,
                "confidence": avg_confidence,
                "elements_count": len(elements_data),
                "risks_count": len(audit_result.get("risks", [])),
                "rule_matches_count": len([r for r in rule_results if r.matched]),
                "audit_execution_time_ms": audit_result.get("execution_time_ms", 0),
            }

        except Exception as e:
            contract.status = "failed"
            db.commit()
            raise e

    def get_contract(
        self, contract_id: str, db: Session,
        current_user_id: str = None, role: str = "admin"
    ) -> Optional[Contract]:
        """获取合同详情，manager 只能访问自己的合同（含历史 null 合同）"""
        query = db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.is_deleted == 0,
        )
        if role == "manager" and current_user_id:
            from sqlalchemy import or_
            query = query.filter(
                or_(Contract.created_by == current_user_id, Contract.created_by.is_(None))
            )
        return query.first()

    def list_contracts(
        self, db: Session, page: int = 1, page_size: int = 20,
        current_user_id: str = None, role: str = "admin"
    ) -> Tuple[List[Contract], int]:
        """获取合同列表，manager 只能看自己上传的合同（含历史 null 合同）"""
        query = db.query(Contract).filter(Contract.is_deleted == 0)
        if role == "manager" and current_user_id:
            from sqlalchemy import or_
            query = query.filter(
                or_(Contract.created_by == current_user_id, Contract.created_by.is_(None))
            )

        total = query.count()
        contracts = query.order_by(Contract.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        return contracts, total

    def delete_contract(self, contract_id: str, db: Session) -> bool:
        """删除合同（软删除）"""
        contract = db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.is_deleted == 0
        ).first()

        if not contract:
            return False

        contract.is_deleted = 1
        db.commit()

        return True


# 单例
contract_service = ContractService()
