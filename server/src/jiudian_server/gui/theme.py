"""Dark neon theme stylesheet for the desktop GUI."""

# Design tokens
COLORS = {
    "background": "#0B0B1E",
    "surface": "#1A1A3E",
    "surface_light": "#252550",
    "primary": "#00C8FF",
    "primary_dark": "#0099CC",
    "secondary": "#FF2D55",
    "secondary_dark": "#CC2244",
    "text": "#E0E0E0",
    "text_secondary": "#8888AA",
    "border": "#2A2A5E",
    "success": "#00FF88",
    "warning": "#FFB800",
}

DARK_NEON_QSS = """
/* Global */
QWidget {
    background-color: #0B0B1E;
    color: #E0E0E0;
    font-family: "Microsoft JhengHei", "Noto Sans TC", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* Main Window */
QMainWindow {
    background-color: #0B0B1E;
}

/* Labels */
QLabel {
    color: #E0E0E0;
    background-color: transparent;
}

QLabel[class="title"] {
    font-size: 18px;
    font-weight: bold;
    color: #00C8FF;
}

QLabel[class="subtitle"] {
    font-size: 14px;
    color: #8888AA;
}

/* Group Box */
QGroupBox {
    background-color: #1A1A3E;
    border: 1px solid #2A2A5E;
    border-radius: 10px;
    margin-top: 12px;
    padding: 16px 10px 10px 10px;
    font-size: 14px;
    font-weight: bold;
    color: #00C8FF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 12px;
    color: #00C8FF;
}

/* Buttons */
QPushButton {
    background-color: #1A1A3E;
    color: #E0E0E0;
    border: 1px solid #00C8FF;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #252550;
    border-color: #00E5FF;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #00C8FF;
    color: #0B0B1E;
}

QPushButton[class="preset"] {
    background-color: #1A1A3E;
    border: 2px solid #00C8FF;
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    min-height: 48px;
}

QPushButton[class="preset"]:hover {
    background-color: #252550;
    border-color: #00E5FF;
}

QPushButton[class="preset"]:checked {
    background-color: #00C8FF;
    color: #0B0B1E;
    border-color: #00E5FF;
}

QPushButton[class="danger"] {
    border-color: #FF2D55;
    color: #FF2D55;
}

QPushButton[class="danger"]:hover {
    background-color: #FF2D55;
    color: #FFFFFF;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0B0B1E;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2A2A5E;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00C8FF;
}

QScrollBar::add-line, QScrollBar::sub-line {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #1A1A3E;
    color: #8888AA;
    border-top: 1px solid #2A2A5E;
    font-size: 12px;
}

/* Frame (used for cards/panels) */
QFrame[class="card"] {
    background-color: #1A1A3E;
    border: 1px solid #2A2A5E;
    border-radius: 10px;
}

QFrame[class="preview"] {
    background-color: #0B0B1E;
    border: 2px solid #2A2A5E;
    border-radius: 8px;
}

QFrame[class="preview-active"] {
    background-color: #0B0B1E;
    border: 2px solid #00C8FF;
    border-radius: 8px;
}

/* Combo Box */
QComboBox {
    background-color: #1A1A3E;
    border: 1px solid #2A2A5E;
    border-radius: 6px;
    padding: 6px 12px;
    color: #E0E0E0;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #00C8FF;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1A1A3E;
    border: 1px solid #00C8FF;
    selection-background-color: #252550;
    color: #E0E0E0;
}

/* Line Edit */
QLineEdit {
    background-color: #1A1A3E;
    border: 1px solid #2A2A5E;
    border-radius: 6px;
    padding: 6px 12px;
    color: #E0E0E0;
    min-height: 28px;
}

QLineEdit:focus {
    border-color: #00C8FF;
}

/* Spin Box */
QSpinBox, QDoubleSpinBox {
    background-color: #1A1A3E;
    border: 1px solid #2A2A5E;
    border-radius: 6px;
    padding: 4px 8px;
    color: #E0E0E0;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00C8FF;
}

/* Slider */
QSlider::groove:horizontal {
    background-color: #2A2A5E;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background-color: #00C8FF;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background-color: #00E5FF;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #2A2A5E;
    border-radius: 8px;
    background-color: #0B0B1E;
}

QTabBar::tab {
    background-color: #1A1A3E;
    color: #8888AA;
    border: 1px solid #2A2A5E;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #252550;
    color: #00C8FF;
    border-color: #00C8FF;
}

QTabBar::tab:hover {
    color: #E0E0E0;
}
"""
