"""Custom exceptions for YouRead."""


class YouReadError(Exception):
    """Base exception for all YouRead errors."""
    pass


class InvalidURLError(YouReadError):
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Invalid YouTube URL: {url}")


class TranscriptNotFoundError(YouReadError):
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        super().__init__(f"No transcript available for video: {video_id}")


class VideoNotFoundError(YouReadError):
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        super().__init__(f"Video not found or unavailable: {video_id}")
