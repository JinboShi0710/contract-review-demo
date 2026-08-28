// -*- coding: utf-8 -*-
/**
 * 合同模板比对页面
 */
import React, { useState } from "react";
import { Card, Typography, Upload, Button, Table, Tag, message, Spin, Alert } from "antd";
import { UploadOutlined, FileOutlined, SwapOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";
import { compareContracts, getComparison } from "../services/api";
import type { ComparisonResult } from "../types/contract";

const { Title, Text } = Typography;

const DIFF_TYPE_COLORS = {
  deleted: "red",
  added: "green",
  modified: "orange",
};

const DIFF_TYPE_LABELS = {
  deleted: "删除",
  added: "新增",
  modified: "修改",
};

const ContractCompare: React.FC = () => {
  const [templateFile, setTemplateFile] = useState<UploadFile | null>(null);
  const [contractFile, setContractFile] = useState<UploadFile | null>(null);
  const [comparing, setComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  const beforeUpload = (file: File) => {
    // 检查文件大小（20MB）
    const isLt20M = file.size / 1024 / 1024 < 20;
    if (!isLt20M) {
      message.error("文件大小超出限制（最大 20MB）");
      return false;
    }

    // 检查文件类型
    const isValidType = [
      "application/pdf",
      "image/jpeg",
      "image/jpg",
      "image/png",
    ].includes(file.type);
    if (!isValidType) {
      message.error("仅支持 PDF、JPG、PNG 格式");
      return false;
    }

    // 阻止自动上传
    return false;
  };

  const handleCompare = async () => {
    if (!templateFile || !contractFile) {
      message.warning("请同时上传模板和合同文件");
      return;
    }

    const template = templateFile.originFileObj || templateFile;
    const contract = contractFile.originFileObj || contractFile;

    if (!template || !contract) {
      message.error("文件无效");
      return;
    }

    setComparing(true);
    setLoading(true);

    try {
      // 发起比对
      const res = await compareContracts(template as File, contract as File);
      if (res.code !== 0) {
        message.error(res.message);
        return;
      }

      message.success("比对完成，正在加载结果...");

      // 获取比对结果
      const resultRes = await getComparison(res.data.comparison_id);
      if (resultRes.code === 0) {
        setComparisonResult(resultRes.data);
      }
    } catch (error) {
      message.error("比对失败，请重试");
    } finally {
      setComparing(false);
      setLoading(false);
    }
  };

  const differenceColumns = [
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      width: 100,
      render: (type: keyof typeof DIFF_TYPE_COLORS) => (
        <Tag color={DIFF_TYPE_COLORS[type]}>{DIFF_TYPE_LABELS[type]}</Tag>
      ),
    },
    {
      title: "模板内容",
      dataIndex: "template_text",
      key: "template_text",
      ellipsis: true,
    },
    {
      title: "合同内容",
      dataIndex: "contract_text",
      key: "contract_text",
      ellipsis: true,
    },
    {
      title: "位置",
      dataIndex: "location",
      key: "location",
      width: 100,
      render: (location: { page: number }) => (
        <Text>第 {location.page} 页</Text>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Title level={4}>合同模板比对</Title>
        <Text type="secondary">
          上传电子版模板和待审合同，系统自动比对两份文档，标注差异位置。
        </Text>

        <div style={{ display: "flex", gap: 24, marginTop: 24 }}>
          {/* 模板文件上传 */}
          <Card
            size="small"
            title="电子版模板"
            style={{ width: 300 }}
            extra={<FileOutlined />}
          >
            <Upload.Dragger
              fileList={templateFile ? [templateFile] : []}
              onChange={({ fileList }) => setTemplateFile(fileList[0] || null)}
              beforeUpload={beforeUpload}
              maxCount={1}
              accept=".pdf,.jpg,.jpeg,.png"
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击上传模板</p>
              <p className="ant-upload-hint">PDF 或图片格式</p>
            </Upload.Dragger>
          </Card>

          {/* 对比图标 */}
          <div style={{ display: "flex", alignItems: "center", paddingTop: 40 }}>
            <SwapOutlined style={{ fontSize: 32, color: "#1890ff" }} />
          </div>

          {/* 合同文件上传 */}
          <Card
            size="small"
            title="待审合同"
            style={{ width: 300 }}
            extra={<FileOutlined />}
          >
            <Upload.Dragger
              fileList={contractFile ? [contractFile] : []}
              onChange={({ fileList }) => setContractFile(fileList[0] || null)}
              beforeUpload={beforeUpload}
              maxCount={1}
              accept=".pdf,.jpg,.jpeg,.png"
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击上传合同</p>
              <p className="ant-upload-hint">PDF 或图片格式</p>
            </Upload.Dragger>
          </Card>
        </div>

        <div style={{ marginTop: 24 }}>
          <Button
            type="primary"
            size="large"
            onClick={handleCompare}
            loading={comparing}
            disabled={!templateFile || !contractFile}
          >
            {comparing ? "比对中..." : "开始比对"}
          </Button>
        </div>
      </Card>

      {/* 比对结果 */}
      {(comparisonResult || loading) && (
        <Card style={{ marginTop: 24 }}>
          <Title level={4}>比对结果</Title>

          {loading ? (
            <div style={{ textAlign: "center", padding: 40 }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">正在加载比对结果...</Text>
              </div>
            </div>
          ) : comparisonResult ? (
            <>
              {/* 概览 */}
              <div style={{ display: "flex", gap: 24, marginBottom: 24 }}>
                <Card size="small" style={{ width: 150 }}>
                  <div style={{ textAlign: "center" }}>
                    <Title level={2} style={{ margin: 0, color: "#1890ff" }}>
                      {comparisonResult.similarity.toFixed(1)}%
                    </Title>
                    <Text type="secondary">相似度</Text>
                  </div>
                </Card>
                <Card size="small" style={{ width: 150 }}>
                  <div style={{ textAlign: "center" }}>
                    <Title level={2} style={{ margin: 0 }}>
                      {comparisonResult.template_pages}
                    </Title>
                    <Text type="secondary">模板页数</Text>
                  </div>
                </Card>
                <Card size="small" style={{ width: 150 }}>
                  <div style={{ textAlign: "center" }}>
                    <Title level={2} style={{ margin: 0 }}>
                      {comparisonResult.contract_pages}
                    </Title>
                    <Text type="secondary">合同页数</Text>
                  </div>
                </Card>
                <Card size="small" style={{ width: 150 }}>
                  <div style={{ textAlign: "center" }}>
                    <Title level={2} style={{ margin: 0, color: comparisonResult.differences.length > 0 ? "#ff4d4f" : "#52c41a" }}>
                      {comparisonResult.differences.length}
                    </Title>
                    <Text type="secondary">差异数量</Text>
                  </div>
                </Card>
              </div>

              {/* 相似度警告 */}
              {comparisonResult.similarity < 30 && (
                <Alert
                  message="警告：两份文档相似度极低，可能不是同一合同"
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* 页数差异警告 */}
              {comparisonResult.template_pages !== comparisonResult.contract_pages && (
                <Alert
                  message={`页数差异：模板 ${comparisonResult.template_pages} 页 vs 合同 ${comparisonResult.contract_pages} 页`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              {/* 差异列表 */}
              {comparisonResult.differences.length > 0 ? (
                <Table
                  columns={differenceColumns}
                  dataSource={comparisonResult.differences}
                  rowKey={(_, index) => String(index ?? 0)}
                  pagination={false}
                  size="small"
                />
              ) : (
                <Alert
                  message="两份文档未发现文本差异"
                  type="success"
                  showIcon
                />
              )}
            </>
          ) : null}
        </Card>
      )}
    </div>
  );
};

export default ContractCompare;
