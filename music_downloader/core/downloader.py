from __future__ import annotations

import threading
import uuid
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Callable

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QRunnable, QThreadPool, QTimer
from yt_dlp import YoutubeDL


# --------- Utilities ---------

def _fmt_bytes(n: Optional[float]) -> str:
    if not n:
        return ""
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    v = float(n)
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.1f} {units[i]}"


def _fmt_eta(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# --------- Job model ---------

class DownloadJob(QObject):
    sig_progress = pyqtSignal(int, str, str, str)  # pct, speed, eta, size
    sig_done = pyqtSignal(str)  # final path
    sig_error = pyqtSignal(str)
    sig_status = pyqtSignal(str)

    def __init__(self, *, url: str, title: str, subtitle: str, fmt: str, bitrate_kbps: int, 
                 video_quality: str = "best", audio_quality: str = "best", outdir: Path):
        super().__init__()
        self.id: str = str(uuid.uuid4())
        self.url = url
        self.title = title
        self.subtitle = subtitle
        self.format = fmt
        self.bitrate_kbps = bitrate_kbps
        self.video_quality = video_quality  # e.g., "2160", "1440", "1080", "720", "best"
        self.audio_quality = audio_quality  # e.g., "320", "256", "192", "128", "best"
        self.outdir = str(outdir)
        self._pause = threading.Event()
        self._cancel = threading.Event()
        self._running = False
        self._last_progress_time = 0

    def request_pause(self):
        self._pause.set()

    def request_resume(self):
        self._pause.clear()

    def request_cancel(self):
        self._cancel.set()

    @property
    def is_paused(self) -> bool:
        return self._pause.is_set()

    @property
    def is_canceled(self) -> bool:
        return self._cancel.is_set()


# --------- Manager ---------
class DownloadManager:
    def __init__(self, download_dir: Path, concurrent: int = 3):
        self._download_dir = Path(download_dir)
        self._concurrent = max(1, int(concurrent))
        self._jobs: Dict[str, DownloadJob] = {}
        self._active_threads: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self._has_aria2c = self._check_aria2c()
        # Shared YoutubeDL info cache to avoid re-extracting video metadata
        self._info_cache: Dict[str, dict] = {}
        # Queue for pending jobs
        self._pending_jobs = []
    
    def _check_aria2c(self) -> bool:
        """Check if aria2c is available for faster downloads."""
        import shutil
        has_it = shutil.which("aria2c") is not None
        if has_it:
            print("aria2c found - using multi-connection downloads")
        else:
            print("aria2c not found - using standard download (slower)")
        return has_it

    def set_download_dir(self, path: Path):
        with self._lock:
            self._download_dir = Path(path)
            self._download_dir.mkdir(parents=True, exist_ok=True)

    def set_concurrency(self, n: int):
        with self._lock:
            self._concurrent = max(1, int(n))

    def create_job(self, item: dict, fmt: str, bitrate_kbps: int, 
                   video_quality: str = "best", audio_quality: str = "best") -> DownloadJob:
        title = item.get("title") or "Untitled"
        channel = item.get("channel") or ""
        duration = item.get("duration_str") or ""
        quality_str = f"{video_quality}p" if video_quality != "best" else "Best"
        subtitle = f"{channel} • {duration} • {fmt.upper()} • {quality_str}"
        job = DownloadJob(
            url=item.get("webpage_url") or item.get("url"),
            title=title,
            subtitle=subtitle,
            fmt=fmt,
            bitrate_kbps=bitrate_kbps,
            video_quality=video_quality,
            audio_quality=audio_quality,
            outdir=self._download_dir,
        )
        with self._lock:
            self._jobs[job.id] = job
        return job

    def submit(self, job: DownloadJob):
        # Start asynchronously using QTimer to avoid blocking UI
        print(f"Submitting job: {job.title}")
        QTimer.singleShot(0, lambda: self._start_or_queue(job))
        print(f"Job queued for start")

    def _start_or_queue(self, job: DownloadJob):
        # Use QThreadPool for better Qt integration
        class DownloadRunnable(QRunnable):
            def __init__(self, manager, job):
                super().__init__()
                self.manager = manager
                self.job = job
                self.setAutoDelete(True)
            
            def run(self):
                print(f"QRunnable started for: {self.job.title}")
                self.manager._run_job(self.job)
        
        with self._lock:
            if len(self._active_threads) >= self._concurrent:
                # poll again later using QTimer
                print(f"Queue full, retrying in 500ms")
                QTimer.singleShot(500, lambda: self._start_or_queue(job))
                return
            
            print(f"Starting download for: {job.title}")
            runnable = DownloadRunnable(self, job)
            self._active_threads[job.id] = runnable
            QThreadPool.globalInstance().start(runnable)
            print(f"Download started in thread pool")

    def pause(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.request_pause()
            job.sig_status.emit("Paused")

    def resume(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            was_paused = job.is_paused
            job.request_resume()
            if was_paused and job.id not in self._active_threads:
                # Resubmit to resume (yt-dlp will continue due to continuedl)
                self.submit(job)
            job.sig_status.emit("Resumed")

    def cancel(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.request_cancel()
            job.sig_status.emit("Canceled")

    # --------- Core runner ---------
    def _run_job(self, job: DownloadJob):
        job._running = True
        job.sig_status.emit("Starting…")
        job.sig_progress.emit(0, "--", "--:--", "--")  # Initialize progress bar immediately

        outtmpl = str(Path(job.outdir) / "%(title)s [%(id)s].%(ext)s")
        common_opts = {
            "outtmpl": outtmpl,
            "continuedl": True,
            "noplaylist": True,
            "retries": 3,  # Reduced for faster failure detection
            "fragment_retries": 3,
            "concurrent_fragments": 16,  # Max fragments for faster downloads
            "progress_hooks": [lambda d: self._on_hook(job, d)],
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
            "noprogress": True,
            # Speed optimizations
            "http_chunk_size": 10485760,  # 10MB chunks for faster downloads
            "socket_timeout": 20,  # Reduced timeout for faster initial connection
            "source_address": None,  # Use default routing for fastest connection
            # Parallelization optimizations
            "concurrent_fragment_downloads": 16,  # Download fragments in parallel
            "throttledratelimit": None,  # Remove any rate limiting
            "buffersize": 16384,  # Larger buffer for faster I/O
            # Skip unnecessary operations
            "writedescription": False,
            "writeinfojson": False,
            "writethumbnail": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            # Faster extraction
            "lazy_playlist": False,  # Don't wait for full playlist metadata
            "playlist_items": None,  # Process all items
            "ignoreerrors": False,  # Stop on first error for faster failure detection
        }
        
        # IMPORTANT: Don't use aria2c for downloads that need merging
        # aria2c can't merge video+audio streams, so we disable it for MP4
        # Only use aria2c for MP3 (single audio stream)
        # For MP4, yt-dlp's built-in downloader handles merging properly

        if job.format == "mp3":
            # Use aria2c for MP3 since it's a single audio stream (no merging needed)
            mp3_opts = dict(common_opts)
            if self._has_aria2c:
                mp3_opts["external_downloader"] = "aria2c"
                mp3_opts["external_downloader_args"] = {
                    "aria2c": [
                        "-x", "16", "-s", "16", "-k", "1M",
                        "--max-connection-per-server=16",
                        "--min-split-size=1M",
                        "--disk-cache=64M",
                    ]
                }
            
            ydl_opts = {
                **mp3_opts,
                "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": str(job.bitrate_kbps),
                    }
                ],
                "postprocessor_args": [
                    "-threads", "0",
                    "-preset", "ultrafast",
                ],
            }
        else:  # mp4
            # Build format string based on user-selected quality
            video_quality = job.video_quality
            audio_quality = job.audio_quality
            
            # DEBUG: Log quality settings
            print(f"\n{'='*80}")
            print(f"QUALITY SETTINGS FOR: {job.title[:50]}")
            print(f"Video Quality: {video_quality}")
            print(f"Audio Quality: {audio_quality}")
            print(f"{'='*80}\n")
            
            # Simplified format selection that GUARANTEES video+audio merge
            # The key is to not have complex fallbacks that might pick video-only
            if video_quality == "best":
                format_str = "bestvideo+bestaudio/best"
            else:
                # Try to get requested quality, but ALWAYS require audio
                height = video_quality
                format_str = f"bestvideo[height<={height}]+bestaudio/bestvideo+bestaudio/best"
            
            # DEBUG: Log format string
            print(f"Format string: {format_str}")
            print(f"This will download SEPARATE video ({video_quality}) + audio ({audio_quality}) streams")
            print(f"FFmpeg will merge them into final MP4\n")
            
            ydl_opts = {
                **common_opts,
                "format": format_str,
                "merge_output_format": "mp4",
                # CRITICAL: Disable external downloaders for MP4 to enable merging
                "external_downloader": None,
                # Convert audio to AAC for universal playback compatibility
                # Opus/Vorbis in MP4 containers don't work in all players
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    },
                ],
                "postprocessor_args": [
                    "-c:v", "copy",  # Keep video as-is (no re-encode)
                    "-c:a", "aac",  # Convert audio to AAC for compatibility
                    "-b:a", "320k",  # High quality audio bitrate
                    "-threads", "0",  # Use all CPU cores
                    "-preset", "ultrafast",  # Fastest encoding speed
                ],
            }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
                # Final file path (postprocessors may change extension)
                final_path = Path(ydl.prepare_filename(info)).with_suffix(
                    ".mp3" if job.format == "mp3" else ".mp4"
                )
            job.sig_done.emit(str(final_path))
        except Exception as e:
            if job.is_canceled:
                job.sig_error.emit("Canceled by user")
            else:
                job.sig_error.emit(str(e))
        finally:
            job._running = False
            with self._lock:
                self._active_threads.pop(job.id, None)

    # progress hook
    def _on_hook(self, job: DownloadJob, d: dict):
        try:
            # Cooperative pause/cancel
            if job.is_canceled:
                raise Exception("User canceled")
            while job.is_paused:
                job.sig_status.emit("Paused…")
                if job.is_canceled:
                    raise Exception("User canceled")
                threading.Event().wait(0.25)

            status = d.get("status")
            if status == "downloading":
                # Throttle progress updates to max 4 per second for smoother UI
                current_time = time.time()
                if current_time - job._last_progress_time < 0.25:
                    return d
                job._last_progress_time = current_time
                
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                pct = int(downloaded * 100 / total) if total else 0
                speed = _fmt_bytes(d.get("speed")) + "/s" if d.get("speed") else "--"
                eta = _fmt_eta(d.get("eta"))
                size = _fmt_bytes(total)
                job.sig_progress.emit(pct, speed, eta, size)
            elif status == "finished":
                job.sig_status.emit("Converting…")
        except Exception as e:
            # Don't let hook errors crash the download
            if "canceled" in str(e).lower():
                raise
            print(f"Progress hook error: {e}")

        return d
