#!/bin/bash

# Docker启动脚本 (Linux/Mac)

echo "╔═══════════════════════════════════════════════════════╗"
echo "║     币安山寨币筛选器 - Docker启动菜单                ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo

echo "[1] 生产模式启动 (Production)"
echo "[2] 开发模式启动 (Development - 支持热更新)"
echo "[3] 仅启动后端"
echo "[4] 仅启动监控"
echo "[5] 停止所有服务"
echo "[6] 查看日志"
echo "[7] 重新构建镜像"
echo "[8] 清理所有容器和数据"
echo "[9] 退出"
echo

read -p "请选择 (1-9): " choice

case $choice in
    1)
        echo
        echo "正在启动生产模式..."
        docker-compose up -d
        echo
        echo "✓ 服务已启动！"
        echo "  后端API: http://localhost:8000"
        echo "  API文档: http://localhost:8000/docs"
        echo
        echo "查看日志: docker-compose logs -f"
        ;;
    2)
        echo
        echo "正在启动开发模式 (支持代码热更新)..."
        docker-compose -f docker-compose.dev.yml up -d
        echo
        echo "✓ 开发环境已启动！"
        echo "  后端API: http://localhost:8000"
        echo "  代码修改后会自动重启"
        echo
        echo "查看日志: docker-compose -f docker-compose.dev.yml logs -f"
        ;;
    3)
        echo
        echo "正在启动后端服务..."
        docker-compose up -d backend
        echo "✓ 后端服务已启动！"
        ;;
    4)
        echo
        echo "正在启动监控服务..."
        docker-compose up -d monitor
        echo "✓ 监控服务已启动！"
        ;;
    5)
        echo
        echo "正在停止所有服务..."
        docker-compose down
        docker-compose -f docker-compose.dev.yml down
        echo "✓ 所有服务已停止！"
        ;;
    6)
        echo
        echo "[1] 查看后端日志"
        echo "[2] 查看监控日志"
        echo "[3] 查看所有日志"
        read -p "选择: " log_choice

        case $log_choice in
            1) docker-compose logs -f backend ;;
            2) docker-compose logs -f monitor ;;
            3) docker-compose logs -f ;;
        esac
        ;;
    7)
        echo
        echo "正在重新构建镜像..."
        docker-compose build --no-cache
        echo "✓ 镜像构建完成！"
        ;;
    8)
        echo
        echo "⚠️  警告: 这将删除所有容器、镜像和数据！"
        read -p "确认删除? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            docker-compose down -v
            docker-compose -f docker-compose.dev.yml down -v
            docker system prune -af
            echo "✓ 清理完成！"
        fi
        ;;
    9)
        exit 0
        ;;
    *)
        echo "无效选择"
        ;;
esac
