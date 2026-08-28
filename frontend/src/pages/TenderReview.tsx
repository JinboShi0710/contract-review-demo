import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert, Button, Card, Collapse, Descriptions, Empty, message, Space, Spin, Tag, Typography } from "antd";
import { ArrowLeftOutlined, DownloadOutlined, FileSearchOutlined } from "@ant-design/icons";
import { exportTender, getTender } from "../services/api";
import type { TenderCategory, TenderReviewItem, TenderTask } from "../types/tender";

const { Title, Paragraph, Text } = Typography;
const ORDER: TenderCategory[] = ["disqualification", "scoring", "materials", "key_parameters", "timeline", "contract_terms", "technical_requirements", "acceptance_delivery"];
const COLORS: Record<string, string> = { required: "red", attention: "orange", reference: "blue" };
const LABELS: Record<string, string> = { required: "必须响应", attention: "重点关注", reference: "参考" };

const TenderReview: React.FC = () => {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState<TenderTask>();
  const [loading, setLoading] = useState(true);
  useEffect(() => { getTender(id).then((res) => { if (res.code === 0) setTask(res.data); else message.error(res.message); }).finally(() => setLoading(false)); }, [id]);
  const grouped = useMemo(() => {
    const map = {} as Record<TenderCategory, TenderReviewItem[]>;
    ORDER.forEach((key) => map[key] = []);
    (task?.items || []).forEach((item) => map[item.category]?.push(item));
    return map;
  }, [task]);
  if (loading) return <div style={{ padding: 80, textAlign: "center" }}><Spin size="large" /></div>;
  if (!task) return <Empty description="任务不存在" />;

  const isOutOfScope = task.summary?.includes("不属于招标审核适用范围");

  const panels = ORDER.map((category) => ({
    key: category,
    label: <Space><Text strong>{task.categories?.[category] || category}</Text><Tag>{grouped[category].length} 项</Tag></Space>,
    children: grouped[category].length ? <Space direction="vertical" size={12} style={{ width: "100%" }}>{grouped[category].map((item) =>
      <Card key={item.id} size="small" style={{ borderLeft: `4px solid ${item.importance === "required" ? "#ff4d4f" : "#faad14"}` }}>
        <Space wrap>
          <Text strong>{item.title}</Text>
          <Tag color={COLORS[item.importance]}>{LABELS[item.importance]}</Tag>
          <Tag>{item.source === "llm" ? "AI归纳" : "关键词扫描"}</Tag>
        </Space>
        <Paragraph style={{ margin: "10px 0 6px" }}>{item.requirement}</Paragraph>
        <Alert type="info" showIcon icon={<FileSearchOutlined />} message={`原文证据 · 第 ${item.source_page || "?"} 页 / 提取行 L${item.source_line || "?"}`} description={item.evidence_quote} />
        {item.action && <Paragraph style={{ margin: "10px 0 0" }}><Text type="secondary">建议动作：</Text>{item.action}</Paragraph>}
      </Card>)}</Space> : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={isOutOfScope ? "该文件不属于招标审核范围" : "AI未识别到有原文证据的该类事项，建议人工抽查"} />,
  }));

  return <div style={{ padding: 24 }}>
    <Space style={{ marginBottom: 16 }}><Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/tenders")}>返回任务</Button><Button type="primary" icon={<DownloadOutlined />} onClick={() => exportTender(id).catch((e) => message.error(e.message))}>导出 Excel 响应清单</Button></Space>
    <Card>
      <Title level={3}>{task.title || task.file_name}</Title>
      <Descriptions column={4} items={[{ key: "file", label: "源文件", children: task.file_name }, { key: "page", label: "页数", children: task.page_count || "-" }, { key: "line", label: "证据行数", children: task.line_count || "-" }, { key: "items", label: "清单事项", children: task.items?.length || 0 }]} />
      {task.summary && <Alert style={{ marginTop: 16 }} type={isOutOfScope ? "warning" : "success"} showIcon message={task.summary} />}
    </Card>
    <Card title="投标响应清单" style={{ marginTop: 16 }}><Collapse items={panels} defaultActiveKey={["technical_requirements", "key_parameters"]} /></Card>
  </div>;
};
export default TenderReview;
