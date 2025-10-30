"""Detect gaps/pauses in word timestamps."""


def find_gaps(words: list[dict], min_gap: float = 0.2) -> list[tuple[float, float]]:
    """
    Find gaps between words that exceed the minimum gap threshold.

    Args:
        words: List of word dictionaries with 'start' and 'end' keys
        min_gap: Minimum gap duration to detect in seconds (default 0.2)

    Returns:
        List of (start, end) tuples representing gaps to speed up
    """
    gaps = []

    for i in range(len(words) - 1):
        current_end = words[i]["end"]
        next_start = words[i + 1]["start"]
        gap_duration = next_start - current_end

        if gap_duration > min_gap:
            gaps.append((current_end, next_start))

    return gaps
