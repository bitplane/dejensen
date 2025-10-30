"""Video editing using ffmpeg."""

import subprocess
from pathlib import Path


def get_video_duration(video_path: Path) -> float:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def cut_segments(video_path: Path, segments: list[tuple[float, float]], output_path: Path, work_dir: Path | None = None) -> None:
    """
    Cut video segments using ffmpeg select filter in a single pass.

    Args:
        video_path: Path to the input video
        segments: List of (start, end) tuples in seconds
        output_path: Path for the output video
        work_dir: Unused, kept for compatibility
    """
    if not segments:
        raise ValueError("No segments to process")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build select filter expression
    video_conditions = []
    audio_conditions = []

    for start, end in segments:
        video_conditions.append(f"between(t,{start},{end})")
        audio_conditions.append(f"between(t,{start},{end})")

    # Join with + (logical OR)
    video_select = "+".join(video_conditions)
    audio_select = "+".join(audio_conditions)

    # Filter: select frames in ranges, reset timestamps to be continuous
    filter_complex = (
        f"[0:v]select='{video_select}',setpts=N/FRAME_RATE/TB[outv];"
        f"[0:a]aselect='{audio_select}',asetpts=N/SR/TB[outa]"
    )

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-c:a", "aac",
        "-y",
        str(output_path),
    ]

    print(f"Processing video with select filter ({len(segments)} segments)...")
    try:
        subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        error_msg = f"ffmpeg failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise RuntimeError(error_msg) from e
