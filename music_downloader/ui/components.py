from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Dict, Optional

import requests
from requests import exceptions
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QGridLayout,
    QFrame,
    QSizePolicy,
)

from core.search import search_youtube
from core.downloader import DownloadManager, DownloadJob


# ---------------- Search Tab ----------------
class SearchTab(QWidget):
    request_download = pyqtSignal(dict, str, int, str, str)  # item, fmt, bitrate, video_quality, audio_quality
    search_results = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._results: List[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # Search bar container
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setSpacing(10)
        
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search for music, paste YouTube URL, or playlist link...")
        self.query.setMinimumHeight(52)
        self.query.returnPressed.connect(self._do_search)
        self.query.setStyleSheet("""
            QLineEdit {
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 26px;
                padding: 0 24px;
                font-size: 14px;
                background: rgba(40, 40, 40, 0.8);
                color: #e8e8e8;
            }
            QLineEdit:hover {
                border: 2px solid rgba(29, 185, 84, 0.3);
                background: rgba(50, 50, 50, 0.9);
            }
            QLineEdit:focus {
                border: 2px solid #1db954;
                background: rgba(50, 50, 50, 1);
            }
        """)

        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(52)
        self.search_btn.setMinimumWidth(140)
        self.search_btn.clicked.connect(self._do_search)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1ed760, stop:1 #1db954);
                border: none;
                border-radius: 26px;
                color: white;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1fef6f, stop:1 #1ed760);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1aa34a, stop:1 #178a3e);
            }
            QPushButton:disabled {
                background: rgba(80, 80, 80, 0.5);
                color: rgba(255, 255, 255, 0.3);
            }
        """)

        search_layout.addWidget(self.query)
        search_layout.addWidget(self.search_btn)
        root.addWidget(search_container)

        # Quality Controls Section with elegant organization
        quality_container = QFrame()
        quality_container.setStyleSheet("""
            QFrame {
                background: rgba(30, 30, 30, 0.5);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                padding: 12px;
            }
        """)
        options_layout = QHBoxLayout(quality_container)
        options_layout.setSpacing(20)
        options_layout.setContentsMargins(20, 12, 20, 12)
        
        # Format section
        format_section = QVBoxLayout()
        format_section.setSpacing(6)
        format_label = QLabel("Format")
        format_label.setStyleSheet("color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        self.format_box = QComboBox()
        self.format_box.addItems(["MP3", "MP4"])
        self.format_box.setMinimumWidth(100)
        format_section.addWidget(format_label)
        format_section.addWidget(self.format_box)
        options_layout.addLayout(format_section)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setStyleSheet("background: rgba(255, 255, 255, 0.1); max-width: 1px;")
        options_layout.addWidget(separator1)
        
        # Video Quality section (for MP4)
        video_quality_section = QVBoxLayout()
        video_quality_section.setSpacing(6)
        video_quality_label = QLabel("Video Quality")
        video_quality_label.setStyleSheet("color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        self.video_quality_box = QComboBox()
        self.video_quality_box.addItems(["Best", "2160p (4K)", "1440p (2K)", "1080p (FHD)", "720p (HD)", "480p", "360p"])
        self.video_quality_box.setCurrentIndex(0)
        self.video_quality_box.setMinimumWidth(140)
        video_quality_section.addWidget(video_quality_label)
        video_quality_section.addWidget(self.video_quality_box)
        options_layout.addLayout(video_quality_section)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("background: rgba(255, 255, 255, 0.1); max-width: 1px;")
        options_layout.addWidget(separator2)
        
        # Unified Audio Quality section (for both MP3 and MP4)
        audio_section = QVBoxLayout()
        audio_section.setSpacing(6)
        audio_label = QLabel("Audio Quality")
        audio_label.setStyleSheet("color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        self.bitrate_box = QComboBox()
        self.bitrate_box.addItems(["Best", "320 kbps", "256 kbps", "192 kbps", "128 kbps"])
        self.bitrate_box.setCurrentIndex(1)  # Default to 320 kbps
        self.bitrate_box.setMinimumWidth(120)
        audio_section.addWidget(audio_label)
        audio_section.addWidget(self.bitrate_box)
        options_layout.addLayout(audio_section)
        
        # Keep reference for compatibility
        self.audio_quality_box = self.bitrate_box

        options_layout.addStretch()
        root.addWidget(quality_container)

        # Grid container with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
        """)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.grid_widget)
        root.addWidget(scroll)

        # Signals
        self.search_results.connect(self._on_results)

    def _do_search(self):
        q = self.query.text().strip()
        if not q:
            return
        
        # Smart URL detection - check if it's a direct URL
        if self._is_url(q):
            if self._is_playlist_url(q):
                self._handle_playlist_url(q)
            else:
                self._handle_video_url(q)
            return
        
        # Regular search
        self.search_btn.setEnabled(False)
        # Clear grid layout
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self._results.clear()

        def worker():
            try:
                results = search_youtube(q, limit=25)
            except Exception as e:
                results = []
            self.search_results.emit(results)

        threading.Thread(target=worker, daemon=True).start()
    
    def _is_url(self, text: str) -> bool:
        """Check if text is a URL."""
        return text.startswith(('http://', 'https://', 'www.', 'youtu.be/', 'youtube.com/'))
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist."""
        return 'list=' in url or '/playlist' in url
    
    def _handle_video_url(self, url: str):
        """Handle direct video URL - add to results and auto-download."""
        from yt_dlp import YoutubeDL
        
        self.search_btn.setEnabled(False)
        
        def worker():
            try:
                ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    item = {
                        "id": info.get("id"),
                        "title": info.get("title"),
                        "duration": info.get("duration"),
                        "duration_str": self._format_duration(info.get("duration")),
                        "channel": info.get("uploader") or info.get("channel"),
                        "thumbnail": info.get("thumbnail"),
                        "webpage_url": url,
                    }
                    # Auto-download
                    fmt = self.format_box.currentText().lower()
                    bitrate = int(self.bitrate_box.currentText().split()[0])
                    video_quality = self._parse_video_quality(self.video_quality_box.currentText())
                    audio_quality = self._parse_audio_quality(self.audio_quality_box.currentText())
                    self.request_download.emit(item, fmt, bitrate, video_quality, audio_quality)
                    self.search_results.emit([item])
            except Exception as e:
                print(f"Error fetching video: {e}")
                self.search_results.emit([])
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _handle_playlist_url(self, url: str):
        """Handle playlist URL - extract all videos and queue downloads."""
        from yt_dlp import YoutubeDL
        import concurrent.futures
        
        self.search_btn.setEnabled(False)
        self.list.clear()
        
        def worker():
            try:
                # Ultra-fast playlist extraction
                ydl_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'extract_flat': 'in_playlist',  # Fastest extraction mode
                    'no_warnings': True,
                    'playlist_items': None,  # Get all items
                    'lazy_playlist': False,  # Process immediately
                    'ignoreerrors': True,  # Don't stop on individual errors
                    'no_color': True,
                    'socket_timeout': 10,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    entries = info.get('entries', [])
                    
                    results = []
                    fmt = self.format_box.currentText().lower()
                    bitrate = int(self.bitrate_box.currentText().split()[0])
                    video_quality = self._parse_video_quality(self.video_quality_box.currentText())
                    audio_quality = self._parse_audio_quality(self.audio_quality_box.currentText())
                    
                    # Batch emit downloads for faster processing
                    batch_items = []
                    for entry in entries:
                        if not entry:
                            continue
                        item = {
                            "id": entry.get("id"),
                            "title": entry.get("title") or f"Video {entry.get('id')}",
                            "duration": entry.get("duration"),
                            "duration_str": self._format_duration(entry.get("duration")),
                            "channel": entry.get("uploader") or entry.get("channel"),
                            "thumbnail": entry.get("thumbnail"),
                            "webpage_url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        }
                        results.append(item)
                        batch_items.append(item)
                        
                        # Emit in batches of 10 for faster UI updates
                        if len(batch_items) >= 10:
                            for batch_item in batch_items:
                                self.request_download.emit(batch_item, fmt, bitrate, video_quality, audio_quality)
                            batch_items = []
                    
                    # Emit remaining items
                    for batch_item in batch_items:
                        self.request_download.emit(batch_item, fmt, bitrate, video_quality, audio_quality)
                    
                    self.search_results.emit(results)
            except Exception as e:
                print(f"Error fetching playlist: {e}")
                self.search_results.emit([])
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _format_duration(self, seconds):
        """Format duration in seconds to HH:MM:SS or MM:SS."""
        if not seconds:
            return ""
        s = int(seconds)
        h, rem = divmod(s, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"

    def _on_results(self, results: List[dict]):
        self._results = results
        self.search_btn.setEnabled(True)
        
        # Clear existing grid items
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Add cards to grid (4 columns)
        for idx, item in enumerate(results):
            row = idx // 4
            col = idx % 4
            card = self._create_result_card(item)
            self.grid_layout.addWidget(card, row, col)
    
    def _create_result_card(self, item: dict) -> QWidget:
        """Create a beautiful card for a search result."""
        card = QFrame()
        card.setObjectName("resultCard")
        card.setFixedSize(260, 340)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QFrame#resultCard {
                background: rgba(30, 30, 30, 0.6);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QFrame#resultCard:hover {
                background: rgba(40, 40, 40, 0.9);
                border: 1px solid rgba(29, 185, 84, 0.5);
                transform: translateY(-4px);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Thumbnail
        thumb_label = QLabel()
        thumb_label.setFixedSize(260, 195)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet("""
            background: rgba(20, 20, 20, 0.8);
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)
        
        # Load thumbnail asynchronously
        thumb_url = item.get("thumbnail")
        if thumb_url:
            def load_thumb():
                pix = _load_pixmap(thumb_url, 240, 180)
                if pix:
                    thumb_label.setPixmap(pix)
                else:
                    thumb_label.setText("🎵")
                    thumb_label.setStyleSheet(thumb_label.styleSheet() + "font-size: 48px; color: #535353;")
            threading.Thread(target=load_thumb, daemon=True).start()
        else:
            thumb_label.setText("🎵")
            thumb_label.setStyleSheet(thumb_label.styleSheet() + "font-size: 48px; color: #535353;")
        
        layout.addWidget(thumb_label)
        
        # Info section
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(5)
        
        # Title
        title = item.get("title") or "Untitled"
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(45)
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
        """)
        info_layout.addWidget(title_label)
        
        # Channel and duration
        channel = item.get("channel") or "Unknown"
        duration = item.get("duration_str") or "--:--"
        meta_label = QLabel(f"{channel}")
        meta_label.setStyleSheet("""
            color: #b3b3b3;
            font-size: 11px;
        """)
        info_layout.addWidget(meta_label)
        
        duration_label = QLabel(f"⏱ {duration}")
        duration_label.setStyleSheet("""
            color: #1db954;
            font-size: 11px;
            font-weight: bold;
        """)
        info_layout.addWidget(duration_label)
        
        info_layout.addStretch()
        layout.addWidget(info_widget)
        
        # Click handler
        card.mousePressEvent = lambda e: self._on_card_click(item)
        
        return card
    
    def _on_card_click(self, item: dict):
        """Handle card click to download."""
        fmt = self.format_box.currentText().lower()
        bitrate = int(self.bitrate_box.currentText().split()[0])
        
        # Get quality selections
        video_quality = self._parse_video_quality(self.video_quality_box.currentText())
        audio_quality = self._parse_audio_quality(self.audio_quality_box.currentText())
        
        self.request_download.emit(item, fmt, bitrate, video_quality, audio_quality)
    
    def _parse_video_quality(self, text: str) -> str:
        """Parse video quality from dropdown text."""
        if "Best" in text:
            return "best"
        # Extract number from text like "2160p (4K)"
        return text.split("p")[0]
    
    def _parse_audio_quality(self, text: str) -> str:
        """Parse audio quality from dropdown text."""
        if "Best" in text:
            return "best"
        # Extract number from text like "320 kbps"
        parts = text.split()
        return parts[0] if parts else "best"



# ---------------- Downloads Tab ----------------
class DownloadsTab(QWidget):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)
        
        # Header
        header = QLabel("📥 Downloads Queue")
        header.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            padding: 10px 0;
        """)
        root.addWidget(header)
        
        # Downloads list
        self.list = QListWidget()
        self.list.setSpacing(12)
        self.list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
        """)
        root.addWidget(self.list)

    def enqueue_download(self, item: dict, fmt: str, bitrate_kbps: int, 
                        video_quality: str = "best", audio_quality: str = "best"):
        print(f"enqueue_download called")
        job = self.manager.create_job(item, fmt, bitrate_kbps, video_quality, audio_quality)
        print(f"Job created: {job.title}")
        row = DownloadRow(job, self.manager)
        print(f"DownloadRow created")
        lwi = QListWidgetItem()
        lwi.setSizeHint(row.sizeHint())
        self.list.addItem(lwi)
        print(f"Item added to list")
        self.list.setItemWidget(lwi, row)
        print(f"Widget set for item")
        # Connect signals after widget is in UI
        row.connect_signals()
        print(f"Signals connected")
        self.manager.submit(job)
        print(f"Job submitted to manager")
        return job


class DownloadRow(QWidget):
    def __init__(self, job: DownloadJob, manager: DownloadManager):
        super().__init__()
        self.job = job
        self.manager = manager
        
        # Elegant card container
        self.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 0.7);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QWidget:hover {
                background: rgba(35, 35, 35, 0.85);
                border: 1px solid rgba(29, 185, 84, 0.3);
            }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 15, 20, 15)
        v.setSpacing(10)
        
        # Title
        self.title = QLabel(job.title)
        self.title.setStyleSheet("""
            color: #e8e8e8;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        v.addWidget(self.title)
        
        # Metadata
        self.meta = QLabel(job.subtitle)
        self.meta.setStyleSheet("""
            color: #888;
            font-size: 11px;
            font-weight: 500;
        """)
        v.addWidget(self.meta)
        
        # Modern progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #1ed760, stop:0.5 #1db954, stop:1 #17a348);
                border-radius: 3px;
            }
        """)
        v.addWidget(self.progress)
        
        # Info label
        self.info = QLabel("⏳ Initializing...")
        self.info.setStyleSheet("""
            color: #1db954;
            font-size: 12px;
            font-weight: bold;
        """)
        v.addWidget(self.info)

        # Modern action buttons
        hbtn = QHBoxLayout()
        hbtn.setSpacing(10)
        
        btn_style = """
            QPushButton {
                background: rgba(50, 50, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e8e8e8;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(60, 60, 60, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background: rgba(40, 40, 40, 0.9);
            }
        """
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setStyleSheet(btn_style)
        
        self.resume_btn = QPushButton("▶ Resume")
        self.resume_btn.setStyleSheet(btn_style)
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(211, 47, 47, 0.2);
                border: 1px solid rgba(211, 47, 47, 0.4);
                border-radius: 8px;
                color: #ff6b6b;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(211, 47, 47, 0.3);
                border: 1px solid rgba(211, 47, 47, 0.6);
            }
        """)
        
        self.open_btn = QPushButton("📂 Open")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: rgba(29, 185, 84, 0.2);
                border: 1px solid rgba(29, 185, 84, 0.4);
                border-radius: 8px;
                color: #1ed760;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(29, 185, 84, 0.3);
                border: 1px solid rgba(29, 185, 84, 0.6);
            }
        """)

        hbtn.addWidget(self.pause_btn)
        hbtn.addWidget(self.resume_btn)
        hbtn.addWidget(self.cancel_btn)
        hbtn.addStretch()
        hbtn.addWidget(self.open_btn)
        
        v.addLayout(hbtn)

        print("Connecting button signals...")
        self.pause_btn.clicked.connect(lambda: self.manager.pause(job.id))
        self.resume_btn.clicked.connect(lambda: self.manager.resume(job.id))
        self.cancel_btn.clicked.connect(lambda: self.manager.cancel(job.id))
        self.open_btn.clicked.connect(self._open_folder)
        print("Button signals connected")
    
    def connect_signals(self):
        """Connect job signals after widget is added to UI."""
        print("Connecting job signals...")
        # Signals - use queued connections for thread safety
        self.job.sig_progress.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)
        self.job.sig_done.connect(self._on_done, Qt.ConnectionType.QueuedConnection)
        self.job.sig_error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)
        self.job.sig_status.connect(self._on_status, Qt.ConnectionType.QueuedConnection)
        print("Job signals connected")

    def _on_progress(self, pct: int, speed: str, eta: str, size: str):
        self.progress.setValue(max(0, min(100, pct)))
        self.info.setText(f"📈 {pct}% • {speed} • {size} • ETA {eta}")
        self.info.setStyleSheet("""
            color: #1db954;
            font-size: 12px;
            font-weight: bold;
        """)

    def _on_done(self, path: str):
        self.info.setText("✅ Completed Successfully!")
        self.progress.setValue(100)
        self.info.setStyleSheet("""
            color: #4caf50;
            font-size: 12px;
            font-weight: bold;
        """)

    def _on_error(self, msg: str):
        self.info.setText(f"❌ Error: {msg}")
        self.info.setStyleSheet("""
            color: #f44336;
            font-size: 12px;
            font-weight: bold;
        """)

    def _on_status(self, msg: str):
        if "Paused" in msg:
            self.info.setText(f"⏸ {msg}")
        elif "Starting" in msg or "Converting" in msg:
            self.info.setText(f"⏳ {msg}")
        elif "Resumed" in msg:
            self.info.setText(f"▶ {msg}")
        elif "Canceled" in msg:
            self.info.setText(f"❌ {msg}")
        else:
            self.info.setText(msg)

    def _open_folder(self):
        outdir = Path(self.job.outdir)
        try:
            if outdir.exists():
                # Windows Explorer
                import os
                os.startfile(outdir)  # type: ignore[attr-defined]
        except Exception:
            pass


# ---------------- Settings Tab ----------------
class SettingsTab(QWidget):
    config_changed = pyqtSignal(dict)

    def __init__(self, config: Dict):
        super().__init__()
        self._config = dict(config)

        v = QVBoxLayout(self)
        v.setContentsMargins(30, 30, 30, 30)
        v.setSpacing(25)

        # Header
        header = QLabel("Settings")
        header.setStyleSheet("""
            color: #e8e8e8;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
        """)
        v.addWidget(header)

        # Storage Section
        storage_group = self._create_group("Storage")
        storage_layout = QVBoxLayout(storage_group)
        storage_layout.setSpacing(15)
        
        dir_row = QHBoxLayout()
        dir_label = QLabel("Download Folder")
        dir_label.setStyleSheet("color: #888; font-size: 12px; font-weight: 600;")
        self.download_dir_label = QLabel(self._config.get("download_dir", ""))
        self.download_dir_label.setStyleSheet("color: #e8e8e8; font-size: 12px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px;")
        pick = QPushButton("Browse...")
        pick.setStyleSheet(self._button_style())
        pick.clicked.connect(self._pick_dir)
        pick.setMinimumHeight(36)
        dir_row.addWidget(self.download_dir_label, 1)
        dir_row.addWidget(pick)
        storage_layout.addWidget(dir_label)
        storage_layout.addLayout(dir_row)
        v.addWidget(storage_group)

        # Quality Section
        quality_group = self._create_group("Quality Defaults")
        quality_layout = QVBoxLayout(quality_group)
        quality_layout.setSpacing(15)
        
        format_row = self._create_setting_row("Default Format", "mp3")
        self.default_format = format_row["widget"]
        self.default_format.addItems(["mp3", "mp4"])
        self.default_format.setCurrentText(self._config.get("default_format", "mp3"))
        quality_layout.addWidget(format_row["label"])
        quality_layout.addWidget(self.default_format)
        
        bitrate_row = self._create_setting_row("Audio Bitrate", "320")
        self.bitrate = bitrate_row["widget"]
        self.bitrate.addItems(["128 kbps", "192 kbps", "320 kbps"])
        self.bitrate.setCurrentText(f"{self._config.get('audio_bitrate_kbps', 320)} kbps")
        quality_layout.addWidget(bitrate_row["label"])
        quality_layout.addWidget(self.bitrate)
        v.addWidget(quality_group)

        # Performance Section
        perf_group = self._create_group("Performance")
        perf_layout = QVBoxLayout(perf_group)
        perf_layout.setSpacing(15)
        
        concurrent_row = self._create_setting_row("Concurrent Downloads", "6")
        self.concurrent = concurrent_row["widget"]
        self.concurrent.addItems(["1", "2", "3", "4", "5", "6", "8", "10", "12", "16"])
        self.concurrent.setCurrentText(str(self._config.get("concurrent_downloads", 6)))
        perf_layout.addWidget(concurrent_row["label"])
        perf_layout.addWidget(self.concurrent)
        v.addWidget(perf_group)

        # Apply Button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1ed760, stop:1 #1db954);
                border: none;
                border-radius: 10px;
                color: white;
                padding: 14px;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #1fef6f, stop:1 #1ed760);
            }
        """)
        apply_btn.clicked.connect(self._apply)
        apply_btn.setMinimumHeight(48)
        v.addWidget(apply_btn)
        v.addStretch(1)
    
    def _create_group(self, title: str) -> QFrame:
        """Create a styled group container."""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background: rgba(30, 30, 30, 0.5);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                padding: 20px;
            }
        """)
        return group
    
    def _create_setting_row(self, label_text: str, default: str) -> Dict:
        """Create a setting row with label and combobox."""
        label = QLabel(label_text)
        label.setStyleSheet("color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        widget = QComboBox()
        widget.setMinimumHeight(40)
        return {"label": label, "widget": widget}
    
    def _button_style(self) -> str:
        """Get button styling."""
        return """
            QPushButton {
                background: rgba(50, 50, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e8e8e8;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(60, 60, 60, 0.8);
                border: 1px solid rgba(29, 185, 84, 0.5);
            }
        """

    def _pick_dir(self):
        cur = self.download_dir_label.text() or str(Path.home())
        sel = QFileDialog.getExistingDirectory(self, "Select Download Folder", cur)
        if sel:
            self.download_dir_label.setText(sel)

    def _apply(self):
        data = self.current_settings()
        self.config_changed.emit(data)

    def current_settings(self) -> Dict:
        return {
            "download_dir": self.download_dir_label.text(),
            "default_format": self.default_format.currentText(),
            "audio_bitrate_kbps": int(self.bitrate.currentText().split()[0]),  # Extract number from "320 kbps"
            "concurrent_downloads": int(self.concurrent.currentText()),
        }


# -------------- Helpers --------------
def _load_pixmap(url: str, w: int, h: int) -> Optional[QPixmap]:
    """Load pixmap from URL with better timeout and error handling."""
    if not url:
        return None
    try:
        # Use shorter timeout and verify SSL
        r = requests.get(url, timeout=3, verify=True)
        r.raise_for_status()
        pix = QPixmap()
        pix.loadFromData(r.content)
        if not pix.isNull():
            return pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    except (exceptions.RequestException, exceptions.Timeout, exceptions.ConnectionError) as e:
        # Silently fail for network issues to avoid cluttering console
        pass
    except Exception as e:
        # Log unexpected errors
        print(f"Thumbnail load error: {e}")
    return None
