# Tretra Trading Station

一个专业的加密货币交易分析平台，集成币安现货山寨币筛选和历史交易回测分析功能。

## 平台简介

Tretra Trading Station 是一个全方位的加密货币交易工具，包含两大核心功能：

1. **山寨币筛选器**: 实时筛选高Beta机会，用于在BTC/ETH开启季度级别上涨时，抓取强势山寨币
2. **交易回测分析**: 导入历史交易数据，进行深度分析和可视化，优化交易策略

## 功能特性

### 界面导航
- ✅ **统一入口**: 顶部导航栏一键切换筛选器和回测分析
- ✅ **全屏显示**: 回测分析界面全屏展示，优化数据可视化体验

### 山寨币筛选器功能
- ✅ **智能筛选**: 只筛选活跃的USDT现货交易对，自动过滤已下架币种
- ✅ **数据存储**: SQLite数据库存储历史K线数据，带数据新鲜度验证
- ✅ **价格比率分析**: 计算山寨币价格相对BTC/ETH的24小时比率变化
- ✅ **多维度涨跌幅**: 实时显示5分钟、15分钟、1小时、4小时涨跌幅
- ✅ **成交量筛选**: 基于24小时成交量过滤低流动性币种
- ✅ **技术指标分析**:
  - SMA (20, 50, 200)
  - EMA (7, 14, 30, 52)
  - MACD 金叉检测
  - RSI 超买超卖
  - 布林带
- ✅ **多时间周期**: 支持 5m, 15m, 1h, 4h 等多个时间级别
- ✅ **价格异动检测**: 实时监测价格突变
- ✅ **专业K线图表**: 基于klinecharts v9.8.5，优化的指标管理，无重复显示
- ✅ **快速交易**: 支持按数量或USDT金额快速下单（市价单）
- ✅ **自选列表**: 添加/移除自选币种，快速跟踪关注标的
- ✅ **通知系统**: 支持邮件和Telegram推送
- ✅ **Web界面**: 简洁专业的React前端界面
- ✅ **实时监控**: 定时自动筛选和警报
- ✅ **Docker部署**: 一键启动，环境隔离

### 交易回测分析功能
- ✅ **CSV数据导入**: 支持从币安、OKX等交易所导入历史交易数据
- ✅ **智能订单聚合**: 自动合并时间相近的拆单订单（60秒窗口，1%价格容差），显示真实交易次数
- ✅ **历史记录管理**: 启动时自动显示最近3次分析记录，一键加载无需重复上传CSV
- ✅ **数据持久化**: 导入的交易数据和分析结果存储到SQLite数据库
- ✅ **多维度分析**: 胜率、盈亏比、最大回撤、夏普比率等专业指标
- ✅ **交易可视化**: 盈亏分布图、累计收益曲线、持仓时长分析
- ✅ **分时段统计**: 按日期、按币种、按交易对分析表现
- ✅ **实时K线对比**: 结合历史交易点位与实时K线图表分析
- ✅ **Excel导出**: 分析结果可导出为Excel文件

### 筛选评分系统

系统对每个币种进行综合评分 (0-100):

1. **Beta分数 (30%)**: 相对BTC/ETH的24小时强度
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
│   │   │   ├── ResultsTable.jsx    # 筛选结果表格
│   │   │   ├── KlineChart.jsx      # K线图表组件
│   │   │   ├── Dashboard.jsx       # 仪表盘
│   │   │   └── ...
│   │   ├── services/      # API服务
│   │   └── App.jsx        # 主应用（含导航）
│   └── package.json
├── backtest/               # 交易回测分析
│   ├── upgraded.py        # Streamlit回测应用
│   ├── .streamlit/        # Streamlit配置
│   └── Trade data/        # 交易数据目录
├── data/                   # 数据库和数据文件
├── logs/                   # 日志文件
├── charts/                 # 生成的图表
├── docker-compose.yml      # Docker编排（4个服务）
├── Dockerfile.backend      # 后端容器
├── Dockerfile.frontend     # 前端容器
├── Dockerfile.backtest     # 回测容器
├── run_backend.py         # 启动后端
├── run_monitor.py         # 启动监控
└── README.md
```

## 快速开始

### 方式一: Docker部署 (推荐)

#### 1. 前置要求
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose

#### 2. 配置环境变量

复制 `.env.example` 为 `.env`:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
# 币安API (必填)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here

# 币安API权限要求:
# - 读取权限: 必需 (查询市场数据)
# - 交易权限: 可选 (如需使用快速下单功能)
# 建议: 设置IP白名单以提高安全性

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

#### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 访问服务

- **前端界面**: http://localhost:3000
  - 山寨币筛选器入口
  - 交易回测分析入口（顶部导航切换）
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **回测服务**: http://localhost:8501 (由前端iframe嵌入)

#### 5. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v
```

### 方式二: 本地开发部署

#### 1. 安装依赖

**后端依赖 (Python 3.11+)**

```bash
cd backend
pip install -r requirements.txt
```

