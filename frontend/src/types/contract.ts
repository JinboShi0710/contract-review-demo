// -*- coding: utf-8 -*-
/**
 * 合同相关 TypeScript 类型定义
 */

// 统一响应格式
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 分页数据
export interface PageData<T = any> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 合同要素
export interface ContractElement {
  id: string;
  element_type: ElementType;
  element_value: string;
  location?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence?: number | null;
}

// 要素类型
export type ElementType =
  | "party_a"   // 甲方
  | "party_b"   // 乙方
  | "amount"     // 合同金额
  | "signing_date"  // 签约时间
  | "contract_no"   // 合同编号
  | "payment_method"  // 付款方式
  | "payment_cycle"  // 付款周期
  | "subject_matter" // 交易标的
  | "validity_period"  // 有效期
  | "signature_text"; // 签章文字

// 合同风险
export interface ContractRisk {
  id: string;
  risk_type: RiskType;  // 风险类型/规则名称
  risk_level: RiskLevel;
  location: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  description?: string;
  // 扩展字段：完整规则执行信息
  rule_id?: string;       // 关联规则ID
  rule_name?: string;     // 规则名称
  rule_type?: string;     // keyword/regex/llm_risk等
  rule_params?: Record<string, any>;  // 规则参数
  matched?: number;       // 0=无法确定 1=有证据通过 2=风险
  matched_items?: string[];  // 命中内容列表
  execution_result?: string;  // LLM分析结果或执行说明
}

// 规则执行结果（用于前端分组展示）
export interface RuleExecutionResult {
  rule_id: string;
  rule_name: string;
  rule_type: string;  // regex/keyword/blacklist/llm_risk/llm_compliance/llm_completeness
  severity: string;  // high/medium/low
  matched: number;   // 0=未执行 1=通过 2=风险
  description?: string;
  rule_params?: Record<string, any>;
  matched_items?: string[];
  execution_result?: string;
}

// 规则分组概览
export interface RuleGroupOverview {
  rule_type: string;
  rule_type_label: string;
  total: number;
  passed: number;
  risk: number;
  uncertain: number;
  rules: RuleExecutionResult[];
}

// 风险类型（兼容规则引擎和LLM返回的类型）
export type RiskType =
  // 规则引擎类型
  | "keyword"         // 关键词规则
  | "regex"          // 正则规则
  | "format"         // 格式规则
  | "blacklist"      // 黑名单规则
  // LLM规则类型
  | "llm_risk"       // LLM风险检测
  | "llm_compliance"  // LLM合规检查
  | "llm_completeness" // LLM完整性检查
  // 旧版兼容
  | "disclaimer"      // 免责声明
  | "high_penalty"    // 违约金过高
  | "missing_clause"  // 缺失条款
  | "missing_page"    // 缺页漏页
  | "signature_issue" // 签章问题
  | "liability"      // 责任不明确
  | "rate_exceed"     // 利率超标
  | "guarantee"       // 担保条款
  | "early_repay"     // 提前还款
  | "overdue_rate"    // 逾期利率
  | "confidentiality"  // 保密条款
  | "dispute"         // 争议解决
  | "effective"       // 生效条件
  | "loan_usage"      // 贷款用途
  | "post_loan"       // 贷后管理
  | "subject"          // 主体资格
  | "sensitive"       // 敏感条款
  | "unfair_clause"    // 霸王条款
  | "comprehensive_fee" // 综合费率
  | "signature_match"  // 签章一致
  | "guarantee_eval"   // 担保评估
  | "electronic"       // 电子合同
  | "regulatory"       // 监管合规
  | "format_contract"  // 格式合同
  | "rate_compliance"  // 利率合规
  | "necessary_clause" // 必要条款
  | "consistency"      // 前后一致
  | "page_integrity"   // 页码完整
  | "authorization"    // 授权完整
  // 中文类型名（LLM返回）
  | "免责声明"
  | "违约金过高"
  | "缺失条款"
  | "缺页漏页"
  | "签章问题"
  | "责任不明确"
  | "利率超标"
  | "担保条款"
  | "提前还款"
  | "逾期利率"
  | "保密条款"
  | "争议解决"
  | "生效条件"
  | "贷款用途"
  | "贷后管理"
  | "主体资格"
  | "敏感条款"
  | "霸王条款"
  | "综合费率"
  | "签章一致"
  | "担保评估"
  | "电子合同"
  | "监管合规"
  | "格式合同"
  | "利率合规"
  | "必要条款"
  | "前后一致"
  | "页码完整"
  | "授权完整"
  | string; // 允许任意字符串（动态风险类型）

