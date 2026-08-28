import json
import unittest
from unittest.mock import patch

from app.services.tender_review_service import (
    _llm_review,
    _parse_json_payload,
    _scan,
)


class TenderReviewServiceTest(unittest.TestCase):
    def test_parse_fenced_json_and_prefixed_location(self):
        payload = _parse_json_payload('```json\n{"source_line":"L88"}\n```')
        self.assertEqual(payload["source_line"], "L88")

    def test_procurement_requirement_keeps_semantic_requirement(self):
        lines = [
            {"line": 1, "page": 1, "text": "智能标书智能体需求说明书"},
            {"line": 2, "page": 1, "text": "系统应自动识别废标红线、否决项和加分项。"},
        ]
        keyword_items = _scan(lines)
        model_response = json.dumps({
            "document_type": "procurement_requirement",
            "document_type_reason": "这是软件功能需求说明书",
            "findings": [{
                "category": "technical_requirements",
                "title": "招标条款智能识别",
                "requirement": lines[1]["text"],
                "evidence_quote": lines[1]["text"],
                "source_page": 1,
                "source_line": "L2",
                "importance": "required",
                "action": "复核",
            }],
        }, ensure_ascii=False)
        with patch("app.services.tender_review_service.llm_client.chat", return_value=model_response):
            result = _llm_review(lines, keyword_items)
        self.assertEqual(result["document_type"], "procurement_requirement")
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["category"], "technical_requirements")

    def test_tender_finding_is_kept_only_with_verifiable_evidence(self):
        lines = [{"line": 1, "page": 1, "text": "投标文件递交截止时间为2026年9月1日10时。"}]
        response = json.dumps({
            "document_type": "tender",
            "document_type_reason": "包含投标人递交要求",
            "findings": [{
                "category": "timeline",
                "title": "投标截止时间",
                "requirement": "须按时递交",
                "evidence_quote": lines[0]["text"],
                "source_page": "P1",
                "source_line": "L1",
                "importance": "required",
                "action": "纳入投标日程",
            }],
        }, ensure_ascii=False)
        with patch("app.services.tender_review_service.llm_client.chat", return_value=response):
            result = _llm_review(lines, _scan(lines))
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["source"], "llm")

if __name__ == "__main__":
    unittest.main()
