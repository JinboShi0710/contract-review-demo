// -*- coding: utf-8 -*-
/**
 * 合同列表页
 */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Table, Button, Tag, Card, Typography, Space, Popconfirm, message } from "antd";
import { EyeOutlined, DeleteOutlined, ReloadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { listContracts, deleteContract } from "../services/api";
import type { ContractListItem, ContractStatus } from "../types/contract";

const { Title } = Typography;

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

const ContractList: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<ContractListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchContracts = async () => {
    setLoading(true);
    try {
      const res = await listContracts(page, pageSize);
      if (res.code === 0) {
        setContracts(res.data.items);
        setTotal(res.data.total);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContracts();
  }, [page, pageSize]);

  const handleDelete = async (id: string) => {
    const res = await deleteContract(id);
    if (res.code === 0) {
      message.success("删除成功");
      fetchContracts();
    } else {
      message.error(res.message);
    }
  };

  const columns: ColumnsType<ContractListItem> = [
    {
      title: "文件名",
      dataIndex: "file_name",
      key: "file_name",
      ellipsis: true,
    },
    {
      title: "合同类型",
      dataIndex: "contract_type",
      key: "contract_type",
      width: 120,
      render: (type: string) => type || "-",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: ContractStatus) => (
        <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>
      ),
    },
    {
      title: "上传时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (time: string) => new Date(time).toLocaleString("zh-CN"),
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
            icon={<EyeOutlined />}
            onClick={() => navigate(`/contract/${record.id}`)}
          >
            查看
          </Button>
          <Popconfirm
            title="确认删除？"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
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
      <Card
        title={
          <Title level={4} style={{ margin: 0 }}>
            合同列表
          </Title>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchContracts}>
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={contracts}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
        />
      </Card>
    </div>
  );
};

export default ContractList;
