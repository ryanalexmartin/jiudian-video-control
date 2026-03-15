"""Window capture input source (macOS via Quartz, Windows via win32gui/BitBlt)."""
from __future__ import annotations

import logging
import sys
import time
from typing import Optional

import cv2
import numpy as np

from .source import InputSource

logger = logging.getLogger(__name__)


class WindowCaptureSource(InputSource):
    """Captures a specific window by its native handle (HWND on Windows, CGWindowID on macOS)."""

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
        self._backend: Optional[_CaptureBackend] = None

    def start(self) -> bool:
        """Initialize the platform-specific capture backend."""
        try:
            if sys.platform == "win32":
                self._backend = _Win32CaptureBackend(self.window_id)
            elif sys.platform == "darwin":
                self._backend = _QuartzCaptureBackend(self.window_id)
            else:
                logger.error("Window capture not supported on %s", sys.platform)
                self.connected = False
                return False

            if not self._backend.verify():
                logger.warning(
                    "Window %d (%s) not found or not capturable",
                    self.window_id, self.name,
                )
                self.connected = False
                return False

            self.connected = True
            logger.info("Started window capture: %s (wid=%d)", self.name, self.window_id)
            return True
        except ImportError as e:
            logger.error("Missing dependency for window capture: %s", e)
            self.connected = False
            return False
        except Exception:
            logger.exception("Error starting window capture for wid=%d", self.window_id)
            self.connected = False
            return False

    def stop(self) -> None:
        """Release resources."""
        self.connected = False
        if self._backend:
            self._backend.release()
            self._backend = None
        logger.info("Stopped window capture: %s (wid=%d)", self.name, self.window_id)

    def grab_frame(self) -> Optional[np.ndarray]:
        """Capture the window at the target frame rate."""
        if self._backend is None:
            return None

        # Rate-limit to target FPS
        now = time.monotonic()
        elapsed = now - self._last_frame_time
        if elapsed < self._frame_interval:
            time.sleep(self._frame_interval - elapsed)
        self._last_frame_time = time.monotonic()

        try:
            return self._backend.capture()
        except Exception:
            logger.exception("Error capturing window %d", self.window_id)
            return None


# ── Platform backends ─────────────────────────────────────────────────


class _CaptureBackend:
    """Abstract capture backend."""

    def verify(self) -> bool:
        raise NotImplementedError

    def capture(self) -> Optional[np.ndarray]:
        raise NotImplementedError

    def release(self) -> None:
        pass


class _Win32CaptureBackend(_CaptureBackend):
    """Capture a window on Windows using PrintWindow + BitBlt."""

    def __init__(self, hwnd: int):
        import win32gui
        import win32ui
        import win32con
        self._win32gui = win32gui
        self._win32ui = win32ui
        self._win32con = win32con
        self._hwnd = hwnd

    def verify(self) -> bool:
        return self._win32gui.IsWindow(self._hwnd)

    def capture(self) -> Optional[np.ndarray]:
        hwnd = self._hwnd
        win32gui = self._win32gui
        win32ui = self._win32ui
        win32con = self._win32con

        if not win32gui.IsWindow(hwnd):
            return None

        # Get client rect (content area without title bar/borders)
        try:
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
        except Exception:
            return None
        w = right - left
        h = bottom - top
        if w <= 0 or h <= 0:
            return None

        hwnd_dc = None
        mfc_dc = None
        save_dc = None
        bmp = None
        try:
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(mfc_dc, w, h)
            save_dc.SelectObject(bmp)

            # PrintWindow captures even if window is partially occluded
            # Flag 3 = PW_RENDERFULLCONTENT | PW_CLIENTONLY
            result = self._print_window(hwnd, save_dc.GetSafeHdc(), 3)
            if not result:
                # Fallback to BitBlt from screen DC
                save_dc.BitBlt(
                    (0, 0), (w, h), mfc_dc,
                    (0, 0), win32con.SRCCOPY,
                )

            bmp_info = bmp.GetInfo()
            bmp_bits = bmp.GetBitmapBits(True)

            arr = np.frombuffer(bmp_bits, dtype=np.uint8)
            arr = arr.reshape(bmp_info["bmHeight"], bmp_info["bmWidth"], 4)
            # BGRA -> BGR
            frame = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            return frame

        except Exception:
            return None
        finally:
            if bmp:
                win32gui.DeleteObject(bmp.GetHandle())
            if save_dc:
                save_dc.DeleteDC()
            if mfc_dc:
                mfc_dc.DeleteDC()
            if hwnd_dc:
                win32gui.ReleaseDC(hwnd, hwnd_dc)

    @staticmethod
    def _print_window(hwnd: int, hdc: int, flags: int) -> bool:
        """Call PrintWindow via ctypes."""
        import ctypes
        return bool(ctypes.windll.user32.PrintWindow(hwnd, hdc, flags))


class _QuartzCaptureBackend(_CaptureBackend):
    """Capture a window on macOS using Quartz CGWindowListCreateImage."""

    def __init__(self, window_id: int):
        import Quartz
        self._cg = Quartz
        self._window_id = window_id

    def verify(self) -> bool:
        image = self._cg.CGWindowListCreateImage(
            self._cg.CGRectNull,
            self._cg.kCGWindowListOptionIncludingWindow,
            self._window_id,
            self._cg.kCGWindowImageBoundsIgnoreFraming,
        )
        return image is not None

    def capture(self) -> Optional[np.ndarray]:
        CG = self._cg
        image = CG.CGWindowListCreateImage(
            CG.CGRectNull,
            CG.kCGWindowListOptionIncludingWindow,
            self._window_id,
            CG.kCGWindowImageBoundsIgnoreFraming,
        )
        if image is None:
            return None

        width = CG.CGImageGetWidth(image)
        height = CG.CGImageGetHeight(image)
        if width == 0 or height == 0:
            return None

        bytes_per_row = CG.CGImageGetBytesPerRow(image)
        data_provider = CG.CGImageGetDataProvider(image)
        data = CG.CGDataProviderCopyData(data_provider)

        # Handle Retina row padding
        arr = np.frombuffer(data, dtype=np.uint8).reshape(height, bytes_per_row)
        arr = arr[:, :width * 4].reshape(height, width, 4)
        frame = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        return frame