// 风险等级
export type RiskLevel = "high" | "medium" | "low" | "高" | "中" | "低";

// 合同状态
export type ContractStatus = "created" | "processing" | "completed" | "failed";

// 合同详情
export interface Contract {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  page_count?: number;
  status: ContractStatus;
  contract_type?: string;
  confidence?: number | null;
  elements: ContractElement[];
  risks: ContractRisk[];
  created_at: string;
}

// 合同列表项
export interface ContractListItem {
  id: string;
  file_name: string;
  file_type: string;
  status: ContractStatus;
  contract_type?: string;
  confidence?: number | null;
  created_at: string;
}

// 上传响应
export interface UploadResponse {
  contract_id: string;
  status: string;
  file_name: string;
}

// 处理响应
export interface ProcessResponse {
  status: string;
  contract_id: string;
  confidence: number | null;
  elements_count: number;
  risks_count: number;
}

// 报告响应
export interface ReportResponse {
  report_id: string;
  download_url: string;
}

// 比对响应
export interface ComparisonResponse {
  comparison_id: string;
  similarity: number;
  template_pages: number;
  contract_pages: number;
  differences_count: number;
  status: string;
}

// 差异项
export interface Difference {
  type: "deleted" | "added" | "modified";
  template_text: string;
  contract_text: string;
  location: {
    page: number;
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
}

// 比对结果
export interface ComparisonResult {
  comparison_id: string;
  similarity: number;
  template_pages: number;
  contract_pages: number;
  differences: Difference[];
  summary: string;
}

// 要素类型显示映射
export const ELEMENT_TYPE_LABELS: Record<ElementType, string> = {
  party_a: "甲方",
  party_b: "乙方",
  amount: "合同金额",
  signing_date: "签约时间",
  contract_no: "合同编号",
  payment_method: "付款方式",
  payment_cycle: "付款周期",
  subject_matter: "交易标的",
  validity_period: "有效期",
  signature_text: "签章文字",
};

// 风险类型显示映射
export const RISK_TYPE_LABELS: Record<RiskType, string> = {
  // 规则引擎类型
  keyword: "关键词规则",
  regex: "正则规则",
  format: "格式规则",
  blacklist: "黑名单规则",
  // LLM规则类型
  llm_risk: "LLM风险检测",
  llm_compliance: "LLM合规检查",
  llm_completeness: "LLM完整性检查",
  // 旧版兼容
  disclaimer: "免责声明",
  high_penalty: "违约金过高",
  missing_clause: "缺失条款",
  missing_page: "缺页漏页",
  signature_issue: "签章问题",
  liability: "责任不明确",
  // 新版风险类型
  rate_exceed: "利率超标",
  guarantee: "担保条款",
  early_repay: "提前还款",
  overdue_rate: "逾期利率",
  confidentiality: "保密条款",
  dispute: "争议解决",
  effective: "生效条件",
  loan_usage: "贷款用途",
  post_loan: "贷后管理",
  subject: "主体资格",
  sensitive: "敏感条款",
  unfair_clause: "霸王条款",
  comprehensive_fee: "综合费率",
  signature_match: "签章一致",
  guarantee_eval: "担保评估",
  electronic: "电子合同",
  regulatory: "监管合规",
  format_contract: "格式合同",
  rate_compliance: "利率合规",
  necessary_clause: "必要条款",
  consistency: "前后一致",
  page_integrity: "页码完整",
  authorization: "授权完整",
  // 中文类型名（直接显示）
  "免责声明": "免责声明",
  "违约金过高": "违约金过高",
  "缺失条款": "缺失条款",
  "缺页漏页": "缺页漏页",
  "签章问题": "签章问题",
  "责任不明确": "责任不明确",
  "利率超标": "利率超标",
  "担保条款": "担保条款",
  "提前还款": "提前还款",
  "逾期利率": "逾期利率",
  "保密条款": "保密条款",
  "争议解决": "争议解决",
  "生效条件": "生效条件",
  "贷款用途": "贷款用途",
  "贷后管理": "贷后管理",
  "主体资格": "主体资格",
  "敏感条款": "敏感条款",
  "霸王条款": "霸王条款",
  "综合费率": "综合费率",
  "签章一致": "签章一致",
  "担保评估": "担保评估",
  "电子合同": "电子合同",
  "监管合规": "监管合规",
  "格式合同": "格式合同",
  "利率合规": "利率合规",
  "必要条款": "必要条款",
  "前后一致": "前后一致",
  "页码完整": "页码完整",
  "授权完整": "授权完整",
};

// 风险等级显示映射
export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  high: "高",
  medium: "中",
  low: "低",
  "高": "高",
  "中": "中",
  "低": "低",
};

