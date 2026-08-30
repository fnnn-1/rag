# 部署说明

## 1. 本地 Docker 部署

### 前置条件

- Windows 11 + WSL2，或 Linux/macOS
- Docker Desktop / Docker Engine
- Docker Compose V2
- 可选的 OpenAI-compatible Chat 与 Embedding 服务

### 启动

```powershell
Set-Location "D:\项目\项目5"
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\build-image.ps1
docker compose up -d
```

如果 `.env` 已存在，不要覆盖它。

### 验证

```powershell
docker compose ps
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health/live
Invoke-WebRequest -UseBasicParsing http://localhost:8000/api/v1/health/ready
```

访问：

```text
Streamlit  http://localhost:8501
Swagger    http://localhost:8000/docs
ReDoc      http://localhost:8000/redoc
```

### 停止

```powershell
docker compose down
```

不要执行 `docker compose down -v`，除非明确希望删除数据库和 Redis 数据卷。

## 2. 云服务器部署建议

推荐服务器最低配置：

```text
2 vCPU / 4 GB RAM / 40 GB SSD
Ubuntu 24.04 LTS
```

生产部署建议：

1. 安装 Docker Engine 与 Compose 插件。
2. 克隆仓库并创建只读权限严格的 `.env`。
3. 不对公网暴露 PostgreSQL 5432 和 Redis 6379。
4. 仅由 Nginx 代理 API 和 Streamlit。
5. 配置 HTTPS、日志轮转和每日数据库备份。
6. 将默认密码、JWT 密钥全部替换为随机强密钥。
7. 关闭 FastAPI `--reload` 并使用多 Worker 生产启动方式。

示例 Nginx 反向代理：

```nginx
server {
    listen 443 ssl http2;
    server_name kb.example.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Request-ID $request_id;
    }

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 3. 数据备份

```powershell
docker exec kb-db pg_dump -U knowledge_base -d knowledge_base -Fc -f /tmp/knowledge_base.dump
docker cp kb-db:/tmp/knowledge_base.dump .\knowledge_base.dump
```

恢复前应先在隔离环境验证备份文件，避免直接覆盖生产数据库。
