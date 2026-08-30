$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

Write-Host "[1/5] Docker services"
docker compose ps

Write-Host "[2/5] Health checks"
Invoke-RestMethod http://localhost:8000/api/v1/health/live | ConvertTo-Json -Compress
Invoke-RestMethod http://localhost:8000/api/v1/health/ready | ConvertTo-Json -Compress

Write-Host "[3/5] Automated tests"
docker exec -e RUN_DB_TESTS=1 kb-api pytest -q

Write-Host "[4/5] RAG evaluation"
docker exec kb-api python scripts/evaluate_rag.py --skip-prepare

Write-Host "[5/5] Secret scan and Git whitespace check"
python scripts/security_scan.py
git diff --check

Write-Host "Final acceptance completed."
