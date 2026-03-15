"""Re-export scene/layer models used by the config subsystem.

The canonical definitions live in ``compositing.models``; this module provides
a convenient import path for consumers that only need the data models without
pulling in the full compositing engine.
"""
from __future__ import annotations

from jiudian_server.compositing.models import Layer, Scene

__all__ = ["Layer", "Scene"]
