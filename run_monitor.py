#!/usr/bin/env python
"""
启动监控服务（定时筛选和警报）
"""
from backend.services.monitor_service import MonitorService

if __name__ == "__main__":
    monitor = MonitorService()

    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     Binance Altcoin Screener - Monitor Service       ║
    ║                                                       ║
    ║  定时筛选山寨币并发送警报                             ║
    ║                                                       ║
    ║  时间周期: 5m, 15m, 1h                                ║
    ║  筛选间隔: 5分钟                                      ║
    ║                                                       ║
    ║  Press Ctrl+C to stop                                 ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    try:
        monitor.start_monitoring(timeframes=['5m', '15m', '1h'])
    except KeyboardInterrupt:
        print("\n\n正在关闭...")
        monitor.stop_monitoring()
