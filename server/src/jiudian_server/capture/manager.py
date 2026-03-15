"""Input manager: manages multiple input sources with thread-safe frame buffering."""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import numpy as np

from .source import InputSource

logger = logging.getLogger(__name__)


class InputManager:
    """Manages multiple input sources, each running in its own capture thread.

    Sources can be added and removed dynamically at runtime.
    Provides thread-safe access to the latest frame from each source.
    """

    def __init__(self):
        self._sources: dict[int, InputSource] = {}
        self._frames: dict[int, Optional[np.ndarray]] = {}
        self._frame_locks: dict[int, threading.Lock] = {}
        self._threads: dict[int, threading.Thread] = {}
        self._stop_events: dict[int, threading.Event] = {}
        self._struct_lock = threading.RLock()
        self._running = False

    @property
    def source_ids(self) -> list[int]:
        """Return sorted list of active source IDs."""
        with self._struct_lock:
            return sorted(self._sources.keys())

    def add_source(self, source_id: int, source: InputSource) -> None:
        """Add or replace a source. Starts its capture thread if the manager is running."""
        with self._struct_lock:
            # Stop existing source at this ID if present
            if source_id in self._sources:
                self._stop_source(source_id)

            self._sources[source_id] = source
            self._frames[source_id] = None
            self._frame_locks[source_id] = threading.Lock()

            if self._running:
                self._start_source(source_id, source)

    def remove_source(self, source_id: int) -> None:
        """Stop and remove a source."""
        with self._struct_lock:
            if source_id not in self._sources:
                return
            self._stop_source(source_id)
            del self._sources[source_id]
            del self._frames[source_id]
            del self._frame_locks[source_id]

    def get_source(self, source_id: int) -> Optional[InputSource]:
        """Get the input source for a given slot."""
        return self._sources.get(source_id)

    def get_frame(self, source_id: int) -> Optional[np.ndarray]:
        """Get the latest frame from a source (thread-safe)."""
        lock = self._frame_locks.get(source_id)
        if lock is None:
            return None
        with lock:
            return self._frames.get(source_id)

    def get_all_frames(self) -> dict[int, np.ndarray]:
        """Get all available frames as a dict (thread-safe)."""
        frames = {}
        with self._struct_lock:
            ids = list(self._sources.keys())
        for i in ids:
            frame = self.get_frame(i)
            if frame is not None:
                frames[i] = frame
        return frames

    def get_sources_status(self) -> list[dict]:
        """Get status of all input sources."""
        status = []
        with self._struct_lock:
            ids = sorted(self._sources.keys())
        for i in ids:
            source = self._sources.get(i)
            status.append({
                "id": i,
                "name": source.name if source else f"輸入 {i + 1}",
                "connected": source.connected if source else False,
                "has_frame": self._frames.get(i) is not None,
            })
        return status

    def start(self) -> None:
        """Start all input sources and their capture threads."""
        self._running = True
        with self._struct_lock:
            for source_id, source in self._sources.items():
                self._start_source(source_id, source)

    def stop(self) -> None:
        """Stop all capture threads and sources."""
        self._running = False
        with self._struct_lock:
            for source_id in list(self._sources.keys()):
                self._stop_source(source_id)
        logger.info("All input sources stopped")

    def _start_source(self, source_id: int, source: InputSource) -> None:
        """Start a single source's capture thread (must hold _struct_lock)."""
        if source.start():
            stop_event = threading.Event()
            self._stop_events[source_id] = stop_event
            thread = threading.Thread(
                target=self._capture_loop,
                args=(source_id, source, stop_event),
                daemon=True,
                name=f"Capture-{source_id}",
            )
            self._threads[source_id] = thread
            thread.start()
            logger.info("Started capture thread for source %d: %s", source_id, source.name)
        else:
            logger.warning("Failed to start source %d: %s", source_id, source.name)

    def _stop_source(self, source_id: int) -> None:
        """Stop a single source's capture thread (must hold _struct_lock)."""
        stop_event = self._stop_events.pop(source_id, None)
        if stop_event:
            stop_event.set()
        thread = self._threads.pop(source_id, None)
        if thread:
            thread.join(timeout=2.0)
        source = self._sources.get(source_id)
        if source:
            source.stop()

    def _capture_loop(self, source_id: int, source: InputSource, stop_event: threading.Event) -> None:
        """Continuous frame grabbing loop for a single source."""
        while not stop_event.is_set() and source.connected:
            try:
                frame = source.grab_frame()
                if frame is not None:
                    lock = self._frame_locks.get(source_id)
                    if lock:
                        with lock:
                            self._frames[source_id] = frame
                else:
                    time.sleep(0.01)
            except Exception:
                logger.exception("Error grabbing frame from source %d", source_id)
                time.sleep(0.1)
