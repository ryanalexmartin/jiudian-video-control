"""Enumerate available capture devices via OpenCV probing."""
from __future__ import annotations

import logging

import cv2

logger = logging.getLogger(__name__)


def enumerate_capture_devices(max_index: int = 10) -> list[dict]:
    """Probe cv2.VideoCapture(i) for indices 0..max_index-1.

    Returns a list of dicts with keys: index, name, width, height.
    """
    devices: list[dict] = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            devices.append({
                "index": i,
                "name": f"Camera {i}",
                "width": w,
                "height": h,
            })
            cap.release()
            logger.debug("Found capture device %d: %dx%d", i, w, h)
        else:
            cap.release()
    logger.info("Enumerated %d capture device(s)", len(devices))
    return devices
