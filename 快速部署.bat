@echo off
chcp 65001 >nul
echo ========================================
echo 多人交易平台 - 快速部署到 GitHub
echo ========================================
echo.

echo [1/5] 初始化 Git 仓库...
git init
if errorlevel 1 (
    echo 错误：Git 初始化失败，请确保已安装 Git
    pause
    exit /b 1
)

echo [2/5] 添加所有文件...
git add .

echo [3/5] 创建提交...
git commit -m "Initial commit - 多人交易平台"

echo [4/5] 设置主分支...
git branch -M main

echo.
echo ========================================
echo 接下来请手动完成以下步骤：
echo ========================================
echo.
echo 1. 访问 https://github.com/new 创建新仓库
echo 2. 仓库名称建议：traders0123
echo 3. 不要勾选任何初始化选项（README、.gitignore等）
echo 4. 创建后，复制仓库地址（例如：https://github.com/你的用户名/traders0123.git）
echo.
set /p repo_url="请粘贴你的 GitHub 仓库地址: "

echo.
echo [5/5] 推送到 GitHub...
git remote add origin %repo_url%
git push -u origin main

if errorlevel 1 (
    echo.
    echo 错误：推送失败，可能需要配置 GitHub 认证
    echo 请参考：https://docs.github.com/zh/authentication
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 成功推送到 GitHub！
echo ========================================
echo.
echo 下一步：部署到 Render
echo.
echo 1. 访问 https://render.com/ 并登录
echo 2. 点击 "New +" → "Web Service"
echo 3. 连接你的 GitHub 仓库
echo 4. 配置：
echo    - Environment: Python 3
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: python server_multiplayer.py
echo    - Plan: Free
echo 5. 点击 "Create Web Service"
echo.
echo 详细说明请查看：部署指南.md
echo.
pause
