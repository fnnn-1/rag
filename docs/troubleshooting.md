# 常见问题排查

## 1. Docker 无法连接

```text
failed to connect to the docker API
```

处理：启动 Docker Desktop，等待状态稳定后运行：

```powershell
docker info
docker compose up -d
```

## 2. 前端无法连接 API

容器内不能使用 `http://localhost:8000` 访问 API，应使用：

```text
http://api:8000
```

检查：

```powershell
docker exec kb-frontend python -c "import requests; print(requests.get('http://api:8000/health').status_code)"
```

## 3. 向量维度错误

```text
expected N dimensions, not M
```

说明 Embedding 模型输出维度和 `EMBEDDING_DIMENSIONS` 不一致。确认真实维度，更新配置并重新创建 API/Worker 容器。系统会迁移向量列，但历史文档仍需重新向量化。

## 4. 文档一直排队

检查 Worker 和 Redis：

```powershell
docker compose ps
docker compose logs --tail=100 worker
docker exec kb-redis redis-cli ping
```

## 5. 文档处理失败

查看文档错误信息和 Worker 日志。常见原因：

- 扫描 PDF 没有文本层
- 文档为空或损坏
- Embedding API 超时、限流或模型名错误
- Embedding 向量维度配置错误

## 6. RAG 总是拒答

- 确认文档状态为 `completed`。
- 确认文档是在当前 Embedding 模型配置下重新处理的。
- 使用 `/search` 接口检查 Top 5 是否包含正确文档。
- 查看重排序后的文本是否与问题存在明确词项或字符重叠。

## 7. 修改 `.env` 后没有生效

`docker compose restart` 不一定重新载入 Compose 环境变量。使用：

```powershell
docker compose up -d --force-recreate api worker frontend
```

## 8. 安全停止项目

```powershell
docker compose down
```

不要添加 `-v`，否则可能删除数据库和 Redis 数据卷。
