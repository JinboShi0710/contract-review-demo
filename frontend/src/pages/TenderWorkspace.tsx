import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Col, message, Row, Space, Table, Tag, Typography, Upload } from "antd";
import { InboxOutlined, ReloadOutlined, RightOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd";
import type { ColumnsType } from "antd/es/table";
import { listTenders, processTender, uploadTender } from "../services/api";
import type { TenderStatus, TenderTask } from "../types/tender";

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const STATUS: Record<TenderStatus, { color: string; label: string }> = {
  created: { color: "default", label: "待审查" }, processing: { color: "processing", label: "审查中" },
  completed: { color: "success", label: "已完成" }, failed: { color: "error", label: "失败" },
};

const TenderWorkspace: React.FC = () => {
  const navigate = useNavigate();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [tasks, setTasks] = useState<TenderTask[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    const response = await listTenders();
    if (response.code === 0) setTasks(response.data.items);
  };
  useEffect(() => { refresh(); }, []);

  const start = async () => {
    const file = fileList[0]?.originFileObj;
    if (!file) return message.warning("请先选择招标文件");
    setLoading(true);
    try {
      const uploaded = await uploadTender(file);
      if (uploaded.code !== 0) throw new Error(uploaded.message);
      message.info("文件已上传，正在提取要求并生成清单…");
      const processed = await processTender(uploaded.data.task_id);
      if (processed.code !== 0) throw new Error(processed.message);
      message.success("招标文件审查完成");
      navigate(`/tender/${uploaded.data.task_id}`);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "处理失败");
      refresh();
    } finally { setLoading(false); }
  };

  const columns: ColumnsType<TenderTask> = [
    { title: "文件", dataIndex: "file_name", ellipsis: true },
    { title: "状态", dataIndex: "status", width: 100, render: (value: TenderStatus) => <Tag color={STATUS[value].color}>{STATUS[value].label}</Tag> },
    { title: "处理说明", dataIndex: "summary", ellipsis: true, render: (value) => value || "-" },
    { title: "创建时间", dataIndex: "created_at", width: 180, render: (value) => new Date(value).toLocaleString("zh-CN") },
    { title: "操作", width: 90, render: (_, row) => <Button type="link" disabled={row.status !== "completed"} onClick={() => navigate(`/tender/${row.id}`)}>查看 <RightOutlined /></Button> },
  ];

  return <div style={{ padding: 24 }}>
    <Row gutter={[20, 20]}>
      <Col span={24}>
        <Card>
          <Title level={3}>招投标文件审核</Title>
          <Paragraph type="secondary">站在投标方视角，提取否决项、评分点、证明材料、重点参数、时间节点和合同约束，形成带原文证据的响应清单。</Paragraph>
          <Dragger accept=".pdf,.docx" maxCount={1} fileList={fileList} beforeUpload={() => false} onChange={({ fileList: next }) => setFileList(next.slice(-1))}>
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖入 PDF、DOCX 招标文件</p>
            <p className="ant-upload-hint">第一阶段适用于能够复制文字的文件，单文件最大 50MB</p>
          </Dragger>
          <Space style={{ marginTop: 16 }}><Button type="primary" size="large" loading={loading} disabled={!fileList.length} onClick={start}>上传并生成清单</Button><Text type="secondary">不会自动作出“投标/不投标”决策</Text></Space>
        </Card>
      </Col>
      <Col span={24}>
        <Card title="审查任务" extra={<Button icon={<ReloadOutlined />} onClick={refresh}>刷新</Button>}>
          <Table rowKey="id" columns={columns} dataSource={tasks} pagination={{ pageSize: 10 }} />
        </Card>
      </Col>
    </Row>
  </div>;
};
export default TenderWorkspace;
