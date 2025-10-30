"""Video downloading using yt-dlp."""

import subprocess
from pathlib import Path


def download_video(url: str, output_dir: Path) -> Path:
    """
    Download a video using yt-dlp.

    Args:
        url: The video URL to download
        output_dir: Directory to save the video

    Returns:
        Path to the downloaded video file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", "best",
        "-o", output_template,
        "--print", "after_move:filepath",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        filepath = result.stdout.strip().split("\n")[-1]
        return Path(filepath)
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise RuntimeError(error_msg) from e
