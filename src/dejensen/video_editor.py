"""Video editing using ffmpeg."""

import subprocess
from pathlib import Path

from dejensen.speed_calculator import calculate_speed_transitions


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
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def speed_ramp_gaps(
    video_path: Path,
    gaps: list[tuple[float, float]],
    output_path: Path,
    video_duration: float,
    target_gap_duration: float = 0.2,
    speed_steps: int = 5,
    work_dir: Path | None = None,
) -> None:
    """
    Speed up gaps with smooth transitions using ffmpeg filter_complex.
    Process each (normal segment + gap) pair separately, then concat files.

    Args:
        video_path: Path to the input video
        gaps: List of (start, end) tuples representing gaps to speed up
        output_path: Path for the output video
        video_duration: Total video duration in seconds
        target_gap_duration: Target duration for each gap in seconds
        speed_steps: Number of speed segments per gap (more = smoother)
        work_dir: Optional directory to save filter scripts for debugging
    """
    if not gaps:
        raise ValueError("No gaps to process")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use work_dir/chunks for intermediate files
    chunks_dir = work_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Process each normal+gap pair into separate files
        part_files = []
        current_pos = 0.0

        for gap_idx, (gap_start, gap_end) in enumerate(gaps):
            # Process normal segment + gap as one chunk
            chunk_segments = []

            # Add normal-speed segment before this gap
            if current_pos < gap_start:
                chunk_segments.append(("normal", current_pos, gap_start, 1.0))

            # Add speed-ramped gap segments
            gap_transitions = calculate_speed_transitions(gap_start, gap_end, target_gap_duration, steps=speed_steps)
            for seg_start, seg_end, speed in gap_transitions:
                chunk_segments.append(("gap", seg_start, seg_end, speed))

            current_pos = gap_end

            # Generate filter for this chunk
            filter_lines = []
            stream_labels = []

            # Get start time of this chunk for fast seeking
            chunk_start = chunk_segments[0][1]  # start time of first segment
            chunk_end = chunk_segments[-1][2]  # end time of last segment

            for i, (seg_type, start, end, speed) in enumerate(chunk_segments):
                # Adjust times relative to chunk_start
                rel_start = start - chunk_start
                rel_end = end - chunk_start
                filter_lines.append(
                    f"[0:v]trim=start={rel_start:.6f}:end={rel_end:.6f},setpts=PTS-STARTPTS,setpts=PTS/{speed:.6f}[v{i}]"
                )
                # Audio: use asetrate to change playback speed (pitch shifts but fast!)
                filter_lines.append(
                    f"[0:a]atrim=start={rel_start:.6f}:end={rel_end:.6f},asetrate=44100*{speed:.6f},aresample=44100,asetpts=PTS-STARTPTS[a{i}]"
                )
                stream_labels.append(f"[v{i}][a{i}]")

            # Concat this chunk
            n_segs = len(chunk_segments)
            concat_line = f"{''.join(stream_labels)}concat=n={n_segs}:v=1:a=1[outv][outa]"
            filter_lines.append(concat_line)

            filter_script = ";\n".join(filter_lines)
            filter_file = chunks_dir / f"filter_{gap_idx}.txt"
            filter_file.write_text(filter_script)

            # Encode this chunk - use -ss BEFORE -i for fast seeking
            part_file = chunks_dir / f"part_{gap_idx:04d}.mp4"
            part_file_tmp = chunks_dir / f"part_{gap_idx:04d}.tmp.mp4"

            # Skip if chunk already exists (crash recovery)
            if part_file.exists():
                print(f"Chunk {gap_idx + 1}/{len(gaps)} already exists, skipping...")
                part_files.append(part_file)
                continue

            cmd = [
                "ffmpeg",
                "-ss",
                str(chunk_start),  # Fast seek to chunk start
                "-t",
                str(chunk_end - chunk_start),  # Duration of chunk
                "-i",
                str(video_path),
                "-filter_complex_script",
                str(filter_file),
                "-map",
                "[outv]",
                "-map",
                "[outa]",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",  # Fast for intermediate files
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-y",
                str(part_file_tmp),
            ]

            print(f"Processing chunk {gap_idx + 1}/{len(gaps)}...")
            subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True)
            # Move into place atomically
            part_file_tmp.rename(part_file)
            part_files.append(part_file)

        # Add final normal segment after last gap
        if current_pos < video_duration:
            part_file = chunks_dir / f"part_{len(gaps):04d}.mp4"
            part_file_tmp = chunks_dir / f"part_{len(gaps):04d}.tmp.mp4"

            # Skip if final segment already exists (crash recovery)
            if not part_file.exists():
                cmd = [
                    "ffmpeg",
                    "-ss",
                    str(current_pos),  # Fast seek
                    "-i",
                    str(video_path),
                    "-to",
                    str(video_duration - current_pos),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-y",
                    str(part_file_tmp),
                ]
                print("Processing final segment...")
                subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True)
                # Move into place atomically
                part_file_tmp.rename(part_file)
            else:
                print("Final segment already exists, skipping...")

            part_files.append(part_file)

        # Concat all parts using concat demuxer (fast!)
        concat_list_file = chunks_dir / "concat_list.txt"
        with open(concat_list_file, "w") as f:
            for part in part_files:
                f.write(f"file '{part.absolute()}'\n")

        print(f"Concatenating {len(part_files)} parts...")
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list_file),
            "-c",
            "copy",  # Just copy, no re-encode!
            "-y",
            str(output_path),
        ]

        subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True)
        print(f"Success! Output saved to: {output_path}")

    except subprocess.CalledProcessError as e:
        error_msg = f"ffmpeg failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        raise RuntimeError(error_msg) from e
