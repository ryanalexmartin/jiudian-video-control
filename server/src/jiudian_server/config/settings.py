"""Application settings using Pydantic BaseSettings."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Global application configuration.

    Values can be overridden via environment variables prefixed with ``JIUDIAN_``,
    e.g. ``JIUDIAN_FPS=60`` or a ``.env`` file.
    """

    model_config = {"env_prefix": "JIUDIAN_"}

    # Video
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30

    # API / network
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # Development
    dev_mode: bool = Field(True, description="Use test patterns instead of real capture devices")

    # Persistence
    config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".jiudian",
        description="Directory for config / scene JSON files",
    )

    # Preview stream
    preview_quality: int = Field(70, ge=1, le=100, description="JPEG quality for preview stream")
    preview_size: tuple[int, int] = (320, 180)

    # Transitions
    transition_duration: float = Field(0.5, ge=0.0, description="Default transition duration (s)")
