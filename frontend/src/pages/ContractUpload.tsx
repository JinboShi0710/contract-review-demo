// -*- coding: utf-8 -*-
/**
 * 合同上传页面
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Button, message, Card, Typography } from "antd";
import {
  UploadOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileWordOutlined,
  FileTextOutlined,
} from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";
import { uploadContract, processContract } from "../services/api";

const { Title, Text } = Typography;

const ContractUpload: React.FC = () => {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const beforeUpload = (file: File) => {
    // 检查文件大小（20MB）
    const isLt20M = file.size / 1024 / 1024 < 20;
    if (!isLt20M) {
      message.error("文件大小超出限制（最大 20MB）");
      return false;
    }

    // 浏览器对 DOCX/TXT 的 MIME 判断并不统一，因此同时校验扩展名。
    const extension = file.name.split(".").pop()?.toLowerCase() || "";
    const isValidType = [
      "pdf", "docx", "txt", "md", "jpg", "jpeg", "png",
    ].includes(extension);
    if (!isValidType) {
      message.error("仅支持 PDF、DOCX、TXT、MD、JPG、PNG 格式");
      return false;
    }

    // 阻止自动上传，改为手动上传
    return false;
  };

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning("请先选择文件");
      return;
    }

    const file = fileList[0].originFileObj || fileList[0];
    if (!file) {
      message.error("文件无效");
      return;
    }

    setUploading(true);

    try {
      // 1. 上传文件
      const uploadRes = await uploadContract(file as File);
      if (uploadRes.code !== 0) {
        message.error(uploadRes.message);
        return;
      }

      message.success("上传成功，正在处理...");

      // 2. 处理合同
      const processRes = await processContract(uploadRes.data.contract_id);
      if (processRes.code !== 0) {
        message.error(processRes.message);
        return;
      }

      message.success("处理完成");
      navigate(`/contract/${uploadRes.data.contract_id}`);
    } catch (error) {
      message.error("操作失败，请重试");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Title level={4}>合同上传</Title>
        <Text type="secondary">
          支持 PDF、DOCX、TXT、MD、JPG、PNG 格式，单文件最大 20MB
        </Text>

        <div style={{ marginTop: 24 }}>
          <Upload.Dragger
            fileList={fileList}
            onChange={({ fileList: newFileList }) => setFileList(newFileList)}
            beforeUpload={beforeUpload}
            maxCount={1}
            accept=".pdf,.docx,.txt,.md,.jpg,.jpeg,.png"
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined style={{ fontSize: 48, color: "#1890ff" }} />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单个合同文件、Word、纯文本、PDF 或图片格式
            </p>
          </Upload.Dragger>
        </div>

        <div style={{ marginTop: 24 }}>
          <Button
            type="primary"
            onClick={handleUpload}
            loading={uploading}
            disabled={fileList.length === 0}
            icon={<UploadOutlined />}
          >
            {uploading ? "处理中..." : "上传并审核"}
          </Button>
        </div>

        <div style={{ marginTop: 24 }}>
          <Title level={5}>支持的文件格式</Title>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <Card size="small" style={{ width: 120 }}>
              <FilePdfOutlined style={{ fontSize: 32, color: "#ff4d4f" }} />
              <div>PDF</div>
            </Card>
            <Card size="small" style={{ width: 120 }}>
              <FileImageOutlined style={{ fontSize: 32, color: "#1890ff" }} />
              <div>JPG</div>
            </Card>
            <Card size="small" style={{ width: 120 }}>
              <FileImageOutlined style={{ fontSize: 32, color: "#52c41a" }} />
              <div>PNG</div>
            </Card>
            <Card size="small" style={{ width: 120 }}>
              <FileWordOutlined style={{ fontSize: 32, color: "#1677ff" }} />
              <div>DOCX</div>
            </Card>
            <Card size="small" style={{ width: 120 }}>
              <FileTextOutlined style={{ fontSize: 32, color: "#595959" }} />
              <div>TXT</div>
            </Card>
            <Card size="small" style={{ width: 120 }}>
              <FileTextOutlined style={{ fontSize: 32, color: "#722ed1" }} />
              <div>MD</div>
            </Card>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ContractUpload;
