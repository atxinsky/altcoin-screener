@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     币安山寨币筛选器 - Docker启动菜单                ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1] 生产模式启动 (Production)
echo [2] 开发模式启动 (Development - 支持热更新)
echo [3] 仅启动后端
echo [4] 仅启动监控
echo [5] 停止所有服务
echo [6] 查看日志
echo [7] 重新构建镜像
echo [8] 清理所有容器和数据
echo [9] 退出
echo.

set /p choice="请选择 (1-9): "

if "%choice%"=="1" goto production
if "%choice%"=="2" goto development
if "%choice%"=="3" goto backend_only
if "%choice%"=="4" goto monitor_only
if "%choice%"=="5" goto stop_all
if "%choice%"=="6" goto view_logs
if "%choice%"=="7" goto rebuild
if "%choice%"=="8" goto cleanup
if "%choice%"=="9" goto exit_menu
goto invalid_choice

:production
    echo.
    echo [步骤 1/3] 检查Docker是否运行...
    docker version >nul 2>&1
    if errorlevel 1 (
        echo ✗ Docker未运行！请先启动Docker Desktop
        pause
        goto end
    )
    echo ✓ Docker正在运行

    echo.
    echo [步骤 2/3] 检查配置文件...
    if not exist .env (
        echo ✗ 未找到.env配置文件！
        echo 请先运行: copy .env.example .env
        echo 然后编辑.env文件填入API密钥
        pause
        goto end
    )
    echo ✓ 配置文件存在

    echo.
    echo [步骤 3/3] 正在启动生产模式...
    docker-compose up -d

    if errorlevel 1 (
        echo.
        echo ✗ 启动失败！请查看上方错误信息
        pause
        goto end
    )

    echo.
    echo ✓ 服务已启动！
    echo.
    echo   后端API: http://localhost:8000
    echo   API文档: http://localhost:8000/docs
    echo.
    echo 查看日志: docker-compose logs -f
    echo 停止服务: docker-compose down
    echo.
    pause
    goto end

:development
    echo.
    echo [步骤 1/3] 检查Docker是否运行...
    docker version >nul 2>&1
    if errorlevel 1 (
        echo ✗ Docker未运行！请先启动Docker Desktop
        pause
        goto end
    )
    echo ✓ Docker正在运行

    echo.
    echo [步骤 2/3] 检查配置文件...
    if not exist .env (
        echo ✗ 未找到.env配置文件！
        echo 请先运行: copy .env.example .env
        echo 然后编辑.env文件填入API密钥
        pause
        goto end
    )
    echo ✓ 配置文件存在

    echo.
    echo [步骤 3/3] 正在启动开发模式 (支持代码热更新)...
    docker-compose -f docker-compose.dev.yml up -d

    if errorlevel 1 (
        echo.
        echo ✗ 启动失败！请查看上方错误信息
        pause
        goto end
    )

    echo.
    echo ✓ 开发环境已启动！
    echo.
    echo   后端API: http://localhost:8000
    echo   代码修改后会自动重启
    echo.
    echo 查看日志: docker-compose -f docker-compose.dev.yml logs -f
    echo 停止服务: docker-compose -f docker-compose.dev.yml down
    echo.
    pause
    goto end

:backend_only
    echo.
    echo 正在启动后端服务...
    docker-compose up -d backend
    if errorlevel 1 (
        echo ✗ 启动失败
        pause
        goto end
    )
    echo ✓ 后端服务已启动！
    pause
    goto end

:monitor_only
    echo.
    echo 正在启动监控服务...
    docker-compose up -d monitor
    if errorlevel 1 (
        echo ✗ 启动失败
        pause
        goto end
    )
    echo ✓ 监控服务已启动！
    pause
    goto end

:stop_all
    echo.
    echo 正在停止所有服务...
    docker-compose down
    docker-compose -f docker-compose.dev.yml down
    echo ✓ 所有服务已停止！
    pause
    goto end

:view_logs
    echo.
    echo [1] 查看后端日志
    echo [2] 查看监控日志
    echo [3] 查看所有日志
    echo.
    set /p log_choice="选择: "

    if "%log_choice%"=="1" (
        docker-compose logs -f backend
    ) else if "%log_choice%"=="2" (
        docker-compose logs -f monitor
    ) else if "%log_choice%"=="3" (
        docker-compose logs -f
    ) else (
        echo 无效选择
        pause
    )
    goto end

:rebuild
    echo.
    echo 正在重新构建镜像...
    docker-compose build --no-cache
    if errorlevel 1 (
        echo ✗ 构建失败
        pause
        goto end
    )
    echo ✓ 镜像构建完成！
    pause
    goto end

:cleanup
    echo.
    echo ╔═══════════════════════════════════════════════════════╗
    echo ║  ⚠️  警告: 这将删除所有容器、镜像和数据！            ║
    echo ╚═══════════════════════════════════════════════════════╝
    echo.
    set /p confirm="确认删除? (yes/no): "
    if "%confirm%"=="yes" (
        docker-compose down -v
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -af
        echo ✓ 清理完成！
    ) else (
        echo 已取消
    )
    pause
    goto end

:exit_menu
    exit /b 0

:invalid_choice
    echo.
    echo 无效选择，请重新运行
    pause
    goto end

:end
    exit /b 0
