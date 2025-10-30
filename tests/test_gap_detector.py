"""Tests for gap detection."""

from dejensen.gap_detector import find_gaps


def test_find_gaps_basic():
    """Test basic gap detection."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
        {"word": "foo", "start": 3.0, "end": 3.5},
    ]

    gaps = find_gaps(words, min_gap=1.0)
    assert len(gaps) == 1
    assert gaps[0] == (0.5, 2.0)


def test_find_gaps_no_gaps():
    """Test when there are no gaps exceeding threshold."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.6, "end": 1.0},
        {"word": "foo", "start": 1.1, "end": 1.5},
    ]

    gaps = find_gaps(words, min_gap=1.0)
    assert len(gaps) == 0


def test_find_gaps_multiple():
    """Test multiple gaps."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 2.0, "end": 2.5},
        {"word": "foo", "start": 4.0, "end": 4.5},
    ]

    gaps = find_gaps(words, min_gap=1.0)
    assert len(gaps) == 2
    assert gaps[0] == (0.5, 2.0)
    assert gaps[1] == (2.5, 4.0)
