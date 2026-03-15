"""Compositor pipeline: runs the render loop in a daemon thread."""
from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Callable, Optional

import numpy as np

from .models import Scene
from .renderer import SceneRenderer
from .transitions import TransitionEngine, TransitionType

if TYPE_CHECKING:
    from ..capture.manager import InputManager

logger = logging.getLogger(__name__)


class CompositorPipeline:
    """Runs the compositing pipeline at a target FPS in a daemon thread.

    Grabs frames from InputManager, renders the active scene (with transitions),
    and emits composited frames via callbacks.
    """

    def __init__(
        self,
        input_manager: "InputManager",
        width: int = 1920,
        height: int = 1080,
        target_fps: int = 30,
        transition_duration: float = 0.5,
    ):
        self.input_manager = input_manager
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps

        self.renderer = SceneRenderer(width, height)
        self.transition_engine = TransitionEngine(self.renderer, transition_duration)

        self._active_scene: Optional[Scene] = None
        self._scene_lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Callbacks for frame delivery
        self._frame_callbacks: list[Callable[[np.ndarray], None]] = []
        self._current_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()

        # Stats
        self.actual_fps: float = 0.0
        self._frame_count: int = 0
        self._fps_timer: float = 0.0

    @property
    def active_scene(self) -> Optional[Scene]:
        with self._scene_lock:
            return self._active_scene

    @property
    def current_frame(self) -> Optional[np.ndarray]:
        with self._frame_lock:
            return self._current_frame

    def set_scene(self, scene: Scene, transition: TransitionType = TransitionType.CUT) -> None:
        """Switch to a new scene, optionally with a transition."""
        with self._scene_lock:
            old_scene = self._active_scene
            if old_scene is not None and transition != TransitionType.CUT:
                self.transition_engine.start_transition(old_scene, scene, transition)
            self._active_scene = scene
        logger.info("Scene switched to: %s (%s)", scene.name, transition.value)

    def add_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Register a callback to receive composited frames."""
        self._frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Unregister a frame callback."""
        try:
            self._frame_callbacks.remove(callback)
        except ValueError:
            pass

    def start(self) -> None:
        """Start the pipeline thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="CompositorPipeline")
        self._thread.start()
        logger.info("Compositor pipeline started at %d FPS target", self.target_fps)

    def stop(self) -> None:
        """Stop the pipeline thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Compositor pipeline stopped")

    def _run_loop(self) -> None:
        """Main render loop running in daemon thread."""
        self._fps_timer = time.monotonic()
        self._frame_count = 0

        while self._running:
            loop_start = time.monotonic()

            try:
                self._render_frame()
            except Exception:
                logger.exception("Error in compositor render loop")

            # FPS tracking
            self._frame_count += 1
            elapsed_since_fps = time.monotonic() - self._fps_timer
            if elapsed_since_fps >= 1.0:
                self.actual_fps = self._frame_count / elapsed_since_fps
                self._frame_count = 0
                self._fps_timer = time.monotonic()

            # Frame rate limiting
            elapsed = time.monotonic() - loop_start
            sleep_time = self.frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _render_frame(self) -> None:
        """Render a single frame and distribute to callbacks."""
        # Grab all input frames
        input_frames = self.input_manager.get_all_frames()

        with self._scene_lock:
            scene = self._active_scene

        if scene is None:
            return

        # Check for active transition
        if self.transition_engine.is_transitioning:
            frame = self.transition_engine.render_transition(input_frames)
            if frame is None:
                # Transition just finished, render current scene
                frame = self.renderer.render(scene, input_frames)
        else:
            frame = self.renderer.render(scene, input_frames)

        # Store current frame
        with self._frame_lock:
            self._current_frame = frame

        # Notify callbacks
        for callback in self._frame_callbacks:
            try:
                callback(frame)
            except Exception:
                logger.exception("Error in frame callback")
