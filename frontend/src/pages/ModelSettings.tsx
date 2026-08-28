import React, { useEffect, useState } from "react";
import {
  Alert,
  AutoComplete,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Spin,
  Typography,
  message,
} from "antd";
import { ApiOutlined, SaveOutlined } from "@ant-design/icons";
import {
  getModelSettings,
  saveModelSettings,
  testModelSettings,
  ModelSettingsPayload,
} from "../services/api";

const { Title, Paragraph, Text } = Typography;

const PROVIDERS = {
  openrouter: {
    label: "OpenRouter",
    baseUrl: "https://openrouter.ai/api/v1",
    models: ["openrouter/free"],
    tip: "OpenRouter 的 openrouter/free 可能限流或自动切换模型，正式使用建议填写稳定的具体模型 ID。",
  },
  deepseek: {
    label: "DeepSeek",
    baseUrl: "https://api.deepseek.com",
    models: ["deepseek-v4-flash", "deepseek-v4-pro"],
    tip: "使用 DeepSeek 开放平台 API Key；V4 Flash 更偏速度和成本，V4 Pro 更偏复杂任务效果。",
  },
  doubao: {
    label: "豆包（火山方舟）",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    models: ["doubao-seed-2-0-lite-260215"],
    tip: "使用火山方舟 API Key。若预设模型不可用，请填写方舟控制台中实际开通的模型 ID 或推理接入点 ID。",
  },
  qwen: {
    label: "通义千问（阿里云百炼）",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    models: ["qwen-plus", "qwen-flash"],
    tip: "使用阿里云百炼 API Key；如使用企业专属空间，可将接口地址替换为控制台提供的专属地址。",
  },
  openai: {
    label: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    models: ["gpt-4.1-mini", "gpt-4.1"],
    tip: "使用 OpenAI API Key。模型名称可按账号实际可用模型手动填写。",
  },
  custom: {
    label: "OpenAI兼容服务",
    baseUrl: "",
    models: [],
    tip: "填写兼容 OpenAI Chat Completions 接口的 Base URL、模型 ID 和 API Key。",
  },
} as const;

type ProviderKey = keyof typeof PROVIDERS;

const detectProvider = (url: string): ProviderKey => {
  if (url.includes("openrouter.ai")) return "openrouter";
  if (url.includes("deepseek.com")) return "deepseek";
  if (url.includes("volces.com")) return "doubao";
  if (url.includes("dashscope.aliyuncs.com") || url.includes("maas.aliyuncs.com")) return "qwen";
  if (url.includes("openai.com")) return "openai";
  return "custom";
};

const ModelSettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [provider, setProvider] = useState<ProviderKey>("openrouter");
  const [keyConfigured, setKeyConfigured] = useState(false);

  useEffect(() => {
    const load = async () => {
      const res = await getModelSettings();
      if (res.code === 0 && res.data) {
        const detected = detectProvider(res.data.base_url);
        setProvider(detected);
        setKeyConfigured(res.data.api_key_configured);
        form.setFieldsValue({
          provider: detected,
          base_url: res.data.base_url,
          model: res.data.model,
          timeout: res.data.timeout,
          api_key: "",
        });
      } else {
        message.error(res.message || "模型配置加载失败");
      }
      setLoading(false);
    };
    load();
  }, [form]);

  const handleProviderChange = (value: ProviderKey) => {
    setProvider(value);
    const preset = PROVIDERS[value];
    form.setFieldValue("base_url", preset.baseUrl);
    if (preset.models.length > 0) {
      form.setFieldValue("model", preset.models[0]);
    }
  };

  const getPayload = async (): Promise<ModelSettingsPayload> => {
    const values = await form.validateFields();
    return {
      base_url: values.base_url.trim(),
      model: values.model.trim(),
      timeout: values.timeout,
      api_key: values.api_key?.trim() || undefined,
    };
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      const res = await testModelSettings(await getPayload());
      res.code === 0
        ? message.success(res.message || "连接成功")
        : message.error(res.message || "连接失败");
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const res = await saveModelSettings(await getPayload());
      if (res.code === 0) {
        setKeyConfigured(Boolean(res.data?.api_key_configured));
        form.setFieldValue("api_key", "");
        message.success(res.message || "保存成功");
      } else {
        message.error(res.message || "保存失败");
      }
    } finally {
      setSaving(false);
    }
  };

  const modelOptions = PROVIDERS[provider].models.map((value) => ({ value }));

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <Card>
        <Title level={2}>大模型设置</Title>
        <Paragraph type="secondary">
          配置合同要素提取、语义审核和报告生成使用的大模型。保存后立即生效，无需重启后端。
        </Paragraph>
        <Alert
          type="info"
          showIcon
          message="API Key 仅发送到本机后端并写入 .env，前端不会读取或回显已保存的密钥。"
          style={{ marginBottom: 24 }}
        />
        <Spin spinning={loading}>
          <Form form={form} layout="vertical" initialValues={{ timeout: 60 }}>
            <Form.Item label="模型供应商" name="provider">
              <Select
                options={Object.entries(PROVIDERS).map(([value, item]) => ({
                  value,
                  label: item.label,
                }))}
                onChange={handleProviderChange}
              />
            </Form.Item>
            <Form.Item
              label="接口地址（Base URL）"
              name="base_url"
              rules={[{ required: true, message: "请输入接口地址" }]}
            >
              <Input placeholder="https://openrouter.ai/api/v1" />
            </Form.Item>
            <Form.Item
              label="模型名称"
              name="model"
              rules={[{ required: true, message: "请输入或选择模型名称" }]}
              extra="可以从建议项中选择，也可以直接输入服务商支持的模型ID。"
            >
              <AutoComplete options={modelOptions} placeholder="例如 openrouter/free" />
            </Form.Item>
            <Form.Item
              label="API Key"
              name="api_key"
              extra={keyConfigured ? "已保存密钥；留空表示继续使用现有密钥。" : "尚未配置密钥。"}
            >
              <Input.Password
                autoComplete="new-password"
                placeholder={keyConfigured ? "已配置，留空不修改" : "请输入 API Key"}
              />
            </Form.Item>
            <Form.Item
              label="请求超时（秒）"
              name="timeout"
              rules={[{ required: true, message: "请输入超时时间" }]}
            >
              <InputNumber min={5} max={600} style={{ width: 180 }} />
            </Form.Item>
            <Space>
              <Button icon={<ApiOutlined />} loading={testing} onClick={handleTest}>
                测试连接
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                保存并应用
              </Button>
            </Space>
            <div style={{ marginTop: 20 }}>
              <Text type="secondary">
                提示：{PROVIDERS[provider].tip}
              </Text>
            </div>
          </Form>
        </Spin>
      </Card>
    </div>
  );
};

export default ModelSettingsPage;
