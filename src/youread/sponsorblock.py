"""SponsorBlock integration for removing sponsor segments."""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

from .models import TranscriptSegment


@dataclass(frozen=True)
class SponsorSegment:
    """A sponsored segment identified by SponsorBlock.

    Attributes:
        start: Start time in seconds.
        end: End time in seconds.
        category: Type of segment (sponsor, selfpromo, intro, etc.).
    """
    start: float
    end: float
    category: str


def fetch_sponsor_segments(video_id: str) -> list[SponsorSegment]:
    """Fetch sponsor segments from SponsorBlock API.

    Args:
        video_id: The YouTube video ID.

    Returns:
        List of SponsorSegment objects. Empty list if none found or API fails.
    """
    # Categories to skip: sponsor, selfpromo
    categories = '["sponsor","selfpromo"]'
    url = f"https://sponsor.ajay.app/api/skipSegments?videoID={video_id}&categories={categories}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        segments = []
        for item in data:
            segment = item.get("segment", [])
            if len(segment) == 2:
                segments.append(SponsorSegment(
                    start=float(segment[0]),
                    end=float(segment[1]),
                    category=item.get("category", "sponsor"),
                ))

        return segments

    except urllib.error.HTTPError:
        # 404 means no segments found - this is normal
        return []
    except urllib.error.URLError:
        # Network error - continue without sponsor removal
        return []
    except json.JSONDecodeError:
        return []


def remove_sponsor_segments(
    transcript: list[TranscriptSegment],
    sponsor_segments: list[SponsorSegment],
) -> list[TranscriptSegment]:
    """Remove transcript segments that overlap with sponsor segments.

    A transcript segment is removed if it overlaps significantly (>50%)
    with any sponsor segment.

    Args:
        transcript: List of transcript segments.
        sponsor_segments: List of sponsor segments to filter out.

    Returns:
        Filtered list of transcript segments with sponsors removed.
    """
    if not sponsor_segments:
        return transcript

    filtered = []
    for segment in transcript:
        segment_start = segment.start
        segment_end = segment.end

        # Check if this segment overlaps with any sponsor segment
        is_sponsored = False
        for sponsor in sponsor_segments:
            # Calculate overlap
            overlap_start = max(segment_start, sponsor.start)
            overlap_end = min(segment_end, sponsor.end)
            overlap_duration = max(0, overlap_end - overlap_start)

            # If more than 50% of the segment is sponsored, remove it
            if segment.duration > 0:
                overlap_ratio = overlap_duration / segment.duration
                if overlap_ratio > 0.5:
                    is_sponsored = True
                    break

        if not is_sponsored:
            filtered.append(segment)

    return filtered
