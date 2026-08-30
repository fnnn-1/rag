# API 使用示例

所有业务接口前缀为：

```text
/api/v1
```

## 1. 注册

```powershell
$body = @{
  email = "demo@example.com"
  password = "StrongPassword123!"
  display_name = "演示用户"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/register `
  -ContentType "application/json" -Body $body
```

## 2. 登录并保存 Token

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=demo@example.com&password=StrongPassword123!"

$headers = @{ Authorization = "Bearer $($login.access_token)" }
```

## 3. 创建知识库

```powershell
$kb = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/knowledge-bases `
  -Headers $headers -ContentType "application/json" `
  -Body (@{ name = "员工制度"; description = "企业制度资料" } | ConvertTo-Json)
```

## 4. 上传文档

PowerShell 7：

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/knowledge-bases/$($kb.id)/documents" `
  -Headers $headers `
  -Form @{ file = Get-Item ".\policy.md" }
```

接口返回 HTTP 202 和文档/任务 ID，可通过文档详情或任务接口轮询处理状态。

## 5. 混合检索

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/knowledge-bases/$($kb.id)/search" `
  -Headers $headers -ContentType "application/json" `
  -Body (@{ query = "报销需要哪些材料"; top_k = 5 } | ConvertTo-Json)
```

## 6. RAG 问答

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/chat/query `
  -Headers $headers -ContentType "application/json" `
  -Body (@{
    knowledge_base_id = $kb.id
    question = "员工报销交通费需要什么材料？"
    top_k = 3
  } | ConvertTo-Json)
```

响应包含：

- `answer`：回答正文
- `grounded`：是否有知识库证据
- `citations`：引用片段
- `trace_id`：请求追踪标识
- 检索和生成耗时
