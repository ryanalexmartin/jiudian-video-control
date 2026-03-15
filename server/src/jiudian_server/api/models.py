"""Pydantic request/response models for the REST API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """System status information."""
    fps: float = 0.0
    cpu_percent: float = 0.0
    ws_connections: int = 0
    uptime_seconds: float = 0.0
    dev_mode: bool = True
    num_inputs: int = 0
    num_outputs: int = 0


class InputStatusResponse(BaseModel):
    """Status of a single input source."""
    id: int
    name: str
    connected: bool
    has_frame: bool


class OutputStatusResponse(BaseModel):
    """Status of a single output."""
    id: int
    name: str
    active: bool
    active_scene_id: str | None = None
    source_type: str = "scene"
    source_id: str | int | None = None


class LayerRequest(BaseModel):
    """Layer definition in API requests."""
    input_id: int
    x: int = 0
    y: int = 0
    width: int = 1920
    height: int = 1080
    z_order: int = 0
    alpha: float = Field(1.0, ge=0.0, le=1.0)
    border_width: int = Field(0, ge=0)
    border_color: str = "#00C8FF"
    visible: bool = True


class SceneResponse(BaseModel):
    """Scene in API responses."""
    id: str
    name: str
    layers: list[LayerRequest]
    background_color: str = "#0B0B1E"
    is_default: bool = False


class CreateSceneRequest(BaseModel):
    """Request to create a new scene."""
    name: str
    layers: list[LayerRequest]
    background_color: str = "#0B0B1E"


class UpdateSceneRequest(BaseModel):
    """Request to update an existing scene."""
    name: str | None = None
    layers: list[LayerRequest] | None = None
    background_color: str | None = None


class ApplySceneRequest(BaseModel):
    """Request to apply a scene to an output."""
    transition: str = "fade"
    duration: float | None = None


class SourceSwitchRequest(BaseModel):
    """Request to quick-switch an output to a single input."""
    input_id: int
    transition: str = "fade"


class AddInputRequest(BaseModel):
    """Request to add a new input source."""
    type: str = "test_pattern"  # "test_pattern" or "camera"
    device_index: int = 0


class SetOutputSourceRequest(BaseModel):
    """Request to set an output window's source."""
    source_type: str  # "input" or "scene"
    source_id: int | str


class MessageResponse(BaseModel):
    """Generic response with a message."""
    status: str = "ok"
    message: str = ""


class CaptureDeviceResponse(BaseModel):
    """A detected capture device."""
    index: int
    name: str
    width: int
    height: int
