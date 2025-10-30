"""Audio transcription using Whisper."""

from pathlib import Path
import whisper
import json


def extract_timestamps(video_path: Path, model_name: str = "base") -> list[dict]:
    """
    Extract word-level timestamps from a video using Whisper.

    Args:
        video_path: Path to the video file
        model_name: Whisper model to use (tiny, base, small, medium, large)

    Returns:
        List of word dictionaries with 'word', 'start', and 'end' keys
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(str(video_path), word_timestamps=True)

    words = []
    for segment in result["segments"]:
        if "words" in segment:
            for word in segment["words"]:
                words.append({
                    "word": word["word"],
                    "start": word["start"],
                    "end": word["end"],
                })

    return words


def save_timestamps(words: list[dict], output_path: Path) -> None:
    """Save word timestamps to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(words, f, indent=2)


def load_timestamps(input_path: Path) -> list[dict]:
    """Load word timestamps from a JSON file."""
    with open(input_path) as f:
        return json.load(f)
