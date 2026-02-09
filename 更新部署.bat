@echo off
chcp 65001 >nul
echo ========================================
echo 推送更新到 GitHub 和 Render
echo ========================================
echo.

echo [1/3] 添加修改的文件...
git add .

echo [2/3] 创建提交...
git commit -m "修复静态文件路径问题"

echo [3/3] 推送到 GitHub...
git push

if errorlevel 1 (
    echo.
    echo 错误：推送失败
    echo 如果是第一次推送，请先运行"快速部署.bat"
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 成功推送到 GitHub！
echo ========================================
echo.
echo Render 会自动检测到更新并重新部署
echo 请等待 3-5 分钟后刷新网页
echo.
echo 管理员密码：admin123
echo.
pause
