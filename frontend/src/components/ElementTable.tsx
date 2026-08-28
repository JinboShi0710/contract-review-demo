// -*- coding: utf-8 -*-
/**
 * 合同要素表格组件
 */
import React from "react";
import { Table, Tag } from "antd";
import type { ContractElement } from "../types/contract";
import { ELEMENT_TYPE_LABELS } from "../types/contract";

interface ElementTableProps {
  elements: ContractElement[];
}

const ElementTable: React.FC<ElementTableProps> = ({ elements }) => {
  const columns = [
    {
      title: "要素类型",
      dataIndex: "element_type",
      key: "element_type",
      width: 150,
      render: (type: string) => (
        <Tag>{ELEMENT_TYPE_LABELS[type as keyof typeof ELEMENT_TYPE_LABELS] || type}</Tag>
      ),
    },
    {
      title: "要素值",
      dataIndex: "element_value",
      key: "element_value",
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={elements}
      rowKey="id"
      pagination={false}
      size="small"
    />
  );
};

export default ElementTable;
