// -*- coding: utf-8 -*-
/**
 * 合同卡片组件
 */
import React from "react";
import { Card, Tag, Typography, Space } from "antd";
import { FilePdfOutlined, FileImageOutlined } from "@ant-design/icons";
import type { ContractListItem, ContractStatus } from "../types/contract";

const { Text } = Typography;

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

interface ContractCardProps {
  contract: ContractListItem;
  onClick?: () => void;
}

const ContractCard: React.FC<ContractCardProps> = ({ contract, onClick }) => {
  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
    >
      <Space direction="vertical" size="small" style={{ width: "100%" }}>
        <Space>
          {contract.file_type === "pdf" ? (
            <FilePdfOutlined style={{ fontSize: 24, color: "#ff4d4f" }} />
          ) : (
            <FileImageOutlined style={{ fontSize: 24, color: "#1890ff" }} />
          )}
          <Text strong ellipsis style={{ maxWidth: 200 }}>
            {contract.file_name}
          </Text>
        </Space>

        <Space>
          <Tag color={STATUS_COLORS[contract.status]}>
            {STATUS_LABELS[contract.status]}
          </Tag>
          {contract.contract_type && (
            <Tag>{contract.contract_type}</Tag>
          )}
        </Space>

        <Text type="secondary" style={{ fontSize: 12 }}>
          {new Date(contract.created_at).toLocaleString("zh-CN")}
        </Text>
      </Space>
    </Card>
  );
};

export default ContractCard;
