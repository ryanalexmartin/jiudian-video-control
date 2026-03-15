"""Window capture input source for macOS using Quartz/CoreGraphics."""
from __future__ import annotations

import logging
import time
from typing import Optional

import cv2
import numpy as np

from .source import InputSource

logger = logging.getLogger(__name__)


class WindowCaptureSource(InputSource):
    """Captures a specific macOS window by its CGWindowID."""

    def __init__(
        self,
        source_id: int,
        window_id: int,
        target_fps: int = 30,
        owner_name: str = "",
        window_name: str = "",
    ):
        label = f"{owner_name}: {window_name}" if window_name else owner_name
        super().__init__(source_id, label or f"Window {window_id}")
        self.window_id = window_id
        self.target_fps = target_fps
        self.owner_name = owner_name
        self.window_name = window_name
        self._frame_interval = 1.0 / target_fps
        self._last_frame_time: float = 0.0
        self._cg_module = None  # Lazy-loaded Quartz module

    def start(self) -> bool:
        """Import Quartz, verify window exists via a test capture."""
        try:
            import Quartz
            self._cg_module = Quartz

            # Test capture to verify window still exists
            image = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                self.window_id,
                Quartz.kCGWindowImageBoundsIgnoreFraming,
            )
            if image is None:
                logger.warning(
                    "Window %d (%s) not found or not capturable",
                    self.window_id, self.name,
                )
                self.connected = False
                return False

            self.connected = True
            logger.info("Started window capture: %s (wid=%d)", self.name, self.window_id)
            return True
        except ImportError:
            logger.error("pyobjc-framework-Quartz not installed")
            self.connected = False
            return False
        except Exception:
            logger.exception("Error starting window capture for wid=%d", self.window_id)
            self.connected = False
            return False

    def stop(self) -> None:
        """Release references."""
        self.connected = False
        self._cg_module = None
        logger.info("Stopped window capture: %s (wid=%d)", self.name, self.window_id)

    def grab_frame(self) -> Optional[np.ndarray]:
        """Capture the window at the target frame rate."""
        if self._cg_module is None:
            return None

        # Rate-limit to target FPS
        now = time.monotonic()
        elapsed = now - self._last_frame_time
        if elapsed < self._frame_interval:
            time.sleep(self._frame_interval - elapsed)
        self._last_frame_time = time.monotonic()

        try:
            CG = self._cg_module
            image = CG.CGWindowListCreateImage(
                CG.CGRectNull,
                CG.kCGWindowListOptionIncludingWindow,
                self.window_id,
                CG.kCGWindowImageBoundsIgnoreFraming,
            )
            if image is None:
                return None

            width = CG.CGImageGetWidth(image)
            height = CG.CGImageGetHeight(image)
            if width == 0 or height == 0:
                return None

            # Get pixel data from CGImage
            bytes_per_row = CG.CGImageGetBytesPerRow(image)
            data_provider = CG.CGImageGetDataProvider(image)
            data = CG.CGDataProviderCopyData(data_provider)

            # Handle Retina row padding: bytes_per_row may exceed width*4
            arr = np.frombuffer(data, dtype=np.uint8).reshape(height, bytes_per_row)
            # Slice to actual pixel width (4 bytes per pixel), discard padding
            arr = arr[:, :width * 4].reshape(height, width, 4)

            # Convert BGRA to BGR for OpenCV
            frame = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            return frame

        except Exception:
            logger.exception("Error capturing window %d", self.window_id)
            return None
