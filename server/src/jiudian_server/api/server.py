"""FastAPI server setup and lifecycle management."""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routes, websocket
from .routes import router
from .websocket import ws_router

if TYPE_CHECKING:
    from ..app import Application

logger = logging.getLogger(__name__)


class ApiServer:
    """Manages the FastAPI + uvicorn server running in a background thread."""

    def __init__(self, app_instance: "Application", host: str = "0.0.0.0", port: int = 8080):
        self.app_instance = app_instance
        self.host = host
        self.port = port
        self._thread: threading.Thread | None = None
        self._server: uvicorn.Server | None = None

        # Create FastAPI app
        self.fastapi = FastAPI(
            title="酒店影像控制系統 API",
            version="1.0.0",
            description="Video control system REST/WebSocket API",
        )

        # CORS for Android app and web clients
        self.fastapi.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Include routers
        self.fastapi.include_router(router)
        self.fastapi.include_router(ws_router)

        # Set app references
        routes.set_app(app_instance)
        websocket.set_app(app_instance)

    @property
    def ws_connection_count(self) -> int:
        return websocket.get_connection_count()

    def start(self) -> None:
        """Start the API server in a background thread."""
        config = uvicorn.Config(
            self.fastapi,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(
            target=self._server.run,
            daemon=True,
            name="ApiServer",
        )
        self._thread.start()
        logger.info("API server started on %s:%d", self.host, self.port)

    def stop(self) -> None:
        """Stop the API server."""
        if self._server:
            self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info("API server stopped")
