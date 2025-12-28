@echo off
chcp 65001 >nul
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║     Docker环境检查                                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1/5] 检查Docker是否安装...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未安装！
    echo.
    echo 请下载并安装Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
) else (
    docker --version
    echo ✓ Docker已安装
)

echo.
echo [2/5] 检查Docker是否运行...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未运行！
    echo.
    echo 请启动Docker Desktop，然后重新运行此脚本
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Docker正在运行
)

echo.
echo [3/5] 检查docker-compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ✗ docker-compose未安装！
    echo Docker Desktop应该包含docker-compose
    pause
    exit /b 1
) else (
    docker-compose --version
    echo ✓ docker-compose可用
)

echo.
echo [4/5] 检查配置文件...
if not exist .env (
    echo ✗ 未找到.env配置文件！
    echo.
    echo 解决方法:
    echo   1. copy .env.example .env
    echo   2. 用记事本编辑.env文件
    echo   3. 填入你的币安API密钥
    echo.

    set /p create_env="是否现在创建.env文件? (y/n): "
    if /i "%create_env%"=="y" (
        copy .env.example .env
        echo ✓ 已创建.env文件
        echo.
        echo 请编辑.env文件填入API密钥，然后重新运行
        notepad .env
    )
    pause
    exit /b 1
) else (
    echo ✓ .env文件存在

    REM 检查是否填写了API密钥
    findstr /C:"your_binance_api_key_here" .env >nul
    if not errorlevel 1 (
        echo ⚠️  警告: API密钥尚未配置
        echo 请编辑.env文件填入真实的API密钥
        echo.
        set /p edit_env="是否现在编辑? (y/n): "
        if /i "%edit_env%"=="y" (
            notepad .env
        )
    ) else (
        echo ✓ API密钥已配置
    )
)

echo.
echo [5/5] 检查Docker镜像...
docker images | findstr altcoin-screener >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到项目镜像，首次启动需要构建
    echo 这可能需要几分钟时间
) else (
    echo ✓ 项目镜像已存在
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║  ✓ 环境检查完成！                                     ║
echo ║                                                       ║
echo ║  准备就绪，可以运行 docker-start.bat 启动服务        ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
pause
