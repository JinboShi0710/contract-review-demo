# Contract Review Demo

这是基于 ContractLens 二次开发的本地演示项目，招投标流程参考 Tender Review Kit，合同审核证据链参考 ArchSight AIOS。上游说明见 [第三方致谢](THIRD_PARTY_NOTICES.md) 和 [Tender Review 许可](backend/app/services/TENDER_REVIEW_ATTRIBUTION.md)。

## 本次代码快照（2026-08-28）

- 保存合同审核、招投标审核、模型配置及用户设置等当前源代码；不代表全部功能已经通过验收。
- 不包含本机 `.env`、数据库、用户合同、报告、日志、虚拟环境或 Node 依赖。
- GitHub 副本的 OCR 令牌改为 `OCR_API_TOKEN` 配置，未修改原电脑文件。将 `backend/.env.example` 复制为 `backend/.env`，填入自己的 LLM 和 OCR 配置。
- 首次运行需要安装依赖并初始化数据库；默认演示账号为 `admin / admin123`，应立即修改密码及 `JWT_SECRET`，不得直接暴露到公网。
- 招投标演示版单次模型输入限制为前 50,000 字符、80 条关键词候选，提示模型最多返回30项。长文不能视为全文审核；免费模型仍可能限流、超时或返回不完整结果。
- 以下保留上游使用说明供参考，功能和默认设置以当前代码为准。

---

# ContractLens

> 合同智能审核开源框架 — *See through every contract.*

基于 OCR + LLM 的合同审核与凭证处理框架，提供开箱即用的要素提取、风险检测、规则引擎和报告导出能力，支持二次开发与行业定制。

---

## 功能特性

| 模块 | 功能 |
|------|------|
| **合同审核** | OCR 识别、关键要素提取、多维风险检测、模板比对 |
| **风险引擎** | 关键词 / 正则 / 黑名单 / LLM 语义四层规则，可视化配置 |
| **凭证处理** | 证件分类识别、要素抽取（含手写体）、语义理解 |
| **报告导出** | 审核报告一键导出为 PDF / Word |
| **规则管理** | 审核点可配置化，支持版本管理与回滚 |

---

## 技术栈

```
后端：FastAPI (Python 3.11+) + SQLAlchemy + SQLite
前端：React 18 + TypeScript + Vite + Ant Design
OCR： PaddleOCR
LLM： DeepSeek V3（兼容 OpenAI API，可替换任意模型）
```

---

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- pip
- Docker & Docker Compose（可选，容器部署）

### 1. 克隆项目

```bash
git clone https://github.com/your-org/contractlens.git
cd contractlens
```

### 2. Docker 部署（推荐）

```bash
# 复制并编辑环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 LLM_API_KEY 和 JWT_SECRET

# 启动（前端 + 后端）
docker-compose up -d

# 访问
# 前端：http://localhost
# 后端：http://localhost:8006
# API 文档：http://localhost:8006/docs
```

**注意**：`JWT_SECRET` 在生产环境必须更换为随机字符串。

### 3. 手动部署

```bash
cd backend
cp .env.example .env
```

编辑 `.env`，填入你的 LLM API Key：

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com   # 或其他兼容 OpenAI API 的服务
LLM_MODEL=deepseek-chat
JWT_SECRET=change-this-secret-in-production
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python init_db.py          # 初始化数据库
uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

后端启动后访问 API 文档：http://localhost:8006/docs

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:3000

---

## 目录结构

```
contractlens/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 路由（合同、凭证、审核规则）
│   │   ├── core/            # 配置、数据库连接
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── services/        # 业务逻辑层
│   │   └── utils/           # OCR 引擎、LLM 客户端
│   ├── .env.example         # 环境变量模板
│   ├── requirements.txt
│   └── init_db.py
├── frontend/
│   └── src/
│       ├── pages/           # 页面（合同列表、审核详情、凭证处理等）
│       ├── services/        # API 调用封装
│       └── types/           # TypeScript 类型定义
└── exports/                 # 导出报告存放目录
```

---

## 配置说明

所有配置均通过环境变量管理，详见 `backend/.env.example`：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM 服务 API Key（必填） | — |
| `LLM_BASE_URL` | LLM 服务地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `APP_NAME` | 系统名称（可自定义） | `ContractLens` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///./data/contract_review.db` |
| `UPLOAD_DIR` | 上传文件目录 | `./uploads` |
| `EXPORT_DIR` | 报告导出目录 | `./exports` |
| `MAX_FILE_SIZE` | 最大上传文件大小 | `20MB` |
| `OCR_USE_GPU` | OCR 是否使用 GPU | `false` |

### 替换 LLM 服务

ContractLens 兼容任何 OpenAI API 格式的 LLM 服务：

```env
# 使用 OpenAI
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# 使用 Ollama（本地）
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5
```

---

## API 文档

启动后端后访问 Swagger UI：http://localhost:8006/docs

主要接口：

```
POST /api/v1/contracts/upload          # 上传合同
POST /api/v1/contracts/{id}/process    # 触发审核（OCR + 要素 + 风险）
GET  /api/v1/contracts/{id}            # 获取审核结果
GET  /api/v1/contracts/{id}/report/export?format=pdf|word  # 导出报告
POST /api/v1/contracts/compare         # 模板比对
GET  /api/v1/audit-rules               # 获取审核规则列表
POST /api/v1/audit-rules               # 创建审核规则
POST /api/v1/vouchers/process          # 凭证处理
```

---

## 运行测试

```bash
cd contractlens   # 项目根目录

# L1 单元测试（~10s）
pytest -k "unit" -v

# L2 冒烟测试（~30s）
pytest -k "fc01 or fc02" -v

# L3 完整测试（~60s+）
pytest .pact/tests/features/ -v
```

---

## 二次开发指南

### 自定义审核规则

在管理界面或通过 API 创建审核规则，支持四种类型：

```json
{
  "name": "禁止免责条款",
  "rule_type": "keyword",
  "params": { "keywords": ["免责声明", "不承担任何责任"] },
  "severity": "high",
  "enabled": true
}
```

规则类型：
- `keyword` — 关键词匹配
- `regex` — 正则表达式校验
- `blacklist` — 黑名单实体匹配
- `llm_risk` / `llm_compliance` / `llm_completeness` — LLM 语义分析

### 替换 OCR 引擎

修改 `backend/app/utils/ocr/engine.py`，实现同样的接口即可接入其他 OCR 服务。

### 行业定制

通过配置审核规则和 LLM Prompt（`backend/app/services/audit_engine.py`）可适配不同行业场景：金融、法律、地产、供应链等。

---

## 当前限制

- 数据库：SQLite（生产环境建议替换为 PostgreSQL/MySQL）
- 并发：单实例部署，多实例需配置共享存储
- 文件：不支持批量上传
- 移动端：仅支持桌面浏览器
- OCR：依赖 PaddleOCR API（远程服务）

---

## 许可证

Apache License 2.0 — see [LICENSE](LICENSE)
