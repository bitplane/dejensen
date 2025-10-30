"""Detect gaps/pauses in word timestamps."""


def find_gaps(words: list[dict], max_gap: float = 0.2) -> list[tuple[float, float]]:
    """
    Find gaps between words that exceed the maximum gap threshold.

    Args:
        words: List of word dictionaries with 'start' and 'end' keys
        max_gap: Maximum allowed gap in seconds (default 0.2)

    Returns:
        List of (start, end) tuples representing gaps to remove
    """
    gaps = []

    for i in range(len(words) - 1):
        current_end = words[i]["end"]
        next_start = words[i + 1]["start"]
        gap_duration = next_start - current_end

        if gap_duration > max_gap:
            gaps.append((current_end, next_start))

    return gaps


def calculate_keep_segments(words: list[dict], max_gap: float = 0.2, video_duration: float | None = None) -> list[tuple[float, float]]:
    """
    Calculate video segments to keep (inverse of gaps).

    Extends segments into gaps by half the max_gap threshold on each side to avoid cutting off
    breaths, trailing sounds, etc due to Whisper timestamp inaccuracies.

    Args:
        words: List of word dictionaries with 'start' and 'end' keys
        max_gap: Maximum allowed gap in seconds
        video_duration: Total video duration in seconds (if None, uses last word end time)

    Returns:
        List of (start, end) tuples representing segments to keep
    """
    if not words:
        return []

    gaps = find_gaps(words, max_gap)

    if not gaps:
        # No gaps to remove, keep entire video
        end_time = video_duration if video_duration else words[-1]["end"]
        return [(0.0, end_time)]

    segments = []
    current_start = 0.0
    padding = max_gap / 2.0  # Keep half the threshold on each side

    for gap_start, gap_end in gaps:
        # Extend segment end into the gap by half threshold
        segment_end = min(gap_start + padding, gap_end)
        segments.append((current_start, segment_end))

        # Next segment starts half threshold before gap ends
        current_start = max(gap_end - padding, gap_start)

    # Add final segment from last gap to end
    end_time = video_duration if video_duration else words[-1]["end"]
    segments.append((current_start, end_time))

    return segments
