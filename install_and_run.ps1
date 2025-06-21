# Datalink4TJ后端安装和运行脚本
Write-Host "正在安装并运行Datalink4TJ后端..." -ForegroundColor Green

# 确保Poetry已安装
if (!(Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "正在安装Poetry..." -ForegroundColor Yellow
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
}

# 安装依赖
Write-Host "正在安装依赖..." -ForegroundColor Yellow
poetry install

# 运行应用
Write-Host "启动应用..." -ForegroundColor Green
poetry run dev 