// -*- coding: utf-8 -*-
/**
 * 风险高亮组件
 */
import React from "react";
import { Tag, Space, Typography } from "antd";
import type { ContractRisk } from "../types/contract";
import {
  RISK_TYPE_LABELS,
  RISK_LEVEL_LABELS,
  RISK_LEVEL_COLORS,
} from "../types/contract";

const { Text } = Typography;

interface RiskHighlightProps {
  risks: ContractRisk[];
  maxDisplay?: number;
}

const RiskHighlight: React.FC<RiskHighlightProps> = ({
  risks,
  maxDisplay = 5,
}) => {
  if (!risks || risks.length === 0) {
    return <Text type="secondary">未检测到风险</Text>;
  }

  return (
    <Space direction="vertical" size="small">
      {risks.slice(0, maxDisplay).map((risk) => (
        <Space key={risk.id}>
          <Tag color={RISK_LEVEL_COLORS[risk.risk_level as keyof typeof RISK_LEVEL_COLORS]}>
            {RISK_LEVEL_LABELS[risk.risk_level as keyof typeof RISK_LEVEL_LABELS]}
          </Tag>
          <Text>
            {RISK_TYPE_LABELS[risk.risk_type as keyof typeof RISK_TYPE_LABELS] || risk.risk_type}
          </Text>
        </Space>
      ))}
      {risks.length > maxDisplay && (
        <Text type="secondary">...还有 {risks.length - maxDisplay} 处</Text>
      )}
    </Space>
  );
};

export default RiskHighlight;
