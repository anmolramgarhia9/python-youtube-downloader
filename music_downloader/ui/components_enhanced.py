"""
Enhanced UI Components with comprehensive UX improvements:
- Empty states
- Loading states
- Staggered animations
- Dynamic stats
- Retry functionality
- Drag-and-drop support
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import List, Dict, Optional

import requests
from requests import exceptions
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize, QMimeData
from PyQt6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent
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

from music_downloader.core.search import search_youtube
from music_downloader.core.downloader import DownloadManager, DownloadJob
from music_downloader.ui.thumbnail_cache import get_thumbnail_cache
from music_downloader.ui.circular_progress import CircularProgress
from music_downloader.ui.animations import AnimationHelper


class DragDropLineEdit(QLineEdit):
    """Enhanced QLineEdit with drag-and-drop URL support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            self.setText(url)
            event.acceptProposedAction()
        elif event.mimeData().hasText():
            text = event.mimeData().text()
            self.setText(text)
            event.acceptProposedAction()


# Placeholder for integration - these enhancements should be added to existing SearchTab
SEARCH_TAB_ENHANCEMENTS = """
Key enhancements to add to existing SearchTab:

1. Replace QLineEdit with DragDropLineEdit for drag-and-drop support
2. Add _is_searching flag and loading state management
3. Add empty state widget creation
4. Modify display_results to show empty states and animate cards
5. Update _do_search to set loading state

Example modifications:

# In __init__:
self.query = DragDropLineEdit()  # Instead of QLineEdit()
self._is_searching = False

# In _do_search:
self._is_searching = True
self.search_btn.setEnabled(False)
self.search_btn.setText("⏳ Searching...")
self.query.setEnabled(False)

# In display_results (after clearing grid):
# Reset loading state
self._is_searching = False
self.search_btn.setEnabled(True)
self.search_btn.setText("Search")
self.query.setEnabled(True)

# Animate cards:
cards = []
for idx, item in enumerate(results):
    card = self._create_result_card(item)
    self.grid_layout.addWidget(card, row, col)
    cards.append(card)
AnimationHelper.stagger_fade_in(cards, delay=30, duration=250)
"""


