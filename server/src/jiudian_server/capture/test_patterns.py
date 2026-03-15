"""Animated test pattern generators for development without capture cards."""
from __future__ import annotations

import math
import time
from typing import Optional

import cv2
import numpy as np

from .source import InputSource


class ColorBarsSource(InputSource):
    """SMPTE-style color bars with a scrolling line indicator."""

    COLORS_BGR = [
        (255, 255, 255),  # White
        (0, 255, 255),    # Yellow
        (255, 255, 0),    # Cyan
        (0, 255, 0),      # Green
        (255, 0, 255),    # Magenta
        (0, 0, 255),      # Red
        (255, 0, 0),      # Blue
    ]

    def __init__(self, source_id: int, width: int = 1920, height: int = 1080):
        super().__init__(source_id, f"色彩條 {source_id + 1}")
        self.width = width
        self.height = height
        self._base_frame: Optional[np.ndarray] = None

    def start(self) -> bool:
        self._base_frame = self._generate_bars()
        self.connected = True
        return True

    def stop(self) -> None:
        self.connected = False
        self._base_frame = None

    def _generate_bars(self) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bar_width = self.width // len(self.COLORS_BGR)
        for i, color in enumerate(self.COLORS_BGR):
            x1 = i * bar_width
            x2 = (i + 1) * bar_width if i < len(self.COLORS_BGR) - 1 else self.width
            frame[:, x1:x2] = color
        # Add source label
        cv2.putText(
            frame, f"INPUT {self.source_id + 1}", (self.width // 2 - 200, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 4,
        )
        return frame

    def grab_frame(self) -> Optional[np.ndarray]:
        if self._base_frame is None:
            return None
        frame = self._base_frame.copy()
        # Animated scrolling line
        t = time.time()
        y = int((t * 100) % self.height)
        cv2.line(frame, (0, y), (self.width, y), (0, 200, 255), 3)
        return frame


class GradientSweepSource(InputSource):
    """Animated gradient sweep across the frame."""

    def __init__(self, source_id: int, width: int = 1920, height: int = 1080):
        super().__init__(source_id, f"漸層掃描 {source_id + 1}")
        self.width = width
        self.height = height

    def start(self) -> bool:
        self.connected = True
        return True

    def stop(self) -> None:
        self.connected = False

    def grab_frame(self) -> Optional[np.ndarray]:
        t = time.time()
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Create horizontal gradient with time-based hue shift
        hue_offset = int((t * 30) % 180)
        x_vals = np.linspace(0, 180, self.width, dtype=np.float32)
        hue_row = ((x_vals + hue_offset) % 180).astype(np.uint8)

        hsv = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        hsv[:, :, 0] = hue_row[np.newaxis, :]
        hsv[:, :, 1] = 255
        hsv[:, :, 2] = 200

        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # Add label
        cv2.putText(
            frame, f"INPUT {self.source_id + 1}", (self.width // 2 - 200, self.height // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 4,
        )
        return frame


class BouncingBoxSource(InputSource):
    """Bouncing box animation to verify motion rendering."""

    def __init__(self, source_id: int, width: int = 1920, height: int = 1080):
        super().__init__(source_id, f"彈跳方塊 {source_id + 1}")
        self.width = width
        self.height = height
        self.box_size = 150

    def start(self) -> bool:
        self.connected = True
        return True

    def stop(self) -> None:
        self.connected = False

    def grab_frame(self) -> Optional[np.ndarray]:
        t = time.time()
        frame = np.full((self.height, self.width, 3), (30, 20, 11), dtype=np.uint8)

        # Bouncing box position
        period_x = 3.0 + self.source_id * 0.5
        period_y = 2.5 + self.source_id * 0.3
        cx = int((math.sin(t * 2 * math.pi / period_x) * 0.5 + 0.5) * (self.width - self.box_size))
        cy = int((math.sin(t * 2 * math.pi / period_y) * 0.5 + 0.5) * (self.height - self.box_size))

        # Neon cyan box
        cv2.rectangle(
            frame, (cx, cy), (cx + self.box_size, cy + self.box_size),
            (255, 200, 0), -1,
        )
        # Glow effect
        cv2.rectangle(
            frame, (cx - 3, cy - 3), (cx + self.box_size + 3, cy + self.box_size + 3),
            (255, 200, 0), 2,
        )

        # Add input label at center
        cv2.putText(
            frame, f"INPUT {self.source_id + 1}", (self.width // 2 - 200, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (224, 224, 224), 3,
        )

        # Add frame counter
        frame_num = int(t * 30) % 9999
        cv2.putText(
            frame, f"#{frame_num:04d}", (cx + 10, cy + self.box_size // 2 + 15),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (30, 20, 11), 3,
        )

        return frame


class GridPatternSource(InputSource):
    """Grid with animated counter and timestamp."""

    def __init__(self, source_id: int, width: int = 1920, height: int = 1080):
        super().__init__(source_id, f"格線圖案 {source_id + 1}")
        self.width = width
        self.height = height

    def start(self) -> bool:
        self.connected = True
        return True

    def stop(self) -> None:
        self.connected = False

    def grab_frame(self) -> Optional[np.ndarray]:
        t = time.time()
        frame = np.full((self.height, self.width, 3), (30, 26, 11), dtype=np.uint8)

        # Draw grid
        grid_color = (80, 60, 30)
        for x in range(0, self.width, 120):
            cv2.line(frame, (x, 0), (x, self.height), grid_color, 1)
        for y in range(0, self.height, 120):
            cv2.line(frame, (0, y), (self.width, y), grid_color, 1)

        # Center crosshair
        cx, cy = self.width // 2, self.height // 2
        cv2.line(frame, (cx - 60, cy), (cx + 60, cy), (0, 200, 255), 2)
        cv2.line(frame, (cx, cy - 60), (cx, cy + 60), (0, 200, 255), 2)
        cv2.circle(frame, (cx, cy), 40, (0, 200, 255), 2)

        # Input label
        cv2.putText(
            frame, f"INPUT {self.source_id + 1}", (cx - 200, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (224, 224, 224), 3,
        )

        # Animated counter
        counter = int(t * 30) % 99999
        cv2.putText(
            frame, f"FRAME {counter:05d}", (cx - 180, cy + 100),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 200, 255), 2,
        )

        # Resolution label
        cv2.putText(
            frame, f"{self.width}x{self.height}", (cx - 120, self.height - 40),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (136, 136, 170), 2,
        )

        # Rotating indicator
        angle = (t * 60) % 360
        rad = math.radians(angle)
        r = 30
        ex = int(cx + r * math.cos(rad))
        ey = int(cy + r * math.sin(rad))
        cv2.circle(frame, (ex, ey), 8, (85, 45, 255), -1)

        return frame


# Map of pattern index to class for easy creation
TEST_PATTERN_CLASSES = [
    ColorBarsSource,
    GradientSweepSource,
    BouncingBoxSource,
    GridPatternSource,
]


def create_test_pattern(source_id: int, width: int = 1920, height: int = 1080) -> InputSource:
    """Create a test pattern source for the given source_id (cycles through available patterns)."""
    cls = TEST_PATTERN_CLASSES[source_id % len(TEST_PATTERN_CLASSES)]
    return cls(source_id, width, height)
