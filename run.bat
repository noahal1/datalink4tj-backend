@echo off
echo 启动 DataLink4TJ 后端服务...

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo 已激活虚拟环境
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
)

REM 启动后端服务
python run.py

REM 如果发生错误，暂停以便查看错误信息
if %ERRORLEVEL% NEQ 0 (
    echo 启动服务时出错，错误代码: %ERRORLEVEL%
    pause
) 