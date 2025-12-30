@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     Tretra Trading Station - 一键启动               ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未运行！请先启动Docker Desktop
    echo.
    pause
    exit /b 1
)

echo ✓ Docker正在运行
echo.
echo 正在启动服务...
echo.

REM 启动容器
docker-compose up -d

if errorlevel 1 (
    echo.
    echo ✗ 启动失败！
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║  ✓ 启动成功！                                         ║
echo ║                                                       ║
echo ║  前端界面: http://localhost:3000                      ║
echo ║  后端API:  http://localhost:8001/docs                ║
echo ║                                                       ║
echo ║  查看日志: docker-compose logs -f                     ║
echo ║  停止服务: docker-compose down                        ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
pause
