from __future__ import annotations

from typing import List, Dict, Any
import requests

from yt_dlp import YoutubeDL

YOUTUBE_API_KEY = "AIzaSyA2W5eZ17UTyw4GM-kdEQbVkNz0B2Hwzz8"


def _best_thumbnail(entry: Dict[str, Any]) -> str | None:
    # Prefer highest resolution thumbnail
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        best = max(thumbs, key=lambda t: (t.get("height") or 0, t.get("width") or 0))
        return best.get("url")
    return entry.get("thumbnail")


def _fmt_duration(seconds: int | None) -> str:
    if not seconds and seconds != 0:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def search_youtube(query: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Search YouTube using the Data API v3."""
    items: List[Dict[str, Any]] = []
    
    try:
        # Use YouTube Data API v3
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(limit, 50),  # API limit is 50
            "key": YOUTUBE_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
        
        if not video_ids:
            return items
        
        # Get video details (duration, etc.)
        details_url = "https://www.googleapis.com/youtube/v3/videos"
        details_params = {
            "part": "contentDetails,snippet",
            "id": ",".join(video_ids),
            "key": YOUTUBE_API_KEY,
        }
        
        details_response = requests.get(details_url, params=details_params, timeout=10)
        details_response.raise_for_status()
        details_data = details_response.json()
        
        for video in details_data.get("items", []):
            video_id = video["id"]
            snippet = video["snippet"]
            content_details = video["contentDetails"]
            
            # Parse ISO 8601 duration (PT1H2M10S -> seconds)
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = _parse_iso8601_duration(duration_str)
            
            # Get best thumbnail
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {})
                .get("url")
                or thumbnails.get("high", {})
                .get("url")
                or thumbnails.get("medium", {})
                .get("url")
                or thumbnails.get("default", {})
                .get("url")
            )
            
            items.append(
                {
                    "id": video_id,
                    "title": snippet.get("title"),
                    "duration": duration_seconds,
                    "duration_str": _fmt_duration(duration_seconds),
                    "channel": snippet.get("channelTitle"),
                    "thumbnail": thumbnail_url,
                    "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
                }
            )
    
    except Exception as e:
        # Fallback to yt-dlp search if API fails
        print(f"YouTube API search failed: {e}, falling back to yt-dlp")
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{int(limit)}:{query}", download=False)
            entries = info.get("entries", []) if isinstance(info, dict) else []
            for e in entries:
                url = e.get("webpage_url") or e.get("url")
                items.append(
                    {
                        "id": e.get("id"),
                        "title": e.get("title"),
                        "duration": e.get("duration"),
                        "duration_str": _fmt_duration(e.get("duration")),
                        "channel": e.get("uploader") or e.get("channel"),
                        "thumbnail": _best_thumbnail(e),
                        "webpage_url": url,
                    }
                )
    
    return items


def _parse_iso8601_duration(duration: str) -> int:
    """Parse ISO 8601 duration string (e.g., PT1H2M10S) to seconds."""
    import re
    
    pattern = re.compile(
        r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
    )
    match = pattern.match(duration)
    
    if not match:
        return 0
    
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    
    return hours * 3600 + minutes * 60 + seconds
