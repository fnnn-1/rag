# 系统架构说明

![系统总体架构](images/system-architecture.svg)

## 1. 组件职责

| 组件 | 职责 |
|---|---|
| Streamlit | 登录、知识库管理、文档上传、聊天与评测展示 |
| FastAPI | REST API、JWT 鉴权、用户数据隔离、请求追踪 |
| PostgreSQL | 用户、知识库、文档、会话、消息和引用数据 |
| pgvector | 文档分块向量存储与余弦相似度检索 |
| PostgreSQL FTS | `tsvector` 全文检索与 GIN 索引 |
| Redis | Celery Broker 和任务结果后端 |
| Celery Worker | 文档解析、分块、Embedding 和索引入库 |
| Chat Model | 基于检索上下文生成有引用的回答 |
| Embedding Model | 文档分块和用户问题向量化 |

## 2. RAG 数据流

![RAG 流程](images/rag-flow.svg)

1. 文档上传接口保存原文件并创建异步任务。
2. Celery Worker 解析 PDF、DOCX、Markdown 或 TXT。
3. 文本经过清洗和重叠分块后调用 Embedding 服务。
4. 分块、向量和全文索引写入 PostgreSQL/pgvector。
5. 问答时同时执行向量检索和全文检索。
6. RRF 融合候选结果，再结合词项重叠进行重排序。
7. 证据门控过滤弱相关片段；证据不足时直接拒答。
8. 证据充分时构造严格 Prompt，调用聊天模型并返回引用。
9. 会话、消息、引用、Trace ID 和耗时持久化。

## 3. 数据隔离

所有知识库资源都通过当前 JWT 用户过滤：

```text
User -> KnowledgeBase -> Document -> DocumentChunk
                  -> Conversation -> Message -> MessageCitation
```

接口在读取、修改或删除资源前都会验证知识库所有者，其他用户访问时统一返回 404，避免泄露资源是否存在。

## 4. 扩展方向

- 将本地文件存储替换为 MinIO、S3 或 OSS。
- 将 Celery Worker 横向扩容并拆分解析、Embedding 队列。
- 使用独立 Reranker 模型替换当前可解释重排序规则。
- 增加组织、部门、角色与知识库级 ACL。
- 增加 OpenTelemetry、Prometheus 和集中日志平台。
