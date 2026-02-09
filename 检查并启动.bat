@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo 检查并启动服务器
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python！
    echo 请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo [1/4] 检查Python语法...
python 测试服务器.py
if errorlevel 1 (
    echo.
    echo [错误] 代码有语法错误，请检查上面的错误信息
    pause
    exit /b 1
)

echo.
echo [2/4] 检查依赖包...
python -c "import flask_socketio" 2>nul
if errorlevel 1 (
    echo 依赖包未安装，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo [3/4] 检查端口1236是否被占用...
netstat -ano | findstr :1236 >nul
if not errorlevel 1 (
    echo [警告] 端口1236已被占用！
    echo 请关闭占用该端口的程序后重试
    echo.
    echo 按任意键查看占用端口的进程...
    pause >nul
    netstat -ano | findstr :1236
    echo.
    pause
    exit /b 1
)
echo 端口1236可用

echo.
echo [4/4] 启动服务器...
echo ========================================
echo 服务器启动中...
echo 访问地址: http://localhost:1236
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python server_multiplayer.py

echo.
echo 服务器已停止
pause
