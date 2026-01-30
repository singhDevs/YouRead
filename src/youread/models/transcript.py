"""Transcript segment model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptSegment:
    """Immutable container for a single transcript segment.

    Attributes:
        text: The spoken text content.
        start: Start time in seconds from video beginning.
        duration: Duration of this segment in seconds.
    """
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        """Calculate the end time of this segment."""
        return self.start + self.duration
