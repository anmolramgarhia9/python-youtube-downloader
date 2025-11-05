"""
Asynchronous thumbnail loading and caching system
Uses QThreadPool for non-blocking image downloads with disk cache
"""

import hashlib
import time
from pathlib import Path
from typing import Optional, Callable
import requests

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ThumbnailSignals(QObject):
    """Signals for thumbnail loading"""
    loaded = pyqtSignal(QPixmap)
    failed = pyqtSignal()


class ThumbnailLoadTask(QRunnable):
    """Runnable task for loading thumbnail asynchronously"""
    
    def __init__(self, url: str, width: int, height: int, cache_dir: Path):
        super().__init__()
        self.url = url
        self.width = width
        self.height = height
        self.cache_dir = cache_dir
        self.signals = ThumbnailSignals()
        self.setAutoDelete(True)
    
    def run(self):
        """Load thumbnail from cache or download"""
        try:
            # Try cache first
            pixmap = self._load_from_cache()
            if pixmap:
                self.signals.loaded.emit(pixmap)
                return
            
            # Download and cache
            pixmap = self._download_and_cache()
            if pixmap:
                self.signals.loaded.emit(pixmap)
            else:
                self.signals.failed.emit()
        except Exception as e:
            print(f"Thumbnail load error: {e}")
            self.signals.failed.emit()
    
    def _get_cache_path(self) -> Path:
        """Get cache file path for URL"""
        url_hash = hashlib.md5(self.url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"
    
    def _load_from_cache(self) -> Optional[QPixmap]:
        """Load thumbnail from cache if valid"""
        cache_path = self._get_cache_path()
        if not cache_path.exists():
            return None
        
        # Check if cache is expired (7 days)
        cache_age = time.time() - cache_path.stat().st_mtime
        if cache_age > 7 * 24 * 3600:  # 7 days in seconds
            cache_path.unlink()
            return None
        
        # Load from cache
        pixmap = QPixmap(str(cache_path))
        if not pixmap.isNull():
            return pixmap.scaled(
                self.width, 
                self.height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
        return None
    
    def _download_and_cache(self) -> Optional[QPixmap]:
        """Download thumbnail and save to cache"""
        try:
            # Download with timeout
            response = requests.get(self.url, timeout=5, verify=True)
            response.raise_for_status()
            
            # Create cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to cache
            cache_path = self._get_cache_path()
            cache_path.write_bytes(response.content)
            
            # Load and scale
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            if not pixmap.isNull():
                return pixmap.scaled(
                    self.width, 
                    self.height, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
        except Exception as e:
            print(f"Download error: {e}")
        return None


class ThumbnailCache:
    """Manages thumbnail loading with caching"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".music_downloader" / "cache" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thread_pool = QThreadPool.globalInstance()
        # Set reasonable thread limit for thumbnails
        self.thread_pool.setMaxThreadCount(min(8, self.thread_pool.maxThreadCount()))
    
    def load_async(
        self, 
        url: str, 
        width: int, 
        height: int,
        on_loaded: Callable[[QPixmap], None],
        on_failed: Optional[Callable[[], None]] = None
    ):
        """
        Load thumbnail asynchronously
        
        Args:
            url: Image URL to load
            width: Target width
            height: Target height
            on_loaded: Callback when pixmap is loaded
            on_failed: Optional callback when loading fails
        """
        task = ThumbnailLoadTask(url, width, height, self.cache_dir)
        task.signals.loaded.connect(on_loaded)
        if on_failed:
            task.signals.failed.connect(on_failed)
        self.thread_pool.start(task)
    
    def clear_cache(self):
        """Clear all cached thumbnails"""
        try:
            for file in self.cache_dir.glob("*.jpg"):
                file.unlink()
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries (older than 7 days)"""
        try:
            cutoff = time.time() - 7 * 24 * 3600
            for file in self.cache_dir.glob("*.jpg"):
                if file.stat().st_mtime < cutoff:
                    file.unlink()
        except Exception as e:
            print(f"Cache cleanup error: {e}")


# Global instance
_thumbnail_cache = None


def get_thumbnail_cache() -> ThumbnailCache:
    """Get global thumbnail cache instance"""
    global _thumbnail_cache
    if _thumbnail_cache is None:
        _thumbnail_cache = ThumbnailCache()
    return _thumbnail_cache
