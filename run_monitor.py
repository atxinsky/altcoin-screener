#!/usr/bin/env python
"""
启动监控服务（定时筛选、警报和自动模拟交易）
24/7 全天候模式，优选时段额外加分
"""
from backend.services.monitor_service import MonitorService

if __name__ == "__main__":
    monitor = MonitorService()

    # 优选交易时间段配置（北京时间）- 这些时段获得+5加分
    # 格式: (开始小时, 开始分钟, 结束小时, 结束分钟)
    PREFERRED_WINDOWS = [
        (7, 30, 8, 30),    # 早上 7:30-8:30
        (11, 30, 12, 30),  # 中午 11:30-12:30
        (15, 30, 16, 30),  # 下午 15:30-16:30
    ]

    print("""
    ============================================================
         Binance Altcoin Screener - Monitor Service

      模式: 24/7 全天候交易（无时间窗口限制）

      功能:
        - 定时筛选山寨币
        - 发送高分机会通知
        - 自动模拟交易

      筛选周期: 5m, 15m, 1h
      筛选间隔: 5分钟

      优选时段 (北京时间，额外+5分):
        - 07:30 - 08:30
        - 11:30 - 12:30
        - 15:30 - 16:30

      模拟交易开仓条件（满足任一即可）:
        - 高分入场: 分数+时段加分 >= 账户设定阈值
        - 爆量突破: volume_surge + 分数 >= 60

      Press Ctrl+C to stop
    ============================================================
    """)

    try:
        monitor.start_monitoring(
            timeframes=['5m', '15m', '1h'],
            trading_windows=PREFERRED_WINDOWS
        )
    except KeyboardInterrupt:
        print("\n\n正在关闭...")
        monitor.stop_monitoring()
