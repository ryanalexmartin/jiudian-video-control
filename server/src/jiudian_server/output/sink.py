"""Abstract base class for output sinks."""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class OutputSink(ABC):
    """Abstract base for video output destinations."""

    def __init__(self, output_id: int, name: str):
        self.output_id = output_id
        self.name = name
        self.active: bool = False

    @abstractmethod
    def start(self) -> bool:
        """Initialize the output. Returns True if successful."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Release the output resources."""
        ...

    @abstractmethod
    def display_frame(self, frame: np.ndarray) -> None:
        """Display a BGR frame on the output."""
        ...
