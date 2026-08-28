import React, { useState } from "react";
import { Alert, Button, Descriptions, Form, Input, Modal, Space, Tag, message } from "antd";
import { LockOutlined } from "@ant-design/icons";
import { changePassword } from "../services/api";
import type { CurrentUser } from "../lib/auth";

interface AccountSettingsProps {
  open: boolean;
  user: CurrentUser;
  onClose: () => void;
  onPasswordChanged: () => void;
}

interface PasswordFormValues {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const ROLE_LABELS: Record<CurrentUser["role"], string> = {
  admin: "管理员",
  reviewer: "审核员",
  manager: "客户经理",
};

const AccountSettings: React.FC<AccountSettingsProps> = ({ open, user, onClose, onPasswordChanged }) => {
  const [form] = Form.useForm<PasswordFormValues>();
  const [saving, setSaving] = useState(false);

  const handleClose = () => {
    form.resetFields();
    onClose();
  };

  const handleSubmit = async (values: PasswordFormValues) => {
    setSaving(true);
    try {
      const response = await changePassword(values.currentPassword, values.newPassword);
      if (response.code !== 0) {
        message.error(response.message || "密码修改失败");
        return;
      }
      message.success("密码修改成功，请使用新密码重新登录");
      form.resetFields();
      onPasswordChanged();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="用户设置" open={open} onCancel={handleClose} footer={null} destroyOnClose>
      <Descriptions
        bordered
        column={1}
        size="small"
        items={[
          { key: "username", label: "用户名", children: user.username },
          { key: "password", label: "密码", children: "••••••••（安全原因不显示明文）" },
          { key: "role", label: "角色", children: <Tag color={user.role === "admin" ? "blue" : "default"}>{ROLE_LABELS[user.role]}</Tag> },
        ]}
      />

      <Alert style={{ marginTop: 16 }} type="info" showIcon message="修改密码后，当前账号会自动退出登录。" />
      <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ marginTop: 16 }}>
        <Form.Item name="currentPassword" label="当前密码" rules={[{ required: true, message: "请输入当前密码" }]}>
          <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
        </Form.Item>
        <Form.Item
          name="newPassword"
          label="新密码"
          rules={[{ required: true, message: "请输入新密码" }, { min: 8, message: "新密码至少需要8个字符" }]}
        >
          <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
        </Form.Item>
        <Form.Item
          name="confirmPassword"
          label="确认新密码"
          dependencies={["newPassword"]}
          rules={[
            { required: true, message: "请再次输入新密码" },
            ({ getFieldValue }) => ({
              validator(_, value) {
                return !value || getFieldValue("newPassword") === value
                  ? Promise.resolve()
                  : Promise.reject(new Error("两次输入的新密码不一致"));
              },
            }),
          ]}
        >
          <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
        </Form.Item>
        <Space style={{ width: "100%", justifyContent: "flex-end" }}>
          <Button onClick={handleClose}>取消</Button>
          <Button type="primary" htmlType="submit" loading={saving}>保存新密码</Button>
        </Space>
      </Form>
    </Modal>
  );
};

export default AccountSettings;
