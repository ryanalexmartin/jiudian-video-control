"""Output window: clean fullscreen display with zero UI chrome."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

from ..i18n import t

if TYPE_CHECKING:
    from ..app import Application

logger = logging.getLogger(__name__)


class OutputWindow(QWidget):
    """A pure video output window — no toolbar, no controls, no chrome.

    In fullscreen mode: frameless, stays on top, black background, cursor hidden.
    All source selection and window management is done from the main control GUI.
    """

    frame_ready = Signal(object)
    closed = Signal(int)

    def __init__(self, output_id: int, app_instance: "Application"):
        super().__init__()
        self.output_id = output_id
        self.app_instance = app_instance
        _label = chr(ord('A') + output_id) if output_id < 26 else str(output_id + 1)
        self.name = f"{t('output_n', n=_label)}"
        self.active: bool = False

        self._source_type: str = "input"
        self._source_id: int | str = 0
        self._is_fullscreen: bool = False

        self._normal_flags = (
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self._fullscreen_flags = (
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowFlags(self._normal_flags)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.setWindowTitle(self.name)
        self.setMinimumSize(640, 400)
        self.resize(960, 540)
        self.setStyleSheet("background-color: #000000;")

        # Display label — fills the entire window
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background-color: #000000;")

        self.frame_ready.connect(self._on_frame_ready)

    # ── Geometry ────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._label.setGeometry(0, 0, self.width(), self.height())

    # ── Public API ──────────────────────────────────────────────────

    def start(self) -> None:
        self.active = True
        self.show()
        self.raise_()

    def stop(self) -> None:
        self.active = False
        if self._is_fullscreen:
            self._exit_fullscreen()
        self.hide()

    @property
    def source_type(self) -> str:
        return self._source_type

    @property
    def source_id(self) -> int | str:
        return self._source_id

    def set_source(self, source_type: str, source_id: int | str) -> None:
        self._source_type = source_type
        self._source_id = source_id

    def display_frame(self, frame: np.ndarray) -> None:
        self.frame_ready.emit(frame)

    def enter_fullscreen(self) -> None:
        if self._is_fullscreen:
            return
        self._is_fullscreen = True
        self._saved_geometry = self.geometry()
        self.setWindowFlags(self._fullscreen_flags)
        self.showFullScreen()
        self.activateWindow()
        self.setCursor(Qt.CursorShape.BlankCursor)

    def exit_fullscreen(self) -> None:
        if not self._is_fullscreen:
            return
        self._is_fullscreen = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setWindowFlags(self._normal_flags)
        if hasattr(self, '_saved_geometry'):
            self.setGeometry(self._saved_geometry)
        self.showNormal()
        self.activateWindow()

    # ── Frame rendering ────────────────────────────────────────────

    @Slot(object)
    def _on_frame_ready(self, frame: np.ndarray) -> None:
        if not self.active:
            return
        try:
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(image)

            label_size = self._label.size()
            if self._is_fullscreen:
                scaled = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            else:
                scaled = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            self._label.setPixmap(scaled)
        except Exception:
            logger.exception("Error displaying frame on output %d", self.output_id)

    # ── Keyboard (Escape exits fullscreen only) ─────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self._is_fullscreen:
            self._exit_fullscreen()
        super().keyPressEvent(event)

    def _exit_fullscreen(self):
        self.exit_fullscreen()

    def closeEvent(self, event):
        self.active = False
        self.closed.emit(self.output_id)
        super().closeEvent(event)
