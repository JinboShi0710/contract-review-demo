# -*- coding: utf-8 -*-
"""
合同要素提取服务
"""
from typing import List, Dict, Any, Tuple, Optional
from app.utils.ocr.engine import ocr_engine


class ElementExtractor:
    """合同要素提取器"""

    def __init__(self):
        self.ocr = ocr_engine

    def extract(
        self, file_path: str
    ) -> Tuple[List[Dict[str, Any]], Optional[float]]:
        """
        从合同文档中提取要素

        Args:
            file_path: 文件路径

        Returns:
            (elements: List[Dict], avg_confidence: float)
        """
        # OCR 识别
        ocr_results, avg_confidence, _ = self.ocr.recognize(file_path)

        if not ocr_results:
            return [], avg_confidence

        # 将 OCR 结果拼接成文本
        full_text = "\n".join([item["text"] for item in ocr_results])

        # 要素提取（简单规则匹配 + LLM 增强）
        elements = self._extract_by_rules(full_text, ocr_results)

        return elements, avg_confidence

    def _extract_by_rules(
        self, full_text: str, ocr_results: List[dict]
    ) -> List[Dict[str, Any]]:
        """
        基于规则的要素提取

        Args:
            full_text: 完整文本
            ocr_results: OCR 识别结果

        Returns:
            要素列表
        """
        elements = []

        # 甲方/乙方提取
        party_a = self._find_pattern(
            full_text,
            r"甲方(?:（[^）\n]*）)?[：:]?[ \t]*(?:\n[ \t]*)?([^\n，,]+)"
        )
        if party_a:
            elements.append({
                "element_type": "party_a",
                "element_value": party_a,
                "location": self._get_location_for_text(ocr_results, party_a),
                "confidence": None,
            })

        party_b = self._find_pattern(
            full_text,
            r"乙方(?:（[^）\n]*）)?[：:]?[ \t]*(?:\n[ \t]*)?([^\n，,]+)"
        )
        if party_b:
            elements.append({
                "element_type": "party_b",
                "element_value": party_b,
                "location": self._get_location_for_text(ocr_results, party_b),
                "confidence": None,
            })

        # 合同金额提取
        amount = self._find_pattern(
            full_text,
            r"(?:合同(?:暂定)?总价|合同金额|总金额|金额)[为：:]*\s*"
            r"(人民币[^\n；;。]{1,40}|[¥￥]?\s*[0-9,，.]+\s*(?:万|亿)?元?)"
        )
        if amount:
            elements.append({
                "element_type": "amount",
                "element_value": amount,
                "location": self._get_location_for_text(ocr_results, amount),
                "confidence": None,
            })

        # 签约时间提取
        signing_date = self._find_pattern(
            full_text,
            r"签约[日期时间]*[：:]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}[日]?)"
        )
        if not signing_date:
            signing_date = self._find_pattern(
                full_text,
                r"签订[日期时间]*[：:]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}[日]?)"
            )
        if signing_date:
            elements.append({
                "element_type": "signing_date",
                "element_value": signing_date,
                "location": self._get_location_for_text(ocr_results, signing_date),
                "confidence": None,
            })

        # 合同编号提取
        contract_no = self._find_pattern(
            full_text,
            r"合同编号[：:]\s*([A-Za-z0-9\-]+)"
        )
        if contract_no:
            elements.append({
                "element_type": "contract_no",
                "element_value": contract_no,
                "location": self._get_location_for_text(ocr_results, contract_no),
                "confidence": None,
            })

        # 付款方式提取
        payment_method = self._find_pattern(
            full_text,
            r"付款方式[：:]\s*([^\n，,]+)"
        )
        if payment_method:
            elements.append({
                "element_type": "payment_method",
                "element_value": payment_method,
                "location": self._get_location_for_text(ocr_results, payment_method),
                "confidence": None,
            })

        # 付款周期提取
        payment_cycle = self._find_pattern(
            full_text,
            r"付款周期[：:]\s*([^\n，,]+)"
        )
        if payment_cycle:
            elements.append({
                "element_type": "payment_cycle",
                "element_value": payment_cycle,
                "location": self._get_location_for_text(ocr_results, payment_cycle),
                "confidence": None,
            })

        # 有效期提取
        validity = self._find_pattern(
            full_text,
            r"有效期[：:]\s*([^\n]+)"
        )
        if validity:
            elements.append({
                "element_type": "validity_period",
                "element_value": validity,
                "location": self._get_location_for_text(ocr_results, validity),
                "confidence": None,
            })

        # 签章文字提取
        signature_text = self._find_pattern(
            full_text,
            r"签章[：:]*\s*([^\n]+)"
        )
        if signature_text:
            elements.append({
                "element_type": "signature_text",
                "element_value": signature_text,
                "location": self._get_location_for_text(ocr_results, signature_text),
                "confidence": None,
            })

        return elements

    def _find_pattern(self, text: str, pattern: str) -> str:
        """查找匹配的文本"""
        import re
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        return ""

    def _get_location_for_text(
        self, ocr_results: List[dict], text: str
    ) -> Dict[str, Any]:
        """获取文本在文档中的位置"""
        for item in ocr_results:
            if text in item["text"]:
                bbox = item.get("bbox")
                if not bbox:
                    return {"page": item.get("page")}
                # 取第一个点和第三个点的坐标作为外接矩形
                x1 = min([p[0] for p in bbox])
                y1 = min([p[1] for p in bbox])
                x2 = max([p[0] for p in bbox])
                y2 = max([p[1] for p in bbox])
                return {
                    "x": int(x1),
                    "y": int(y1),
                    "width": int(x2 - x1),
                    "height": int(y2 - y1),
                }
        return {}


# 单例
element_extractor = ElementExtractor()
