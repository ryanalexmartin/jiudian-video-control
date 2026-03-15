"""DirectShow (Windows) / V4L2 (Linux) / AVFoundation (macOS) capture via OpenCV."""
from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from .source import InputSource

logger = logging.getLogger(__name__)


class CameraCaptureSource(InputSource):
    """Captures video from a system camera/capture card using OpenCV VideoCapture."""

    def __init__(
        self,
        source_id: int,
        device_index: int,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
    ):
        super().__init__(source_id, f"擷取卡 {source_id + 1}")
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[cv2.VideoCapture] = None

    def start(self) -> bool:
        """Open the capture device."""
        try:
            # Use DirectShow on Windows for better capture card support
            import sys
            if sys.platform == "win32":
                self._cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            else:
                self._cap = cv2.VideoCapture(self.device_index)

            if not self._cap.isOpened():
                logger.warning("Failed to open capture device %d", self.device_index)
                self.connected = False
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)

            self.connected = True
            logger.info(
                "Opened capture device %d (%dx%d @ %d fps)",
                self.device_index, self.width, self.height, self.fps,
            )
            return True
        except Exception:
            logger.exception("Error opening capture device %d", self.device_index)
            self.connected = False
            return False

    def stop(self) -> None:
        """Release the capture device."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self.connected = False
        logger.info("Released capture device %d", self.device_index)

    def grab_frame(self) -> Optional[np.ndarray]:
        """Grab a frame from the capture device."""
        if self._cap is None or not self._cap.isOpened():
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame
