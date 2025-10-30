"""Video downloading using yt-dlp."""

import subprocess
from pathlib import Path


def download_video(url: str, output_dir: Path) -> Path:
    """
    Download a video using yt-dlp, using the video title as filename.

    Args:
        url: The video URL to download
        output_dir: Directory where video should be saved

    Returns:
        Path to the downloaded video file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Let yt-dlp generate filename from video title
    output_template = str(output_dir / "%(title)s [%(id)s].%(ext)s")

    cmd = [
        "yt-dlp",
        "-f",
        "best",
        "-o",
        output_template,
        "--print",
        "after_move:filepath",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # yt-dlp prints the final filepath when using --print after_move:filepath
        downloaded_path = Path(result.stdout.strip().splitlines()[-1])
        return downloaded_path
    except subprocess.CalledProcessError as e:
        error_msg = f"yt-dlp failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise RuntimeError(error_msg) from e
