"""Application lifecycle: initializes and wires all components together."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .api.server import ApiServer
from .capture.manager import InputManager
from .capture.test_patterns import create_test_pattern
from .capture.directshow import CameraCaptureSource
from .capture.window_capture import WindowCaptureSource
from .compositing.models import Layer, Scene
from .compositing.pipeline import CompositorPipeline
from .compositing.transitions import TransitionType
from .config.defaults import generate_default_scenes
from .config.persistence import load_inputs, save_inputs
from .gui.main_window import MainWindow
from .gui.theme import DARK_NEON_QSS
from .output.display import OutputWindow
from .output.preview import PreviewGenerator
from .utils.qr_code import generate_qr_pixmap, get_local_ip

logger = logging.getLogger(__name__)


class Application:
    """Main application that wires together all components."""

    def __init__(
        self,
        dev_mode: bool = True,
        api_port: int = 8080,
        api_host: str = "0.0.0.0",
        config_dir: str | None = None,
        width: int = 1920,
        height: int = 1080,
        target_fps: int = 30,
    ):
        self.dev_mode = dev_mode
        self.api_port = api_port
        self.api_host = api_host
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".jiudian"
        self.width = width
        self.height = height
        self.target_fps = target_fps

        # Components (initialized in start())
        self.input_manager: Optional[InputManager] = None
        self.pipeline: Optional[CompositorPipeline] = None
        self.output_windows: dict[int, OutputWindow] = {}
        self._next_output_id: int = 0
        self.preview_generator: Optional[PreviewGenerator] = None
        self.api_server: Optional[ApiServer] = None
        self.main_window: Optional[MainWindow] = None
        self.scenes: dict[str, Scene] = {}
        self.settings: Optional[object] = None
        self.start_time: float = 0.0

        # Frame delivery timer
        self._frame_timer: Optional[QTimer] = None

        # Input config tracking
        self._input_configs: list[dict] = []
        self._next_input_id: int = 0

        # Create a simple settings-like object for compatibility
        class _Settings:
            pass
        self.settings = _Settings()
        self.settings.dev_mode = dev_mode

    def start(self, qt_app: QApplication) -> MainWindow:
        """Initialize all components and return the main window."""
        self.start_time = time.time()
        logger.info("Starting 酒店影像控制系統...")

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Setup input sources (loads from config or uses defaults)
        self._setup_inputs()

        # Load scenes (defaults + saved) based on active inputs
        self._regenerate_default_scenes()
        self._load_saved_scenes()

        # Setup compositing pipeline
        self.pipeline = CompositorPipeline(
            self.input_manager,
            width=self.width,
            height=self.height,
            target_fps=self.target_fps,
        )

        # Setup preview generator
        self.preview_generator = PreviewGenerator(
            width=320, height=180, quality=70,
        )

        # Setup one default output window (not auto-shown)
        self._setup_outputs()

        # Apply default scene
        if self.input_manager.source_ids:
            first_id = self.input_manager.source_ids[0]
            default_scene_id = f"fullscreen_{first_id + 1}"
            default_scene = self.scenes.get(default_scene_id)
            if default_scene:
                self.pipeline.set_scene(default_scene)

        # Start components
        self.input_manager.start()
        self.pipeline.start()

        # Start frame delivery timer (~30fps)
        self._frame_timer = QTimer()
        self._frame_timer.timeout.connect(self._deliver_frames)
        self._frame_timer.start(33)  # ~30fps

        # Setup API server
        self.api_server = ApiServer(self, host=self.api_host, port=self.api_port)
        self.api_server.start()

        # Create and setup main window
        qt_app.setStyleSheet(DARK_NEON_QSS)
        self.main_window = MainWindow(self)

        # Set server address and QR code
        local_ip = get_local_ip()
        server_url = f"http://{local_ip}:{self.api_port}"
        self.main_window.set_server_address(f"{local_ip}:{self.api_port}")

        qr_pixmap = generate_qr_pixmap(server_url)
        if qr_pixmap:
            self.main_window.set_qr_pixmap(qr_pixmap)

        logger.info("System ready. API at %s", server_url)
        return self.main_window

    # ── Input Management ───────────────────────────────────────────

    def _setup_inputs(self) -> None:
        """Initialize exactly 4 input sources (IDs 0-3) from saved config or defaults."""
        self.input_manager = InputManager()

        saved = load_inputs(self.config_dir)
        # Build a lookup of saved configs keyed by ID (only IDs 0-3)
        saved_by_id: dict[int, dict] = {}
        if saved:
            for entry in saved:
                sid = entry["id"]
                if 0 <= sid <= 3:
                    saved_by_id[sid] = entry

        for i in range(4):
            if i in saved_by_id:
                entry = saved_by_id[i]
                if entry["type"] == "test_pattern":
                    source = create_test_pattern(i, self.width, self.height)
                elif entry["type"] == "window":
                    source = WindowCaptureSource(
                        i,
                        entry.get("window_id", 0),
                        target_fps=self.target_fps,
                        owner_name=entry.get("owner_name", ""),
                        window_name=entry.get("window_name", ""),
                    )
                else:
                    device_idx = entry.get("device_index", i)
                    source = CameraCaptureSource(
                        i, device_idx,
                        width=self.width, height=self.height,
                        fps=self.target_fps,
                    )
                self._input_configs.append(entry)
            else:
                # Default: test pattern in dev mode, camera in prod
                if self.dev_mode:
                    source = create_test_pattern(i, self.width, self.height)
                    self._input_configs.append({"id": i, "type": "test_pattern", "device_index": i})
                else:
                    source = CameraCaptureSource(
                        i, i, width=self.width, height=self.height, fps=self.target_fps,
                    )
                    self._input_configs.append({"id": i, "type": "camera", "device_index": i})
            self.input_manager.add_source(i, source)

        self._next_input_id = 4
        self._save_input_config()
        logger.info(
            "Input sources configured: 4 (%s mode)",
            "dev/test" if self.dev_mode else "capture",
        )

    def add_input_source(self, source_type: str, device_index: int = 0) -> int:
        """Add a new input source dynamically.

        Args:
            source_type: "test_pattern" or "camera"
            device_index: capture device index (for cameras)

        Returns:
            The new source ID.
        """
        source_id = self._next_input_id
        self._next_input_id += 1

        if source_type == "test_pattern":
            source = create_test_pattern(source_id, self.width, self.height)
        else:
            source = CameraCaptureSource(
                source_id, device_index,
                width=self.width, height=self.height, fps=self.target_fps,
            )

        self.input_manager.add_source(source_id, source)
        self._input_configs.append({
            "id": source_id,
            "type": source_type,
            "device_index": device_index,
        })

        # Regenerate default scenes and save
        self._regenerate_default_scenes()
        self._save_input_config()

        # Notify output windows and GUI
        self._refresh_output_source_lists()

        logger.info("Added input source %d (%s)", source_id, source_type)
        return source_id

    def remove_input_source(self, source_id: int) -> bool:
        """Remove an input source dynamically."""
        if source_id not in self.input_manager.source_ids:
            return False

        self.input_manager.remove_source(source_id)
        self._input_configs = [c for c in self._input_configs if c["id"] != source_id]

        # Regenerate default scenes and save
        self._regenerate_default_scenes()
        self._save_input_config()

        # Notify output windows and GUI
        self._refresh_output_source_lists()

        logger.info("Removed input source %d", source_id)
        return True

    def reconfigure_input(
        self,
        source_id: int,
        source_type: str,
        device_index: int = 0,
        window_id: int = 0,
        owner_name: str = "",
        window_name: str = "",
    ) -> bool:
        """Replace an input slot with a new source type.

        Args:
            source_id: Slot to reconfigure (0-3).
            source_type: "test_pattern", "camera", or "window".
            device_index: Capture device index (for cameras).
            window_id: macOS CGWindowID (for window capture).
            owner_name: Window owner application name.
            window_name: Window title.
        """
        if source_id < 0 or source_id > 3:
            return False

        # Remove old source
        self.input_manager.remove_source(source_id)

        # Create new source
        if source_type == "test_pattern":
            source = create_test_pattern(source_id, self.width, self.height)
            config = {"id": source_id, "type": source_type, "device_index": device_index}
        elif source_type == "window":
            source = WindowCaptureSource(
                source_id, window_id,
                target_fps=self.target_fps,
                owner_name=owner_name,
                window_name=window_name,
            )
            config = {
                "id": source_id, "type": "window",
                "window_id": window_id,
                "owner_name": owner_name,
                "window_name": window_name,
            }
        else:
            source = CameraCaptureSource(
                source_id, device_index,
                width=self.width, height=self.height, fps=self.target_fps,
            )
            config = {"id": source_id, "type": source_type, "device_index": device_index}

        self.input_manager.add_source(source_id, source)

        # Update config
        self._input_configs = [c for c in self._input_configs if c["id"] != source_id]
        self._input_configs.append(config)
        self._input_configs.sort(key=lambda c: c["id"])
        self._save_input_config()

        logger.info("Reconfigured input %d -> %s", source_id, source_type)
        return True

    def _save_input_config(self) -> None:
        """Persist current input configuration."""
        save_inputs(self.config_dir, self._input_configs)

    def _regenerate_default_scenes(self) -> None:
        """Regenerate default scenes based on current input IDs."""
        input_ids = self.input_manager.source_ids if self.input_manager else [0, 1, 2, 3]
        new_defaults = generate_default_scenes(input_ids)

        # Remove old default scenes, keep user scenes
        user_scenes = {sid: s for sid, s in self.scenes.items() if not s.is_default}
        self.scenes = {s.id: s for s in new_defaults}
        self.scenes.update(user_scenes)

    def _refresh_output_source_lists(self) -> None:
        """No-op: outputs are now fixed (A/B) with simple input buttons."""
        pass

    # ── Output Management ──────────────────────────────────────────

    def _setup_outputs(self) -> None:
        """Create exactly two output windows (A and B)."""
        self.create_output_window()  # Output A (id=0)
        self.create_output_window()  # Output B (id=1)

    def create_output_window(self) -> OutputWindow:
        """Create a new output window and return it."""
        output_id = self._next_output_id
        self._next_output_id += 1

        window = OutputWindow(output_id, self)
        window.closed.connect(self._on_output_window_closed)
        self.output_windows[output_id] = window
        logger.info("Created output window %d", output_id)
        return window

    def close_output_window(self, output_id: int) -> None:
        """Close and remove an output window."""
        window = self.output_windows.pop(output_id, None)
        if window:
            window.stop()
            logger.info("Closed output window %d", output_id)

    def _on_output_window_closed(self, output_id: int) -> None:
        """Handle an output window being closed by the user."""
        self.output_windows.pop(output_id, None)

    # ── Frame Delivery ─────────────────────────────────────────────

    def _deliver_frames(self) -> None:
        """Timer callback: deliver frames to all output windows and previews."""
        if not self.input_manager or not self.pipeline:
            return

        # Get pipeline frame (for scene-based outputs)
        pipeline_frame = self.pipeline.current_frame

        # Deliver to each output window
        for window in list(self.output_windows.values()):
            if not window.active:
                continue
            try:
                frame = self._get_frame_for_output(window, pipeline_frame)
                if frame is not None:
                    window.display_frame(frame)
            except Exception:
                logger.exception("Error delivering frame to output %d", window.output_id)

        # Update preview generator
        if self.preview_generator:
            if pipeline_frame is not None:
                self.preview_generator.update_preview("output_0", pipeline_frame)
            for sid in self.input_manager.source_ids:
                input_frame = self.input_manager.get_frame(sid)
                if input_frame is not None:
                    self.preview_generator.update_preview(f"input_{sid}", input_frame)

    def _get_frame_for_output(self, window: OutputWindow, pipeline_frame) -> Optional:
        """Get the appropriate frame for an output window based on its source selection."""
        if window.source_type == "input":
            # Raw input frame
            return self.input_manager.get_frame(window.source_id)
        else:
            # Scene-based: if it's the active scene, use pipeline frame
            active_scene = self.pipeline.active_scene if self.pipeline else None
            if active_scene and active_scene.id == window.source_id:
                return pipeline_frame
            else:
                # Render the selected scene on-demand
                scene = self.scenes.get(window.source_id)
                if scene and self.pipeline:
                    input_frames = self.input_manager.get_all_frames()
                    return self.pipeline.renderer.render(scene, input_frames)
                return pipeline_frame  # Fallback

    def set_output_input(self, output_id: int, input_id: int) -> bool:
        """Set an output window to show a specific input source."""
        window = self.output_windows.get(output_id)
        if window is None:
            logger.warning("Output %d not found", output_id)
            return False
        window.set_source("input", input_id)
        logger.info("Output %d now showing input %d", output_id, input_id)
        return True

    # ── Scene Management ───────────────────────────────────────────

    def apply_scene(
        self,
        scene_id: str,
        transition: str = "fade",
        duration: float | None = None,
    ) -> bool:
        """Apply a scene to the pipeline."""
        scene = self.scenes.get(scene_id)
        if scene is None:
            logger.warning("Scene not found: %s", scene_id)
            return False

        try:
            trans_type = TransitionType(transition)
        except ValueError:
            trans_type = TransitionType.FADE

        if self.pipeline:
            if duration is not None:
                self.pipeline.transition_engine.default_duration = duration
            self.pipeline.set_scene(scene, trans_type)

        logger.info("Applied scene: %s (%s)", scene.name, transition)
        return True

    def save_scenes(self) -> None:
        """Save custom scenes to JSON file."""
        import json
        custom_scenes = {
            sid: s.model_dump()
            for sid, s in self.scenes.items()
            if not s.is_default
        }
        scenes_file = self.config_dir / "scenes.json"
        scenes_file.write_text(json.dumps(custom_scenes, ensure_ascii=False, indent=2))
        logger.info("Saved %d custom scenes", len(custom_scenes))

    def _load_saved_scenes(self) -> None:
        """Load custom scenes from JSON file."""
        import json
        scenes_file = self.config_dir / "scenes.json"
        if scenes_file.exists():
            try:
                data = json.loads(scenes_file.read_text())
                for sid, scene_data in data.items():
                    self.scenes[sid] = Scene(**scene_data)
                logger.info("Loaded %d custom scenes", len(data))
            except Exception:
                logger.exception("Error loading saved scenes")

    # ── Shutdown ───────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Gracefully shut down all components."""
        logger.info("Shutting down...")

        if self._frame_timer:
            self._frame_timer.stop()

        if self.pipeline:
            self.pipeline.stop()

        if self.input_manager:
            self.input_manager.stop()

        for window in list(self.output_windows.values()):
            window.stop()
        self.output_windows.clear()

        if self.api_server:
            self.api_server.stop()

        logger.info("Shutdown complete")
