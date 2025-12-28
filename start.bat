@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════╗
echo ║     币安山寨币筛选器 - 快速启动                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1] 启动后端API服务器
echo [2] 启动监控服务 (定时筛选+通知)
echo [3] 同时启动后端和监控
echo [4] 退出
echo.

set /p choice="请选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 正在启动后端API服务器...
    python run_backend.py
) else if "%choice%"=="2" (
    echo.
    echo 正在启动监控服务...
    python run_monitor.py
) else if "%choice%"=="3" (
    echo.
    echo 正在启动后端和监控服务...
    start "Backend API" python run_backend.py
    timeout /t 2 >nul
    start "Monitor Service" python run_monitor.py
    echo.
    echo 两个服务已在新窗口启动！
    echo.
    pause
) else if "%choice%"=="4" (
    exit
) else (
    echo 无效选择，请重新运行
    pause
)
