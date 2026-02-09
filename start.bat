@echo off
chcp 65001 >nul
echo 正在启动模拟交易平台服务器...
echo.
python server.py
pause
