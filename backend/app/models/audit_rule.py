# -*- coding: utf-8 -*-
"""
审核点配置相关 SQLAlchemy 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class AuditRule(Base):
    """审核点配置模型"""
    __tablename__ = "audit_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)  # 配置名称
    description = Column(Text, nullable=True)  # 配置描述
    rule_type = Column(String(50), nullable=False)  # keyword/regex/format/blacklist/llm_risk/llm_compliance/llm_completeness
    enabled = Column(Boolean, nullable=False, default=True)  # 是否启用
    params = Column(JSON, nullable=True)  # 规则参数（关键词列表、正则表达式等）
    severity = Column(String(20), nullable=False, default="medium")  # high/medium/low
    is_global = Column(Boolean, nullable=False, default=False)  # 是否全局配置
    created_by = Column(String(50), nullable=False)  # 创建者
    is_deleted = Column(Integer, nullable=False, default=0)  # 软删除标记
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditRuleVersion(Base):
    """审核点配置版本历史模型"""
    __tablename__ = "audit_rule_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(36), nullable=False)  # 关联的配置ID
    version = Column(Integer, nullable=False)  # 版本号
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)
    params = Column(JSON, nullable=True)
    severity = Column(String(20), nullable=False)
    change_type = Column(String(20), nullable=False)  # create/update/delete
    changed_by = Column(String(50), nullable=False)  # 修改人
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# 默认审核点配置（金融领域合同审核）
DEFAULT_AUDIT_RULES = [
    # ========== 格式校验类规则 ==========
    {
        "name": "日期格式校验",
        "description": "校验合同日期格式是否符合 YYYY年MM月DD日 规范",
        "rule_type": "regex",
        "params": {"pattern": r"\d{4}年\d{1,2}月\d{1,2}日"},
        "severity": "low",
        "is_global": True,
    },
    {
        "name": "金额格式校验",
        "description": "校验金额数字格式正确（如：100万元、50.00万元）",
        "rule_type": "regex",
        "params": {"pattern": r"\d+(?:\.\d{1,2})?\s*(?:万|亿)?元"},
        "severity": "low",
        "is_global": True,
    },
    {
        "name": "合同编号格式校验",
        "description": "校验合同编号格式（银行标准格式）",
        "rule_type": "regex",
        "params": {"pattern": r"[A-Z]{2,}\d{4,}[A-Z0-9]*"},
        "severity": "low",
        "is_global": True,
    },

    # ========== 关键词检测类规则 ==========
    {
        "name": "利率超标风险检测",
        "description": "检测合同中利率相关条款是否存在超高利率风险",
        "rule_type": "keyword",
        "params": {"keywords": ["年利率", "日利率", "月利率", "综合利率", "利率上限", "超过"]},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "担保资质缺失检测",
        "description": "检测担保类合同是否包含必要的担保人资质条款",
        "rule_type": "keyword",
        "params": {"keywords": ["抵押", "质押", "保证担保", "连带责任", "抵押物", "担保人"]},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "提前还款违约金检测",
        "description": "检测是否存在提前还款违约金/补偿金条款",
        "rule_type": "keyword",
        "params": {"keywords": ["提前还款", "提前清偿", "违约金", "补偿金", "手续费"]},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "逾期利率过高检测",
        "description": "检测逾期利率/罚息/滞纳金相关条款",
        "rule_type": "keyword",
        "params": {"keywords": ["逾期利率", "罚息", "滞纳金", "逾期罚则", "逾期催收"]},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "保密条款完整性检测",
        "description": "检测合同是否包含保密条款",
        "rule_type": "keyword",
        "params": {"keywords": ["保密", "机密", "不得泄露", "信息披露", "商业秘密"]},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "争议解决条款检测",
        "description": "检测合同是否约定争议解决方式（仲裁或法院）",
        "rule_type": "keyword",
        "params": {"keywords": ["仲裁", "管辖法院", "诉讼", "争议解决", "所在地"]},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "合同生效条件检测",
        "description": "检测合同是否明确生效条件",
        "rule_type": "keyword",
        "params": {"keywords": ["本合同自", "生效", "签署", "盖章", "之日起", "签订"]},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "贷款用途限制检测",
        "description": "检测贷款类合同是否明确约定贷款用途",
        "rule_type": "keyword",
        "params": {"keywords": ["贷款用途", "资金用途", "限于", "专项使用", "不得用于"]},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "贷后管理条款检测",
        "description": "检测信贷合同是否包含贷后管理条款",
        "rule_type": "keyword",
        "params": {"keywords": ["贷后管理", "资金监控", "用途检查", "回访", "检查"]},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "主体资格条款检测",
        "description": "检测合同各方主体资格是否明确",
        "rule_type": "keyword",
        "params": {"keywords": ["营业执照", "法人代表", "授权代表", "有效证件"]},
        "severity": "medium",
        "is_global": True,
    },

    # ========== 黑名单类规则 ==========
    {
        "name": "敏感条款黑名单",
        "description": "检测是否存在监管明确禁止的不公平条款",
        "rule_type": "blacklist",
        "params": {"patterns": ["终身追偿", "裸贷", "暴力催收", "强制公证", "砍头息"]},
        "severity": "high",
        "is_global": True,
    },

    # ========== LLM 风险识别类规则 ==========
    {
        "name": "霸王条款识别",
        "description": "识别合同中可能存在的霸王条款（明显不利于借款人的条款）",
        "rule_type": "llm_risk",
        "params": {"prompt": "请识别合同中是否存在霸王条款，如：1)单方随时解除权 2)不对等违约责任 3)强制公证 4)不利于借款人的解释权条款 5)单方面变更合同条款权利。请以JSON格式返回发现的霸王条款。"},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "贷款综合费率评估",
        "description": "评估贷款合同综合费率是否超过法定上限（不超过年化36%）",
        "rule_type": "llm_risk",
        "params": {"prompt": "请识别合同中所有与费用相关的条款（利率、服务费、管理费、咨询费、担保费等），计算综合年化费率，判断是否超过36%法定上限。如超过请明确指出超标金额和比例。"},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "签章一致性审核",
        "description": "审核合同签章与合同双方名称是否一致",
        "rule_type": "llm_risk",
        "params": {"prompt": "请核对合同中的签章/盖章信息与合同双方（甲方、乙方）名称是否一致，如发现不一致请指出具体位置。"},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "担保物评估合规性",
        "description": "检查抵押/质押合同中担保物评估是否符合监管要求",
        "rule_type": "llm_risk",
        "params": {"prompt": "请检查抵押/质押合同中：1)担保物是否明确 2)评估价值是否合理 3)是否需要第三方评估 4)担保物保险是否约定。如有违规请指出。"},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "电子合同有效性评估",
        "description": "评估电子合同是否符合电子签名法要求",
        "rule_type": "llm_risk",
        "params": {"prompt": "请检查电子合同是否满足：1)有可靠的电子签名 2)合同内容完整未被篡改 3)签署时间有效。如有不满足请指出。"},
        "severity": "medium",
        "is_global": True,
    },

    # ========== LLM 合规检查类规则 ==========
    {
        "name": "监管政策合规检查",
        "description": "检查合同是否符合银保监会相关监管规定",
        "rule_type": "llm_compliance",
        "params": {"prompt": "请根据《商业银行贷款暂行办法》《个人贷款管理暂行办法》《网络借贷信息中介机构业务活动管理暂行办法》等监管规定，检查合同是否存在违反监管要求的内容，如有不符请详细说明违反的具体条款和监管规定。"},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "格式合同规范性检查",
        "description": "检查是否为格式合同，以及格式合同的合规性",
        "rule_type": "llm_compliance",
        "params": {"prompt": "请检查：1)是否为银行提供的格式合同 2)格式合同中是否有不合理地免除银行责任、加重借款人责任的内容 3)是否对重大权益条款进行了提示和说明 4)是否有合理的退出机制。"},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "利率约定合规性检查",
        "description": "检查贷款利率约定是否符合LPR利率管理规定",
        "rule_type": "llm_compliance",
        "params": {"prompt": "请检查合同中利率约定：1)是否明确标注为年化利率 2)逾期利率是否超过LPR的4倍 3)是否存在隐藏费用导致实际利率超标 4)利率变更条款是否合规。"},
        "severity": "high",
        "is_global": True,
    },

    # ========== LLM 完整性检查类规则 ==========
    {
        "name": "必要条款完整性检查",
        "description": "检查贷款合同必要条款是否完整",
        "rule_type": "llm_completeness",
        "params": {"prompt": "请检查贷款合同是否包含以下必要条款：1)当事人信息（姓名/名称、证件号、地址）2)贷款金额（大写和小写）3)贷款期限 4)利率及还款方式 5)担保条款 6)违约责任 7)争议解决条款 8)签署日期。如有缺失请列出缺失的条款。"},
        "severity": "high",
        "is_global": True,
    },
    {
        "name": "合同条款前后一致性检查",
        "description": "检查合同正文中关键条款前后是否一致",
        "rule_type": "llm_completeness",
        "params": {"prompt": "请检查合同正文中以下内容前后是否一致：1)贷款金额大小写是否一致 2)还款计划与合同条款是否一致 3)各方名称在全文中是否一致 4)日期是否有矛盾 5)账号信息是否一致。如有不一致请指出具体位置。"},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "合同页码完整性检查",
        "description": "检查合同是否存在缺页、跳页等问题",
        "rule_type": "llm_completeness",
        "params": {"prompt": "请通过分析合同条款的逻辑连贯性，判断合同是否存在缺页、漏页、条款不完整、附件缺失等问题。如果发现逻辑断裂或内容跳跃请指出。"},
        "severity": "medium",
        "is_global": True,
    },
    {
        "name": "授权文件完整性检查",
        "description": "检查合同所需的授权委托文件是否完整",
        "rule_type": "llm_completeness",
        "params": {"prompt": "请检查涉及代理签署的合同是否附有完整的授权委托书，包括：授权人信息、被授权人信息、授权范围、授权期限、授权人签章等。如有缺失请指出。"},
        "severity": "medium",
        "is_global": True,
    },
]
