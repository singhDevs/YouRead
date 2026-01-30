"""Video metadata fetching from YouTube."""

import json
import re
import urllib.request
import urllib.error
from typing import Optional

from .models import VideoInfo
from .exceptions import VideoNotFoundError


def fetch_video_metadata(video_id: str) -> VideoInfo:
    """Fetch video metadata (title, channel) from YouTube.

    Uses YouTube's oEmbed API which doesn't require an API key.

    Args:
        video_id: The YouTube video ID (11 characters).

    Returns:
        VideoInfo object containing video metadata.

    Raises:
        VideoNotFoundError: If the video doesn't exist or is unavailable.
    """
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

    try:
        with urllib.request.urlopen(oembed_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        title = data.get("title", "Untitled Video")
        channel = data.get("author_name", "Unknown Channel")

        return VideoInfo(
            video_id=video_id,
            title=title,
            channel=channel,
        )

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise VideoNotFoundError(video_id) from e
        raise VideoNotFoundError(video_id) from e
    except urllib.error.URLError as e:
        raise VideoNotFoundError(video_id) from e
    except json.JSONDecodeError as e:
        raise VideoNotFoundError(video_id) from e


def sanitize_filename(title: str) -> str:
    """Convert a video title into a safe filename.

    Removes or replaces characters that are invalid in filenames.

    Args:
        title: The video title to sanitize.

    Returns:
        A filesystem-safe version of the title.
    """
    # Remove or replace invalid filename characters
    # Windows: \ / : * ? " < > |
    # Also handle newlines and tabs
    sanitized = re.sub(r'[\\/:*?"<>|\n\t\r]', '', title)

    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)

    # Trim whitespace
    sanitized = sanitized.strip()

    # Limit length (leave room for .md extension)
    max_length = 200
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0]

    # Fallback if empty
    if not sanitized:
        sanitized = "untitled"

    return sanitized
