"""Preview generator: produces JPEG thumbnails for API and WebSocket streaming."""
from __future__ import annotations

import io
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """Generates JPEG preview thumbnails from video frames at a configurable interval.

    Used by both the REST API (input/output previews) and WebSocket (live streaming).
    """

    def __init__(
        self,
        width: int = 320,
        height: int = 180,
        quality: int = 70,
        interval: float = 0.2,
    ):
        self.width = width
        self.height = height
        self.quality = quality
        self.interval = interval

        self._previews: dict[str, bytes] = {}
        self._preview_lock = threading.Lock()

    def generate_preview(self, frame: np.ndarray) -> bytes:
        """Generate a JPEG preview from a BGR frame."""
        resized = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        _, jpeg = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        return jpeg.tobytes()

    def update_preview(self, key: str, frame: np.ndarray) -> None:
        """Update the stored preview for a given key (e.g., 'input_0', 'output_0')."""
        jpeg = self.generate_preview(frame)
        with self._preview_lock:
            self._previews[key] = jpeg

    def get_preview(self, key: str) -> Optional[bytes]:
        """Get the latest JPEG preview for a key."""
        with self._preview_lock:
            return self._previews.get(key)

    def get_all_previews(self) -> dict[str, bytes]:
        """Get all current previews."""
        with self._preview_lock:
            return dict(self._previews)
