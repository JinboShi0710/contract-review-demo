# -*- coding: utf-8 -*-
"""
DeepSeek LLM 客户端封装
"""
import time
from typing import Optional, List, Dict, Any
from openai import OpenAI, Timeout
from app.core.config import settings


class LLMClient:
    """DeepSeek LLM 客户端封装"""

    _instance: Optional["LLMClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        if not settings.LLM_API_KEY:
            print("警告：未配置 LLM_API_KEY，LLM 功能将不可用")
            self._client = None
        else:
            self._client = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                timeout=settings.LLM_TIMEOUT,
                max_retries=0,
            )

        self._initialized = True

    def reconfigure(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
    ) -> None:
        """运行时重新加载 LLM 配置，无需重启后端。"""
        settings.LLM_API_KEY = api_key
        settings.LLM_BASE_URL = base_url
        settings.LLM_MODEL = model
        settings.LLM_TIMEOUT = timeout
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=0,
        ) if api_key else None

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> str:
        """
        发送对话请求

        Args:
            messages: [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的模型

        Returns:
            assistant 的回复内容
        """
        if not self._client:
            raise RuntimeError("LLM 客户端未初始化，请配置 LLM_API_KEY")

        model = model or settings.LLM_MODEL

        start_time = time.time()
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,  # 低温度，更确定性
        )
        elapsed = time.time() - start_time

        print(f"LLM 调用完成，耗时 {elapsed:.2f}s")

        content = response.choices[0].message.content
        if not content or not content.strip():
            raise RuntimeError("LLM 返回了空内容")
        return content

    def extract_contract_elements(self, contract_text: str) -> Dict[str, Any]:
        """
        从合同文本中提取关键要素

        Args:
            contract_text: 合同全文（OCR 识别结果拼接）

        Returns:
            要素字典
        """
        prompt = f"""你是一个专业的合同审核助手。请从以下合同文本中提取关键要素，返回 JSON 格式：

要素类型：
- party_a: 甲方名称
- party_b: 乙方名称
- amount: 合同金额
- signing_date: 签约时间
- contract_no: 合同编号
- payment_method: 付款方式
- payment_cycle: 付款周期
- subject_matter: 交易标的
- validity_period: 有效期
- contract_type: 合同类型（借款合同/担保合同/购销合同/租赁合同/咨询服务合同/其他）
- document_category: 文档类别（合同/协议/会议纪要/通知/报告/其他）
- is_contract: 是否属于合同或协议（true/false）
- document_type_reason: 判断文档类别的简短理由

请直接返回 JSON，不要包含其他内容：
{{
  "party_a": "...",
  "party_b": "...",
  "amount": "...",
  "signing_date": "...",
  "contract_no": "...",
  "payment_method": "...",
  "payment_cycle": "...",
  "subject_matter": "...",
  "validity_period": "...",
  "contract_type": "购销合同",
  "document_category": "合同",
  "is_contract": true,
  "document_type_reason": "存在甲乙双方、交易标的、价款和权利义务条款"
}}

合同文本：
{contract_text[:20000]}"""

        try:
            response = self.chat([
                {"role": "user", "content": prompt}
            ])

            # 简单解析 JSON
            import json
            import re

            # 尝试提取 JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except Exception as e:
            print(f"LLM 要素提取失败: {e}")
            return {}

    def detect_risks(self, contract_text: str) -> List[Dict[str, Any]]:
        """
        检测合同中的风险条款

        Args:
            contract_text: 合同全文

        Returns:
            风险列表
        """
        prompt = f"""你是一个专业的合同审核助手。请检测以下合同中的风险条款，返回 JSON 数组格式：

风险类型（使用中文）：
- 免责声明
- 违约金过高
- 缺失条款
- 责任不明确
- 签章问题
- 缺页漏页

风险等级：高/中/低

请返回 JSON 数组格式，每个风险包含：
- risk_type: 风险类型（中文）
- risk_level: 高/中/低
- description: 风险描述
- location_hint: 位置提示（在合同中的位置）

请直接返回 JSON，不要包含其他内容：
[
  {{
    "risk_type": "免责声明",
    "risk_level": "高",
    "description": "发现免责条款...",
    "location_hint": "第X条"
  }}
]

合同文本：
{contract_text[:20000]}"""

        try:
            response = self.chat([
                {"role": "user", "content": prompt}
            ])

            import json
            import re

            # 尝试提取 JSON 数组
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []
        except Exception as e:
            print(f"LLM 风险检测失败: {e}")
            return []

    def identify_contract_type(self, contract_text: str) -> str:
        """
        识别合同类型

        Args:
            contract_text: 合同全文

        Returns:
            合同类型：借款合同/担保合同/购销合同/其他
        """
        prompt = f"""你是一个专业的合同审核助手。请判断以下合同的类型，返回一个词语：

合同类型选项：
- 借款合同
- 担保合同
- 购销合同
- 租赁合同
- 咨询服务合同
- 其他

请直接返回一个词语，不要包含其他内容。

合同文本：
{contract_text[:1500]}"""

        try:
            response = self.chat([
                {"role": "user", "content": prompt}
            ])

            # 提取第一个匹配的类型
            import re
            types = ["借款合同", "担保合同", "购销合同", "租赁合同", "咨询服务合同", "其他"]
            for t in types:
                if t in response:
                    return t
            return "其他"
        except Exception as e:
            print(f"LLM 合同类型识别失败: {e}")
            return "其他"


# 单例
llm_client = LLMClient()