**前端依赖 (Node.js 18+)**

```bash
cd frontend
npm install
```

#### 2. 启动服务

**启动后端API**:
```bash
python run_backend.py
```
访问: http://localhost:8000

**启动前端**:
```bash
cd frontend
npm run dev
```
访问: http://localhost:3000

**启动监控服务** (可选):
```bash
python run_monitor.py
```

## 使用指南

### Web界面功能

#### 1. 仪表盘
- 查看BTC/ETH实时价格和24小时涨跌幅
- 查看系统统计信息（总筛选次数、发现的机会数量）
- 查看账户余额（需要配置交易权限）

#### 2. 筛选结果
- **实时数据**: 显示最新筛选出的高分币种
- **多维度信息**:
  - 总分、Beta分数、成交量分数、技术分数
  - 当前价格
  - **5分钟/15分钟/1小时涨跌幅** (实时更新)
  - BTC/ETH比率24小时变化
  - 24小时成交量
  - 技术信号（SMA、MACD、EMA、量能、异动）
- **排序功能**: 点击列标题可按任意维度排序
- **操作按钮**:
  - 查看K线图
  - 添加/移除自选
  - 快速下单

#### 3. K线图表
- 基于 klinecharts v9.8.5 专业图表库
- 自动显示技术指标：
  - EMA (7, 14, 30, 52)
  - 成交量 (VOL)
  - MACD
