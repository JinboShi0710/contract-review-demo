// -*- coding: utf-8 -*-
/**
 * API 调用服务
 */
import type {
  ApiResponse,
  PageData,
  Contract,
  ContractListItem,
  UploadResponse,
  ProcessResponse,
  ComparisonResponse,
  ComparisonResult,
} from "../types/contract";
import { getToken } from "../lib/auth";
import type { TenderListResponse, TenderTask, TenderUploadResponse } from "../types/tender";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8006";

/**
 * 通用请求封装
 */
async function request<T>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const token = getToken();
    const headers = new Headers(options.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    const data = await response.json();
    return data as ApiResponse<T>;
  } catch (error) {
    return {
      code: -1,
      message: error instanceof Error ? error.message : "网络异常，请重试",
      data: null as T,
    };
  }
}

/**
 * 上传合同文件
 */
export async function uploadContract(
  file: File
): Promise<ApiResponse<UploadResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/api/v1/contracts/upload", {
    method: "POST",
    body: formData,
  });
}

/**
 * 处理合同（OCR + 要素提取 + 风险检测）
 */
export async function processContract(
  contractId: string
): Promise<ApiResponse<ProcessResponse>> {
  return request<ProcessResponse>(`/api/v1/contracts/${contractId}/process`, {
    method: "POST",
  });
}

/**
 * 获取合同详情
 */
export async function getContract(
  contractId: string
): Promise<ApiResponse<Contract>> {
  return request<Contract>(`/api/v1/contracts/${contractId}`);
}

/**
 * 获取合同列表
 */
export async function listContracts(
  page: number = 1,
  pageSize: number = 20
): Promise<ApiResponse<PageData<ContractListItem>>> {
  return request<PageData<ContractListItem>>(
    `/api/v1/contracts?page=${page}&page_size=${pageSize}`
  );
}

/**
 * 删除合同
 */
export async function deleteContract(
  contractId: string
): Promise<ApiResponse<null>> {
  return request<null>(`/api/v1/contracts/${contractId}`, {
    method: "DELETE",
  });
}

/**
 * 导出审核报告（PDF 或 Word），触发浏览器下载
 */
export async function exportReport(
  contractId: string,
  format: "pdf" | "word"
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/contracts/${contractId}/report/export?format=${format}`;
  const token = getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(url, { headers });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || "报告导出失败");
  }

  const blob = await response.blob();
  const suffix = format === "word" ? "docx" : "pdf";
  const filename = `audit_report_${contractId.slice(0, 8)}.${suffix}`;

  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

/**
 * 合同模板比对
 */
export async function compareContracts(
  templateFile: File,
  contractFile: File
): Promise<ApiResponse<ComparisonResponse>> {
  const formData = new FormData();
  formData.append("template_file", templateFile);
  formData.append("contract_file", contractFile);

  return request<ComparisonResponse>("/api/v1/contracts/compare", {
    method: "POST",
    body: formData,
  });
}

/**
 * 获取比对结果
 */
export async function getComparison(
  comparisonId: string
): Promise<ApiResponse<ComparisonResult>> {
  return request<ComparisonResult>(`/api/v1/contracts/comparisons/${comparisonId}`);
}

// ========== 招投标审核 API ==========

export async function uploadTender(file: File): Promise<ApiResponse<TenderUploadResponse>> {
  const formData = new FormData();
  formData.append("file", file);
  return request<TenderUploadResponse>("/api/v1/tenders/upload", { method: "POST", body: formData });
}

export async function processTender(taskId: string): Promise<ApiResponse<TenderTask>> {
  return request<TenderTask>(`/api/v1/tenders/${taskId}/process`, { method: "POST" });
}

export async function listTenders(): Promise<ApiResponse<TenderListResponse>> {
  return request<TenderListResponse>("/api/v1/tenders");
}

export async function getTender(taskId: string): Promise<ApiResponse<TenderTask>> {
  return request<TenderTask>(`/api/v1/tenders/${taskId}`);
}

export async function exportTender(taskId: string): Promise<void> {
  const token = getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}/api/v1/tenders/${taskId}/export`, { headers });
  if (!response.ok) throw new Error("清单导出失败");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `tender_review_${taskId.slice(0, 8)}.xlsx`;
  link.click();
  URL.revokeObjectURL(url);
}

// ========== 凭证分类 API ==========

import type {
  VoucherClassificationResponse,
  VoucherClassificationListData,
} from "../types/contract";

/**
 * 凭证分类
 */
export async function classifyVoucher(
  file: File
): Promise<ApiResponse<VoucherClassificationResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  return request<VoucherClassificationResponse>("/api/v1/vouchers/classify", {
    method: "POST",
    body: formData,
  });
}

/**
 * 获取凭证分类历史列表
 */
export async function listVoucherClassifications(
  page: number = 1,
  pageSize: number = 20
): Promise<ApiResponse<VoucherClassificationListData>> {
  return request<VoucherClassificationListData>(
    `/api/v1/vouchers/classifications?page=${page}&page_size=${pageSize}`
  );
}

// ========== 凭证要素 API ==========

