"""WebSocket handler for real-time state sync and preview streaming."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from ..app import Application

logger = logging.getLogger(__name__)

ws_router = APIRouter()

# Active WebSocket connections
_connections: set[WebSocket] = set()
_app: "Application | None" = None


def set_app(app: "Application") -> None:
    """Set the application instance for WebSocket handler."""
    global _app
    _app = app


def get_connection_count() -> int:
    return len(_connections)


async def broadcast_state() -> None:
    """Broadcast current state to all connected clients."""
    if _app is None:
        return

    state = _build_state_message()
    message = json.dumps(state)

    disconnected = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    _connections.difference_update(disconnected)


def _build_state_message() -> dict:
    """Build a state_sync message with current system state."""
    if _app is None:
        return {"type": "state_sync", "data": {}}

    # Active scene info
    active_scene = None
    if _app.pipeline and _app.pipeline.active_scene:
        scene = _app.pipeline.active_scene
        active_scene = {
            "id": scene.id,
            "name": scene.name,
        }

    # Input status (dynamic)
    inputs = []
    if _app.input_manager:
        inputs = _app.input_manager.get_sources_status()

    # Scene list
    scenes = [
        {"id": s.id, "name": s.name, "is_default": s.is_default}
        for s in _app.scenes.values()
    ]

    # Output windows with per-output source info
    outputs = []
    for output_id, window in sorted(_app.output_windows.items()):
        outputs.append({
            "id": output_id,
            "name": window.name,
            "active": window.active,
            "source_type": window.source_type,
            "source_id": window.source_id,
        })

    return {
        "type": "state_sync",
        "data": {
            "active_scene": active_scene,
            "inputs": inputs,
            "scenes": scenes,
            "outputs": outputs,
            "fps": _app.pipeline.actual_fps if _app.pipeline else 0,
            "timestamp": time.time(),
        },
    }


async def _send_preview_frame(ws: WebSocket) -> None:
    """Send the current output preview as base64 JPEG."""
    if _app is None or _app.preview_generator is None:
        return

    preview = _app.preview_generator.get_preview("output_0")
    if preview is None:
        return

    b64 = base64.b64encode(preview).decode("ascii")
    message = json.dumps({
        "type": "preview_frame",
        "data": {
            "output_id": 0,
            "frame": b64,
        },
    })
    try:
        await ws.send_text(message)
    except Exception:
        pass


async def _handle_command(ws: WebSocket, data: dict) -> None:
    """Handle an incoming command from a WebSocket client."""
    cmd_type = data.get("command")

    if cmd_type == "apply_scene":
        scene_id = data.get("scene_id")
        transition = data.get("transition", "fade")
        if scene_id and _app:
            _app.apply_scene(scene_id, transition=transition)
            await broadcast_state()

    elif cmd_type == "switch_input":
        input_id = data.get("input_id")
        if input_id is not None and _app:
            scene_id = f"fullscreen_{input_id + 1}"
            _app.apply_scene(scene_id, transition="fade")
            await broadcast_state()

    elif cmd_type == "set_output_input":
        output_id = data.get("output_id")
        input_id = data.get("input_id")
        if output_id is not None and input_id is not None and _app:
            _app.set_output_input(int(output_id), int(input_id))
            await broadcast_state()

    elif cmd_type == "get_state":
        state = _build_state_message()
        await ws.send_text(json.dumps(state))

    elif cmd_type == "get_preview":
        await _send_preview_frame(ws)

    else:
        await ws.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown command: {cmd_type}",
        }))


@ws_router.websocket("/ws/control")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time control and preview streaming."""
    await ws.accept()
    _connections.add(ws)
    logger.info("WebSocket client connected (%d total)", len(_connections))

    try:
        # Send initial state
        state = _build_state_message()
        await ws.send_text(json.dumps(state))

        # Start preview streaming task
        preview_task = asyncio.create_task(_preview_stream_loop(ws))

        # Listen for commands
        while True:
            text = await ws.receive_text()
            try:
                data = json.loads(text)
                await _handle_command(ws, data)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                }))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        _connections.discard(ws)
        logger.info("WebSocket connections: %d", len(_connections))


async def _preview_stream_loop(ws: WebSocket) -> None:
    """Periodically send preview frames to a WebSocket client."""
    try:
        while ws in _connections:
            await _send_preview_frame(ws)
            await asyncio.sleep(0.2)  # ~5 FPS preview
    except Exception:
        pass
