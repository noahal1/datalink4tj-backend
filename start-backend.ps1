# 后端启动脚本
Set-Location -Path $PSScriptRoot
Write-Host "正在启动后端服务..." -ForegroundColor Green
uvicorn main:app --reload --host 0.0.0.0 --port 8000 