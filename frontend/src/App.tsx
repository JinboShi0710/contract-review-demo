// -*- coding: utf-8 -*-
/**
 * 主应用组件
 */
import React, { useState } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Layout, Menu, Space, Typography, Dropdown } from "antd";
import {
  UploadOutlined,
  FileTextOutlined,
  SwapOutlined,
  IdcardOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  RobotOutlined,
  FileSearchOutlined,
  KeyOutlined,
} from "@ant-design/icons";
import ContractUpload from "./pages/ContractUpload";
import ContractList from "./pages/ContractList";
import ContractReview from "./pages/ContractReview";
import ContractCompare from "./pages/ContractCompare";
import VoucherProcess from "./pages/VoucherProcess";
import AuditRuleManagement from "./pages/AuditRuleManagement";
import Login from "./pages/Login";
import ModelSettings from "./pages/ModelSettings";
import TenderWorkspace from "./pages/TenderWorkspace";
import TenderReview from "./pages/TenderReview";
import AccountSettings from "./components/AccountSettings";
import { isLoggedIn, getUser, clearAuth } from "./lib/auth";

const { Header, Content } = Layout;

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  if (!isLoggedIn()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
};

const RequireAdmin: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  if (getUser()?.role !== "admin") {
    return <Navigate to="/upload" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const currentUser = getUser();
  const [accountSettingsOpen, setAccountSettingsOpen] = useState(false);

  const selectedKey = location.pathname === "/model-settings" ? "model-settings"
    : location.pathname.startsWith("/tender") ? "tenders"
    : location.pathname === "/audit-rules" ? "audit-rules"
    : location.pathname === "/voucher" ? "voucher"
    : location.pathname === "/compare" ? "compare"
    : location.pathname === "/contracts" ? "list"
    : "upload";

  const menuItems = [
    {
      key: "tenders",
      icon: <FileSearchOutlined />,
      label: "招投标审核",
      onClick: () => navigate("/tenders"),
    },
    {
      key: "upload",
      icon: <UploadOutlined />,
      label: "上传合同",
      onClick: () => navigate("/upload"),
    },
    {
      key: "list",
      icon: <FileTextOutlined />,
      label: "合同列表",
      onClick: () => navigate("/contracts"),
    },
    {
      key: "compare",
      icon: <SwapOutlined />,
      label: "模板比对",
      onClick: () => navigate("/compare"),
    },
    {
      key: "voucher",
      icon: <IdcardOutlined />,
      label: "凭证处理",
      onClick: () => navigate("/voucher"),
    },
    {
      key: "audit-rules",
      icon: <SettingOutlined />,
      label: "审核配置",
      onClick: () => navigate("/audit-rules"),
    },
    ...(currentUser?.role === "admin" ? [{
      key: "model-settings",
      icon: <RobotOutlined />,
      label: "模型设置",
      onClick: () => navigate("/model-settings"),
    }] : []),
  ];

  const handleLogout = () => {
    clearAuth();
    navigate("/login", { replace: true });
  };

  const userMenuItems = [
    {
      key: "account-settings",
      icon: <KeyOutlined />,
      label: "用户设置",
      onClick: () => setAccountSettingsOpen(true),
    },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: handleLogout,
    },
  ];

  const isLoginPage = location.pathname === "/login";

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {!isLoginPage && (
        <Header style={{ display: "flex", alignItems: "center" }}>
          <div style={{ color: "white", fontSize: 18, fontWeight: "bold", marginRight: 40 }}>
            ContractLens
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={menuItems}
            style={{ flex: 1 }}
          />
          {currentUser && (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ color: "white", cursor: "pointer", marginLeft: 16 }}>
                <UserOutlined />
                <span>{currentUser.username}</span>
                <Typography.Text
                  style={{
                    color: "rgba(255,255,255,0.65)",
                    fontSize: 12,
                  }}
                >
                  {currentUser.role === "admin" ? "管理员"
                    : currentUser.role === "reviewer" ? "审核员"
                    : "客户经理"}
                </Typography.Text>
              </Space>
            </Dropdown>
          )}
        </Header>
      )}
      <Content style={{ background: "#f0f2f5" }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<RequireAuth><ContractUpload /></RequireAuth>} />
          <Route path="/contracts" element={<RequireAuth><ContractList /></RequireAuth>} />
          <Route path="/contract/:id" element={<RequireAuth><ContractReview /></RequireAuth>} />
          <Route path="/tenders" element={<RequireAuth><TenderWorkspace /></RequireAuth>} />
          <Route path="/tender/:id" element={<RequireAuth><TenderReview /></RequireAuth>} />
          <Route path="/compare" element={<RequireAuth><ContractCompare /></RequireAuth>} />
          <Route path="/voucher" element={<RequireAuth><VoucherProcess /></RequireAuth>} />
          <Route path="/audit-rules" element={<RequireAuth><AuditRuleManagement /></RequireAuth>} />
          <Route path="/model-settings" element={<RequireAuth><RequireAdmin><ModelSettings /></RequireAdmin></RequireAuth>} />
        </Routes>
      </Content>
      {currentUser && (
        <AccountSettings
          open={accountSettingsOpen}
          user={currentUser}
          onClose={() => setAccountSettingsOpen(false)}
          onPasswordChanged={handleLogout}
        />
      )}
    </Layout>
  );
};

export default App;
