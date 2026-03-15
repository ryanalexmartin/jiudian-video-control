"""Custom widgets for the dark neon theme GUI."""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


class NeonButton(QPushButton):
    """A button with neon glow effect styling."""

    def __init__(self, text: str, parent: Optional[QWidget] = None, accent: str = "primary"):
        super().__init__(text, parent)
        self.setProperty("class", "preset")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Glow effect
        glow = QGraphicsDropShadowEffect(self)
        color = QColor("#00C8FF") if accent == "primary" else QColor("#FF2D55")
        glow.setColor(color)
        glow.setBlurRadius(15)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)


class GlassmorphicCard(QFrame):
    """A semi-transparent card with glassmorphism-style appearance."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(QColor(0, 200, 255, 30))
        glow.setBlurRadius(20)
        glow.setOffset(0, 2)
        self.setGraphicsEffect(glow)


class PreviewWidget(QFrame):
    """Widget that displays a video preview frame with a label."""

    clicked = Signal(int)

    def __init__(
        self,
        source_id: int,
        label_text: str,
        parent: Optional[QWidget] = None,
        preview_size: QSize = QSize(320, 180),
    ):
        super().__init__(parent)
        self.source_id = source_id
        self.preview_size = preview_size
        self.setProperty("class", "preview")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(preview_size.width() + 12, preview_size.height() + 36)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # Label
        self._title = QLabel(label_text)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("color: #8888AA; font-size: 11px; font-weight: bold;")
        layout.addWidget(self._title)

        # Preview image
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setFixedSize(preview_size)
        self._image_label.setStyleSheet("background-color: #0B0B1E; border-radius: 4px;")
        layout.addWidget(self._image_label)

    def update_frame(self, frame: np.ndarray) -> None:
        """Update the preview with a BGR frame."""
        resized = cv2.resize(
            frame,
            (self.preview_size.width(), self.preview_size.height()),
            interpolation=cv2.INTER_AREA,
        )
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        image = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        self._image_label.setPixmap(QPixmap.fromImage(image))

    def set_active(self, active: bool) -> None:
        """Toggle active border appearance."""
        self.setProperty("class", "preview-active" if active else "preview")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_label(self, text: str) -> None:
        """Update the label text."""
        self._title.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.source_id)
        super().mousePressEvent(event)


class StatusIndicator(QWidget):
    """Small colored dot indicator for connection/status."""

    def __init__(self, parent: Optional[QWidget] = None, color: str = "#00FF88"):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(12, 12)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(QPen(self._color.darker(150), 1))
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()
