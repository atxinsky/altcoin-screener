# Docker 部署指南

本文档介绍如何使用Docker部署币安山寨币筛选器。

## 目录

- [为什么使用Docker](#为什么使用docker)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [两种模式](#两种模式)
- [代码修改和热更新](#代码修改和热更新)
- [常用命令](#常用命令)
- [故障排除](#故障排除)

## 为什么使用Docker

✅ **环境一致性**: 无需安装Python、Node.js等依赖，开箱即用
✅ **快速部署**: 一条命令启动所有服务
✅ **易于维护**: 轻松更新、回滚、备份
✅ **隔离性好**: 不影响系统其他应用
✅ **跨平台**: Windows、Linux、Mac统一部署方式

## 前置要求

### 1. 安装Docker

**Windows:**
- 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 启动Docker Desktop
- 确认安装: `docker --version`

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker
```

**Mac:**
- 下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

### 2. 安装Docker Compose

Docker Desktop已包含Docker Compose，Linux用户需单独安装：

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

验证安装:
```bash
docker-compose --version
```

## 快速开始

### 第一次部署

1. **配置环境变量**
   ```bash
   # 复制配置文件
   cp .env.example .env

   # 编辑 .env 文件，填入币安API密钥
   # BINANCE_API_KEY=your_api_key
   # BINANCE_API_SECRET=your_secret
   ```

2. **启动服务**

   **Windows用户:**
   ```cmd
   # 方式1: 使用图形菜单
   双击 docker-start.bat
   选择 [1] 生产模式启动

   # 方式2: 命令行
   docker-compose up -d
   ```

   **Linux/Mac用户:**
   ```bash
   # 方式1: 使用脚本
   chmod +x docker-start.sh
   ./docker-start.sh

   # 方式2: 直接命令
   docker-compose up -d
   ```

3. **访问服务**
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

4. **查看日志**
   ```bash
   # 查看所有服务日志
   docker-compose logs -f

   # 只看后端日志
   docker-compose logs -f backend

   # 只看监控日志
   docker-compose logs -f monitor
   ```

## 两种模式

### 1. 生产模式 (Production)

**特点:**
- 性能优化
- 代码打包到镜像中
- 适合正式运行

**启动:**
```bash
docker-compose up -d
```

**修改代码后需要:**
```bash
# 1. 停止服务
docker-compose down

# 2. 重新构建镜像
docker-compose build

# 3. 重新启动
docker-compose up -d
```

### 2. 开发模式 (Development) ⭐ 推荐用于开发

**特点:**
- ✅ 支持代码热更新
- ✅ 修改Python代码后自动重启
- ✅ 无需重新构建镜像
- ✅ 实时查看修改效果

**启动:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**代码修改流程:**
1. 用编辑器修改 `backend/` 下的任何Python文件
2. 保存文件
3. Docker会自动检测变化并重启服务（1-2秒）
4. 刷新浏览器即可看到效果

**示例:**
```bash
# 1. 启动开发模式
docker-compose -f docker-compose.dev.yml up -d

# 2. 实时查看日志（可以看到自动重启）
docker-compose -f docker-compose.dev.yml logs -f backend

# 3. 修改代码
# 编辑 backend/services/screening_service.py
# 保存后会自动看到:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete

# 4. 停止服务
docker-compose -f docker-compose.dev.yml down
```

## 代码修改和热更新

### 开发模式下的工作流程

开发模式使用了**Volume挂载**技术，将本地代码目录挂载到容器中，实现零延迟的代码同步。

```yaml
# docker-compose.dev.yml 中的关键配置
volumes:
  - ./backend:/app/backend           # 挂载后端代码
  - ./run_backend.py:/app/run_backend.py
  - ./data:/app/data                 # 数据持久化
  - ./charts:/app/charts             # 图表持久化
```

**支持的修改类型:**

✅ **Python代码修改** - 自动重启
```python
# 修改 backend/services/screening_service.py
# 保存后1-2秒自动生效
```

✅ **配置文件修改** - 需手动重启
```bash
# 修改 .env 后
docker-compose -f docker-compose.dev.yml restart
```

✅ **依赖包更新** - 需重新构建
```bash
# 修改 requirements.txt 后
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
```

### 生产模式下的更新流程

```bash
# 1. 修改代码
vim backend/services/screening_service.py

# 2. 停止服务
docker-compose down

# 3. 重新构建（加入新代码）
docker-compose build

# 4. 启动服务
docker-compose up -d

# 或者一条命令搞定：
docker-compose up -d --build
```

### 快捷脚本

**Windows (`docker-start.bat`):**
```cmd
双击运行，选择：
[2] 开发模式启动 (Development - 支持热更新)
```

**Linux/Mac (`docker-start.sh`):**
```bash
./docker-start.sh
选择 [2]
```

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 启动开发模式
docker-compose -f docker-compose.dev.yml up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 日志查看

```bash
# 查看所有日志
docker-compose logs

# 实时跟踪日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f monitor

# 查看最近100行
docker-compose logs --tail=100
```

### 镜像和容器管理

```bash
# 查看运行中的容器
docker-compose ps

# 查看所有容器（包括已停止）
docker ps -a

# 进入容器shell
docker-compose exec backend bash
docker-compose exec monitor bash

# 重新构建镜像
docker-compose build

# 强制重新构建（无缓存）
docker-compose build --no-cache

# 删除容器和网络
docker-compose down

# 删除容器、网络和卷（清除数据）
docker-compose down -v
```

### 数据管理

```bash
# 备份数据库
docker cp altcoin-screener-backend:/app/data/screener.db ./backup/

# 恢复数据库
docker cp ./backup/screener.db altcoin-screener-backend:/app/data/

# 查看容器内文件
docker-compose exec backend ls -la /app/data
```

### 性能监控

```bash
# 查看资源使用
docker stats

# 查看特定容器资源
docker stats altcoin-screener-backend

# 查看容器进程
docker-compose top
```

## 服务架构

```
┌─────────────────────────────────────────┐
│         Docker Network                  │
│  (screener-network)                     │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │   Backend    │  │   Monitor    │   │
│  │   :8000      │  │   Service    │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                  │            │
│         └────────┬─────────┘            │
│                  │                      │
│         ┌────────▼─────────┐           │
│         │  Shared Volumes  │           │
│         │  - data/         │           │
│         │  - charts/       │           │
│         │  - logs/         │           │
│         └──────────────────┘           │
└─────────────────────────────────────────┘
```

## 故障排除

### 1. 端口被占用

**问题:** `Error: bind: address already in use`

**解决:**
```bash
# Windows - 查找占用端口的进程
netstat -ano | findstr :8000

# 杀死进程
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9

# 或修改docker-compose.yml中的端口映射
ports:
  - "8001:8000"  # 改用8001端口
```

### 2. 构建失败

**问题:** 依赖安装失败

**解决:**
```bash
# 清理Docker缓存
docker system prune -a

# 使用国内镜像源（修改Dockerfile）
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# 重新构建
docker-compose build --no-cache
```

### 3. 容器启动后立即退出

**问题:** 查看日志发现错误

**解决:**
```bash
# 查看完整日志
docker-compose logs backend

# 常见原因:
# - .env文件缺失或配置错误
# - 数据库文件权限问题
# - 依赖包版本冲突

# 进入容器调试
docker-compose run --rm backend bash
python run_backend.py
```

### 4. 热更新不工作（开发模式）

**问题:** 修改代码后没有自动重启

**检查:**
```bash
# 1. 确认使用的是dev配置
docker-compose -f docker-compose.dev.yml ps

# 2. 检查volume挂载
docker-compose -f docker-compose.dev.yml exec backend ls -la /app/backend

# 3. 检查uvicorn是否使用--reload参数
docker-compose -f docker-compose.dev.yml logs backend | grep reload

# 4. 重新启动
docker-compose -f docker-compose.dev.yml restart backend
```

### 5. 数据丢失

**问题:** 重启后数据没了

**原因:** 使用了 `docker-compose down -v`（删除了volumes）

**解决:**
```bash
# 停止时不要加 -v 参数
docker-compose down

# 如果已删除，从备份恢复
docker cp ./backup/screener.db altcoin-screener-backend:/app/data/
```

### 6. 内存不足

**问题:** 容器OOM (Out of Memory)

**解决:**
```yaml
# 在docker-compose.yml中限制内存
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

## 高级配置

### 自定义网络

```yaml
networks:
  screener-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### 环境变量覆盖

```bash
# 临时修改环境变量
docker-compose run -e MIN_VOLUME_USD=5000000 backend python run_backend.py
```

### 多实例部署

```bash
# 启动多个后端实例（负载均衡）
docker-compose up -d --scale backend=3
```

### 持久化配置

```yaml
# 使用命名卷代替绑定挂载
volumes:
  screener-data:
    driver: local
  screener-charts:
    driver: local

services:
  backend:
    volumes:
      - screener-data:/app/data
      - screener-charts:/app/charts
```

## 生产环境建议

### 1. 使用环境变量文件

```bash
# .env.prod
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx
LOG_LEVEL=WARNING
UPDATE_INTERVAL=300
```

```bash
# 指定环境文件
docker-compose --env-file .env.prod up -d
```

### 2. 启用自动重启

```yaml
services:
  backend:
    restart: always  # 总是自动重启
```

### 3. 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. 日志轮转

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 总结

### 日常开发流程（推荐）

```bash
# 1. 首次启动
docker-compose -f docker-compose.dev.yml up -d

# 2. 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 3. 修改代码（自动生效）
# 编辑 backend/ 下的文件
# 保存即可，无需手动重启

# 4. 停止服务
docker-compose -f docker-compose.dev.yml down
```

### 生产部署流程

```bash
# 1. 配置环境
cp .env.example .env
vim .env

# 2. 构建并启动
docker-compose up -d --build

# 3. 验证服务
curl http://localhost:8000/health

# 4. 查看日志
docker-compose logs -f

# 5. 更新代码
git pull
docker-compose up -d --build
```

**Docker化后的优势总结:**
- ✅ 代码修改**超简单**：开发模式下保存即生效
- ✅ 环境**超干净**：不污染本地Python环境
- ✅ 部署**超快速**：一条命令搞定
- ✅ 维护**超方便**：重启、回滚、备份都很容易

---

有问题查看 [常见问题](#故障排除) 或提Issue！
