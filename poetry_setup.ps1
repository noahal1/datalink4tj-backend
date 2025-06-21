# Poetry完整安装脚本
Write-Host "开始Datalink4TJ后端项目安装..." -ForegroundColor Green

# 工作目录，确保后续命令都在正确的目录执行
$scriptPath = $PSScriptRoot
Set-Location $scriptPath

# 1. 移除旧的虚拟环境（如果存在）
if (Test-Path -Path ".\.venv") {
    Write-Host "移除现有虚拟环境..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".\.venv"
}

# 2. 清除缓存的Poetry锁文件
if (Test-Path -Path "poetry.lock") {
    Write-Host "移除Poetry锁文件..." -ForegroundColor Yellow
    Remove-Item -Force "poetry.lock"
}

# 3. 创建新的虚拟环境
Write-Host "创建新的虚拟环境..." -ForegroundColor Yellow
poetry env use python

# 4. 安装依赖
Write-Host "安装项目依赖..." -ForegroundColor Yellow
poetry install --no-root

# 5. 安装当前项目
Write-Host "安装当前项目..." -ForegroundColor Yellow
poetry install

Write-Host "安装完成！" -ForegroundColor Green
Write-Host "可通过以下命令运行项目：" -ForegroundColor Cyan
Write-Host "  poetry run dev    # 开发模式" -ForegroundColor White
Write-Host "  poetry run start  # 生产模式" -ForegroundColor White 