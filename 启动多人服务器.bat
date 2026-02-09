@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo 多人实时模拟交易平台服务器
echo 端口: 1236
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] 检查Python环境...
python --version

echo.
echo [2/3] 检查依赖包...
python -c "import flask_socketio" 2>nul
if errorlevel 1 (
    echo 依赖包未安装，正在安装...
    echo 这可能需要几分钟，请耐心等待...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败！
        echo 请手动运行: pip install -r requirements.txt
        echo 或双击运行 "安装依赖.bat"
        echo.
        pause
        exit /b 1
    )
    echo 依赖安装完成！
) else (
    echo 依赖包已安装
)

echo.
echo [3/3] 启动服务器...
echo.
echo ========================================
echo 服务器启动成功！
echo 访问地址: http://localhost:1236
echo 局域网访问: http://[您的IP地址]:1236
echo ========================================
echo.
echo 提示: 保持此窗口打开，关闭窗口将停止服务器
echo 按 Ctrl+C 可以停止服务器
echo.
echo ========================================
echo.

python server_multiplayer.py

echo.
echo 服务器已停止
pause
