# 企业级智能知识库问答系统

面向企业内部员工的智能知识库问答系统，支持用户认证、知识库管理，并将逐步加入文档上传、异步解析、向量化、混合检索、RAG 问答和引用来源。

## 第三天状态

已完成文档上传和异步处理：

- 支持 PDF、DOCX、Markdown 和 TXT
- 文件大小和扩展名校验
- 本地上传文件持久化
- Celery + Redis 后台异步处理
- 文档解析、文本清洗和分块
- 文档处理状态查询
- 文档列表、详情和删除
- 任务失败原因记录
- 用户只能访问自己知识库中的文档
- Streamlit 文档上传和状态展示

第三天文档接口：

```text
POST   /api/v1/knowledge-bases/{knowledge_base_id}/documents
GET    /api/v1/knowledge-bases/{knowledge_base_id}/documents
GET    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
GET    /api/v1/jobs/{job_id}
```

支持的文件类型：

```text
.pdf
.docx
.md
.markdown
.txt
```

默认单文件大小限制：20 MB。
## 第二天状态

已完成用户认证和知识库管理：

- 用户注册、登录和 JWT 鉴权
- 当前用户信息接口
- 知识库创建、查询、更新和删除
- 用户资源隔离
- PostgreSQL 表自动初始化
- Streamlit 登录和知识库管理页面
- 认证与权限集成测试

## 第一天状态

已完成项目基础骨架：

- FastAPI API 服务
- PostgreSQL + pgvector
- Redis
- Celery Worker
- Streamlit 前端占位页
- Docker Compose 编排
- 基础环境变量和配置入口
- `/health` 与 `/api/v1/health` 健康检查

## 前置环境

- Windows 11 / WSL2
- Docker Desktop
- Git

## 快速启动

首次使用时复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

首次构建应用镜像（Windows 中文路径使用脚本规避 Docker BuildKit 路径兼容问题）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-image.ps1
```

启动全部服务：

```powershell
docker compose up -d
```

查看状态：

```powershell
docker compose ps
```

停止服务：

```powershell
docker compose down
```

第二天和第三天集成测试（容器内执行）：

```powershell
docker exec -e RUN_DB_TESTS=1 kb-api pytest -q
```

## 服务地址

- API：http://localhost:8000
- Swagger：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc
- Streamlit：http://localhost:8501

健康检查：

```powershell
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8000/api/v1/health
```

## 第二天新增接口

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/knowledge-bases
GET    /api/v1/knowledge-bases
GET    /api/v1/knowledge-bases/{knowledge_base_id}
PATCH  /api/v1/knowledge-bases/{knowledge_base_id}
DELETE /api/v1/knowledge-bases/{knowledge_base_id}
```

## 项目结构

```text
app/       FastAPI 后端和领域模块
frontend/  Streamlit 前端
tests/     自动化测试
scripts/   开发和评测脚本
data/      上传文件、处理结果和示例数据
docs/      架构和项目文档
```

## 开发计划

1. 用户认证和知识库管理
2. 文档上传和异步解析
3. Embedding 与 pgvector
4. 全文检索、混合检索和重排序
5. 严格基于资料的 RAG 问答
6. 评测、测试和项目包装



## 安全说明

- `.env` 只用于本地配置，不提交 API Key。
- 生产环境必须修改 `SECRET_KEY` 和数据库密码。
- 示例资料应使用自拟或已脱敏的内容。

## 第四天状态

已完成向量化和混合检索基础能力：

- `document_chunks` 分块表
- Embedding Provider 适配层
- OpenAI-compatible Embedding API 支持
- 无 API Key 时的离线 Hash Embedding fallback
- pgvector 余弦相似度检索
- PostgreSQL `tsvector` 全文检索
- RRF 混合排序
- HNSW 向量索引和 GIN 全文索引
- 知识库级数据过滤
- 检索结果包含文档来源、分块内容和多个得分

检索接口：

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/search
```

请求示例：

```json
{
  "query": "hotel costs receipts",
  "top_k": 5
}
```

未配置真实 Embedding API 时，系统会使用 `hash-fallback` 保证本地开发和测试可运行；配置 `LLM_API_KEY` 和 `EMBEDDING_MODEL` 后自动切换为 `openai-compatible`。
## 第五天状态

已完成完整 RAG 问答链路：

- 会话、消息和引用数据模型
- Prompt 模板和严格知识库问答规则
- LLM OpenAI-compatible 调用
- 无 API Key 时的抽取式离线回答 fallback
- 基于词项/字符重叠和检索得分的重排序
- 证据门控和无依据拒答
- 回答引用文档分块来源
- 检索、生成和 Trace ID 调试信息
- Streamlit 问答界面和引用展开

问答接口：

```text
POST /api/v1/chat/query
```

当没有足够证据时，接口返回 `grounded=false`，并固定回复：

```text
知识库中未找到足够依据，无法准确回答该问题。
```

配置 `LLM_API_KEY` 和 `LLM_MODEL` 后使用云端模型；未配置时使用 `extractive-fallback`，保证本地演示不依赖外部模型。

## 模型凭证配置

对话模型和 Embedding 模型支持使用不同的 API 凭证：

```env
LLM_BASE_URL=对话模型接口地址
LLM_API_KEY=对话模型API Key
LLM_MODEL=对话模型名称

EMBEDDING_BASE_URL=Embedding接口地址（与对话接口相同可留空）
EMBEDDING_API_KEY=Embedding模型API Key
EMBEDDING_MODEL=Embedding模型名称
```

`.env` 不得提交到仓库；配置后需要重启 `api` 和 `worker` 服务。
