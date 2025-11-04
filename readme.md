# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Music Downloader** is a Windows desktop application built with PyQt6 that downloads audio and video from YouTube. It features a modern UI with search, download queue management, and configurable quality settings.

## Development Commands

### Running the Application
```powershell
python music_downloader/main.py
```

### Virtual Environment (if using)
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Deactivate
deactivate
```

### Dependencies
```powershell
# Install dependencies
pip install -r requirements.txt

# Core dependencies:
# - PyQt6>=6.6 (GUI framework)
# - yt-dlp>=2024.07.02 (YouTube download engine)
# - requests>=2.31 (HTTP requests for thumbnails/API)
```

### Testing Individual Components
```powershell
# Test search functionality
python -c "from music_downloader.core.search import search_youtube; print(search_youtube('test query', limit=5))"

# Test downloader
python -c "from music_downloader.core.downloader import DownloadManager; print('DownloadManager loaded')"
```

## Architecture

### High-Level Structure

The application follows a **layered architecture** with clear separation of concerns:

```
music_downloader/
├── main.py              # Entry point, config management, Qt app setup
├── config.json          # User settings (download dir, quality, concurrency)
├── core/                # Business logic layer (no UI dependencies)
│   ├── downloader.py    # Download orchestration, job management
│   ├── search.py        # YouTube API & yt-dlp search integration
│   └── converter.py     # Placeholder for future conversion utilities
└── ui/                  # Presentation layer (PyQt6 components)
    ├── app_ui.py        # Main window, tab management, system tray
    ├── components.py    # Tab widgets (Search, Downloads, Settings)
    └── toast.py         # Toast notification system
```

### Key Architectural Patterns

#### 1. **Signal-Based Communication**
- PyQt signals connect UI events to business logic without tight coupling
- `SearchTab.request_download` → `AppWindow._on_request_download` → `DownloadsTab.enqueue_download`
- `DownloadJob` emits progress signals (`sig_progress`, `sig_done`, `sig_error`) that UI components subscribe to
- All cross-thread communication uses **queued connections** for thread safety

#### 2. **Concurrent Download Management**
- `DownloadManager` controls download concurrency using `QThreadPool`
- Each `DownloadJob` runs in a separate thread as a `QRunnable`
- Configurable concurrent download limit (default: 6)
- Jobs queue automatically when concurrency limit is reached
- **Important**: Uses `QTimer.singleShot` for non-blocking job submission to avoid UI freezes

#### 3. **Format-Specific Download Strategy**
- **MP3 downloads**: Single audio stream → can use `aria2c` for multi-connection speed boost
- **MP4 downloads**: Video+audio streams → must use yt-dlp's built-in downloader (aria2c cannot merge streams)
- Video quality selection: Best, 2160p (4K), 1440p, 1080p, 720p, etc.
- Audio always converted to AAC in MP4 for universal player compatibility

#### 4. **YouTube Search Dual-Path**
- Primary: YouTube Data API v3 (fast, structured results with thumbnails)
- Fallback: yt-dlp search (if API fails or rate-limited)
- API key stored in `core/search.py` (hardcoded for simplicity)

#### 5. **URL-Based Auto-Download**
- Direct video URLs trigger immediate download
- Playlist URLs extract all videos and batch-queue downloads
- Uses `extract_flat='in_playlist'` for fast playlist processing without individual video metadata

### Threading Model

1. **Main Thread**: Qt event loop, UI rendering
2. **Worker Threads**: Search queries, thumbnail loading (using `threading.Thread`)
3. **Download Threads**: yt-dlp downloads (managed by `QThreadPool`)
4. **Progress Updates**: Throttled to 4 updates/second to prevent UI lag

### Configuration Management

- `config.json` persists settings between sessions
- Loaded on startup, saved on exit via `AppWindow.get_config()`
- Settings propagate to `DownloadManager` via `_apply_settings()`
- Missing config keys auto-filled with `DEFAULT_CONFIG` values

## Common Development Patterns

### Adding a New Download Format

1. Update `format_box` options in `SearchTab.__init__()` (components.py)
2. Add format handling in `DownloadManager._run_job()` (downloader.py)
3. Define yt-dlp options (`ydl_opts`) with appropriate `format` string and `postprocessors`
4. Update `final_path` logic to handle new extension

### Adding New Quality Options

1. Add dropdown items in `SearchTab.__init__()` or `SettingsTab.__init__()`
2. Update parsing methods (`_parse_video_quality`, `_parse_audio_quality`)
3. Modify format string generation in `downloader.py` based on quality values

### Handling Download Errors

- All exceptions in `_run_job()` are caught and emitted via `job.sig_error`
- UI displays error in `DownloadRow._on_error()`
- Toast notifications shown via `AppWindow._notify_error()`

### Styling Guidelines

- Extensive inline QSS (Qt Style Sheets) for custom theming
- Color scheme: Dark background (`#0f0f0f`), Spotify-green accents (`#1db954`)
- Rounded corners (8-26px border-radius) for modern aesthetic
- Hover effects and gradient buttons throughout

## Known Constraints

- **Windows-only**: Uses `os.startfile()` for opening folders
- **FFmpeg required**: Must be in PATH for audio conversion (yt-dlp dependency)
- **aria2c optional**: Speeds up MP3 downloads if available in PATH
- **Single config file**: No multi-user support, config stored next to `main.py`

## Critical Implementation Details

### Thread-Safe Progress Updates
```python
# downloader.py: Progress hook throttling
if current_time - job._last_progress_time < 0.25:
    return d  # Skip update if < 250ms since last
```

### Playlist Batch Processing
```python
# components.py: Emit downloads in batches of 10
if len(batch_items) >= 10:
    for batch_item in batch_items:
        self.request_download.emit(...)
    batch_items = []
```

### System Tray Minimize-to-Tray
```python
# app_ui.py: Override closeEvent
def closeEvent(self, event):
    if self.tray and self.tray.isVisible():
        event.ignore()  # Don't actually close
        self.hide()     # Just hide window
```

## Code Quality Expectations

- **Type hints**: Use `from __future__ import annotations` for forward references
- **Error handling**: Catch specific exceptions, avoid bare `except:`
- **Comments**: Explain "why" not "what" (code should be self-documenting)
- **Threading**: Always use queued connections for cross-thread signals
- **Resource cleanup**: Use context managers (`with` statements) for file/network operations
