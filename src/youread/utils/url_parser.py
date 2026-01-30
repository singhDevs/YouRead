"""YouTube URL parsing utilities."""

import re
from ..exceptions import InvalidURLError


# Patterns for various YouTube URL formats
YOUTUBE_PATTERNS = [
    # Standard watch URLs: youtube.com/watch?v=VIDEO_ID
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",
    # Short URLs: youtu.be/VIDEO_ID
    r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})",
    # Embed URLs: youtube.com/embed/VIDEO_ID
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    # Shorts URLs: youtube.com/shorts/VIDEO_ID
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    # Mobile URLs: m.youtube.com/watch?v=VIDEO_ID
    r"(?:https?://)?m\.youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",
    # Live URLs: youtube.com/live/VIDEO_ID
    r"(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})",
]


def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL.

    Supports multiple URL formats:
    - youtube.com/watch?v=VIDEO_ID
    - youtu.be/VIDEO_ID
    - youtube.com/embed/VIDEO_ID
    - youtube.com/shorts/VIDEO_ID
    - m.youtube.com/watch?v=VIDEO_ID
    - youtube.com/live/VIDEO_ID

    Args:
        url: A YouTube URL in any supported format.

    Returns:
        The 11-character video ID.

    Raises:
        InvalidURLError: If the URL doesn't match any known YouTube format.
    """
    url = url.strip()

    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise InvalidURLError(url)
