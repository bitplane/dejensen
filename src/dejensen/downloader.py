"""Video downloading using yt-dlp."""

import subprocess
from pathlib import Path


def download_video(url: str, output_path: Path) -> Path:
    """
    Download a video using yt-dlp to a specific output path.

    Args:
        url: The video URL to download
        output_path: Full path where video should be saved

    Returns:
        Path to the downloaded video file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-f",
        "best",
        "-o",
        str(output_path),
        url,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise RuntimeError(error_msg) from e
