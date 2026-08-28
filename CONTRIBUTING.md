# Contributing to ContractLens

感谢您关注 ContractLens！本项目欢迎所有形式的贡献，包括但不限于代码贡献、文档完善、Bug 报告和功能建议。

---

## 如何贡献

### 报告问题

请通过 GitHub Issues 报告：
- Bug 报告：包含复现步骤、环境信息、预期 vs 实际行为
- 功能建议：描述用例和解决什么问题
- 安全问题：请勿在公开 Issue 中披露，发送至项目维护者邮箱

### 代码贡献

1. **Fork & Clone**
   ```bash
   git clone https://github.com/your-org/contractlens.git
   cd contractlens
   ```

2. **创建分支**
   ```bash
   git checkout -b feat/your-feature-name
   # 或修复
   git checkout -b fix/issue-description
   ```

3. **开发环境**
   ```bash
   # 后端
   cd backend
   cp .env.example .env
   # 编辑 .env 填入必要的 API Key
   pip install -r requirements.txt
   python init_db.py

   # 前端
   cd frontend
   npm install
   ```

4. **运行测试**
   ```bash
   # L1 单元测试
   pytest -k "unit" -v

   # L2 冒烟测试
   pytest -k "fc01 or fc02" -v

   # L3 完整测试
   pytest -v
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feat/your-feature-name
   ```

6. **创建 Pull Request**
   - 使用清晰的标题描述改动
   - 说明解决的问题或新增的功能
   - 确保所有测试通过

---

## 代码规范

### Python（后端）

- 变量/函数/方法：`snake_case`
- 类名：`PascalCase`
- 数据库表/字段：`snake_case`
- 遵循 PEP 8
- 新增依赖必须登记到 `architecture.md`

### TypeScript（前端）

- 变量/函数：`camelCase`
- 组件/类：`PascalCase`
- 遵循项目现有类型定义

### 提交信息格式

```
<type>(<scope>): <description>

类型：feat | fix | docs | refactor | test | chore
范围：可选，affected module or feature
```

示例：
```
feat(audit): add new LLM rule for contract completeness check
fix(auth): correct JWT token expiration handling
docs(readme): update deployment instructions
```

---

## 项目结构

```
contractlens/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/       # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── services/     # 业务逻辑
│   │   └── utils/        # 工具（OCR、LLM）
│   ├── tests/            # 测试
│   └── requirements.txt
├── frontend/             # React 前端
│   ├── src/
│   │   ├── components/  # 通用组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API 调用
│   │   └── types/        # 类型定义
│   └── package.json
└── docker-compose.yml    # 容器编排
```

---

## 审核规则开发

### 添加新的 LLM 审核规则

规则存储在 `audit_rules` 表中，可通过 API 或直接插入数据库：

```sql
INSERT INTO audit_rules (id, name, description, rule_type, enabled, params, severity, is_global, created_by, is_deleted, created_at, updated_at)
VALUES (
    lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))),
    '规则名称',
    '规则描述',
    'llm_risk',  -- llm_risk | llm_completeness | llm_compliance
    true,
    '{"prompt": "LLM 提示词，要求返回 JSON 格式的 risks 数组"}',
    'medium',    -- high | medium | low
    true,
    'contributor',
    0,
    datetime('now'),
    datetime('now')
);
```

规则类型说明：
- `llm_risk` — 风险识别类规则
- `llm_completeness` — 完整性检查类规则
- `llm_compliance` — 合规性检查类规则

### 添加正则/关键词规则

```json
{
  "name": "禁止免责条款",
  "rule_type": "keyword",
  "params": {
    "keywords": ["免责声明", "不承担任何责任"]
  },
  "severity": "high",
  "enabled": true
}
```

---

## 行为契约（PACT）

本项目使用 PACT 工作流管理功能开发：

```
/pact.pid       → 定义功能意图
/pact.contract  → 约定行为契约
/pact.build     → 实现功能
/pact.verify    → 验证实现
/pact.ship      → 测试与发布
```

贡献代码前请熟悉项目工作流程。

---

## 测试覆盖

- **L1**：单元测试，测试独立函数/方法
- **L2**：冒烟测试，核心路径验证
- **L3**：完整测试 + 前端 E2E

所有新增功能必须包含对应测试用例。

---

## 许可证

通过贡献代码，您同意将您的作品按 Apache 2.0 许可证授权。

---

## 联系方式

- GitHub Issues：https://github.com/your-org/contractlens/issues
- 讨论区：https://github.com/your-org/contractlens/discussions
