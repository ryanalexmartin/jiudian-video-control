"""Entry point for the Jiudian Video Control System server."""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="酒店影像控制系統 - 伺服器",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dev", action="store_true", default=True, help="使用測試圖案（開發模式）")
    parser.add_argument("--no-dev", dest="dev", action="store_false", help="使用實際擷取卡")
    parser.add_argument("--port", type=int, default=8080, help="API 伺服器連接埠")
    parser.add_argument("--host", default="0.0.0.0", help="API 伺服器位址")
    parser.add_argument("--width", type=int, default=1920, help="輸出解析度寬度")
    parser.add_argument("--height", type=int, default=1080, help="輸出解析度高度")
    parser.add_argument("--fps", type=int, default=30, help="目標影格率")
    parser.add_argument("--config-dir", default=None, help="設定檔目錄")
    parser.add_argument("--verbose", "-v", action="store_true", help="顯示詳細日誌")
    args = parser.parse_args()

    # Setup logging
    import logging
    from .utils.log import setup_logging
    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("=== 酒店影像控制系統 ===")
    logger.info("Mode: %s", "開發模式（測試圖案）" if args.dev else "正式模式（擷取卡）")

    # Create Qt application
    from PySide6.QtWidgets import QApplication

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("酒店影像控制系統")
    qt_app.setOrganizationName("Jiudian")

    # Create and start application
    from .app import Application

    app = Application(
        dev_mode=args.dev,
        api_port=args.port,
        api_host=args.host,
        config_dir=args.config_dir,
        width=args.width,
        height=args.height,
        target_fps=args.fps,
    )

    main_window = app.start(qt_app)
    main_window.show()

    # Run Qt event loop
    logger.info("GUI ready, entering event loop")
    exit_code = qt_app.exec()

    # Cleanup
    app.shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
