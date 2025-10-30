"""Calculate speed transitions for smooth gap compression."""


def _total_time_for_peak(p: float, steps: int, gap_duration: float) -> float:
    """Calculate total output duration for a given peak speed."""
    d = gap_duration / steps
    total = 0.0
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0.0
        # Smooth curve: edges at 20% of peak, middle at 100%
        base_curve = 4.0 * t * (1.0 - t)  # parabola 0→1→0
        c = 0.2 + 0.8 * base_curve  # scale to 0.2→1.0→0.2
        v = 1.0 + (p - 1.0) * c  # >= 1.0
        total += d / v
    return total


def _solve_peak_speed(gap_duration: float, target_duration: float, steps: int) -> float:
    """Solve for peak speed using bisection."""
    # Feasibility: with p=1, T=gap_duration; as p→∞, T→0.
    if not (0 < target_duration <= gap_duration):
        raise ValueError("target_duration must be in (0, gap_duration].")
    lo, hi = 1.0, 1e6  # big upper bound; monotone so safe
    for _ in range(80):  # ~double precision bisection
        mid = (lo + hi) / 2.0
        Tmid = _total_time_for_peak(mid, steps, gap_duration)
        if Tmid > target_duration:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def calculate_speed_transitions(
    gap_start: float, gap_end: float, target_duration: float, steps: int = 11
) -> list[tuple[float, float, float]]:
    """
    Calculate speed transitions to compress a gap using smooth easing.

    Takes a time gap and calculates how to speed it up to fit in target_duration
    using a symmetric easing curve. Edge segments play at 1.0x (no speedup),
    middle segments play faster. The curve is quadratic ease-in-out.

    Args:
        gap_start: Start time of the gap in seconds
        gap_end: End time of the gap in seconds
        target_duration: Desired output duration in seconds
        steps: Number of speed segments (default 11)

    Returns:
        List of (segment_start, segment_end, speed_multiplier) tuples

    Example:
        >>> transitions = calculate_speed_transitions(10.0, 12.0, 0.5, steps=5)
        >>> # Returns 5 segments covering 10.0-12.0s that play in 0.5s total
    """
    gap_duration = gap_end - gap_start
    p = _solve_peak_speed(gap_duration, target_duration, steps)
    seg_len = gap_duration / steps
    segments = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0.0
        # Smooth curve: edges at 20% of peak, middle at 100%
        base_curve = 4.0 * t * (1.0 - t)  # parabola 0→1→0
        c = 0.2 + 0.8 * base_curve  # scale to 0.2→1.0→0.2
        v = 1.0 + (p - 1.0) * c
        seg_start = gap_start + i * seg_len
        seg_end = seg_start + seg_len
        segments.append((seg_start, seg_end, v))
    return segments
