@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo 安装Python依赖包
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo.
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo 检测到Python版本:
python --version
echo.

echo 正在安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 安装失败！
    echo.
    echo 可能的解决方法:
    echo 1. 检查网络连接
    echo 2. 尝试使用: pip install --user -r requirements.txt
    echo 3. 使用国内镜像: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行 "启动多人服务器.bat" 来启动服务器
echo.
pause
