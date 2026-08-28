# -*- coding: utf-8 -*-
"""
审核执行引擎
规则引擎 + LLM语义审核 合并执行
"""
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.audit_rule import AuditRule
from app.services.rule_engine import RuleEngine, RuleMatchResult
from app.utils.llm.client import llm_client


# LLM 风险检测提示词
RISK_DETECTION_PROMPT = """你是一个合同风险审核专家。请根据以下合同内容，判断是否存在以下风险：

风险类型：
- 免责声明：合同中存在对一方不利的免责条款
- 霸王条款：合同中存在明显不公平的条款
- 违规条款：合同中存在违反监管规定的条款

合同内容：
{contract_text}

规则命中结果（供参考）：
{rule_matches}

请以JSON格式返回审核结果：
{{"risks": [
  {{
    "risk_type": "风险类型",
    "description": "风险描述",
    "severity": "high/medium/low",
    "location": "风险位置或上下文"
  }}
]}}

如果没有发现风险，返回空的risks数组。
只返回JSON，不要返回其他内容。
"""


class AuditEngine:
    """审核执行引擎"""

    def __init__(self):
        pass

    def execute_audit(
        self,
        db: Session,
        contract_text: str,
        rule_results: List[RuleMatchResult],
        llm_rules: List[Dict],
        contract_type: Optional[str] = None,
    ) -> Dict:
        """
        执行完整审核流程

        Args:
            db: 数据库会话
            contract_text: 合同文本
            rule_results: 规则引擎执行结果
            llm_rules: 需要LLM处理的规则配置

        Returns:
            审核结果
        """
        start_time = time.time()

        # 1. 规则引擎结果
        rule_risks = self._process_rule_results(rule_results)

        # 2. LLM 语义审核
        llm_risks, llm_passes, llm_assessed_rule_ids = self._execute_llm_audit(
            contract_text, rule_results, llm_rules, contract_type=contract_type
        )

        # 3. 合并结果
        all_risks = rule_risks + llm_risks

        elapsed_time = time.time() - start_time

        return {
            "total_risks": len(all_risks),
            "high_risks": len([r for r in all_risks if r["severity"] == "high"]),
            "medium_risks": len([r for r in all_risks if r["severity"] == "medium"]),
            "low_risks": len([r for r in all_risks if r["severity"] == "low"]),
            "risks": all_risks,
            "llm_passes": llm_passes,
            "llm_assessed_rule_ids": llm_assessed_rule_ids,
            "rule_matches": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "rule_type": r.rule_type,
                    "severity": r.severity,
                    "matched": r.matched,
                    "details": r.details,
                    "matched_items": r.matched_items,
                }
                for r in rule_results
            ],
            "execution_time_ms": int(elapsed_time * 1000),
        }

    def _process_rule_results(
        self,
        rule_results: List[RuleMatchResult],
    ) -> Tuple[List[Dict], List[str]]:
        """处理规则匹配结果，转换为风险列表"""
        risks = []

        for result in rule_results:
            if result.matched:
                risks.append({
                    "risk_type": result.rule_name,  # 使用规则名称而非规则类型
                    "description": result.details or f"命中规则: {result.rule_name}",
                    "severity": result.severity,
                    "location": ", ".join(result.matched_items[:3]) if result.matched_items else None,
                    "source": "rule",
                    "rule_id": result.rule_id,
                    "rule_type": result.rule_type,  # 保留规则类型以便分类统计
                })

        return risks

    def _execute_llm_audit(
        self,
        contract_text: str,
        rule_results: List[RuleMatchResult],
        llm_rules: List[Dict],
        contract_type: Optional[str] = None,
    ) -> List[Dict]:
        """执行LLM语义审核"""
        if not llm_rules or not contract_text.strip():
            return [], [], []

        # 构建规则命中的摘要（供LLM参考）
        matched_rules = [
            f"- {r.rule_name}({r.severity}): {r.details}"
            for r in rule_results
            if r.matched
        ]
        rule_summary = "\n".join(matched_rules) if matched_rules else "无"

        # 语义审核失败时必须向上抛出，不能把“调用失败”伪装成“没有风险”。
        return self._call_llm_for_rules(
            contract_text, rule_summary, llm_rules, contract_type=contract_type
        )

    def _call_llm_for_rules(
        self,
        contract_text: str,
        rule_summary: str,
        llm_rules: List[Dict],
        contract_type: Optional[str] = None,
    ) -> Tuple[List[Dict], List[str]]:
        """一次调用处理全部语义规则，避免逐条串行请求。"""
        import json

        rule_payload = [
            {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "rule_type": rule["rule_type"],
                "default_severity": rule.get("severity", "low"),
                "requirement": rule.get("params", {}).get("prompt")
                    or rule.get("description", ""),
            }
            for rule in llm_rules
        ]

        prompt = f"""
你是采用 ArchSight AIOS Contract Audit 工作流的工程合同审核助手。
当前合同类型：{contract_type or "未识别"}。
请一次性执行下面全部审核规则，并建立可人工回查的证据链。

重要要求：
1. 仅在合同确实存在问题时返回风险；不适用或未发现问题的规则不要返回。
2. 不要把“OCR/Markdown格式”“不是某类合同”本身当作合同风险。
3. 每条风险必须准确填写对应的 rule_id；不得编造规则。
4. 对同一问题避免重复描述。
5. 只基于合同原文，不把合同外事实或缺失资料直接认定为违约事实。
6. 每条风险必须提供一段连续、逐字复制、不拼接不改写的原文短摘（建议20-60字）和页码；证据不足时写“需核验”，不得编造。
7. 输出仅用于履约管理辅助，不构成最终法律意见、责任归属、索赔或是否可签结论。
8. 同一独立问题即使触发多条规则，也只保留最有代表性的一条。
9. 同一条规则下如存在多个彼此独立的问题，必须分别返回多条风险，并使用不同的 independent_issue_key；不得只保留其中一项。
10. 空格、换行、标点、千分位分隔符或OCR排版差异不属于实质性矛盾；只有金额、日期、主体、义务等内容发生实质冲突时，才能判为前后不一致。

合同内容：
{contract_text[:20000]}

参考信息：
{rule_summary}

审核规则：
{json.dumps(rule_payload, ensure_ascii=False)}

只返回JSON。assessed_rule_ids 必须列出你实际完成审核的全部规则ID；
未发现风险不等于通过。只有找到能直接证明满足该规则的合同原文时，才能写入 passes；
无法找到正向原文证据的规则只列入 assessed_rule_ids，系统会将其判为“无法确定”。
{{"assessed_rule_ids": ["已完成审核的规则ID"], "passes": [{{
  "rule_id": "规则ID",
  "evidence_page": 1,
  "evidence_clause": "条款号或标题",
  "evidence_quote": "能够直接证明合规的合同原文短摘，不超过100字",
  "review_role": "法务/商务/造价/财务/项目经理/授权签章负责人之一"
}}], "risks": [{{
  "rule_id": "规则ID",
  "risk_type": "风险类型",
  "description": "风险事实和可能影响",
  "severity": "high/medium/low",
  "evidence_page": 1,
  "evidence_clause": "条款号或标题，无法确定则填需核验",
  "evidence_quote": "合同原文短摘，不超过100字",
  "review_role": "法务/商务/造价/财务/项目经理/授权签章负责人之一",
  "disposition": "建议复核或需核验",
  "independent_issue_key": "用于合并同一问题的简短标识"
}}]}}
"""

        last_error = None
        for attempt in range(2):
            retry_note = ""
            if attempt:
                retry_note = "\n上一次输出不是有效JSON。请严格只返回JSON对象，不要输出安全分类、解释或Markdown。"
            response = llm_client.chat([{"role": "user", "content": prompt + retry_note}])
            try:
                json_str = response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]

                result = json.loads(json_str)
                risks = result.get("risks")
                if not isinstance(risks, list):
                    raise ValueError("返回结果缺少 risks 数组")
                passes = result.get("passes", [])
                if not isinstance(passes, list):
                    raise ValueError("返回结果中的 passes 必须是数组")

                rules_by_id = {rule["id"]: rule for rule in llm_rules}
                assessed_rule_ids = [
                    rule_id for rule_id in result.get("assessed_rule_ids", [])
                    if rule_id in rules_by_id
                ]
                missing_assessments = set(rules_by_id) - set(assessed_rule_ids)
                if missing_assessments:
                    raise ValueError(
                        f"模型未确认完成 {len(missing_assessments)} 条规则的审核"
                    )
                valid_risks = []
                normalized_contract = "".join(contract_text.split())
                for risk in risks:
                    rule = rules_by_id.get(risk.get("rule_id"))
                    if not rule or not risk.get("description"):
                        continue
                    risk["source"] = "llm"
                    risk["rule_name"] = rule["name"]
                    risk["rule_type"] = rule["rule_type"]
                    if risk.get("severity") not in ("high", "medium", "low"):
                        risk["severity"] = rule.get("severity", "low")
                    if not risk.get("risk_type"):
                        risk["risk_type"] = rule["name"]
                    quote = str(risk.get("evidence_quote") or "").strip()
                    candidates = [quote] + [
                        item.strip() for item in re.split(r"[；;。]", quote)
                        if len("".join(item.split())) >= 8
                    ]
                    verified_quote = next((
                        item for item in sorted(candidates, key=len, reverse=True)
                        if "".join(item.split()) in normalized_contract
                    ), "")
                    risk["evidence_verified"] = bool(verified_quote)
                    if verified_quote:
                        risk["evidence_quote"] = verified_quote
                    if not risk["evidence_verified"]:
                        risk["disposition"] = "需核验"
                    if risk.get("disposition") not in ("建议复核", "需核验"):
                        risk["disposition"] = "建议复核"
                    if not risk.get("review_role"):
                        risk["review_role"] = "法务/商务"
                    valid_risks.append(risk)

                # “通过”必须有能够在合同全文中逐字反查的正向证据。
                # 模型仅声称“已审核/未发现”不能构成通过。
                valid_passes = []
                risk_rule_ids = {risk["rule_id"] for risk in valid_risks}
                for passed in passes:
                    rule = rules_by_id.get(passed.get("rule_id"))
                    if not rule or passed.get("rule_id") in risk_rule_ids:
                        continue
                    quote = str(passed.get("evidence_quote") or "").strip()
                    normalized_quote = "".join(quote.split())
                    if len(normalized_quote) < 8 or normalized_quote not in normalized_contract:
                        continue
                    valid_passes.append({
                        "rule_id": passed["rule_id"],
                        "rule_name": rule["name"],
                        "rule_type": rule["rule_type"],
                        "evidence_page": passed.get("evidence_page"),
                        "evidence_clause": passed.get("evidence_clause"),
                        "evidence_quote": quote,
                        "review_role": passed.get("review_role") or "法务/商务",
                        "evidence_verified": True,
                    })

                deduplicated = []
                seen_keys = set()
                for risk in valid_risks:
                    key = risk.get("independent_issue_key") or risk.get("risk_type")
                    key = str(key).strip().lower()
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    deduplicated.append(risk)
                # 返回的风险本身也说明对应规则已经执行，避免模型漏填 assessed_rule_ids。
                assessed_rule_ids = list(dict.fromkeys(
                    assessed_rule_ids + [risk["rule_id"] for risk in deduplicated]
                ))
                return deduplicated, valid_passes, assessed_rule_ids
            except Exception as exc:
                last_error = exc
                print(
                    f"LLM批量解析失败（第 {attempt + 1} 次）: {exc}; "
                    f"response={response[:200] if response else 'empty'}",
                    flush=True,
                )

        raise RuntimeError(f"AI语义审核返回格式异常，重试后仍无法解析: {last_error}")


# 单例
audit_engine = AuditEngine()
