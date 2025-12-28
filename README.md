# 币安山寨币筛选器 (Binance Altcoin Screener)

一个专业的币安现货山寨币筛选系统，用于在BTC/ETH开启季度级别上涨时，抓取高Beta机会。

## 功能特性

### 核心功能
- ✅ **数据存储**: SQLite数据库存储历史K线数据
- ✅ **价格比率分析**: 计算山寨币价格相对BTC/ETH的比率变化
- ✅ **成交量筛选**: 基于24小时成交量过滤低流动性币种
- ✅ **技术指标分析**:
  - SMA (20, 50, 200)
  - EMA (7, 14, 30, 52)
  - MACD 金叉检测
  - RSI 超买超卖
  - 布林带
- ✅ **多时间周期**: 支持 5m, 15m, 1h, 4h 等多个时间级别
- ✅ **价格异动检测**: 实时监测价格突变
- ✅ **K线图表生成**: 自动生成带技术指标和异动标记的K线图
- ✅ **通知系统**: 支持邮件和Telegram推送
- ✅ **Web界面**: 简洁专业的React前端界面
- ✅ **实时监控**: 定时自动筛选和警报

### 筛选评分系统

系统对每个币种进行综合评分 (0-100):

1. **Beta分数 (30%)**: 相对BTC/ETH的强度
2. **成交量分数 (20%)**: 流动性指标
3. **技术分数 (50%)**: 技术指标综合评估
   - 价格在SMA 20之上: +20分
   - MACD金叉: +20分
   - 价格在所有EMA之上: +20分
   - RSI在健康区间(40-70): +20分
   - 成交量激增: +20分

## 系统架构

```
binance-altcoin-screener/
├── backend/                 # Python后端
│   ├── app/                # FastAPI应用
│   │   ├── main.py        # 主应用
│   │   └── routes.py      # API路由
│   ├── database/           # 数据库模型
│   │   ├── models.py      # SQLAlchemy模型
│   │   └── database.py    # 数据库连接
│   ├── services/           # 业务逻辑
│   │   ├── binance_service.py      # 币安API集成
│   │   ├── indicator_service.py    # 技术指标计算
│   │   ├── screening_service.py    # 筛选逻辑
│   │   ├── chart_service.py        # 图表生成
│   │   ├── notification_service.py # 通知服务
│   │   └── monitor_service.py      # 监控服务
│   └── config.py           # 配置管理
├── frontend/               # React前端
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── services/      # API服务
│   │   └── App.jsx        # 主应用
│   └── package.json
├── data/                   # 数据库文件
├── logs/                   # 日志文件
├── charts/                 # 生成的图表
├── run_backend.py         # 启动后端
├── run_monitor.py         # 启动监控
└── README.md
```

## 快速开始

### 1. 安装依赖

#### 后端依赖 (Python 3.8+)

```bash
cd backend
pip install -r requirements.txt
```

#### 前端依赖 (Node.js 16+)

```bash
cd frontend
npm install
```

### 2. 配置

复制 `.env.example` 为 `.env` 并填写配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
# 币安API (必填)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here

# 邮件配置 (可选)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# Telegram配置 (可选)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 筛选阈值
MIN_VOLUME_USD=1000000        # 最小成交量 (默认100万美元)
MIN_PRICE_CHANGE_5M=2.0       # 5分钟最小变动 (默认2%)
MIN_PRICE_CHANGE_15M=3.0      # 15分钟最小变动 (默认3%)
BETA_THRESHOLD=1.2            # Beta阈值
```

### 3. 启动服务

#### 方式一: 启动Web界面 (推荐)

1. **启动后端API**:
```bash
python run_backend.py
```
访问: http://localhost:8000

2. **启动前端**:
```bash
cd frontend
npm run dev
```
访问: http://localhost:3000

#### 方式二: 仅运行监控服务

```bash
python run_monitor.py
```

这将每5分钟自动筛选一次，发现高分机会时发送通知。

### 4. 使用Web界面

1. 打开浏览器访问 `http://localhost:3000`
2. 查看BTC/ETH市场概览
3. 设置筛选参数（时间周期、最小成交量、最小变动）
4. 点击"开始筛选"
5. 查看筛选结果表格
6. 点击"图表"按钮查看K线图

## API文档

启动后端后访问 `http://localhost:8000/docs` 查看完整的API文档。