- 支持多时间周期切换 (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- 显示价格异动检测点
- 实时价格和涨跌幅显示
- 鼠标悬停显示K线详情和振幅

#### 4. 快速交易
- **两种下单方式**:
  - 按数量: 直接输入币种数量
  - 按USDT金额: 输入USDT金额，系统自动计算数量
- **买入/卖出**: 支持市价单快速成交
- **注意**: 需要币安API具有交易权限

#### 5. 自选列表
- 添加感兴趣的币种到自选
- 快速筛选和跟踪关注标的
- 自选币种带星标显示

#### 6. 历史排名
- 查看过去7天的筛选结果
- 自动过滤已下架币种，只显示当前活跃的交易对
- 追踪高分币种的历史表现

## 核心改进说明

### 最新优化 (v1.1)

#### 1. 活跃市场过滤
- 从币安获取市场数据时，只返回 `active=True` 的交易对
- 从588个交易对优化到436个活跃交易对
- 自动过滤已下架币种（如RNDR、COCOS、TVK等）

#### 2. 数据新鲜度验证
- 筛选时验证K线数据时间戳
- 如果最新K线超过1小时，自动跳过该币种
- 避免已停止交易的币种进入筛选结果

#### 3. BTC/ETH比率计算修正
- 根据筛选时间周期自动调整回看期：
  - 5m周期: 288根K线 = 24小时
  - 15m周期: 96根K线 = 24小时
  - 1h周期: 24根K线 = 24小时
  - 4h周期: 6根K线 = 24小时
- 确保比率变化始终反映24小时的相对表现

#### 4. 多时间周期涨跌幅
- 新增5分钟、15分钟、1小时涨跌幅列
- 实时显示短期价格动态
- 可按涨跌幅排序，快速找到强势币种

#### 5. K线图表优化
- 参考banbot实现，优化指标管理
- 解决切换时间周期时指标重复创建的问题
- 图表初始化只执行一次，数据更新不重建指标
- 更流畅的用户体验

## API文档

启动后端后访问 `http://localhost:8001/docs` 查看完整的API文档。

### 主要API端点

- `GET /api/market-overview` - 获取BTC/ETH市场概览
- `POST /api/screen` - 执行筛选
- `GET /api/top-opportunities` - 获取最佳机会（含涨跌幅数据）
- `POST /api/chart` - 生成K线图
- `GET /api/indicators` - 获取技术指标
- `GET /api/historical` - 获取历史K线数据
- `GET /api/top-gainers` - 获取涨幅榜
- `GET /api/history/rankings` - 获取历史排名（自动过滤非活跃币种）
- `POST /api/watchlist` - 添加自选
- `DELETE /api/watchlist/{symbol}` - 移除自选
- `POST /api/trade/order` - 创建市价单
- `GET /api/trade/balances` - 获取账户余额

## 获取币安API密钥

1. 登录币安账户
2. 访问 [API管理](https://www.binance.com/zh-CN/my/settings/api-management)
3. 创建新的API密钥
4. **权限设置**:
   - **仅查看数据**: 勾选"读取"权限（必需）
   - **使用交易功能**: 勾选"现货与杠杆交易"权限（可选）
5. 设置IP白名单 (强烈推荐)
6. 将API Key和Secret填入 `.env` 文件

### 交易权限说明

如果您想使用快速下单功能，需要启用交易权限：
- 在币安API管理页面勾选"启用现货与杠杆交易"
- 建议添加IP白名单以提高安全性
- 首次使用前建议小额测试

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
计算山寨币价格相对BTC和ETH的24小时比率变化，筛选出涨幅超过BTC/ETH的强势币种。

**示例**: 如果某币的BTC比率变化为+50%，意味着：
- 假设BTC涨了10%
- 该币涨了约15%（相对BTC强1.5倍）

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

### Docker命令参考

```bash
# 查看服务日志
docker-compose logs backend    # 后端日志
docker-compose logs frontend   # 前端日志
docker-compose logs monitor    # 监控服务日志

# 重启特定服务
docker-compose restart backend

# 重新构建并启动
docker-compose up -d --build

# 进入容器
docker exec -it altcoin-screener-backend bash

# 清理数据
docker-compose down -v  # 删除所有数据卷
```

### 自定义筛选参数

在Web界面或通过API自定义:
- 时间周期 (5m, 15m, 1h, 4h)
- 最小成交量
- 最小价格变动
- 评分阈值

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
- 检查API权限（需要"读取"权限，交易功能需额外权限）

**问题**: "Invalid API-key, IP, or permissions"
- 如果使用快速交易功能，需要启用"现货与杠杆交易"权限
- 建议添加服务器IP到白名单

### 2. Docker相关问题

**问题**: 端口占用
```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "3001:80"   # 前端改为3001
  - "8002:8000" # 后端改为8002
```

**问题**: 容器无法启动
```bash
# 查看详细日志
docker-compose logs

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### 3. K线图显示问题

**问题**: 图表加载失败或显示空白
- 检查浏览器控制台错误
- 确认symbol格式正确（如 BTC/USDT）
- 检查网络连接

**问题**: 指标重复显示
- 已在v1.1版本修复
- 如仍有问题，清除浏览器缓存重试

### 4. 数据库错误

Docker部署会自动管理数据库，如需重置:
```bash
docker-compose down -v  # 删除数据卷
docker-compose up -d    # 重新启动
```

本地部署可手动删除:
```bash
rm -rf backend/data/altcoin_screener.db
python run_backend.py  # 自动创建新数据库
```

### 5. 通知发送失败

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

- 使用数据库缓存历史数据
- 合理设置监控间隔（建议5分钟）
- 预筛选：先用成交量过滤，只对高流动性币种进行详细分析
- 只筛选活跃币种（已自动实现）

### 数据库维护

定期清理旧数据（在容器内执行）:
```bash
docker exec -it altcoin-screener-backend bash
sqlite3 backend/data/altcoin_screener.db

# 删除30天前的K线数据
DELETE FROM kline_data WHERE timestamp < datetime('now', '-30 days');

# 删除7天前的筛选结果
DELETE FROM screening_results WHERE timestamp < datetime('now', '-7 days');

# 优化数据库
VACUUM;
```

## 安全建议

1. ✅ 优先使用只读API密钥（如不需交易功能）
2. ✅ 启用交易功能时，务必设置IP白名单
3. ✅ 不要提交 `.env` 文件到版本控制
4. ✅ 定期更换API密钥
5. ✅ 使用HTTPS（生产环境）
6. ✅ 首次交易前小额测试
7. ✅ 设置合理的交易限额

## 更新日志

### v1.2 (2025-12-29) - Tretra Trading Station
- 🎉 **重大更新**: 重命名为 Tretra Trading Station
- ✨ 新增交易回测分析功能（Streamlit）
- ✨ 新增顶部导航栏，一键切换筛选器和回测分析
- ✨ 全屏回测界面，优化数据可视化体验
- 📊 支持CSV导入币安、OKX历史交易数据
- 📊 多维度交易分析：胜率、盈亏比、最大回撤、夏普比率
- 🗄️ 新增数据库模型：ImportedTrade、BacktestAnalysis、ImportHistory
- 🐳 新增 Dockerfile.backtest，Docker编排支持4个服务
- 🔧 回测服务与主程序共享环境变量配置
- 🔧 修复回测CSV文件保存路径，适配Docker环境

### v1.1 (2025-12-28)
- ✨ 新增5分钟/15分钟/1小时涨跌幅显示
- 🔧 修复BTC/ETH比率计算，正确适配不同时间周期
- 🔧 修复K线图指标重复创建问题
- ⚡ 优化活跃市场过滤，自动排除已下架币种
- ⚡ 新增数据新鲜度验证，避免陈旧数据
- 🎨 优化历史排名显示，只显示当前活跃币种
- 📝 完善API响应字段，补充缺失的涨跌幅数据

### v1.0
- 🎉 初始版本发布
- ✅ 核心筛选功能
- ✅ Web界面
- ✅ Docker支持
- ✅ 通知系统

## 免责声明

⚠️ **本工具仅用于信息参考，不构成投资建议。**

- 加密货币交易具有高风险
- 过往表现不代表未来结果
- 请自行承担交易风险
- 建议在使用前充分测试和理解系统
- 使用交易功能前请确保理解市价单的风险
- 建议设置止损，做好风险管理

## 许可证

MIT License

---

**祝交易顺利！记得做好风险管理。** 🚀