class EnhancedDownloadsTab(QWidget):
    """Enhanced Downloads Tab with stats, empty states, and retry functionality"""
    
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self._download_count = 0
        self._completed_count = 0
        self._failed_count = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)
        
        # Header with stats
        header_container = QHBoxLayout()
        self.header = QLabel("📥 Downloads Queue")
        self.header.setStyleSheet("""
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            padding: 10px 0;
        """)
        header_container.addWidget(self.header)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("""
            color: #888;
            font-size: 13px;
            font-weight: 600;
            padding: 10px 0;
        """)
        header_container.addWidget(self.stats_label)
        header_container.addStretch()
        
        root.addLayout(header_container)
        
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
        
        # Empty state for downloads
        self.empty_state = self._create_empty_state()
        root.addWidget(self.empty_state)
        root.addWidget(self.list)
        self._update_empty_state()
    
    def _create_empty_state(self) -> QWidget:
        """Create empty state widget for when no downloads."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        icon = QLabel("📥")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("No downloads yet")
        title.setStyleSheet("""
            color: #e8e8e8;
            font-size: 20px;
            font-weight: 600;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Search for music and click on a result to start downloading")
        subtitle.setStyleSheet("""
            color: #888;
            font-size: 13px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        return container
    
    def _update_empty_state(self):
        """Show/hide empty state based on list contents."""
        has_items = self.list.count() > 0
        self.empty_state.setVisible(not has_items)
        self.list.setVisible(has_items)
    
    def _update_stats(self):
        """Update the stats label with current queue status."""
        active = self._download_count - self._completed_count - self._failed_count
        if self._download_count == 0:
            self.stats_label.setText("")
        else:
            self.stats_label.setText(
                f"Active: {active} • Completed: {self._completed_count} • Failed: {self._failed_count} • Total: {self._download_count}"
            )
    
    def enqueue_download(self, item: dict, fmt: str, bitrate_kbps: int, 
                        video_quality: str = "best", audio_quality: str = "best"):
        print(f"enqueue_download called")
        job = self.manager.create_job(item, fmt, bitrate_kbps, video_quality, audio_quality)
        print(f"Job created: {job.title}")
        row = EnhancedDownloadRow(job, self.manager, self)
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
        
        # Update stats
        self._download_count += 1
        self._update_stats()
        self._update_empty_state()
        
        return job


class EnhancedDownloadRow(QWidget):
    """Enhanced Download Row with retry functionality"""
    
    def __init__(self, job: DownloadJob, manager: DownloadManager, parent_tab=None):
        super().__init__()
        self.job = job
        self.manager = manager
        self.parent_tab = parent_tab
        self._has_failed = False
        
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

        # Main horizontal layout with circular progress on left
        main_h = QHBoxLayout(self)
        main_h.setContentsMargins(20, 15, 20, 15)
        main_h.setSpacing(15)
        
        # Circular progress indicator
        self.circular_progress = CircularProgress(size=70)
        main_h.addWidget(self.circular_progress)
        
        # Info section (vertical layout)
        v = QVBoxLayout()
        v.setSpacing(8)
        main_h.addLayout(v)
        
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
        
        self.retry_btn = QPushButton("🔄 Retry")
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 152, 0, 0.2);
                border: 1px solid rgba(255, 152, 0, 0.4);
                border-radius: 8px;
                color: #ff9800;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 152, 0, 0.3);
                border: 1px solid rgba(255, 152, 0, 0.6);
            }
        """)
        self.retry_btn.setVisible(False)

        hbtn.addWidget(self.pause_btn)
        hbtn.addWidget(self.resume_btn)
        hbtn.addWidget(self.cancel_btn)
        hbtn.addWidget(self.retry_btn)
        hbtn.addStretch()
        hbtn.addWidget(self.open_btn)
        
        v.addLayout(hbtn)

        print("Connecting button signals...")
        self.pause_btn.clicked.connect(lambda: self.manager.pause(job.id))
        self.resume_btn.clicked.connect(lambda: self.manager.resume(job.id))
        self.cancel_btn.clicked.connect(lambda: self.manager.cancel(job.id))
        self.open_btn.clicked.connect(self._open_folder)
        self.retry_btn.clicked.connect(self._on_retry)
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
        self.circular_progress.set_progress(pct)  # Update circular progress
        self.info.setText(f"📈 {pct}% • {speed} • {size} • ETA {eta}")
        self.info.setStyleSheet("""
            color: #1db954;
            font-size: 12px;
            font-weight: bold;
        """)

    def _on_done(self, path: str):
        self.info.setText("✅ Completed Successfully!")
        self.progress.setValue(100)
        self.circular_progress.set_progress(100)  # Complete
        self.info.setStyleSheet("""
            color: #4caf50;
            font-size: 12px;
            font-weight: bold;
        """)
        # Update parent stats
        if self.parent_tab:
            self.parent_tab._completed_count += 1
            self.parent_tab._update_stats()

    def _on_error(self, msg: str):
        self._has_failed = True
        self.info.setText(f"❌ Error: {msg}")
        self.info.setStyleSheet("""
            color: #f44336;
            font-size: 12px;
            font-weight: bold;
        """)
        # Show retry button
        self.retry_btn.setVisible(True)
        self.pause_btn.setVisible(False)
        self.resume_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        # Update parent stats
        if self.parent_tab:
            self.parent_tab._failed_count += 1
            self.parent_tab._update_stats()

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
    
    def _on_retry(self):
        """Retry failed download."""
        if self._has_failed:
            # Hide retry button, show normal controls
            self.retry_btn.setVisible(False)
            self.pause_btn.setVisible(True)
            self.cancel_btn.setVisible(True)
            self._has_failed = False
            
            # Reset UI state
            self.info.setText("⏳ Retrying...")
            self.info.setStyleSheet("""
                color: #1db954;
                font-size: 12px;
                font-weight: bold;
            """)
            self.progress.setValue(0)
            self.circular_progress.set_progress(0)
            
            # Update stats
            if self.parent_tab:
                self.parent_tab._failed_count -= 1
                self.parent_tab._update_stats()
            
            # Resubmit job
            self.manager.submit(self.job)

    def _open_folder(self):
        outdir = Path(self.job.outdir)
        try:
            if outdir.exists():
                # Windows Explorer
                import os
                os.startfile(outdir)  # type: ignore[attr-defined]
        except Exception:
            pass
