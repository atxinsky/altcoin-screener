#!/usr/bin/env python
"""
启动监控服务（定时筛选、警报和自动模拟交易）
"""
from backend.services.monitor_service import MonitorService

if __name__ == "__main__":
    monitor = MonitorService()

    # 交易时间窗口配置（北京时间）
    # 格式: (开始小时, 开始分钟, 结束小时, 结束分钟)
    TRADING_WINDOWS = [
        (7, 30, 8, 30),    # 早上 7:30-8:30
        (11, 30, 12, 30),  # 中午 11:30-12:30
        (15, 30, 16, 30),  # 下午 15:30-16:30
    ]

    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        Binance Altcoin Screener - Monitor Service            ║
    ║                                                               ║
    ║  功能:                                                        ║
    ║    - 定时筛选山寨币                                           ║
    ║    - 发送高分机会通知                                         ║
    ║    - 自动模拟交易（在交易时间窗口内）                         ║
    ║                                                               ║
    ║  筛选周期: 5m, 15m, 1h                                        ║
    ║  筛选间隔: 5分钟                                              ║
    ║                                                               ║
    ║  交易时间窗口 (北京时间):                                     ║
    ║    - 07:30 - 08:30                                            ║
    ║    - 11:30 - 12:30                                            ║
    ║    - 15:30 - 16:30                                            ║
    ║                                                               ║
    ║  模拟交易开仓条件:                                            ║
    ║    - 总分 >= 75                                               ║
    ║    - 技术分 >= 60                                             ║
    ║    - MACD金叉 + 价格在所有EMA之上                             ║
    ║    - 成交量分 >= 40                                           ║
    ║                                                               ║
    ║  Press Ctrl+C to stop                                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        monitor.start_monitoring(
            timeframes=['5m', '15m', '1h'],
            trading_windows=TRADING_WINDOWS,
            enable_time_windows=True  # 设为 False 可全天交易
        )
    except KeyboardInterrupt:
        print("\n\n正在关闭...")
        monitor.stop_monitoring()
