// -*- coding: utf-8 -*-
/**
 * 报告查看组件
 */
import React from "react";
import { Button, Space, message } from "antd";
import { DownloadOutlined } from "@ant-design/icons";

interface ReportViewerProps {
  reportId: string;
  downloadUrl: string;
}

const ReportViewer: React.FC<ReportViewerProps> = ({ reportId: _reportId, downloadUrl }) => {
  const handleDownload = () => {
    window.open(downloadUrl, "_blank");
    message.success("报告下载已开始");
  };

  return (
    <Space direction="vertical">
      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={handleDownload}
      >
        下载 PDF 报告
      </Button>
    </Space>
  );
};

export default ReportViewer;
