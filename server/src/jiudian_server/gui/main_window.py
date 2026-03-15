"""Main application window for the desktop GUI."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QTimer, QSize, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QStatusBar,
    QComboBox,
    QTabWidget,
    QDialog,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
)

from ..i18n import t, set_language, get_language, on_language_change
from .widgets import NeonButton, PreviewWidget

if TYPE_CHECKING:
    from ..app import Application

logger = logging.getLogger(__name__)

# Output labels (A, B)
_OUTPUT_LABELS = ["A", "B"]


class InputConfigDialog(QDialog):
    """Dialog to configure an input slot (test pattern, camera, or window capture)."""

    def __init__(
        self,
        source_id: int,
        current_type: str,
        current_device: int,
        app_instance: "Application",
        current_window_id: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.source_id = source_id
        self._app = app_instance
        self.setWindowTitle(t("configure_input", n=source_id + 1))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Status section ──────────────────────────────────────────
        status_group = QGroupBox(t("input_status"))
        status_layout = QGridLayout(status_group)

        source = app_instance.input_manager.get_source(source_id) if app_instance.input_manager else None
        is_active = source.connected if source else False
        status_text = t("input_connected") if is_active else t("input_disconnected")
        status_color = "#00FF88" if is_active else "#FF4444"

        status_layout.addWidget(QLabel(t("input_status") + ":"), 0, 0)
        status_val = QLabel(status_text)
        status_val.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        status_layout.addWidget(status_val, 0, 1)

        # Resolution from current frame
        frame = app_instance.input_manager.get_frame(source_id) if app_instance.input_manager else None
        if frame is not None:
            h, w = frame.shape[:2]
            res_text = f"{w} x {h}"
        else:
            res_text = "—"
        status_layout.addWidget(QLabel(t("input_resolution") + ":"), 1, 0)
        res_val = QLabel(res_text)
        res_val.setStyleSheet("color: #00C8FF;")
        status_layout.addWidget(res_val, 1, 1)

        layout.addWidget(status_group)

        # ── Type selection ──────────────────────────────────────────
        type_label = QLabel(t("input_type") + ":")
        type_label.setStyleSheet("color: #8888AA; font-weight: bold;")
        layout.addWidget(type_label)

        self._type_group = QButtonGroup(self)
        self._radio_test = QRadioButton(t("test_pattern"))
        self._radio_camera = QRadioButton(t("camera"))
        self._radio_window = QRadioButton(t("window_capture"))
        self._type_group.addButton(self._radio_test, 0)
        self._type_group.addButton(self._radio_camera, 1)
        self._type_group.addButton(self._radio_window, 2)

        if current_type == "camera":
            self._radio_camera.setChecked(True)
        elif current_type == "window":
            self._radio_window.setChecked(True)
        else:
            self._radio_test.setChecked(True)

        layout.addWidget(self._radio_test)
        layout.addWidget(self._radio_camera)
        layout.addWidget(self._radio_window)

        # ── Camera section ──────────────────────────────────────────
        self._camera_group = QGroupBox(t("available_cameras"))
        camera_layout = QVBoxLayout(self._camera_group)
        self._camera_list = QListWidget()
        self._camera_list.setMaximumHeight(120)
        camera_layout.addWidget(self._camera_list)
        layout.addWidget(self._camera_group)

        # Populate camera list
        self._camera_devices: list[dict] = []
        self._populate_cameras(current_device)

        # ── Window section ──────────────────────────────────────────
        self._window_group = QGroupBox(t("available_windows"))
        window_layout = QVBoxLayout(self._window_group)
        self._window_list = QListWidget()
        self._window_list.setMaximumHeight(180)
        window_layout.addWidget(self._window_list)

        refresh_btn = QPushButton(t("refresh_windows"))
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._populate_windows)
        window_layout.addWidget(refresh_btn)
        layout.addWidget(self._window_group)

        # Populate window list
        self._window_entries: list[dict] = []
        self._populate_windows(select_window_id=current_window_id)

        # ── Show/hide sections based on type ────────────────────────
        self._type_group.idToggled.connect(self._on_type_changed)
        self._on_type_changed()

        # ── OK / Cancel ─────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_cameras(self, select_device: int = 0) -> None:
        """Enumerate cameras and fill the camera list."""
        from ..capture.enumerate import enumerate_capture_devices
        self._camera_list.clear()
        self._camera_devices = enumerate_capture_devices()

        if not self._camera_devices:
            item = QListWidgetItem(t("no_devices_found"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._camera_list.addItem(item)
            return

        for dev in self._camera_devices:
            text = f"Camera {dev['index']} — {dev['width']}x{dev['height']}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, dev["index"])
            self._camera_list.addItem(item)
            if dev["index"] == select_device:
                self._camera_list.setCurrentItem(item)

    def _populate_windows(self, select_window_id: int = 0) -> None:
        """Enumerate macOS windows and fill the window list."""
        from ..capture.enumerate_windows import enumerate_windows
        self._window_list.clear()
        self._window_entries = enumerate_windows()

        if not self._window_entries:
            item = QListWidgetItem(t("no_windows_found"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._window_list.addItem(item)
            return

        for entry in self._window_entries:
            b = entry["bounds"]
            title = entry["window_name"]
            owner = entry["owner_name"]
            label = f"{owner}: {title}" if title else owner
            text = f"{label} ({b['width']}x{b['height']})"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry["window_id"])
            self._window_list.addItem(item)
            if entry["window_id"] == select_window_id:
                self._window_list.setCurrentItem(item)

    def _on_type_changed(self) -> None:
        is_camera = self._radio_camera.isChecked()
        is_window = self._radio_window.isChecked()
        self._camera_group.setVisible(is_camera)
        self._window_group.setVisible(is_window)
        self.adjustSize()

    @property
    def selected_type(self) -> str:
        if self._radio_camera.isChecked():
            return "camera"
        if self._radio_window.isChecked():
            return "window"
        return "test_pattern"

    @property
    def selected_device_index(self) -> int:
        item = self._camera_list.currentItem()
        if item is not None:
            val = item.data(Qt.ItemDataRole.UserRole)
            if val is not None:
                return int(val)
        return 0

    @property
    def selected_window_info(self) -> dict:
        """Return {window_id, owner_name, window_name} for the selected window."""
        item = self._window_list.currentItem()
        if item is None:
            return {"window_id": 0, "owner_name": "", "window_name": ""}
        wid = item.data(Qt.ItemDataRole.UserRole)
        if wid is None:
            return {"window_id": 0, "owner_name": "", "window_name": ""}
        for entry in self._window_entries:
            if entry["window_id"] == wid:
                return {
                    "window_id": entry["window_id"],
                    "owner_name": entry["owner_name"],
                    "window_name": entry["window_name"],
                }
        return {"window_id": int(wid), "owner_name": "", "window_name": ""}


class MainWindow(QMainWindow):
    """Desktop GUI main window with fixed 4 inputs and 2 outputs (A/B)."""

    def __init__(self, app_instance: "Application"):
        super().__init__()
        self.app_instance = app_instance
        self._input_previews: dict[int, PreviewWidget] = {}
        self._output_previews: dict[int, PreviewWidget] = {}

        # Per-output input selector buttons: {output_id: {input_id: QPushButton}}
        self._input_select_btns: dict[int, dict[int, QPushButton]] = {}

        self.setWindowTitle(t("app_title"))
        self.setMinimumSize(1280, 720)
        self.resize(1440, 900)

        self._build_ui()
        self._setup_timers()

        on_language_change(self._retranslate_ui)

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ── Left panel: previews ─────────────────────────────────
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        self._output_group_box = QGroupBox(t("output_preview"))
        self._build_output_section(self._output_group_box)
        left_panel.addWidget(self._output_group_box)

        self._inputs_group = QGroupBox(t("input_preview"))
        self._build_inputs_section(self._inputs_group)
        left_panel.addWidget(self._inputs_group)

        left_panel.addStretch()
        main_layout.addLayout(left_panel, stretch=3)

        # ── Right panel: routing + connection tabs ───────────────
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        # Language toggle
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self._lang_label = QLabel(t("language") + ":")
        self._lang_label.setStyleSheet("color: #8888AA;")
        lang_row.addWidget(self._lang_label)
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("繁體中文", "zh_tw")
        self._lang_combo.addItem("English", "en")
        if get_language() == "en":
            self._lang_combo.setCurrentIndex(1)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self._lang_combo.setFixedWidth(120)
        lang_row.addWidget(self._lang_combo)
        right_panel.addLayout(lang_row)

        self._right_tabs = QTabWidget()
        self._routing_tab = self._build_routing_tab()
        self._connection_tab = self._build_connection_tab()
        self._right_tabs.addTab(self._routing_tab, t("io_control"))
        self._right_tabs.addTab(self._connection_tab, t("connection_info"))
        right_panel.addWidget(self._right_tabs)
        main_layout.addLayout(right_panel, stretch=2)

        # ── Status bar ───────────────────────────────────────────
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._fps_label = QLabel("FPS: --")
        self._fps_label.setStyleSheet("color: #00C8FF; font-weight: bold;")
        self._cpu_label = QLabel("CPU: --%")
        self._cpu_label.setStyleSheet("color: #8888AA;")
        self._conn_label = QLabel(f"{t('connections')}: 0")
        self._conn_label.setStyleSheet("color: #8888AA;")
        self._status_bar.addPermanentWidget(self._fps_label)
        self._status_bar.addPermanentWidget(self._cpu_label)
        self._status_bar.addPermanentWidget(self._conn_label)
        self._status_bar.showMessage(t("started"))

    # ── Output Previews (A and B) ────────────────────────────────────

    def _build_output_section(self, group: QGroupBox) -> None:
        layout = QHBoxLayout(group)
        layout.setSpacing(12)
        for output_id, label_letter in enumerate(_OUTPUT_LABELS):
            preview = PreviewWidget(
                output_id,
                t("output_n", n=label_letter),
                preview_size=QSize(320, 180),
            )
            self._output_previews[output_id] = preview
            layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Input Grid (fixed 4 inputs) with configure buttons ───────────

    def _build_inputs_section(self, group: QGroupBox) -> None:
        self._inputs_layout = QVBoxLayout(group)
        self._input_grid_widget = QWidget()
        self._input_grid = QGridLayout(self._input_grid_widget)
        self._input_grid.setSpacing(8)
        self._inputs_layout.addWidget(self._input_grid_widget)
        self._refresh_input_previews()

    def _refresh_input_previews(self) -> None:
        """Rebuild the input preview grid with configure buttons."""
        for preview in self._input_previews.values():
            preview.setParent(None)
            preview.deleteLater()
        self._input_previews.clear()

        # Clear all items from grid
        while self._input_grid.count():
            item = self._input_grid.takeAt(0)
            w = item.widget()
            if w and w not in self._input_previews.values():
                w.setParent(None)
                w.deleteLater()

        if not self.app_instance.input_manager:
            return

        source_ids = self.app_instance.input_manager.source_ids
        for idx, sid in enumerate(source_ids):
            # Container for preview + configure button
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            # Input type label
            input_type = self._get_input_type(sid)
            if input_type == "window":
                type_text = t("window_capture")
            elif input_type == "camera":
                type_text = t("camera")
            else:
                type_text = t("test_pattern")
            label = f"{t('input_n', n=sid + 1)} [{type_text}]"
            preview = PreviewWidget(sid, label, preview_size=QSize(280, 158))
            self._input_previews[sid] = preview
            container_layout.addWidget(preview)

            # Configure button
            cfg_btn = QPushButton(t("configure"))
            cfg_btn.setFixedHeight(24)
            cfg_btn.setStyleSheet(
                "QPushButton { color: #8888AA; background: rgba(0,200,255,10); "
                "border: 1px solid #8888AA; border-radius: 4px; font-size: 11px; }"
                "QPushButton:hover { color: #00C8FF; border-color: #00C8FF; "
                "background: rgba(0,200,255,25); }"
            )
            cfg_btn.clicked.connect(
                lambda checked, s=sid: self._on_configure_input(s)
            )
            container_layout.addWidget(cfg_btn)

            row, col = divmod(idx, 2)
            self._input_grid.addWidget(container, row, col)

    def _get_input_type(self, source_id: int) -> str:
        """Get the current type of an input source from config."""
        for cfg in self.app_instance._input_configs:
            if cfg["id"] == source_id:
                return cfg.get("type", "test_pattern")
        return "test_pattern"

    def _get_input_device_index(self, source_id: int) -> int:
        """Get the current device index of an input source from config."""
        for cfg in self.app_instance._input_configs:
            if cfg["id"] == source_id:
                return cfg.get("device_index", source_id)
        return source_id

    def _get_input_window_id(self, source_id: int) -> int:
        """Get the current window_id of an input source from config."""
        for cfg in self.app_instance._input_configs:
            if cfg["id"] == source_id:
                return cfg.get("window_id", 0)
        return 0

    def _on_configure_input(self, source_id: int) -> None:
        """Open configuration dialog for an input slot."""
        current_type = self._get_input_type(source_id)
        current_device = self._get_input_device_index(source_id)
        current_window_id = self._get_input_window_id(source_id)

        dialog = InputConfigDialog(
            source_id, current_type, current_device,
            self.app_instance, current_window_id, self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_type = dialog.selected_type

            if new_type == "window":
                win_info = dialog.selected_window_info
                self.app_instance.reconfigure_input(
                    source_id, "window",
                    window_id=win_info["window_id"],
                    owner_name=win_info["owner_name"],
                    window_name=win_info["window_name"],
                )
            else:
                new_device = dialog.selected_device_index
                self.app_instance.reconfigure_input(source_id, new_type, new_device)

            self._refresh_input_previews()
            logger.info("Reconfigured input %d: %s", source_id, new_type)

    # ── Routing Tab ─────────────────────────────────────────────────

    def _build_routing_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)

        # Build routing section for each output (A, B)
        for output_id, label_letter in enumerate(_OUTPUT_LABELS):
            self._build_output_routing(layout, output_id, label_letter)

        layout.addStretch()
        return tab

    def _build_output_routing(
        self, parent_layout: QVBoxLayout, output_id: int, label_letter: str,
    ) -> None:
        """Build an output routing section: label + [1][2][3][4] + show/hide + fullscreen."""
        group = QGroupBox(f"{t('output_n', n=label_letter)}")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        # Input selector buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        input_label = QLabel(t("source") + ":")
        input_label.setStyleSheet("color: #8888AA;")
        btn_row.addWidget(input_label)

        self._input_select_btns[output_id] = {}

        for input_id in range(4):
            btn = QPushButton(str(input_id + 1))
            btn.setFixedSize(48, 36)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { color: #00C8FF; background: rgba(0,200,255,15); "
                "border: 1px solid #00C8FF; border-radius: 6px; "
                "font-size: 16px; font-weight: bold; }"
                "QPushButton:hover { background: rgba(0,200,255,40); }"
                "QPushButton:checked { background: rgba(0,200,255,80); "
                "color: #0B0B1E; font-weight: bold; }"
            )
            btn.clicked.connect(
                lambda checked, oid=output_id, iid=input_id: self._on_select_input(oid, iid)
            )
            btn_row.addWidget(btn)
            self._input_select_btns[output_id][input_id] = btn

        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        # Control buttons row: show/hide + fullscreen
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)

        show_btn = NeonButton(t("show"))
        show_btn.setFixedWidth(80)

        def toggle_show(checked, oid=output_id, b=show_btn):
            w = self.app_instance.output_windows.get(oid)
            if w:
                if w.active:
                    w.stop()
                    b.setText(t("show"))
                else:
                    w.start()
                    b.setText(t("hide"))

        show_btn.clicked.connect(toggle_show)
        ctrl_row.addWidget(show_btn)

        fs_btn = NeonButton(t("fullscreen"))
        fs_btn.setFixedWidth(100)

        def toggle_fs(checked, oid=output_id):
            w = self.app_instance.output_windows.get(oid)
            if w:
                if w._is_fullscreen:
                    w.exit_fullscreen()
                else:
                    if not w.active:
                        w.start()
                    w.enter_fullscreen()

        fs_btn.clicked.connect(toggle_fs)
        ctrl_row.addWidget(fs_btn)
        ctrl_row.addStretch()

        group_layout.addLayout(ctrl_row)
        parent_layout.addWidget(group)

    def _on_select_input(self, output_id: int, input_id: int) -> None:
        """Handle input selector button click for an output."""
        logger.info("Output %d -> Input %d", output_id, input_id)

        # Update button checked states for this output
        for iid, btn in self._input_select_btns.get(output_id, {}).items():
            btn.setChecked(iid == input_id)

        # Route the output to the selected input
        self.app_instance.set_output_input(output_id, input_id)

    # ── Connection Tab ──────────────────────────────────────────────

    def _build_connection_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._addr_label_widget = QLabel(t("server_address") + ":")
        self._addr_label_widget.setStyleSheet("color: #8888AA; font-size: 11px;")
        layout.addWidget(self._addr_label_widget)

        self._addr_value = QLabel(t("loading"))
        self._addr_value.setStyleSheet("color: #00C8FF; font-size: 16px; font-weight: bold;")
        self._addr_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._addr_value)

        layout.addSpacing(12)

        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setFixedSize(200, 200)
        self._qr_label.setStyleSheet("background-color: white; border-radius: 8px;")
        layout.addWidget(self._qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._qr_hint = QLabel(t("scan_qr"))
        self._qr_hint.setStyleSheet("color: #8888AA; font-size: 11px;")
        self._qr_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._qr_hint)

        layout.addStretch()
        return tab

    # ── Language ─────────────────────────────────────────────────────

    def _on_language_changed(self, index: int) -> None:
        lang = self._lang_combo.itemData(index)
        if lang and lang != get_language():
            set_language(lang)

    def _retranslate_ui(self) -> None:
        """Update all UI text after a language change."""
        self.setWindowTitle(t("app_title"))
        self._output_group_box.setTitle(t("output_preview"))
        self._inputs_group.setTitle(t("input_preview"))
        self._right_tabs.setTabText(0, t("io_control"))
        self._right_tabs.setTabText(1, t("connection_info"))
        self._lang_label.setText(t("language") + ":")

        for output_id, label_letter in enumerate(_OUTPUT_LABELS):
            preview = self._output_previews.get(output_id)
            if preview:
                preview.set_label(t("output_n", n=label_letter))

        self._refresh_input_previews()

        self._addr_label_widget.setText(t("server_address") + ":")
        self._qr_hint.setText(t("scan_qr"))
        self._status_bar.showMessage(t("started"))

    # ── Timers ──────────────────────────────────────────────────────

    def _setup_timers(self) -> None:
        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(self._update_previews)
        self._preview_timer.start(200)

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

    # ── Slots ───────────────────────────────────────────────────────

    @Slot()
    def _update_previews(self) -> None:
        if not self.app_instance.input_manager:
            return
        # Update input previews
        for sid, preview in self._input_previews.items():
            frame = self.app_instance.input_manager.get_frame(sid)
            if frame is not None:
                preview.update_frame(frame)
        # Update output previews (A and B)
        for output_id, preview in self._output_previews.items():
            window = self.app_instance.output_windows.get(output_id)
            if window and window.source_type == "input":
                frame = self.app_instance.input_manager.get_frame(window.source_id)
                if frame is not None:
                    preview.update_frame(frame)

    @Slot()
    def _update_status(self) -> None:
        if self.app_instance.pipeline:
            fps = self.app_instance.pipeline.actual_fps
            self._fps_label.setText(f"FPS: {fps:.1f}")
        try:
            import psutil
            cpu = psutil.cpu_percent()
            self._cpu_label.setText(f"CPU: {cpu:.0f}%")
        except ImportError:
            pass
        ws_count = 0
        if hasattr(self.app_instance, 'api_server') and self.app_instance.api_server:
            ws_count = getattr(self.app_instance.api_server, 'ws_connection_count', 0)
        self._conn_label.setText(f"{t('connections')}: {ws_count}")

    # ── Public ──────────────────────────────────────────────────────

    def set_server_address(self, address: str) -> None:
        self._addr_value.setText(address)

    def set_qr_pixmap(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            self._qr_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._qr_label.setPixmap(scaled)

    def closeEvent(self, event):
        logger.info("Main window closing")
        if self.app_instance:
            self.app_instance.shutdown()
        super().closeEvent(event)
