"""Tests for speed transition calculation."""

import pytest
from dejensen.speed_calculator import calculate_speed_transitions


def test_basic_compression():
    """Test basic gap compression from 2s to 0.5s."""
    segments = calculate_speed_transitions(10.0, 12.0, 0.5, steps=5)

    # Should return 5 segments
    assert len(segments) == 5

    # First segment should start at gap_start
    assert segments[0][0] == 10.0

    # Last segment should end at gap_end
    assert abs(segments[-1][1] - 12.0) < 0.001

    # Segments should be contiguous (within floating point tolerance)
    for i in range(len(segments) - 1):
        assert abs(segments[i][1] - segments[i + 1][0]) < 0.001

    # Edge speeds should be symmetric
    assert abs(segments[0][2] - segments[-1][2]) < 0.001

    # Middle should be fastest
    middle_idx = len(segments) // 2
    for i, seg in enumerate(segments):
        if i != middle_idx:
            assert seg[2] <= segments[middle_idx][2]


def test_timing_constraint():
    """Verify output duration matches target."""
    gap_start, gap_end = 5.0, 8.0  # 3 second gap
    target = 0.8  # compress to 0.8s

    segments = calculate_speed_transitions(gap_start, gap_end, target, steps=11)

    # Calculate actual output duration
    total_output = 0.0
    for seg_start, seg_end, speed in segments:
        input_duration = seg_end - seg_start
        output_duration = input_duration / speed
        total_output += output_duration

    # Should match target within small tolerance
    assert abs(total_output - target) < 0.001


def test_minimal_compression():
    """Test when target is close to gap duration."""
    segments = calculate_speed_transitions(0.0, 2.0, 1.9, steps=5)

    # All speeds should be close to 1.0 (very gentle speedup)
    for _, _, speed in segments:
        assert 1.0 <= speed < 1.2  # Should be between 1x and 1.2x


def test_extreme_compression():
    """Test very aggressive compression (10s to 1s)."""
    segments = calculate_speed_transitions(0.0, 10.0, 1.0, steps=11)

    # Should still satisfy timing constraint
    total_output = sum((end - start) / speed for start, end, speed in segments)
    assert abs(total_output - 1.0) < 0.001

    # Middle should be very fast
    middle_speed = segments[len(segments) // 2][2]
    assert middle_speed > 5.0  # Should be much faster than edges


def test_odd_and_even_steps():
    """Test with both odd and even number of steps."""
    for steps in [5, 7, 9, 11, 4, 6, 8, 10]:
        segments = calculate_speed_transitions(10.0, 15.0, 2.0, steps=steps)

        assert len(segments) == steps

        # Verify timing
        total_output = sum((end - start) / speed for start, end, speed in segments)
        assert abs(total_output - 2.0) < 0.001


def test_minimum_steps():
    """Test with minimum useful number of steps."""
    segments = calculate_speed_transitions(0.0, 2.0, 0.5, steps=3)

    assert len(segments) == 3
    # Should still satisfy timing
    total_output = sum((end - start) / speed for start, end, speed in segments)
    assert abs(total_output - 0.5) < 0.001


def test_symmetry():
    """Test that speed curve is symmetric."""
    segments = calculate_speed_transitions(0.0, 10.0, 2.0, steps=11)

    # Speeds should be symmetric around middle
    for i in range(len(segments) // 2):
        left_speed = segments[i][2]
        right_speed = segments[-(i + 1)][2]
        assert abs(left_speed - right_speed) < 0.001


def test_invalid_inputs():
    """Test error handling for invalid inputs."""
    # Target longer than gap (would need slowdown, not speedup)
    with pytest.raises(ValueError):
        calculate_speed_transitions(0.0, 2.0, 3.0, steps=5)

    # Negative target
    with pytest.raises(ValueError):
        calculate_speed_transitions(0.0, 2.0, -1.0, steps=5)

    # Zero target
    with pytest.raises(ValueError):
        calculate_speed_transitions(0.0, 2.0, 0.0, steps=5)


def test_segment_coverage():
    """Test that segments exactly cover the gap with no overlap."""
    segments = calculate_speed_transitions(5.5, 8.3, 1.2, steps=7)

    # First starts at gap_start
    assert segments[0][0] == 5.5

    # Last ends at gap_end
    assert abs(segments[-1][1] - 8.3) < 0.001

    # No gaps or overlaps between segments (within floating point tolerance)
    for i in range(len(segments) - 1):
        assert abs(segments[i][1] - segments[i + 1][0]) < 0.001

    # Total input duration equals gap duration
    total_input = sum(end - start for start, end, _ in segments)
    expected_input = 8.3 - 5.5
    assert abs(total_input - expected_input) < 0.001


def test_speed_values_reasonable():
    """Test that all speeds are >= 1.0 (never slow down)."""
    segments = calculate_speed_transitions(0.0, 5.0, 1.0, steps=9)

    for _, _, speed in segments:
        assert speed >= 1.0, f"Speed {speed} is less than 1.0x"


def test_different_gap_sizes():
    """Test with various gap sizes and compression ratios."""
    test_cases = [
        (0.0, 0.5, 0.1, 5),  # Small gap, 5x compression
        (10.0, 20.0, 2.0, 11),  # Medium gap, 5x compression
        (0.0, 100.0, 10.0, 15),  # Large gap, 10x compression
        (0.0, 30.0, 0.2, 11),  # Extreme compression (150x)
    ]

    for gap_start, gap_end, target, steps in test_cases:
        segments = calculate_speed_transitions(gap_start, gap_end, target, steps)

        # Verify timing constraint
        total_output = sum((end - start) / speed for start, end, speed in segments)
        assert abs(total_output - target) < 0.001, f"Failed for gap [{gap_start}, {gap_end}] -> {target}s"


def test_edge_speeds_reasonable():
    """Test that edge speeds are reasonable even for extreme compression."""
    # 30s gap compressed to 0.2s (150x compression ratio)
    segments = calculate_speed_transitions(0.0, 30.0, 0.2, steps=11)

    edge_speed = segments[0][2]
    peak_speed = segments[5][2]

    # Edge speed should be about 20% of peak speed
    assert abs(edge_speed / peak_speed - 0.2) < 0.05

    # Edge speed should be much less than peak (smooth ramp up)
    assert edge_speed < peak_speed * 0.3

    # Verify timing still works
    total_output = sum((end - start) / speed for start, end, speed in segments)
    assert abs(total_output - 0.2) < 0.001
