# 更新日志 (Changelog)

## v1.0.0 (2025-12-28)

### 首次发布

#### 核心功能
- ✅ 币安现货山寨币数据采集
- ✅ BTC/ETH价格比率分析
- ✅ 多时间周期支持 (5m, 15m, 1h, 4h)
- ✅ 成交量筛选
- ✅ 技术指标分析 (SMA, EMA, MACD, RSI, 布林带)
- ✅ 价格异动检测
- ✅ K线图表自动生成
- ✅ SQLite数据库存储
- ✅ RESTful API (FastAPI)
- ✅ React Web界面
- ✅ 邮件通知
- ✅ Telegram通知
- ✅ 实时监控服务

#### 技术栈
- **后端**: Python 3.8+, FastAPI, SQLAlchemy
- **前端**: React 18, Ant Design, Recharts
- **数据库**: SQLite
- **API集成**: CCXT (币安)
- **图表**: Plotly
- **通知**: SMTP, python-telegram-bot

#### 评分系统
- Beta分数 (30%): 相对BTC/ETH强度
- 成交量分数 (20%): 流动性评估
- 技术分数 (50%): 综合技术指标

#### 文档
- 完整的README (中英文)
- 快速使用指南
- API文档
- 安装和启动脚本

### 已知问题
- 暂无

### 计划功能 (v1.1.0)
- [ ] 支持更多交易所 (OKX, Bybit)
- [ ] 添加回测功能
- [ ] 实时WebSocket数据流
- [ ] 更多技术指标 (KDJ, VWAP等)
- [ ] 自定义警报规则
- [ ] 性能优化
- [ ] Docker部署支持

---

## 版本说明

### 版本号规则
遵循语义化版本 (Semantic Versioning):
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正
