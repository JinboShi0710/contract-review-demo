// -*- coding: utf-8 -*-
/**
 * 凭证处理页面（合并分类+要素提取）
 */
import React, { useState } from "react";
import { Card, Typography, Upload, Table, Tag, message, Spin, Empty } from "antd";
import { UploadOutlined, FileOutlined } from "@ant-design/icons";
import { processVoucher } from "../services/api";
import type { VoucherProcessResponse } from "../types/contract";

const { Title, Text } = Typography;

const VoucherProcess: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [processResult, setProcessResult] = useState<VoucherProcessResponse | null>(null);

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

  const handleProcess = async (file: File) => {
    setUploading(true);
    setProcessResult(null);

    try {
      const res = await processVoucher(file);
      if (res.code !== 0) {
        message.error(res.message);
        return;
      }

      setProcessResult(res.data);
      message.success("处理完成");
    } catch (error) {
      message.error("处理失败，请重试");
    } finally {
      setUploading(false);
    }
  };

  const resultColumns = [
    {
      title: "要素名称",
      dataIndex: "label",
      key: "label",
      width: 150,
    },
    {
      title: "要素值",
      dataIndex: "value",
      key: "value",
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Title level={4}>凭证处理</Title>
        <Text type="secondary">
          上传凭证图片，系统自动识别凭证类型并提取关键要素。
        </Text>

        <div style={{ display: "flex", gap: 24, marginTop: 24 }}>
          {/* 凭证上传 */}
          <Card
            size="small"
            title="上传凭证"
            style={{ width: 400 }}
            extra={<FileOutlined />}
          >
            <Upload.Dragger
              onChange={({ fileList }) => {
                const file = fileList[0]?.originFileObj || fileList[0];
                if (file) {
                  handleProcess(file as File);
                }
              }}
              beforeUpload={beforeUpload}
              maxCount={1}
              accept=".pdf,.jpg,.jpeg,.png"
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击上传凭证</p>
              <p className="ant-upload-hint">PDF 或图片格式，最大 20MB</p>
            </Upload.Dragger>
          </Card>

          {/* 处理结果 */}
          <Card
            size="small"
            title="处理结果"
            style={{ width: 500 }}
            extra={uploading ? <Spin size="small" /> : null}
          >
            {processResult ? (
              <div>
                {/* 分类结果 */}
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary">凭证类型：</Text>
                  <Tag color="blue" style={{ fontSize: 14, marginLeft: 8 }}>
                    {processResult.classification_name}
                  </Tag>
                </div>

                {/* 要素列表 */}
                <Text type="secondary">提取要素：</Text>
                {processResult.elements.length > 0 ? (
                  <Table
                    size="small"
                    dataSource={processResult.elements}
                    columns={resultColumns}
                    rowKey={(_record, index) => String(index ?? 0)}
                    pagination={false}
                    style={{ marginTop: 8 }}
                  />
                ) : (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="未识别到要素"
                    style={{ marginTop: 16 }}
                  />
                )}
              </div>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请上传凭证图片" />
            )}
          </Card>
        </div>
      </Card>
    </div>
  );
};

export default VoucherProcess;
