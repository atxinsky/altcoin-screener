from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from backend.database.database import init_db, get_db_session
from backend.app import routes
from backend.config import settings


# Create FastAPI app
app = FastAPI(
    title="Binance Altcoin Screener",
    description="Screen altcoins for beta opportunities when BTC/ETH are trending",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
import os
os.makedirs("./charts", exist_ok=True)
os.makedirs("./frontend/dist", exist_ok=True)

app.mount("/charts", StaticFiles(directory="./charts"), name="charts")

# Include routers
app.include_router(routes.router, prefix="/api", tags=["api"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("Initializing SQLite database...")
    init_db()
    print("SQLite database initialized successfully")

    # Initialize TimescaleDB for K-line data
    try:
        from backend.database.timescale_db import init_timescale_db
        print("Initializing TimescaleDB...")
        init_timescale_db()
        print("TimescaleDB initialized successfully")
    except Exception as e:
        print(f"Warning: TimescaleDB initialization failed: {e}")
        print("K-line storage will not be available")

    # Start background K-line collector
    try:
        from backend.services.kline_collector import start_background_collector
        print("Starting background K-line collector...")
        start_background_collector()
        print("Background K-line collector started")
    except Exception as e:
        print(f"Warning: K-line collector failed to start: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Binance Altcoin Screener API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
