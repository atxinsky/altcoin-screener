#!/usr/bin/env python
"""
启动后端API服务器
"""
import uvicorn
from backend.app.main import app
from backend.config import settings

if __name__ == "__main__":
    # Docker内部使用8000，外部映射到8001
    port = 8000
    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║       Tretra Trading Station - Backend API           ║
    ║                                                       ║
    ║  API Server: http://localhost:{port}                    ║
    ║  API Docs:   http://localhost:{port}/docs               ║
    ║                                                       ║
    ║  Press Ctrl+C to stop                                 ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=settings.LOG_LEVEL.lower()
    )
