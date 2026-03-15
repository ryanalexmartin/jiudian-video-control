"""Abstract base class for input sources."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class InputSource(ABC):
    """Abstract base for video input sources (capture cards, test patterns, etc.)."""

    def __init__(self, source_id: int, name: str):
        self.source_id = source_id
        self.name = name
        self.connected: bool = False

    @abstractmethod
    def start(self) -> bool:
        """Start capturing. Returns True if successful."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop capturing and release resources."""
        ...

    @abstractmethod
    def grab_frame(self) -> Optional[np.ndarray]:
        """Grab a single BGR frame. Returns None if unavailable."""
        ...