### 主要API端点

- `GET /api/market-overview` - 获取BTC/ETH市场概览
- `POST /api/screen` - 执行筛选
- `GET /api/top-opportunities` - 获取最佳机会
- `POST /api/chart` - 生成K线图
- `GET /api/indicators/{symbol}` - 获取技术指标
- `GET /api/historical/{symbol}` - 获取历史数据

## 获取币安API密钥

1. 登录币安账户
2. 访问 [API管理](https://www.binance.com/zh-CN/my/settings/api-management)
3. 创建新的API密钥
4. 设置IP白名单 (推荐)
5. 权限设置: 只需要"读取"权限

## 配置Telegram通知

1. 创建Telegram Bot:
   - 在Telegram中搜索 `@BotFather`
   - 发送 `/newbot` 并按提示创建
   - 获取Bot Token

2. 获取Chat ID:
   - 搜索 `@userinfobot`
   - 发送任意消息获取你的Chat ID

3. 将Token和Chat ID填入 `.env` 文件

## 配置邮件通知

### Gmail示例

1. 启用两步验证
2. 生成应用专用密码:
   - Google账户 → 安全性 → 两步验证 → 应用专用密码
3. 在 `.env` 中填入应用密码

## 筛选策略说明

### 1. Beta筛选
计算山寨币价格相对BTC和ETH的比率变化，筛选出涨幅超过BTC/ETH的强势币种。

### 2. 技术指标筛选
- **趋势**: 价格必须在主要均线(SMA/EMA)之上
- **动量**: MACD金叉信号
- **强度**: RSI在健康区间，避免极端超买

### 3. 成交量确认
- 最小24h成交量过滤 (默认100万美元)
- 成交量激增检测 (超过20日均量1.5倍)

### 4. 价格异动
实时检测突然的价格变动，捕捉早期机会。

## 高级功能

### 自定义筛选参数

在Web界面或通过API自定义:
- 时间周期 (5m, 15m, 1h, 4h)
- 最小成交量
- 最小价格变动
- 评分阈值

### 批量生成图表

```python
from backend.services.binance_service import BinanceService
from backend.services.chart_service import ChartService
from backend.services.indicator_service import IndicatorService

binance = BinanceService()
chart_service = ChartService()
indicator_service = IndicatorService()

# 生成图表
df = binance.fetch_ohlcv('BTC/USDT', '1h', 500)
df = indicator_service.calculate_all_indicators(df)
chart_path = chart_service.create_kline_chart(df, 'BTC/USDT', '1h')
```

### 自定义监控间隔

编辑 `.env`:
```env
UPDATE_INTERVAL=300  # 秒 (默认5分钟)
```

## 故障排除

### 1. 币安API错误

**问题**: "API key is invalid"
- 检查API密钥是否正确
- 确认IP白名单设置
- 检查API权限 (需要"读取"权限)

### 2. 图表生成失败

**问题**: Kaleido安装失败
```bash
pip install --upgrade kaleido
```

### 3. 数据库错误

删除并重新创建数据库:
```bash
rm -rf data/screener.db
python run_backend.py  # 自动创建新数据库
```

### 4. 通知发送失败

**邮件**:
- 检查SMTP设置
- 确认应用专用密码正确
- 查看防火墙设置

**Telegram**:
- 验证Bot Token
- 确认Chat ID正确
- 先给Bot发送一条消息激活

## 性能优化

### 减少API调用

- 使用缓存
- 合理设置监控间隔
- 仅筛选活跃币种

### 数据库优化

定期清理旧数据:
```sql
DELETE FROM klines WHERE timestamp < datetime('now', '-30 days');
DELETE FROM screening_results WHERE timestamp < datetime('now', '-7 days');
```

## 安全建议

1. ✅ 使用只读API密钥
2. ✅ 设置IP白名单
3. ✅ 不要提交 `.env` 文件到版本控制
4. ✅ 定期更换API密钥
5. ✅ 使用HTTPS (生产环境)

## 免责声明

⚠️ **本工具仅用于信息参考，不构成投资建议。**

- 加密货币交易具有高风险
- 过往表现不代表未来结果
- 请自行承担交易风险
- 建议在使用前充分测试和理解系统

## 开发者

如需定制开发或技术支持，请联系开发者。

## 许可证

MIT License

---

**祝交易顺利！记得做好风险管理。** 🚀
