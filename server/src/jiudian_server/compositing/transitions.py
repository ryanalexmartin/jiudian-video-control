"""Transition effects between scenes."""
from __future__ import annotations

import time
from enum import Enum
from typing import Optional

import cv2
import numpy as np

from .models import Scene
from .renderer import SceneRenderer


class TransitionType(str, Enum):
    CUT = "cut"
    FADE = "fade"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"


class TransitionEngine:
    """Manages transitions between scenes."""

    def __init__(self, renderer: SceneRenderer, duration: float = 0.5):
        self.renderer = renderer
        self.default_duration = duration

        self._from_scene: Optional[Scene] = None
        self._to_scene: Optional[Scene] = None
        self._transition_type: TransitionType = TransitionType.CUT
        self._start_time: float = 0.0
        self._duration: float = 0.0
        self._active: bool = False

    @property
    def is_transitioning(self) -> bool:
        return self._active

    def start_transition(
        self,
        from_scene: Scene,
        to_scene: Scene,
        transition_type: TransitionType = TransitionType.FADE,
        duration: Optional[float] = None,
    ) -> None:
        """Begin a transition from one scene to another."""
        if transition_type == TransitionType.CUT:
            # Cut is instant, no transition needed
            self._active = False
            return

        self._from_scene = from_scene
        self._to_scene = to_scene
        self._transition_type = transition_type
        self._duration = duration if duration is not None else self.default_duration
        self._start_time = time.monotonic()
        self._active = True

    def render_transition(
        self,
        input_frames: dict[int, np.ndarray],
    ) -> Optional[np.ndarray]:
        """Render the current transition frame, or None if no transition is active."""
        if not self._active or self._from_scene is None or self._to_scene is None:
            return None

        elapsed = time.monotonic() - self._start_time
        progress = min(elapsed / self._duration, 1.0)

        if progress >= 1.0:
            self._active = False
            return None

        frame_from = self.renderer.render(self._from_scene, input_frames)
        frame_to = self.renderer.render(self._to_scene, input_frames)

        if self._transition_type == TransitionType.FADE:
            return self._fade(frame_from, frame_to, progress)
        elif self._transition_type == TransitionType.WIPE_LEFT:
            return self._wipe(frame_from, frame_to, progress, direction="left")
        elif self._transition_type == TransitionType.WIPE_RIGHT:
            return self._wipe(frame_from, frame_to, progress, direction="right")
        else:
            return frame_to

    def _fade(
        self,
        frame_from: np.ndarray,
        frame_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """Cross-fade between two frames."""
        return cv2.addWeighted(frame_to, progress, frame_from, 1.0 - progress, 0)

    def _wipe(
        self,
        frame_from: np.ndarray,
        frame_to: np.ndarray,
        progress: float,
        direction: str = "left",
    ) -> np.ndarray:
        """Wipe transition from one frame to another."""
        h, w = frame_from.shape[:2]
        result = frame_from.copy()
        boundary = int(w * progress)

        if direction == "left":
            result[:, :boundary] = frame_to[:, :boundary]
        else:
            result[:, w - boundary :] = frame_to[:, w - boundary :]

        return result
