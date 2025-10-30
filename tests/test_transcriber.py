"""Tests for transcriber."""

import tempfile
from pathlib import Path
from dejensen.transcriber import save_timestamps, load_timestamps


def test_save_and_load_timestamps():
    """Test saving and loading timestamps."""
    words = [
        {"word": "hello", "start": 0.0, "end": 0.5},
        {"word": "world", "start": 0.6, "end": 1.0},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_timestamps.json"
        save_timestamps(words, output_path)

        assert output_path.exists()
        loaded = load_timestamps(output_path)
        assert loaded == words


def test_save_timestamps_creates_directory():
    """Test that save_timestamps creates parent directories."""
    words = [{"word": "test", "start": 0.0, "end": 0.5}]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "timestamps.json"
        save_timestamps(words, output_path)

        assert output_path.exists()
        loaded = load_timestamps(output_path)
        assert loaded == words
