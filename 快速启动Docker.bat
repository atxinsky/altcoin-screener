@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     Tretra Trading Station - 快速启动               ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM 1. 检查Docker
echo [1/4] 检查Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未运行！
    echo.
    echo 请先启动Docker Desktop，然后重新运行此脚本
    echo.
    pause
    exit /b 1
)
echo ✓ Docker正在运行

REM 2. 检查.env
echo.
echo [2/4] 检查配置...
if not exist .env (
    echo ⚠️  创建配置文件...
    copy .env.example .env >nul
    echo.
    echo ⚠️  请先配置API密钥！
    echo.
    notepad .env
    echo.
    echo 配置完成后按任意键继续...
    pause >nul
)

REM 3. 检查镜像是否存在
echo.
echo [3/4] 检查镜像...
docker images | findstr altcoin-screener-backend >nul 2>&1
if errorlevel 1 (
    echo ⚠️  首次运行，需要构建镜像（约需2-5分钟）...
    echo.
    docker-compose build
    if errorlevel 1 (
        echo.
        echo ✗ 构建失败！请检查网络连接
        pause
        exit /b 1
    )
)
echo ✓ 镜像已就绪

REM 4. 启动服务
echo.
echo [4/4] 启动服务...
echo.
echo 选择模式:
echo [1] 开发模式 (推荐 - 代码自动更新)
echo [2] 生产模式
echo.
set /p mode="请选择 (1/2): "

if "%mode%"=="1" (
    echo.
    echo 正在启动开发模式...
    docker-compose -f docker-compose.dev.yml up -d
) else (
    echo.
    echo 正在启动生产模式...
    docker-compose up -d
)

if errorlevel 1 (
    echo.
    echo ✗ 启动失败！
    echo.
    echo 常见原因:
    echo - 端口8000已被占用
    echo - 配置文件错误
    echo.
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║  ✓ 启动成功！                                         ║
echo ║                                                       ║
echo ║  前端界面: http://localhost:3000                       ║
echo ║  后端API: http://localhost:8001/docs                  ║
echo ║                                                       ║
echo ║  查看日志: docker-compose logs -f                     ║
echo ║  停止服务: docker-compose down                        ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM 等待服务启动
echo 等待服务启动...
timeout /t 5 /nobreak >nul

REM 健康检查
echo.
echo 测试连接...
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  服务可能还在启动中，请稍等片刻
    echo.
    echo 运行以下命令查看启动进度:
    echo   docker-compose logs -f backend
) else (
    echo ✓ 服务运行正常！
    echo.
    echo 现在可以打开浏览器访问: http://localhost:3000
)

echo.
pause
