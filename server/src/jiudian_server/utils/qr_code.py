"""QR code generation utility for server connection URL."""
from __future__ import annotations

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_qr_pixmap(url: str) -> Optional["QPixmap"]:
    """Generate a QPixmap containing a QR code for the given URL.

    Returns None if qrcode library is not available.
    """
    try:
        import qrcode
        from PySide6.QtGui import QPixmap, QImage

        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to QPixmap
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        return pixmap
    except ImportError:
        logger.warning("qrcode library not available, QR code will not be displayed")
        return None
    except Exception:
        logger.exception("Failed to generate QR code")
        return None


def get_local_ip() -> str:
    """Get the local network IP address."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
