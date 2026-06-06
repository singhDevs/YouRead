"""Transcript extraction from YouTube videos."""

from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from .models import TranscriptSegment
from .exceptions import TranscriptNotFoundError, VideoNotFoundError


def fetch_transcript(
    video_id: str,
    languages: Optional[list[str]] = None,
) -> list[TranscriptSegment]:
    """Fetch the transcript for a YouTube video.

    Attempts to fetch transcript in the following order:
    1. Manual captions in preferred languages
    2. Auto-generated captions in preferred languages

    Args:
        video_id: The YouTube video ID (11 characters).
        languages: Preferred languages in order of priority.
                   Defaults to ["en"] (English only).

    Returns:
        List of TranscriptSegment objects containing the full transcript.

    Raises:
        TranscriptNotFoundError: If no transcript is available.
        VideoNotFoundError: If the video doesn't exist or is unavailable.
    """
    if languages is None:
        languages = ["en"]

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        transcript = _find_best_transcript(transcript_list, languages)
        fetched_transcript = transcript.fetch()

        transcript_segments = []
        for snippet in fetched_transcript:
            transcript_segments.append(
                TranscriptSegment(
                    text=snippet.text,
                    start=snippet.start,
                    duration=snippet.duration,
                )
            )
        return transcript_segments

    except VideoUnavailable as e:
        raise VideoNotFoundError(video_id) from e
    except (NoTranscriptFound, TranscriptsDisabled) as e:
        raise TranscriptNotFoundError(video_id) from e


def _find_best_transcript(transcript_list, languages: list[str]):
    """Find the best available transcript from the list.

    Priority:
    1. Manual transcript in preferred language
    2. Auto-generated transcript in preferred language

    Args:
        transcript_list: TranscriptList object from YouTubeTranscriptApi.list().
        languages: List of preferred language codes.

    Returns:
        The best available Transcript object.

    Raises:
        NoTranscriptFound: If no usable transcript is found.
    """
    # Try manual transcripts first (priority)
    try:
        return transcript_list.find_manually_created_transcript(languages)
    except NoTranscriptFound:
        pass

    # Fall back to auto-generated transcripts
    return transcript_list.find_generated_transcript(languages)


def transcript_to_text(segments: list[TranscriptSegment]) -> str:
    """Convert transcript segments to a single text string.

    Joins all segment text with spaces, cleaning up whitespace.

    Args:
        segments: List of TranscriptSegment objects.

    Returns:
        Single string containing the full transcript text.
    """
    transcript_text = ""
    for segment in segments:
        transcript_text += segment.text.strip() + " "
    return transcript_text.strip()
