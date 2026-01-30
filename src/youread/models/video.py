"""Video metadata model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoInfo:
    """Immutable container for YouTube video metadata.

    Attributes:
        video_id: The unique YouTube video identifier (11 characters).
        title: The video title.
        channel: The channel name that uploaded the video.
    """
    video_id: str
    title: str
    channel: str

    def __post_init__(self) -> None:
        if not self.video_id:
            raise ValueError("video_id cannot be empty")
