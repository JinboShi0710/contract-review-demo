// -*- coding: utf-8 -*-
/**
 * 合同审核详情页
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  Typography,
  Descriptions,
  Tag,
  Table,
  Button,
  Space,
  Spin,
  message,
  Alert,
  Collapse,
  Dropdown,
} from "antd";
import type { MenuProps } from "antd";
import {
  FilePdfOutlined,
  FileImageOutlined,
  DownloadOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  FileWordOutlined,
} from "@ant-design/icons";
import { getContract, exportReport } from "../services/api";
import type { Contract, ContractStatus, ContractRisk, RuleGroupOverview } from "../types/contract";
import {
  ELEMENT_TYPE_LABELS,
} from "../types/contract";

const { Title, Text, Paragraph } = Typography;

const STATUS_COLORS: Record<ContractStatus, string> = {
  created: "default",
  processing: "processing",
  completed: "success",
  failed: "error",
};

const STATUS_LABELS: Record<ContractStatus, string> = {
  created: "待处理",
  processing: "处理中",
  completed: "已完成",
  failed: "失败",
};

// 规则类型分组标签
const RULE_TYPE_LABELS: Record<string, string> = {
  regex: "格式校验规则",
  keyword: "关键词检测规则",
  blacklist: "黑名单规则",
  document_validation: "文档有效性校验",
  llm_risk: "AIOS 增强·风险识别",
  llm_compliance: "AIOS 增强·合规检查",
  llm_completeness: "AIOS 增强·完整性检查",
};

// 规则执行状态
const MATCHED_STATUS = {
  0: { label: "无法确定", color: "warning", icon: <WarningOutlined style={{ color: "#faad14" }} /> },
  1: { label: "未发现风险", color: "success", icon: <CheckCircleOutlined style={{ color: "#52c41a" }} /> },
  2: { label: "风险", color: "error", icon: <ExclamationCircleOutlined style={{ color: "#ff4d4f" }} /> },
};

const formatLlmAnalysis = (
  raw?: string,
  params?: Record<string, any>,
): string => {
  if (!raw) return "";
  try {
    const result = JSON.parse(raw);
    const description = result.description || "本项需要进一步人工核验";
    const page = result.evidence_page || params?.evidence_page;
    const clause = result.evidence_clause || params?.evidence_clause;
    const role = result.review_role || params?.review_role || "相关业务人员";
    const location = page
      ? `相关证据位于第${page}页${clause ? `“${clause}”` : ""}`
      : "暂未能准确定位原文证据";
    return `${description}。${location}，建议由${role}复核确认。`;
  } catch {
    return raw;
  }
};

// 分组规则执行结果
const groupRisksByRuleType = (risks: ContractRisk[]): RuleGroupOverview[] => {
  const groups: Record<string, ContractRisk[]> = {};

  // 按 rule_type 分组
  risks.forEach((risk) => {
    const type = risk.rule_type || "unknown";
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(risk);
  });

  // 转换为 RuleGroupOverview 数组
  return Object.entries(groups).map(([ruleType, rules]) => {
    const passed = rules.filter((r) => r.matched === 1).length;
    const riskCount = rules.filter((r) => r.matched === 2).length;
    const uncertain = rules.filter((r) => !r.matched || r.matched === 0).length;

    return {
      rule_type: ruleType,
      rule_type_label: RULE_TYPE_LABELS[ruleType] || ruleType,
      total: rules.length,
      passed,
      risk: riskCount,
      uncertain,
      rules: rules.map((r) => ({
        rule_id: r.rule_id || "",
        rule_name: r.rule_name || r.risk_type,
        rule_type: r.rule_type || "unknown",
        severity: r.risk_level,
        matched: r.matched || 0,
        description: r.description,
        rule_params: r.rule_params,
        matched_items: r.matched_items || [],
        execution_result: r.execution_result,
      })),
    };
  }).sort((a, b) => {
    // 排序：有关风险的排在前面
    if (a.risk > 0 && b.risk === 0) return -1;
    if (a.risk === 0 && b.risk > 0) return 1;
    return 0;
  });
};

// 生成 Collapse items
const getCollapseItems = (risks: ContractRisk[]) => {
  return groupRisksByRuleType(risks).map((group) => {
    const groupPanels = group.rules.map((rule, idx) => {
      const status = MATCHED_STATUS[(rule.matched || 0) as keyof typeof MATCHED_STATUS] || MATCHED_STATUS[0];
      const severityColor = rule.severity === "high" ? "#ff4d4f" : rule.severity === "medium" ? "#fa8c16" : "#52c41a";
      return (
        <Card
          key={rule.rule_id || idx}
          size="small"
          style={{
            marginBottom: 12,
            borderLeft: `3px solid ${(rule.matched || 0) === 2 ? "#ff4d4f" : (rule.matched || 0) === 1 ? "#52c41a" : "#d9d9d9"}`,
          }}
        >
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            <Space style={{ width: "100%", justifyContent: "space-between" }}>
              <Space>
                {status.icon}
                <Text strong>{rule.rule_name}</Text>
                <Tag color={severityColor}>
                  {rule.severity === "high" ? "高风险" : rule.severity === "medium" ? "中风险" : "低风险"}
                </Tag>
              </Space>
              <Tag>{status.label}</Tag>
            </Space>
            {rule.description && (
              <Text type="secondary" style={{ fontSize: 12 }}>{rule.description}</Text>
            )}
            {rule.matched_items && rule.matched_items.length > 0 && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>命中内容：</Text>
                <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                  {rule.matched_items.slice(0, 5).map((item, i) => (
                    <li key={i}><Text code style={{ fontSize: 11 }}>{item}</Text></li>
                  ))}
                  {rule.matched_items.length > 5 && (
                    <li><Text type="secondary" style={{ fontSize: 11 }}>...还有 {rule.matched_items.length - 5} 条</Text></li>
                  )}
                </ul>
              </div>
            )}
            {rule.rule_type?.startsWith("llm_") && rule.rule_params?.audit_framework && (
              <div style={{ background: "#f6ffed", padding: 10, borderRadius: 6 }}>
                <Space direction="vertical" size={2}>
                  <Text strong style={{ fontSize: 12 }}>AIOS 证据链</Text>
                  <Text style={{ fontSize: 12 }}>
                    审查范围：{rule.rule_params.evidence_scope || (rule.rule_params.evidence_page ? `第${rule.rule_params.evidence_page}页` : "需核验")}
                    {rule.rule_params.evidence_clause ? ` · ${rule.rule_params.evidence_clause}` : ""}
                  </Text>
                  <Text style={{ fontSize: 12 }}>处理：{rule.rule_params.disposition || "需核验"}</Text>
                  <Text style={{ fontSize: 12 }}>复核岗位：{rule.rule_params.review_role || "法务/商务"}</Text>
                  <Tag color={rule.rule_params.evidence_verified ? "green" : "orange"}>
                    {rule.rule_params.evidence_verified
                      ? "原文证据已反查"
                      : rule.rule_params.assessment_completed
                        ? "未识别到通过证据，无法确定"
                        : "原文证据待核验"}
                  </Tag>
                </Space>
              </div>
            )}
            {rule.execution_result && rule.rule_type?.startsWith("llm_") && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>分析说明：</Text>
                <Paragraph style={{ marginTop: 4, marginBottom: 0 }}>
                  {formatLlmAnalysis(rule.execution_result, rule.rule_params)}
                </Paragraph>
              </div>
            )}
            {rule.rule_params && Object.keys(rule.rule_params).length > 0 && !rule.rule_type?.startsWith("llm_") && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>规则参数：</Text>
                <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                  {Object.entries(rule.rule_params).filter(([key]) => key !== "prompt").slice(0, 3).map(([key, value]) => (
                    <li key={key}><Text type="secondary" style={{ fontSize: 11 }}>{key}: {Array.isArray(value) ? value.join(", ").slice(0, 50) : String(value).slice(0, 50)}</Text></li>
                  ))}
                </ul>
              </div>
            )}
          </Space>
        </Card>
      );
    });
    return {
      key: group.rule_type,
      label: <Space><Text strong>{group.rule_type_label}</Text><Tag color={group.passed > 0 ? "green" : "default"}>{group.passed}/{group.total} 未发现风险</Tag>{group.risk > 0 && <Tag color="red">{group.risk} 风险</Tag>}{group.uncertain > 0 && <Tag color="orange">{group.uncertain} 无法确定</Tag>}</Space>,
      children: groupPanels,
    };
  });
};

const ContractReview: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchContract = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await getContract(id);
      if (res.code === 0) {
        setContract(res.data);
      } else {
        message.error(res.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContract();
  }, [id]);

  const handleExportReport = async (format: "pdf" | "word") => {
    if (!id) return;
    setGenerating(true);
    try {
      await exportReport(id, format);
      message.success(`${format.toUpperCase()} 报告导出成功`);
    } catch (e: any) {
      message.error(e.message || "报告导出失败");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!contract) {
    return (
      <div style={{ padding: 24 }}>
        <Alert message="合同不存在或已删除" type="error" showIcon />
      </div>
    );
  }

  const elementColumns = [
    {
      title: "要素类型",
      dataIndex: "element_type",
      key: "element_type",
      width: 150,
      render: (type: string) => ELEMENT_TYPE_LABELS[type as keyof typeof ELEMENT_TYPE_LABELS] || type,
    },
    {
      title: "要素值",
      dataIndex: "element_value",
      key: "element_value",
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        {/* 返回按钮 */}
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          返回
        </Button>

        {/* 基本信息 */}
        <Card>
          <Title level={4}>
            {contract.file_type === "pdf" ? (
              <FilePdfOutlined style={{ color: "#ff4d4f" }} />
            ) : (
              <FileImageOutlined style={{ color: "#1890ff" }} />
            )}
            {" "}{contract.file_name}
          </Title>

          <Descriptions column={2} style={{ marginTop: 16 }}>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_COLORS[contract.status]}>
                {STATUS_LABELS[contract.status]}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="合同类型">
              {contract.contract_type || "未识别"}
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {(contract.file_size / 1024 / 1024).toFixed(2)} MB
            </Descriptions.Item>
            <Descriptions.Item label="页数">
              {contract.page_count || "-"}
            </Descriptions.Item>
            <Descriptions.Item label="上传时间">
              {new Date(contract.created_at).toLocaleString("zh-CN")}
            </Descriptions.Item>
          </Descriptions>

          {contract.status === "completed" && (
            <Dropdown
              menu={{
                items: [
                  {
                    key: "pdf",
                    icon: <FilePdfOutlined />,
                    label: "导出 PDF",
                    onClick: () => handleExportReport("pdf"),
                  },
                  {
                    key: "word",
                    icon: <FileWordOutlined />,
                    label: "导出 Word",
                    onClick: () => handleExportReport("word"),
                  },
                ] as MenuProps["items"],
              }}
              disabled={generating}
            >
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                loading={generating}
                style={{ marginTop: 16 }}
              >
                导出审核报告
              </Button>
            </Dropdown>
          )}
        </Card>

        {/* 风险提示概览 */}
        {contract.risks && contract.risks.length > 0 && (() => {
          const groups = groupRisksByRuleType(contract.risks);
          const totalRules = groups.reduce((sum, g) => sum + g.total, 0);
          const totalPassed = groups.reduce((sum, g) => sum + g.passed, 0);
          const totalRisk = groups.reduce((sum, g) => sum + g.risk, 0);
          const totalUncertain = groups.reduce((sum, g) => sum + (g.uncertain || 0), 0);

          return (
            <Alert
              message={`审核完成：共 ${totalRules} 条规则，${totalPassed} 条未发现风险，${totalRisk} 条风险，${totalUncertain} 条无法确定`}
              type={totalRisk > 0 || totalUncertain > 0 ? "warning" : "success"}
              showIcon
              style={{ marginBottom: 16 }}
            />
          );
        })()}

        {/* 要素提取结果 */}
        <Card title="合同要素">
          <Table
            columns={elementColumns}
            dataSource={contract.elements}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </Card>

        {/* 审核规则执行详情 - 分组展示 */}
        <Card title="审核规则执行详情">
          {contract.risks && contract.risks.length > 0 ? (
            <Collapse defaultActiveKey={[]} accordion items={getCollapseItems(contract.risks)} />
          ) : (
            <Text type="secondary">未配置审核规则，请先在审核配置中添加规则</Text>
          )}
        </Card>
      </Space>
    </div>
  );
};

export default ContractReview;
