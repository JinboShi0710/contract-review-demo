# -*- coding: utf-8 -*-
"""
规则引擎
支持关键词匹配、正则匹配、格式校验、黑名单匹配
"""
import re
from typing import List, Dict, Any, Optional


class RuleMatchResult:
    """规则匹配结果"""
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        rule_type: str,
        severity: str,
        matched: bool,
        details: Optional[str] = None,
        matched_items: Optional[List[str]] = None
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.severity = severity
        self.matched = matched
        self.details = details
        self.matched_items = matched_items or []

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_type": self.rule_type,
            "severity": self.severity,
            "matched": self.matched,
            "details": self.details,
            "matched_items": self.matched_items,
        }


class RuleEngine:
    """规则引擎"""

    def __init__(self, rules: List[Dict]):
        """
        初始化规则引擎

        Args:
            rules: 审核点配置列表
        """
        self.rules = [r for r in rules if r.get("enabled", True)]
        self.keyword_rules = [r for r in self.rules if r["rule_type"] == "keyword"]
        self.regex_rules = [r for r in self.rules if r["rule_type"] == "regex"]
        self.format_rules = [r for r in self.rules if r["rule_type"] == "format"]
        self.blacklist_rules = [r for r in self.rules if r["rule_type"] == "blacklist"]

    def execute_all(self, text: str) -> List[RuleMatchResult]:
        """
        执行所有规则

        Args:
            text: 待检测文本

        Returns:
            匹配结果列表
        """
        results = []

        # 并行执行各类规则
        results.extend(self._execute_keyword_rules(text))
        results.extend(self._execute_regex_rules(text))
        results.extend(self._execute_format_rules(text))
        results.extend(self._execute_blacklist_rules(text))

        return results

    def execute_keyword_rules(self, text: str) -> List[RuleMatchResult]:
        """只执行关键词规则"""
        return self._execute_keyword_rules(text)

    def execute_llm_rules(self) -> List[Dict]:
        """返回需要LLM处理的规则配置（供上层调用）"""
        return [
            {
                "rule_id": r["id"],
                "rule_name": r["name"],
                "rule_type": r["rule_type"],
                "severity": r["severity"],
                "params": r.get("params", {}),
            }
            for r in self.rules
            if r["rule_type"] in ("llm_risk", "llm_compliance", "llm_completeness")
        ]

    def _execute_keyword_rules(self, text: str) -> List[RuleMatchResult]:
        """执行关键词规则"""
        results = []
        required_presence_rules = {
            "保密条款完整性检测",
            "争议解决条款检测",
            "合同生效条件检测",
            "主体资格条款检测",
        }
        for rule in self.keyword_rules:
            params = rule.get("params", {})
            keywords = params.get("keywords", [])
            matched_keywords = [kw for kw in keywords if kw in text]

            presence_required = (
                params.get("match_mode") == "required"
                or rule["name"] in required_presence_rules
            )
            is_risk = not matched_keywords if presence_required else bool(matched_keywords)
            if presence_required:
                details = (
                    f"已发现必要内容关键词: {', '.join(matched_keywords[:5])}"
                    if matched_keywords else "未发现该必要条款的明确表述"
                )
            else:
                details = f"命中 {len(matched_keywords)} 个风险关键词" if matched_keywords else None

            results.append(RuleMatchResult(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["rule_type"],
                severity=rule["severity"],
                matched=is_risk,
                details=details,
                matched_items=matched_keywords,
            ))

        return results

    def _execute_regex_rules(self, text: str) -> List[RuleMatchResult]:
        """执行正则规则"""
        results = []
        # PDF提取常在日期和金额中插入空格，金额还可能带千分位。
        # 校验前做等价归一化，避免把“500,000.00 元”误判为没有金额。
        search_text = re.sub(r"[\s,，]", "", text)
        for rule in self.regex_rules:
            params = rule.get("params", {})
            pattern = params.get("pattern", "")

            try:
                regex = re.compile(pattern)
                matches = regex.findall(search_text)

                forbidden = params.get("match_mode") == "forbidden"
                is_risk = bool(matches) if forbidden else not bool(matches)
                details = (
                    f"发现 {len(matches)} 处禁止格式" if forbidden and matches
                    else "未发现符合要求的格式" if not forbidden and not matches
                    else f"格式校验通过，匹配 {len(matches)} 处"
                )
                results.append(RuleMatchResult(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_type=rule["rule_type"],
                    severity=rule["severity"],
                    matched=is_risk,
                    details=details,
                    matched_items=matches[:10],  # 最多返回10个
                ))
            except re.error as e:
                results.append(RuleMatchResult(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_type=rule["rule_type"],
                    severity=rule["severity"],
                    matched=False,
                    details=f"正则表达式错误: {str(e)}",
                ))

        return results

    def _execute_format_rules(self, text: str) -> List[RuleMatchResult]:
        """执行独立的格式规则，不能重复执行 regex 规则。"""
        results = []
        search_text = re.sub(r"[\s,，]", "", text)
        for rule in self.format_rules:
            params = rule.get("params", {})
            pattern = params.get("pattern", "")
            try:
                matches = re.findall(pattern, search_text)
                # 常见合同金额既可能写作“500,000.00”，也可能写作
                # “人民币伍拾万元整”。配置中的窄正则不应把这两种合法写法误报。
                if rule.get("name") == "金额格式校验" and not matches:
                    amount_patterns = (
                        r"[¥￥]\d+(?:\.\d{1,2})?",
                        r"人民币[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元角分整]+",
                    )
                    matches = [
                        match.group(0)
                        for amount_pattern in amount_patterns
                        for match in re.finditer(amount_pattern, search_text)
                    ]
                forbidden = params.get("match_mode") == "forbidden"
                is_risk = bool(matches) if forbidden else not bool(matches)
                results.append(RuleMatchResult(
                    rule_id=rule["id"],
                    rule_name=rule["name"],
                    rule_type=rule["rule_type"],
                    severity=rule["severity"],
                    matched=is_risk,
                    details=("发现禁止格式" if forbidden and matches else
                             "未发现符合要求的格式" if is_risk else "格式校验通过"),
                    matched_items=matches[:10],
                ))
            except re.error as exc:
                results.append(RuleMatchResult(
                    rule_id=rule["id"], rule_name=rule["name"],
                    rule_type=rule["rule_type"], severity=rule["severity"],
                    matched=False, details=f"正则表达式错误: {exc}",
                ))
        return results

    def _execute_blacklist_rules(self, text: str) -> List[RuleMatchResult]:
        """执行黑名单规则"""
        results = []
        for rule in self.blacklist_rules:
            params = rule.get("params", {})
            blacklist = params.get("blacklist") or params.get("patterns", [])

            matched_items = [item for item in blacklist if item in text]

            results.append(RuleMatchResult(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["rule_type"],
                severity=rule["severity"],
                matched=len(matched_items) > 0,
                details=f"命中 {len(matched_items)} 个黑名单项" if matched_items else None,
                matched_items=matched_items,
            ))

        return results


# 单例缓存（避免每次审核都重新加载规则）
_cached_engine: Optional[RuleEngine] = None
_cached_rules_hash: Optional[str] = None


def get_rule_engine(rules: List[Dict]) -> RuleEngine:
    """获取规则引擎实例（带缓存）"""
    global _cached_engine, _cached_rules_hash
    rules_hash = str(hash(frozenset(r["id"] for r in rules)))

    if _cached_engine is None or _cached_rules_hash != rules_hash:
        _cached_engine = RuleEngine(rules)
        _cached_rules_hash = rules_hash

    return _cached_engine
