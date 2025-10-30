"""Tests for gap detection."""

import pytest
from dejensonify.gap_detector import find_gaps, calculate_keep_segments


def test_find_gaps_basic():
    """Test basic gap detection."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
        {"word": "foo", "start": 3.0, "end": 3.5},
    ]

    gaps = find_gaps(words, max_gap=1.0)
    assert len(gaps) == 1
    assert gaps[0] == (0.5, 2.0)


def test_find_gaps_no_gaps():
    """Test when there are no gaps exceeding threshold."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.6, "end": 1.0},
        {"word": "foo", "start": 1.1, "end": 1.5},
    ]

    gaps = find_gaps(words, max_gap=1.0)
    assert len(gaps) == 0


def test_find_gaps_multiple():
    """Test multiple gaps."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
        {"word": "foo", "start": 4.0, "end": 4.5},
    ]

    gaps = find_gaps(words, max_gap=1.0)
    assert len(gaps) == 2
    assert gaps[0] == (0.5, 2.0)
    assert gaps[1] == (2.5, 4.0)


def test_calculate_keep_segments_basic():
    """Test calculating segments to keep."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
        {"word": "foo", "start": 3.0, "end": 3.5},
    ]

    segments = calculate_keep_segments(words, max_gap=1.0)
    assert len(segments) == 2
    assert segments[0] == (0.0, 0.5)
    assert segments[1] == (2.0, 3.5)


def test_calculate_keep_segments_no_gaps():
    """Test when there are no gaps to remove."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.6, "end": 1.0},
    ]

    segments = calculate_keep_segments(words, max_gap=1.0)
    assert len(segments) == 1
    assert segments[0] == (0.0, 1.0)


def test_calculate_keep_segments_with_duration():
    """Test with explicit video duration."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
    ]

    segments = calculate_keep_segments(words, max_gap=1.0, video_duration=5.0)
    assert len(segments) == 2
    assert segments[0] == (0.0, 0.5)
    assert segments[1] == (2.0, 5.0)


def test_calculate_keep_segments_empty():
    """Test with empty word list."""
    segments = calculate_keep_segments([])
    assert segments == []
