# Tretra Trading Station

专业加密货币交易分析平台，集成山寨币筛选、交易回测和模拟交易功能。

## 功能特性

### 山寨币筛选器
- **智能筛选**: 只筛选活跃的 USDT 现货交易对，自动过滤已下架币种
- **多维度评分**: Beta强度(30%) + 成交量(20%) + 技术指标(50%)
- **技术指标**: SMA/EMA 均线系统、MACD 金叉、RSI、布林带
- **多时间周期**: 支持 5m, 15m, 1h, 4h 等周期
- **专业K线图**: 基于 klinecharts，支持指标叠加
- **快速交易**: 按数量或 USDT 金额快速下单
- **自选列表**: 跟踪关注的币种

### 交易回测分析
- **数据导入**: 支持币安、OKX 的 CSV/Excel 交易记录
- **智能聚合**: 自动合并拆单订单（60秒窗口）
- **多维分析**: 胜率、盈亏比、最大回撤、夏普比率
- **可视化**: 盈亏分布、累计收益曲线、持仓时长分析
- **年度筛选**: 按年度和交易对筛选分析
- **Excel导出**: 导出完整分析报告

### 模拟交易
- **自动开仓**: 根据筛选分数自动开仓
- **时间窗口**: 指定交易时段（北京时间 7:30-8:30, 11:30-12:30, 15:30-16:30）
- **止盈止损**: 自动止盈止损管理

### 通知系统
- **多渠道**: 邮件 + Telegram 推送
- **频率控制**: 最小间隔、每日上限、静默时段
- **智能过滤**: 只推送高分机会

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/atxinsky/altcoin-screener.git
cd altcoin-screener

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 3. 启动服务
docker-compose up -d

# 4. 访问
# 前端界面: http://localhost:3080
# API文档:  http://localhost:8001/docs
```

### 本地开发

```bash
# 后端 (Python 3.9+)
pip install -r backend/requirements.txt
python run_backend.py  # 访问 http://localhost:8001

# 前端 (Node.js 18+)
cd frontend && npm install && npm run dev  # 访问 http://localhost:3080

# 回测 (可选)
cd backtest && pip install -r requirements.txt
streamlit run upgraded.py  # 访问 http://localhost:8501
```

## 项目结构

```
├── backend/                # FastAPI 后端
│   ├── app/               # 路由和主应用
│   ├── services/          # 业务逻辑（筛选、通知、监控）
│   └── database/          # SQLAlchemy 模型
├── frontend/              # React + Ant Design 前端
│   └── src/components/    # UI 组件（K线图、筛选面板等）
├── backtest/              # Streamlit 回测分析
├── docker-compose.yml     # 4服务编排
└── .env.example           # 配置模板
```

## 配置说明

### 币安 API（必填）

```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

获取方式: [币安API管理](https://www.binance.com/zh-CN/my/settings/api-management)

| 功能 | 所需权限 |
|------|----------|
| 筛选/监控 | 读取 |
| 快速交易 | 读取 + 现货交易 |

> 建议设置 IP 白名单以提高安全性

### 通知配置（可选）

**邮件 (Gmail)**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # 应用专用密码
EMAIL_TO=recipient@example.com
```

**Telegram**
```env
TELEGRAM_BOT_TOKEN=your_bot_token  # @BotFather 创建
TELEGRAM_CHAT_ID=your_chat_id      # @userinfobot 获取
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3080 | React 主界面 |
| 后端 | 8001 | FastAPI API |
| 回测 | 8501 | Streamlit（嵌入前端） |

## 常用命令

```bash
# 查看日志
docker-compose logs -f backend
docker-compose logs -f monitor

# 重启服务
docker-compose restart backend

# 重新构建
docker-compose up -d --build

# 停止所有服务
docker-compose down
```

## 更新日志

### v1.3 (2025-12-30)
- 通知设置面板（频率控制、静默时段、每日限额）
- 交易时间窗口限制（北京时间）
- 回测支持 Excel 文件和按年度筛选
- K线图北京时间显示修复

### v1.2 (2025-12-29)
- 重命名为 Tretra Trading Station
- 新增 Streamlit 交易回测分析模块
- Docker 4服务编排

### v1.1 (2025-12-28)
- 多周期涨跌幅显示（5m/15m/1h）
- 活跃市场过滤，排除下架币种
- K线图指标优化

### v1.0 (2025-12-27)
- 初始版本：筛选、K线、通知、Docker

## 技术栈

- **后端**: Python 3.9+, FastAPI, SQLAlchemy, CCXT
- **前端**: React 18, Ant Design, klinecharts
- **回测**: Streamlit, Pandas, Plotly
- **数据库**: SQLite
- **部署**: Docker, Docker Compose

## 免责声明

本工具仅用于信息参考，不构成投资建议。加密货币交易具有高风险，请自行承担交易风险。建议使用前充分测试，首次交易小额试水。

## License

MIT
