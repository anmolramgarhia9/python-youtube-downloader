# Music Downloader (PyQt6)
# Windows desktop app entrypoint.

from __future__ import annotations

import sys
import os
import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui.app_ui import AppWindow


DEFAULT_CONFIG = {
    "download_dir": str(Path.home() / "Downloads" / "MusicDownloader"),
    "default_format": "mp3",  # mp3 | mp4
    "audio_bitrate_kbps": 320,  # 128 | 192 | 320
    "concurrent_downloads": 6,  # Increased default for faster playlists
    "theme": "dark",  # dark | light (light not implemented yet)
}


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        # fill missing keys with defaults
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config_path: Path, data: dict) -> None:
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def resource_path(*parts: str) -> str:
    base = Path(__file__).resolve().parent
    return str((base / "assets" / Path(*parts)).resolve())


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / "config.json"
    config = load_config(config_path)

    # Ensure download directory exists
    Path(config["download_dir"]).mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)

    # App icon (optional placeholder)
    icon_path = Path(resource_path("icons", "app.ico"))
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Ultra-modern elegant dark theme
    app.setStyleSheet("""
        /* Global Styles */
        QMainWindow, QWidget {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 #0f0f0f, stop:1 #1a1a1a);
            color: #e8e8e8;
            font-family: 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: none;
            background: transparent;
            border-radius: 12px;
        }
        
        QTabBar {
            background: transparent;
        }
        
        QTabBar::tab {
            background: rgba(40, 40, 40, 0.6);
            color: #888;
            padding: 14px 28px;
            margin-right: 6px;
            margin-bottom: 2px;
            border: none;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #1ed760, stop:1 #1db954);
            color: #fff;
            padding-bottom: 16px;
        }
        
        QTabBar::tab:hover:!selected {
            background: rgba(60, 60, 60, 0.8);
            color: #fff;
        }
        
        /* ComboBox */
        QComboBox {
            background: rgba(40, 40, 40, 0.8);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 10px 15px;
            color: #e8e8e8;
            font-size: 13px;
        }
        
        QComboBox:hover {
            border: 2px solid rgba(29, 185, 84, 0.5);
            background: rgba(50, 50, 50, 0.9);
        }
        
        QComboBox:focus {
            border: 2px solid #1db954;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 30px;
            padding-right: 10px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #888;
            margin-right: 8px;
        }
        
        QComboBox QAbstractItemView {
            background: #252525;
            color: #e8e8e8;
            selection-background-color: #1db954;
            selection-color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }
        
        QComboBox QAbstractItemView::item {
            padding: 8px 15px;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background: rgba(29, 185, 84, 0.2);
        }
        
        /* ScrollBars */
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        QScrollBar:horizontal {
            background: transparent;
            height: 10px;
        }
        
        QScrollBar::handle:horizontal {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            min-width: 30px;
        }
        
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
        
        QScrollBar::add-page, QScrollBar::sub-page {
            background: none;
        }
    """)

    win = AppWindow(config=config, config_path=config_path)
    win.show()

    rc = app.exec()

    # Save config on exit
    try:
        save_config(config_path, win.get_config())
    except Exception:
        pass

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
