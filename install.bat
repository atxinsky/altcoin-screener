@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════╗
echo ║     币安山寨币筛选器 - 安装脚本                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python！请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/3] 安装Python依赖包...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo 警告: 部分包安装失败，可能会影响功能
)

echo.
echo [3/3] 检查配置文件...
if not exist .env (
    echo 未找到 .env 配置文件
    echo 正在复制 .env.example 为 .env ...
    copy .env.example .env
    echo.
    echo ⚠️  请编辑 .env 文件，填入你的币安API密钥！
    echo.
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║     安装完成！                                        ║
echo ║                                                       ║
echo ║  下一步:                                              ║
echo ║  1. 编辑 .env 文件，填入币安API密钥                   ║
echo ║  2. 运行 start.bat 启动服务                           ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
pause
