# Tretra Trading Station

专业加密货币交易分析平台 - 山寨币筛选 + 交易回测

## 核心功能

| 功能 | 说明 |
|------|------|
| **山寨币筛选** | 实时筛选高Beta机会，多维度评分系统 |
| **交易回测** | 导入历史交易数据，深度分析表现 |
| **模拟交易** | 自动交易监控，指定时间窗口执行 |
| **通知推送** | 邮件/Telegram 通知，频率可控 |

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入币安 API 密钥

# 2. 启动服务
docker-compose up -d

# 3. 访问
# 前端: http://localhost:3000
# API:  http://localhost:8001/docs
```

### 本地开发

```bash
# 后端
pip install -r backend/requirements.txt
python run_backend.py

# 前端
cd frontend && npm install && npm run dev
```

## 系统架构

```
├── backend/          # FastAPI 后端 (Python 3.9+)
├── frontend/         # React + Ant Design 前端
├── backtest/         # Streamlit 回测分析
├── docker-compose.yml
└── .env.example      # 配置模板
```

## 筛选评分系统

总分 100 分 = Beta(30%) + 成交量(20%) + 技术指标(50%)

- **Beta分数**: 相对 BTC/ETH 的24小时强度
- **成交量分数**: 流动性评估
- **技术分数**: SMA/EMA/MACD/RSI 综合评估

## 配置说明

### 币安 API

```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

- 筛选功能只需「读取」权限
- 快速交易需开启「现货交易」权限
- 建议设置 IP 白名单

### 通知配置

```env
# 邮件
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3000 | React 界面 |
| 后端 | 8001 | FastAPI |
| 回测 | 8501 | Streamlit（嵌入前端） |

## 更新日志

### v1.3 (2025-12-30)
- 通知设置面板（频率控制、静默时段）
- 交易时间窗口限制（北京时间）
- 回测按年度筛选
- K线图北京时间显示
- 文档完善

### v1.2 (2025-12-29)
- 重命名为 Tretra Trading Station
- 新增交易回测分析模块
- Docker 4服务编排

### v1.1 (2025-12-28)
- 多周期涨跌幅显示
- 活跃市场过滤
- K线图优化

### v1.0 (2025-12-27)
- 初始版本发布

## 常用命令

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 重新构建
docker-compose up -d --build

# 停止服务
docker-compose down
```

## 免责声明

本工具仅用于信息参考，不构成投资建议。加密货币交易具有高风险，请自行承担风险。

## License

MIT
