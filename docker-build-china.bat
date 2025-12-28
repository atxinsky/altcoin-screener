@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     使用国内镜像源构建Docker镜像                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo 说明: 此脚本已配置国内镜像源，适合中国大陆用户
echo.
echo 使用的镜像源:
echo   - Debian APT: 阿里云镜像
echo   - Python pip: 清华大学镜像
echo   - Node npm: 淘宝镜像
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo [1/3] 清理旧的构建缓存...
docker builder prune -f
echo ✓ 缓存已清理

echo.
echo [2/3] 开始构建镜像（首次构建约需5-10分钟）...
echo.

REM 构建后端镜像
echo ▶ 正在构建后端镜像...
docker-compose build --no-cache backend
if errorlevel 1 (
    echo.
    echo ✗ 后端镜像构建失败！
    echo.
    echo 可能的原因:
    echo 1. 网络仍然不稳定，请重试
    echo 2. Docker磁盘空间不足
    echo 3. requirements.txt中某个包版本问题
    echo.
    echo 查看详细错误信息后，可以尝试:
    echo - 重新运行此脚本
    echo - 检查网络连接
    echo - 运行: docker system df 检查磁盘空间
    echo.
    pause
    exit /b 1
)
echo ✓ 后端镜像构建成功

echo.
echo ▶ 正在构建监控服务镜像...
docker-compose build --no-cache monitor
if errorlevel 1 (
    echo.
    echo ✗ 监控服务镜像构建失败！
    pause
    exit /b 1
)
echo ✓ 监控服务镜像构建成功

echo.
echo [3/3] 验证镜像...
docker images | findstr altcoin-screener
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║  ✓ 构建完成！                                         ║
echo ║                                                       ║
echo ║  现在可以运行:                                        ║
echo ║    docker-compose up -d                               ║
echo ║  或使用:                                              ║
echo ║    快速启动Docker.bat                                 ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
pause
