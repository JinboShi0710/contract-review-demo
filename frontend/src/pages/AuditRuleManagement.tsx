// -*- coding: utf-8 -*-
/**
 * 审核点配置管理页面
 */
import React, { useState, useEffect } from "react";
import {
  Card,
  Table,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Typography,
  Alert,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
  listAuditRules,
  createAuditRule,
  updateAuditRule,
  deleteAuditRule,
  importDefaultRules,
  AuditRuleItem,
} from "../services/api";

const { Title, Text } = Typography;
const { TextArea } = Input;

const RULE_TYPE_OPTIONS = [
  { value: "keyword", label: "关键词规则" },
  { value: "regex", label: "正则规则" },
  { value: "format", label: "格式规则" },
  { value: "blacklist", label: "黑名单规则" },
  { value: "llm_risk", label: "LLM风险检测" },
  { value: "llm_compliance", label: "LLM合规检查" },
  { value: "llm_completeness", label: "LLM完整性检查" },
];

const SEVERITY_OPTIONS = [
  { value: "high", label: "高风险", color: "red" },
  { value: "medium", label: "中风险", color: "orange" },
  { value: "low", label: "低风险", color: "green" },
];

const getSeverityColor = (severity: string) => {
  const option = SEVERITY_OPTIONS.find((o) => o.value === severity);
  return option?.color || "default";
};

const getRuleTypeLabel = (type: string) => {
  const option = RULE_TYPE_OPTIONS.find((o) => o.value === type);
  return option?.label || type;
};

const AuditRuleManagement: React.FC = () => {
  const [rules, setRules] = useState<AuditRuleItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<AuditRuleItem | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const res = await listAuditRules();
      if (res.code === 0) {
        setRules(res.data.items || []);
      } else {
        message.error(res.message || "加载配置失败");
      }
    } catch {
      message.error("加载配置失败");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (rule: AuditRuleItem) => {
    setEditingRule(rule);
    form.setFieldsValue({
      name: rule.name,
      description: rule.description,
      rule_type: rule.rule_type,
      severity: rule.severity,
      params: JSON.stringify(rule.params, null, 2),
    });
    setModalVisible(true);
  };

  const handleDelete = async (ruleId: string) => {
    try {
      const res = await deleteAuditRule(ruleId);
      if (res.code === 0) {
        message.success("删除成功");
        fetchRules();
      } else {
        message.error(res.message || "删除失败");
      }
    } catch {
      message.error("删除失败");
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const params = JSON.parse(values.params || "{}");

      const res = editingRule
        ? await updateAuditRule(editingRule.id, values.name, params, values.severity, values.description)
        : await createAuditRule(values.name, values.rule_type, params, values.severity, values.description);

      if (res.code === 0) {
        message.success(editingRule ? "更新成功" : "创建成功");
        setModalVisible(false);
        fetchRules();
      } else {
        message.error(res.message || "操作失败");
      }
    } catch (error) {
      if (error instanceof SyntaxError) {
        message.error("参数格式错误，请输入有效的JSON");
      } else {
        message.error("操作失败");
      }
    }
  };

  const handleImport = async () => {
    try {
      const res = await importDefaultRules();
      if (res.code === 0) {
        message.success(`成功导入 ${res.data?.count || 0} 个规则`);
        fetchRules();
      } else {
        message.error(res.message || "导入失败");
      }
    } catch {
      message.error("导入失败");
    }
  };

  const columns: ColumnsType<AuditRuleItem> = [
    {
      title: "规则名称",
      dataIndex: "name",
      key: "name",
      width: 200,
    },
    {
      title: "规则类型",
      dataIndex: "rule_type",
      key: "rule_type",
      width: 120,
      render: (type: string) => getRuleTypeLabel(type),
    },
    {
      title: "严重程度",
      dataIndex: "severity",
      key: "severity",
      width: 100,
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>
          {SEVERITY_OPTIONS.find((o) => o.value === severity)?.label || severity}
        </Tag>
      ),
    },
    {
      title: "状态",
      dataIndex: "enabled",
      key: "enabled",
      width: 80,
      render: (enabled: boolean) => (enabled ? "启用" : "禁用"),
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
    },
    {
      title: "操作",
      key: "action",
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            修改
          </Button>
          <Popconfirm
            title="确定删除此配置？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>
            审核点配置管理
          </Title>
          <Space>
            <Button icon={<UploadOutlined />} onClick={handleImport}>
              导入默认规则
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              新建配置
            </Button>
          </Space>
        </div>

        <Alert
          message="说明"
          description="全局审核点由管理员配置，所有合同审核都会执行。自定义审核点为自己创建的补充审核点。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={rules}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingRule ? "修改审核配置" : "新建审核配置"}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="规则名称"
            rules={[{ required: true, message: "请输入规则名称" }]}
          >
            <Input placeholder="请输入规则名称" />
          </Form.Item>

          <Form.Item
            name="rule_type"
            label="规则类型"
            rules={[{ required: true, message: "请选择规则类型" }]}
          >
            <Select placeholder="请选择规则类型" options={RULE_TYPE_OPTIONS} />
          </Form.Item>

          <Form.Item
            name="severity"
            label="严重程度"
            rules={[{ required: true, message: "请选择严重程度" }]}
          >
            <Select placeholder="请选择严重程度" options={SEVERITY_OPTIONS} />
          </Form.Item>

          <Form.Item name="description" label="规则描述">
            <TextArea rows={2} placeholder="请输入规则描述" />
          </Form.Item>

          <Form.Item
            name="params"
            label="规则参数"
            extra={
              <Text type="secondary">
                关键词规则: {"{ keywords: ['免责声明', '违约金'] }"}
                <br />
                正则规则: {"{ pattern: '\\d{4}年\\d{1,2}月\\d{1,2}日' }"}
                <br />
                LLM规则: {"{ prompt: '检测合同中的风险条款' }"}
              </Text>
            }
          >
            <TextArea rows={4} placeholder='{"keywords": []}' />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AuditRuleManagement;
