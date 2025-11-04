from __future__ import annotations

from pathlib import Path
from typing import Dict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QFileDialog,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QMessageBox,
    QApplication,
    QSystemTrayIcon,
    QMenu,
    QStyle,
)

from .components import SearchTab, DownloadsTab, SettingsTab
from .toast import ToastManager
from core.downloader import DownloadManager


class AppWindow(QMainWindow):
    def __init__(self, config: Dict, config_path: Path):
        super().__init__()
        self.setWindowTitle("Music Downloader")
        self.resize(1180, 740)

        self._config = dict(config)
        self._config_path = config_path

        # Download manager
        self.manager = DownloadManager(
            download_dir=Path(self._config["download_dir"]),
            concurrent=self._config.get("concurrent_downloads", 3),
        )

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.search_tab = SearchTab()
        self.downloads_tab = DownloadsTab(self.manager)
        self.settings_tab = SettingsTab(self._config)

        self.tabs.addTab(self.search_tab, "Home")
        self.tabs.addTab(self.downloads_tab, "Downloads")
        self.tabs.addTab(self.settings_tab, "Settings")

        # Wiring
        self.search_tab.request_download.connect(self._on_request_download)
        self.settings_tab.config_changed.connect(self._on_config_changed)

        # System tray
        self._init_tray()

        # Toasts
        self.toasts = ToastManager(self)

        # Apply starting settings
        self._apply_settings()

    # ---------- Events ----------
    def _on_request_download(self, item: dict, fmt: str, bitrate_kbps: int, video_quality: str, audio_quality: str):
        # enqueue and hook notifications
        print(f"_on_request_download called for: {item.get('title')}")
        job = self.downloads_tab.enqueue_download(item, fmt, bitrate_kbps, video_quality, audio_quality)
        print(f"Job created with ID: {job.id}")
        job.sig_done.connect(lambda path, title=job.title: self._notify_complete(title, path))
        job.sig_error.connect(lambda msg, title=job.title: self._notify_error(title, msg))
        print(f"Switching to Downloads tab")
        self.tabs.setCurrentIndex(1)  # Switch to downloads tab

    def _on_config_changed(self, new_conf: Dict):
        self._config.update(new_conf)
        self._apply_settings()

    def _apply_settings(self):
        # Update download dir and concurrency in manager
        self.manager.set_download_dir(Path(self._config["download_dir"]))
        self.manager.set_concurrency(int(self._config.get("concurrent_downloads", 3)))

    def get_config(self) -> Dict:
        # Gather settings from settings tab
        settings = self.settings_tab.current_settings()
        merged = dict(self._config)
        merged.update(settings)
        return merged

    # ---------- Tray & notifications ----------
    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.tray.setIcon(icon)
        menu = QMenu()
        act_show = menu.addAction("Show")
        act_quit = menu.addAction("Exit")
        act_show.triggered.connect(self._show_from_tray)
        act_quit.triggered.connect(lambda: QApplication.instance().quit())
        self.tray.setContextMenu(menu)
        self.tray.show()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _notify_complete(self, title: str, path: str):
        self.toasts.show_toast(f"Downloaded: {title}")
        if self.tray.isVisible():
            self.tray.showMessage("Download complete", title, QSystemTrayIcon.MessageIcon.Information, 3000)

    def _notify_error(self, title: str, msg: str):
        self.toasts.show_toast(f"Failed: {title}")
        if self.tray.isVisible():
            self.tray.showMessage("Download failed", f"{title}: {msg}", QSystemTrayIcon.MessageIcon.Critical, 3000)

    def closeEvent(self, event):
        # Minimize to tray
        if self.tray and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage("Music Downloader", "Still running in the tray.", QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            super().closeEvent(event)
