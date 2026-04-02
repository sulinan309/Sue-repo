"""FastAPI application entry point for WatchBot.

Serves the admin API and WebSocket endpoint for call handling.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from watchbot.admin.api import router as admin_router
from watchbot.config import load_config
from watchbot.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    await init_db(config)
    yield
    await close_db()


app = FastAPI(
    title="WatchBot",
    description="AI Guard System for Unmanned Warehouses - 摄像头看 + 电话说",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
