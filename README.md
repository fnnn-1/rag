# 企业级智能知识库问答系统

面向企业内部员工的智能知识库问答系统，计划支持文档上传、异步解析、向量化、混合检索、RAG 问答、引用来源和基础用户权限。

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
2. PDF、Word、Markdown、TXT 文档处理
3. Celery 异步入库
4. Embedding 与 pgvector
5. 全文检索、混合检索和重排序
6. 严格基于资料的 RAG 问答
7. 评测、测试和项目包装

## 安全说明

- `.env` 只用于本地配置，不提交 API Key。
- 生产环境必须修改 `SECRET_KEY` 和数据库密码。
- 示例资料应使用自拟或已脱敏的内容。
