#!/usr/bin/env python
"""
启动后端API服务器
"""
import uvicorn
from backend.app.main import app
from backend.config import settings

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║       Tretra Trading Station - Backend API           ║
    ║                                                       ║
    ║  API Server: http://localhost:8001                    ║
    ║  API Docs:   http://localhost:8001/docs               ║
    ║                                                       ║
    ║  Press Ctrl+C to stop                                 ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level=settings.LOG_LEVEL.lower()
    )
