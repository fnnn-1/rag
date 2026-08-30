# 最终验收清单

## 功能

- [x] 用户注册、登录和 JWT 鉴权
- [x] 用户知识库数据隔离
- [x] PDF、DOCX、Markdown、TXT 上传
- [x] Celery 异步文档处理
- [x] 文本清洗、分块和向量化
- [x] pgvector 向量检索
- [x] PostgreSQL 全文检索
- [x] RRF 融合与证据重排序
- [x] 严格 RAG 问答与引用
- [x] 知识库外问题拒答
- [x] 会话、消息和引用持久化
- [x] Streamlit 完整演示界面

## 工程质量

- [x] Docker Compose 一键运行
- [x] 环境变量模板与密钥隔离
- [x] 健康检查、请求 ID 和结构化日志
- [x] 安全响应头和 CORS 配置
- [x] 自动化测试
- [x] 标准评测数据集和报告
- [x] README、架构、部署、API 和排错文档

## 验收命令

```powershell
docker compose ps
docker exec -e RUN_DB_TESTS=1 kb-api pytest -q
docker exec kb-api python scripts/evaluate_rag.py --skip-prepare
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health/ready
```

## 发布前人工确认

- [ ] 公开仓库中不存在真实密钥和私有资料
- [ ] README 中的评测指标注明数据集范围
- [ ] 项目截图不包含邮箱、Token、API Key 或内部文件
- [ ] 云服务器使用 HTTPS、强密钥和数据库备份