import type {
  VoucherElementResponse,
  VoucherProcessResponse,
} from "../types/contract";

/**
 * 提取凭证要素
 */
export async function extractVoucherElements(
  file: File
): Promise<ApiResponse<VoucherElementResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  return request<VoucherElementResponse>("/api/v1/vouchers/elements/extract", {
    method: "POST",
    body: formData,
  });
}

/**
 * 凭证处理（分类+要素提取）
 */
export async function processVoucher(
  file: File
): Promise<ApiResponse<VoucherProcessResponse>> {
  const formData = new FormData();
  formData.append("file", file);

  return request<VoucherProcessResponse>("/api/v1/vouchers/process", {
    method: "POST",
    body: formData,
  });
}

// ========== 审核规则 API ==========

export interface AuditRuleItem {
  id: string;
  name: string;
  description?: string;
  rule_type: string;
  enabled: boolean;
  params: Record<string, any>;
  severity: string;
  is_global: boolean;
  created_by: string;
  created_at: string;
}

export interface AuditRuleListResponse {
  items: AuditRuleItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditRuleResponse {
  id: string;
  name: string;
  description?: string;
  rule_type: string;
  enabled: boolean;
  params: Record<string, any>;
  severity: string;
  is_global: boolean;
  created_by: string;
  created_at: string;
}

/**
 * 获取审核规则列表
 */
export async function listAuditRules(): Promise<ApiResponse<AuditRuleListResponse>> {
  return request<AuditRuleListResponse>("/api/v1/audit-rules");
}

/**
 * 创建审核规则
 */
export async function createAuditRule(
  name: string,
  ruleType: string,
  params: Record<string, any>,
  severity: string,
  description?: string
): Promise<ApiResponse<AuditRuleResponse>> {
  return request<AuditRuleResponse>("/api/v1/audit-rules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      rule_type: ruleType,
      params,
      severity,
      description,
    }),
  });
}

/**
 * 更新审核规则
 */
export async function updateAuditRule(
  ruleId: string,
  name?: string,
  params?: Record<string, any>,
  severity?: string,
  description?: string,
  enabled?: boolean
): Promise<ApiResponse<AuditRuleResponse>> {
  const payload: Record<string, any> = {};
  if (name !== undefined) payload.name = name;
  if (params !== undefined) payload.params = params;
  if (severity !== undefined) payload.severity = severity;
  if (description !== undefined) payload.description = description;
  if (enabled !== undefined) payload.enabled = enabled;

  return request<AuditRuleResponse>(`/api/v1/audit-rules/${ruleId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * 删除审核规则
 */
export async function deleteAuditRule(
  ruleId: string
): Promise<ApiResponse<null>> {
  return request<null>(`/api/v1/audit-rules/${ruleId}`, {
    method: "DELETE",
  });
}

/**
 * 导入默认规则
 */
export async function importDefaultRules(): Promise<ApiResponse<{ count: number }>> {
  return request<{ count: number }>("/api/v1/audit-rules/import", {
    method: "POST",
  });
}

// ========== 认证 API ==========

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: string;
  username: string;
  role: "admin" | "reviewer" | "manager";
}

/**
 * 用户登录
 */
export async function login(
  username: string,
  password: string
): Promise<ApiResponse<LoginResponse>> {
  return request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

/**
 * 获取当前用户信息
 */
export async function getMe(): Promise<ApiResponse<UserInfo>> {
  return request<UserInfo>("/api/v1/auth/me");
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<ApiResponse<null>> {
  return request<null>("/api/v1/auth/password", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

// ========== 用户管理 API ==========

export interface UserItem {
  id: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

/**
 * 创建用户（仅 admin）
 */
export async function createUser(
  username: string,
  password: string,
  role: string
): Promise<ApiResponse<UserItem>> {
  return request<UserItem>("/api/v1/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, role }),
  });
}

/**
 * 用户列表（仅 admin）
 */
export async function listUsers(): Promise<ApiResponse<UserItem[]>> {
  return request<UserItem[]>("/api/v1/users");
}

/**
 * 禁用/启用用户（仅 admin）
 */
export async function updateUser(
  userId: string,
  isActive: boolean
): Promise<ApiResponse<UserItem>> {
  return request<UserItem>(`/api/v1/users/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
}

/**
 * 获取健康状态
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    return data.status === "healthy";
  } catch {
    return false;
  }
}

// ========== 模型配置 API（仅 admin） ==========

export interface ModelSettings {
  base_url: string;
  model: string;
  timeout: number;
  api_key_configured: boolean;
}

export interface ModelSettingsPayload {
  base_url: string;
  model: string;
  timeout: number;
  api_key?: string;
}

export async function getModelSettings(): Promise<ApiResponse<ModelSettings>> {
  return request<ModelSettings>("/api/v1/model-settings");
}

export async function saveModelSettings(
  payload: ModelSettingsPayload
): Promise<ApiResponse<ModelSettings>> {
  return request<ModelSettings>("/api/v1/model-settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function testModelSettings(
  payload: ModelSettingsPayload
): Promise<ApiResponse<{ reply: string }>> {
  return request<{ reply: string }>("/api/v1/model-settings/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
