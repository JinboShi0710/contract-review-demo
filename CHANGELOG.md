# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-04-03

### Added

- **合同上传** — 支持 PDF/图片合同文件上传
- **合同列表** — 合同管理列表，支持状态筛选
- **合同审核** — OCR 识别、要素提取、多维风险检测
- **模板比对** — 待审合同与模板合同的差异比对
- **凭证处理** — 证件分类识别、要素抽取（含手写体）
- **审核点配置化** — 可视化配置审核规则，支持 keyword/regex/blacklist/LLM 四种类型
- **审核结果详尽呈现** — 完整的风险标注与要素展示
- **审核报告导出** — 支持 PDF / Word 格式导出
- **用户认证** — JWT Token 认证，支持注册/登录
- **合同条款编号连续性** — LLM 检测条款编号缺失/重复/跨级

### Features

- **LLM 审核规则库** — 16 条内置 LLM 语义规则
  - 贷款类：费率、利率、担保物、电子合同
  - 泛商业：履约能力、付款节点、违约责任对等
- **四层风险检测** — 关键词 / 正则 / 黑名单 / LLM 语义
- **Docker 容器化部署** — 一键启动前后端服务

### Technology

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：React 18 + TypeScript + Vite + Ant Design
- **OCR**：PaddleOCR
- **LLM**：DeepSeek V3（兼容 OpenAI API）

### Documentation

- `CONTRIBUTING.md` — 贡献指南
- `LICENSE` — Apache 2.0
- `README.md` — 项目说明与快速开始
