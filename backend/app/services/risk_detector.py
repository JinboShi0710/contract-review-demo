# -*- coding: utf-8 -*-
"""
合同风险检测服务
"""
from typing import List, Dict, Any
from app.core.config import settings
from app.utils.ocr.engine import ocr_engine


class RiskDetector:
    """合同风险检测器"""

    def __init__(self):
        self.ocr = ocr_engine
        self.risk_keywords = settings.RISK_KEYWORDS

    def detect(self, file_path: str) -> List[Dict[str, Any]]:
        """
        检测合同中的风险条款

        Args:
            file_path: 文件路径

        Returns:
            风险列表
        """
        # OCR 识别
        ocr_results, _, _ = self.ocr.recognize(file_path)

        if not ocr_results:
            return []

        # 基于关键词的风险检测
        risks = self._detect_by_keywords(ocr_results)

        return risks

    def _detect_by_keywords(
        self, ocr_results: List[dict]
    ) -> List[Dict[str, Any]]:
        """
        基于关键词的风险检测

        Args:
            ocr_results: OCR 识别结果

        Returns:
            风险列表
        """
        risks = []

        for item in ocr_results:
            text = item["text"]
            bbox = item["bbox"]

            for keyword in self.risk_keywords:
                if keyword in text:
                    # 确定风险等级
                    risk_level = self._assess_risk_level(keyword, text)

                    risks.append({
                        "risk_type": self._get_risk_type(keyword),
                        "risk_level": risk_level,
                        "location": self._bbox_to_location(bbox),
                        "description": f"检测到风险关键词：{keyword}",
                        "matched_text": text,
                    })

        return risks

    def _assess_risk_level(self, keyword: str, context: str) -> str:
        """
        评估风险等级

        Args:
            keyword: 匹配的关键词
            context: 上下文文本

        Returns:
            high/medium/low
        """
        # 高风险关键词
        high_risk = ["免责条款", "免责声明", "不承担", "不负责", "损失赔偿"]
        if keyword in high_risk:
            # 检查是否有"不"字加强语气
            if "不" in context:
                return "high"
            return "medium"

        # 中风险关键词
        medium_risk = ["违约金过高"]
        if keyword in medium_risk:
            return "medium"

        return "low"

    def _get_risk_type(self, keyword: str) -> str:
        """
        获取风险类型

        Args:
            keyword: 关键词

        Returns:
            风险类型
        """
        type_mapping = {
            "免责声明": "disclaimer",
            "免责条款": "disclaimer",
            "不承担": "disclaimer",
            "不负责": "disclaimer",
            "损失赔偿": "liability",
            "违约金过高": "high_penalty",
        }
        return type_mapping.get(keyword, "other")

    def _bbox_to_location(self, bbox: List[List[float]]) -> Dict[str, Any]:
        """
        将边界框转换为位置信息

        Args:
            bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            {x, y, width, height}
        """
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]

        x1, y1 = min(xs), min(ys)
        x2, y2 = max(xs), max(ys)

        return {
            "x": int(x1),
            "y": int(y1),
            "width": int(x2 - x1),
            "height": int(y2 - y1),
        }


# 单例
risk_detector = RiskDetector()
