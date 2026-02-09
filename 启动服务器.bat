@echo off
cd /d "%~dp0"
echo ========================================
echo 正在启动模拟交易平台服务器...
echo 端口: 1236
echo ========================================
echo.
python -m http.server 1236
pause
