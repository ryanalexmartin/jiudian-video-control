"""FastAPI REST routes for the video control API."""
from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..compositing.models import Layer, Scene
from ..compositing.transitions import TransitionType
from .models import (
    AddInputRequest,
    ApplySceneRequest,
    CaptureDeviceResponse,
    CreateSceneRequest,
    InputStatusResponse,
    MessageResponse,
    OutputStatusResponse,
    SceneResponse,
    SetOutputSourceRequest,
    SourceSwitchRequest,
    SystemStatusResponse,
    UpdateSceneRequest,
)

if TYPE_CHECKING:
    from ..app import Application

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Application instance reference (set during server startup)
_app: "Application | None" = None


def set_app(app: "Application") -> None:
    """Set the application instance for route handlers."""
    global _app
    _app = app


def _get_app() -> "Application":
    if _app is None:
        raise HTTPException(status_code=503, detail="Server not ready")
    return _app


@router.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """Get system status."""
    app = _get_app()
    try:
        import psutil
        cpu = psutil.cpu_percent()
    except ImportError:
        cpu = 0.0

    num_inputs = len(app.input_manager.source_ids) if app.input_manager else 0

    return SystemStatusResponse(
        fps=app.pipeline.actual_fps if app.pipeline else 0.0,
        cpu_percent=cpu,
        ws_connections=getattr(app.api_server, 'ws_connection_count', 0) if app.api_server else 0,
        uptime_seconds=time.time() - app.start_time if app.start_time else 0.0,
        dev_mode=app.settings.dev_mode if app.settings else True,
        num_inputs=num_inputs,
        num_outputs=len(app.output_windows),
    )


@router.get("/inputs", response_model=list[InputStatusResponse])
async def list_inputs():
    """List all input sources and their status."""
    app = _get_app()
    if app.input_manager is None:
        return []
    return [InputStatusResponse(**s) for s in app.input_manager.get_sources_status()]


@router.post("/inputs", response_model=MessageResponse)
async def add_input(req: AddInputRequest):
    """Add a new input source."""
    app = _get_app()
    source_id = app.add_input_source(req.type, device_index=req.device_index)
    return MessageResponse(message=f"Added input {source_id} ({req.type})")


@router.delete("/inputs/{input_id}", response_model=MessageResponse)
async def remove_input(input_id: int):
    """Remove an input source."""
    app = _get_app()
    if not app.remove_input_source(input_id):
        raise HTTPException(404, f"Input {input_id} not found")
    return MessageResponse(message=f"Removed input {input_id}")


@router.get("/inputs/devices", response_model=list[CaptureDeviceResponse])
async def list_capture_devices():
    """Enumerate available capture devices."""
    from ..capture.enumerate import enumerate_capture_devices
    devices = enumerate_capture_devices()
    return [CaptureDeviceResponse(**d) for d in devices]


@router.get("/inputs/{input_id}/preview")
async def get_input_preview(input_id: int):
    """Get a JPEG preview thumbnail of an input."""
    app = _get_app()
    if app.preview_generator is None:
        raise HTTPException(404, "Preview not available")

    preview = app.preview_generator.get_preview(f"input_{input_id}")
    if preview is None:
        # Try to generate one from current frame
        if app.input_manager:
            frame = app.input_manager.get_frame(input_id)
            if frame is not None:
                preview = app.preview_generator.generate_preview(frame)

    if preview is None:
        raise HTTPException(404, "No frame available for this input")

    return Response(content=preview, media_type="image/jpeg")


@router.get("/outputs", response_model=list[OutputStatusResponse])
async def list_outputs():
    """List all outputs and their source info."""
    app = _get_app()
    outputs = []
    for output_id, window in sorted(app.output_windows.items()):
        outputs.append(OutputStatusResponse(
            id=output_id,
            name=window.name,
            active=window.active,
            active_scene_id=app.pipeline.active_scene.id if app.pipeline and app.pipeline.active_scene else None,
            source_type=window.source_type,
            source_id=window.source_id,
        ))
    return outputs


@router.post("/outputs/{output_id}/source", response_model=MessageResponse)
async def set_output_source(output_id: int, req: SetOutputSourceRequest):
    """Set an output window's source (input or scene)."""
    from .websocket import broadcast_state

    app = _get_app()
    window = app.output_windows.get(output_id)
    if window is None:
        raise HTTPException(404, f"Output {output_id} not found")
    window.set_source(req.source_type, req.source_id)
    await broadcast_state()
    return MessageResponse(message=f"Output {output_id} source set to {req.source_type}:{req.source_id}")


@router.get("/scenes", response_model=list[SceneResponse])
async def list_scenes():
    """List all available scenes."""
    app = _get_app()
    return [
        SceneResponse(
            id=s.id, name=s.name,
            layers=[l.model_dump() for l in s.layers],
            background_color=s.background_color,
            is_default=s.is_default,
        )
        for s in app.scenes.values()
    ]


@router.post("/scenes", response_model=SceneResponse)
async def create_scene(req: CreateSceneRequest):
    """Create a new scene."""
    app = _get_app()
    scene_id = f"custom_{uuid.uuid4().hex[:8]}"
    scene = Scene(
        id=scene_id,
        name=req.name,
        layers=[Layer(**l.model_dump()) for l in req.layers],
        background_color=req.background_color,
    )
    app.scenes[scene_id] = scene
    app.save_scenes()

    return SceneResponse(
        id=scene.id, name=scene.name,
        layers=[l.model_dump() for l in scene.layers],
        background_color=scene.background_color,
    )


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(scene_id: str, req: UpdateSceneRequest):
    """Update an existing scene."""
    app = _get_app()
    scene = app.scenes.get(scene_id)
    if scene is None:
        raise HTTPException(404, f"Scene '{scene_id}' not found")

    if req.name is not None:
        scene.name = req.name
    if req.layers is not None:
        scene.layers = [Layer(**l.model_dump()) for l in req.layers]
    if req.background_color is not None:
        scene.background_color = req.background_color

    app.scenes[scene_id] = scene
    app.save_scenes()

    return SceneResponse(
        id=scene.id, name=scene.name,
        layers=[l.model_dump() for l in scene.layers],
        background_color=scene.background_color,
        is_default=scene.is_default,
    )


@router.post("/scenes/{scene_id}/apply", response_model=MessageResponse)
async def apply_scene(scene_id: str, req: ApplySceneRequest | None = None):
    """Apply a scene to the output with optional transition."""
    app = _get_app()
    if scene_id not in app.scenes:
        raise HTTPException(404, f"Scene '{scene_id}' not found")

    transition = req.transition if req else "fade"
    duration = req.duration if req else None
    app.apply_scene(scene_id, transition=transition, duration=duration)

    return MessageResponse(message=f"Applied scene '{scene_id}' with {transition} transition")
