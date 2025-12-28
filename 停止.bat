@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     币安山寨币筛选器 - 停止服务                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

docker-compose down

echo.
echo ✓ 服务已停止
echo.
pause
