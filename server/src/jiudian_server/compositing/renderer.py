"""Scene renderer: composites input frames into an output frame using NumPy/OpenCV."""
from __future__ import annotations

import cv2
import numpy as np

from .models import Layer, Scene


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' to (B, G, R) tuple for OpenCV."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)


class SceneRenderer:
    """Renders a Scene by compositing input frames onto a canvas."""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def render(
        self,
        scene: Scene,
        input_frames: dict[int, np.ndarray],
    ) -> np.ndarray:
        """Render a scene given current input frames.

        Args:
            scene: The scene to render.
            input_frames: Dict mapping input_id -> BGR frame (np.ndarray).

        Returns:
            Composited BGR frame of size (height, width, 3).
        """
        # Create canvas with background color
        bg_bgr = _hex_to_bgr(scene.background_color)
        canvas = np.full((self.height, self.width, 3), bg_bgr, dtype=np.uint8)

        # Render layers in z_order
        for layer in scene.get_sorted_layers():
            frame = input_frames.get(layer.input_id)
            if frame is None:
                continue
            self._composite_layer(canvas, layer, frame)

        return canvas

    def _composite_layer(
        self,
        canvas: np.ndarray,
        layer: Layer,
        frame: np.ndarray,
    ) -> None:
        """Composite a single layer onto the canvas in-place."""
        # Resize input frame to layer dimensions
        if layer.width <= 0 or layer.height <= 0:
            return
        resized = cv2.resize(frame, (layer.width, layer.height), interpolation=cv2.INTER_LINEAR)

        # Draw border if specified
        if layer.border_width > 0:
            border_bgr = _hex_to_bgr(layer.border_color)
            cv2.rectangle(
                resized,
                (0, 0),
                (layer.width - 1, layer.height - 1),
                border_bgr,
                layer.border_width,
            )

        # Calculate overlap region with canvas bounds
        x1 = max(layer.x, 0)
        y1 = max(layer.y, 0)
        x2 = min(layer.x + layer.width, self.width)
        y2 = min(layer.y + layer.height, self.height)

        if x2 <= x1 or y2 <= y1:
            return  # Completely outside canvas

        # Source region in the resized frame
        sx1 = x1 - layer.x
        sy1 = y1 - layer.y
        sx2 = sx1 + (x2 - x1)
        sy2 = sy1 + (y2 - y1)

        src_region = resized[sy1:sy2, sx1:sx2]
        dst_region = canvas[y1:y2, x1:x2]

        # Alpha blending
        if layer.alpha >= 1.0:
            canvas[y1:y2, x1:x2] = src_region
        else:
            alpha = layer.alpha
            canvas[y1:y2, x1:x2] = cv2.addWeighted(src_region, alpha, dst_region, 1.0 - alpha, 0)
