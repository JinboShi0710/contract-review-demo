# Contract Review Demo

合同与招投标文件智能审查演示系统。

面向文件初审场景，结合文档解析、确定性规则和大模型语义分析，提取合同要素、提示风险、整理投标响应要求，并提供原文依据供人工核对。

> 当前为本地演示版本，重点建设合同审核和招投标审核。尚未完成生产级稳定性、安全性及审核准确率验证，不应将结果直接作为最终业务决策。

## 主要功能

### 合同审核

- 上传 PDF、JPG/JPEG、PNG、DOCX、TXT、Markdown 文件。
- 文本型文件优先直接提取文字，扫描件和图片使用远程 OCR。
- 提取合同主体、金额、编号、交易标的等要素。
- 结合关键词、格式规则和大模型开展风险与完整性检查。
- 展示风险说明、原文证据、位置及复核建议。
- 区分有依据的通过、风险和无法确定；模型未识别到问题不等于合同没有问题。
- 支持查看审核记录及导出 PDF / Word 报告。

### 招投标审核

- 上传可提取文字的 PDF 或 DOCX。
- 识别招标采购文件、采购需求说明书、合同及其他文档类型。
- 对适用文档整理否决与废标事项、评分事项、证明材料、重点参数、时间节点、合同条款、技术要求和验收交付要求。
- 对模型引用进行原文反查，展示证据及提取行号。
- 导出 Excel 投标响应清单，便于补充责任人和完成情况。

### 模型与账户配置

- 在页面配置模型供应商、接口地址、模型名称、API Key 和请求超时。
- 提供 OpenRouter、DeepSeek、豆包、通义千问等供应商配置入口，也可填写兼容接口。
- 支持连接测试；保存的 API Key 不在页面回显。
- 支持用户信息查看、密码修改、角色展示和退出登录。

### 其他保留模块

模板比对、凭证处理和审核规则管理入口仍保留。其中模板比对、凭证处理不是本轮重点完善的功能，不代表已完成全面验证。

## 典型使用流程

1. 登录系统，在模型设置中配置可用的模型服务。
2. 选择合同审核或招投标审核，上传文件。
3. 等待解析与语义分析完成。
4. 查看要素、风险或响应事项，结合原文核对关键结论。
5. 导出报告或清单，进入人工复核。

## 本地启动（Windows PowerShell）

需要 Python、Node.js 和 npm。以下命令针对首次下载；已有本地配置时不要覆盖 `.env`。

### 1. 获取代码

```powershell
git clone https://github.com/JinboShi0710/contract-review-demo.git
cd contract-review-demo
```

私有仓库需要先获得访问权限，也可以通过 GitHub 下载 ZIP 并解压。

### 2. 配置并启动后端

在项目根目录执行：

```powershell
cd backend
py -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

根据自己的服务填写：

- `LLM_API_KEY`：模型服务密钥。
- `LLM_BASE_URL`：模型接口地址。
- `LLM_MODEL`：服务商支持的模型 ID。
- `LLM_TIMEOUT`：模型请求超时设置。
- `JWT_SECRET`：自行生成的随机密钥。
- `OCR_API_TOKEN`：使用远程 OCR 时需要的令牌。

随后执行：

```powershell
& ".\.venv\Scripts\python.exe" init_db.py
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8006
```

### 3. 启动前端

新开一个 PowerShell 窗口，进入下载目录中的 `contract-review-demo\frontend`，执行：

```powershell
npm.cmd install
npm.cmd run dev
```

- 页面：http://localhost:3000
- 后端健康检查：http://127.0.0.1:8006/health
- API 文档：http://127.0.0.1:8006/docs

首次初始化的演示账号为 `admin / admin123`，登录后应修改密码。前后端窗口均需保持运行。

## 当前边界

- 招投标审核只向模型提供带行号文本的前 **50,000 字符**、最多 **80 条关键词候选**，并在提示中要求最多返回 **30 项**。超过范围的文档不能视为完成全文审核。
- DOCX 的提取位置不等于 Word 最终排版页码；应结合原文和行号定位。
- 模型调用可能限流、超时、返回空内容或不完整 JSON；同一文件重复审核也可能产生差异。
- 审核依据主要来自上传文档、配置规则和模型分析，未建设独立的行业知识库或权威法规核验服务。
- 原文反查用于核对引用，不等于证实分析结论正确。签章、黑名单和其他外部事实仍需额外证据。
- 当前仍存在长时间等待、失败提示与任务进度展示需要完善的问题。演示前应使用准备好的样本实测。

## 数据与安全

- 仓库不包含本机密钥、数据库、合同、报告、日志和依赖目录。
- 本地部署不等于全部数据都在本地：模型分析会将相关文本发送至所配置的服务，远程 OCR 会处理上传的文件。
- 测试请优先使用脱敏材料，不要直接上传保密合同或个人敏感信息。
- 不要将 `.env`、真实令牌及用户数据提交到仓库。
- 本项目尚不适合直接暴露到公网。

## 技术与目录

后端使用 FastAPI、SQLAlchemy 和 SQLite；前端使用 React、TypeScript、Vite 和 Ant Design。文档处理使用 pypdf、python-docx 等工具，模型调用通过兼容接口接入。

- `backend/app/api/v1/`：合同、招投标、账户和配置接口。
- `backend/app/services/`：审核、提取、报告和清单生成逻辑。
- `backend/app/utils/`：文档处理、OCR 和模型客户端。
- `backend/tests/`：现有自动化测试。
- `frontend/src/pages/`：业务页面。
- `frontend/src/components/`：页面组件。

## 开发检查

后端目录：

```powershell
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
```

前端目录：

```powershell
npm.cmd exec tsc -- --noEmit
npm.cmd run build
```

这些检查不代表真实模型调用、审核质量及全部业务流程已验证。

## 开源来源与许可

本项目在 ContractLens 基础上二次开发，招投标流程参考 Tender Review Kit，合同审核工作流参考 ArchSight AIOS。相关原始版权和许可声明予以保留，不表示获得上游项目的官方背书。

详见 [第三方致谢](THIRD_PARTY_NOTICES.md)、[Tender Review 许可声明](backend/app/services/TENDER_REVIEW_ATTRIBUTION.md) 和 [LICENSE](LICENSE)。