// 风险等级颜色映射
export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  high: "red",
  medium: "orange",
  low: "yellow",
  "高": "red",
  "中": "orange",
  "低": "低",
};

// ========== 凭证分类类型 ==========

// 分类类型
export type VoucherClassificationType =
  | "ID_CARD"           // 身份证
  | "HOUSEHOLD_REGISTER" // 户口簿
  | "TEMPORARY_ID_CARD"  // 临时身份证
  | "OTHER_ID"           // 其他证件
  | "BIRTH_CERTIFICATE"  // 出生证明
  | "REGULAR_CERTIFICATE" // 普通存单
  | "LARGE_SPECIAL_CERTIFICATE"  // 大额特种存单
  | "PERSONAL_LARGE_CERTIFICATE" // 个人大额存单
  | "GOVERNMENT_BOND"    // 凭证式国债
  | "TRANSFER_CHECK"     // 转账支票
  | "DEPOSIT_SLIP"       // 进账单
  | "SPECIAL_DEBIT_VOUCHER"    // 特种转账借方凭证
  | "SPECIAL_CREDIT_VOUCHER"   // 特种转账贷方凭证
  | "OTHER_VOUCHER";     // 其他凭证

// 凭证分类响应
export interface VoucherClassificationResponse {
  classification_id: string;
  classification_type: VoucherClassificationType;
  classification_name: string;
  confidence_level: string;
}

// 凭证分类列表项
export interface VoucherClassificationListItem {
  classification_id: string;
  file_name: string;
  classification_type: VoucherClassificationType;
  classification_name: string;
  created_at: string;
}

// 凭证分类列表响应
export interface VoucherClassificationListData {
  items: VoucherClassificationListItem[];
  total: number;
  page: number;
  page_size: number;
}

// 分类类型显示映射
export const VOUCHER_CLASSIFICATION_LABELS: Record<VoucherClassificationType, string> = {
  ID_CARD: "身份证",
  HOUSEHOLD_REGISTER: "户口簿",
  TEMPORARY_ID_CARD: "临时身份证",
  OTHER_ID: "其他证件",
  BIRTH_CERTIFICATE: "出生证明",
  REGULAR_CERTIFICATE: "普通存单",
  LARGE_SPECIAL_CERTIFICATE: "大额特种存单",
  PERSONAL_LARGE_CERTIFICATE: "个人大额存单",
  GOVERNMENT_BOND: "凭证式国债",
  TRANSFER_CHECK: "转账支票",
  DEPOSIT_SLIP: "进账单",
  SPECIAL_DEBIT_VOUCHER: "特种转账借方凭证",
  SPECIAL_CREDIT_VOUCHER: "特种转账贷方凭证",
  OTHER_VOUCHER: "其他凭证",
};

// ========== 凭证要素类型 ==========

// 凭证要素项（动态类型，不约束）
export interface VoucherElementItem {
  label: string;  // 要素名称（自动识别）
  value: string;  // 要素值
}

// 凭证要素响应
export interface VoucherElementResponse {
  voucher_id: string;
  file_name: string;
  elements: VoucherElementItem[];
}

// 凭证处理响应（合并分类+要素）
export interface VoucherProcessResponse {
  voucher_id: string;
  file_name: string;
  classification_type: string;
  classification_name: string;
  elements: VoucherElementItem[];
}
