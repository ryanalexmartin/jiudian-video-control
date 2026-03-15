"""Enumerate visible macOS windows using Quartz/CoreGraphics."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def enumerate_windows() -> list[dict]:
    """Return a list of capturable macOS windows.

    Each entry: {window_id, owner_name, window_name, bounds: {x, y, width, height}}.
    Returns an empty list on non-macOS or if pyobjc is not installed.
    """
    if os.uname().sysname != "Darwin":
        return []

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

    # Get our own PID to filter out Python windows
    my_pid = os.getpid()

    results: list[dict] = []
    for win in window_list:
        # Only include normal windows (layer 0) — skip menu bar, status items, etc.
        layer = win.get("kCGWindowLayer", -1)
        if layer != 0:
            continue

        owner_pid = win.get("kCGWindowOwnerPID", 0)
        if owner_pid == my_pid:
            continue

        bounds = win.get("kCGWindowBounds", {})
        w = int(bounds.get("Width", 0))
        h = int(bounds.get("Height", 0))

        # Skip tiny windows
        if w < 100 or h < 100:
            continue

        owner_name = win.get("kCGWindowOwnerName", "")
        window_name = win.get("kCGWindowName", "")

        # Skip windows with no owner
        if not owner_name:
            continue

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
