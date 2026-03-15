"""Enumerate visible windows (macOS via Quartz, Windows via win32gui)."""
from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)


def enumerate_windows() -> list[dict]:
    """Return a list of capturable windows.

    Each entry: {window_id, owner_name, window_name, bounds: {x, y, width, height}}.
    Supports macOS (Quartz) and Windows (win32gui).
    Returns an empty list if the platform is unsupported or dependencies are missing.
    """
    if sys.platform == "win32":
        return _enumerate_windows_win32()
    elif sys.platform == "darwin":
        return _enumerate_windows_macos()
    return []


def _enumerate_windows_win32() -> list[dict]:
    """Enumerate visible windows on Windows using win32gui."""
    try:
        import win32gui
        import win32process
    except ImportError:
        logger.debug("pywin32 not installed, window enumeration unavailable")
        return []

    my_pid = os.getpid()
    results: list[dict] = []

    def _enum_callback(hwnd: int, _extra: object) -> None:
        # Only visible windows
        if not win32gui.IsWindowVisible(hwnd):
            return
        # Skip minimized
        if win32gui.IsIconic(hwnd):
            return

        # Get window rect
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        except Exception:
            return
        w = right - left
        h = bottom - top
        if w < 100 or h < 100:
            return

        # Filter out own process
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == my_pid:
                return
        except Exception:
            pass

        window_name = win32gui.GetWindowText(hwnd) or ""
        # Skip windows with no title (usually invisible helper windows)
        if not window_name:
            return

        # Get the executable name as owner_name
        owner_name = _get_process_name_win32(pid)

        results.append({
            "window_id": hwnd,
            "owner_name": owner_name,
            "window_name": window_name,
            "bounds": {"x": left, "y": top, "width": w, "height": h},
        })

    try:
        win32gui.EnumWindows(_enum_callback, None)
    except Exception:
        logger.exception("Failed to enumerate windows")
        return []

    logger.info("Enumerated %d capturable window(s)", len(results))
    return results


def _get_process_name_win32(pid: int) -> str:
    """Get the executable name for a PID on Windows."""
    try:
        import win32api
        import win32con
        import win32process
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        try:
            exe = win32process.GetModuleFileNameEx(handle, 0)
            return os.path.basename(exe)
        finally:
            win32api.CloseHandle(handle)
    except Exception:
        return f"PID {pid}"


def _enumerate_windows_macos() -> list[dict]:
    """Enumerate visible windows on macOS using Quartz."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGNullWindowID,
            kCGWindowListOptionOnScreenOnly,
            kCGWindowListExcludeDesktopElements,
        )
    except ImportError:
        logger.debug("pyobjc-framework-Quartz not installed, window enumeration unavailable")
        return []

    try:
        options = kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements
        window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
    except Exception:
        logger.exception("Failed to enumerate windows")
        return []

    if not window_list:
        return []

    my_pid = os.getpid()
    results: list[dict] = []

    for win in window_list:
        layer = win.get("kCGWindowLayer", -1)
        if layer != 0:
            continue

        owner_pid = win.get("kCGWindowOwnerPID", 0)
        if owner_pid == my_pid:
            continue

        bounds = win.get("kCGWindowBounds", {})
        w = int(bounds.get("Width", 0))
        h = int(bounds.get("Height", 0))
        if w < 100 or h < 100:
            continue

        owner_name = win.get("kCGWindowOwnerName", "")
        if not owner_name:
            continue

        window_name = win.get("kCGWindowName", "")
        window_id = win.get("kCGWindowNumber", 0)

        results.append({
            "window_id": window_id,
            "owner_name": owner_name,
            "window_name": window_name or "",
            "bounds": {
                "x": int(bounds.get("X", 0)),
                "y": int(bounds.get("Y", 0)),
                "width": w,
                "height": h,
            },
        })

    logger.info("Enumerated %d capturable window(s)", len(results))
    return results
