"""Video editing using ffmpeg."""

import subprocess
from pathlib import Path
import tempfile


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
    Cut video into segments and concatenate them, removing gaps.

    Args:
        video_path: Path to the input video
        segments: List of (start, end) tuples in seconds
        output_path: Path for the output video
        work_dir: Directory to store segments (if None, uses temp directory that gets cleaned up)
    """
    if not segments:
        raise ValueError("No segments to process")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use work_dir if provided, otherwise use temp directory
    if work_dir:
        work_dir.mkdir(parents=True, exist_ok=True)
        segments_dir = work_dir
        cleanup = False
    else:
        temp_context = tempfile.TemporaryDirectory()
        segments_dir = Path(temp_context.name)
        cleanup = True

    try:
        segment_files = []

        # Extract each segment
        for i, (start, end) in enumerate(segments):
            segment_file = segments_dir / f"segment_{i:04d}.mp4"
            duration = end - start

            # Check if segment already exists
            if segment_file.exists():
                print(f"  Using existing segment {i}: {start:.2f} - {end:.2f} (duration: {duration:.2f}s)")
                segment_files.append(segment_file)
                continue

            # Use input seeking for speed, but re-encode for accuracy
            cmd = [
                "ffmpeg",
                "-accurate_seek",
                "-ss", str(start),
                "-i", str(video_path),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "copy",
                str(segment_file),
            ]

            print(f"  Extracting segment {i}: {start:.2f} - {end:.2f} (duration: {duration:.2f}s)")
            subprocess.run(cmd, capture_output=True, check=True)
            segment_files.append(segment_file)

        # Create concat file with absolute paths
        concat_file = segments_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for segment_file in segment_files:
                # Use absolute path to avoid path resolution issues
                abs_path = segment_file.resolve()
                f.write(f"file '{abs_path}'\n")

        # Concatenate segments (must re-encode to fix timestamps)
        print("Concatenating all segments...")
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264",
            "-preset", "medium",
            "-c:a", "aac",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"ffmpeg concatenation failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\n{e.stderr}"
            raise RuntimeError(error_msg) from e
    finally:
        if cleanup:
            temp_context.cleanup()
