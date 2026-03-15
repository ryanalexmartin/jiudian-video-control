"""Video capture: input sources, test patterns, device enumeration, and input manager."""
from .directshow import CameraCaptureSource
from .enumerate import enumerate_capture_devices
from .enumerate_windows import enumerate_windows
from .manager import InputManager
from .source import InputSource
from .test_patterns import create_test_pattern
from .window_capture import WindowCaptureSource

__all__ = [
    "CameraCaptureSource",
    "InputManager",
    "InputSource",
    "WindowCaptureSource",
    "create_test_pattern",
    "enumerate_capture_devices",
    "enumerate_windows",
]
