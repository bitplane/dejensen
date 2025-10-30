"""Command-line interface for dejensen."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from dejensen.downloader import download_video
from dejensen.transcriber import extract_timestamps, save_timestamps, load_timestamps
from dejensen.gap_detector import find_gaps
from dejensen.video_editor import speed_ramp_gaps, get_video_duration


def main():
    """Main entry point for the dejensen CLI."""
    parser = argparse.ArgumentParser(
        description="Remove annoying pauses from presentation videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a YouTube video
  dejensen https://www.youtube.com/watch?v=VIDEO_ID

  # Process a local video file
  dejensen /path/to/video.mp4

  # Use custom settings
  dejensen video.mp4 -g 0.5 -t 0.1 -s 7 -m small
        """,
    )

    parser.add_argument("url_or_path", help="YouTube URL or local video file path")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=Path("./output"), help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "-g", "--max-gap", type=float, default=0.2, help="Minimum gap duration to speed up in seconds (default: 0.2)"
    )
    parser.add_argument(
        "-t", "--target-gap", type=float, default=0.2, help="Target duration for sped-up gaps in seconds (default: 0.2)"
    )
    parser.add_argument(
        "-s", "--speed-steps", type=int, default=5, help="Number of speed transition steps per gap (default: 5)"
    )
    parser.add_argument(
        "-m",
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to use (default: base)",
    )
    parser.add_argument("--no-cleanup", action="store_true", help="Keep intermediate files (.tmp directory)")
    parser.add_argument("--use-timestamps", type=Path, help="Use existing timestamps JSON file instead of transcribing")

    args = parser.parse_args()

    try:
        # Step 1: Get or download the video
        is_url = args.url_or_path.startswith("https://") or args.url_or_path.startswith("http://")

        if is_url:
            # Generate output filename from URL (will be determined by yt-dlp)
            # For now, use a temp name and rename after
            print(f"Downloading video from: {args.url_or_path}")
            temp_video = args.output_dir / "temp_download.mp4"
            video_path = download_video(args.url_or_path, temp_video)

            # Rename to something reasonable (yt-dlp might have changed the extension)
            if video_path.stem == "temp_download":
                # Try to get title from the video filename
                final_name = video_path.stem
            video_path_final = args.output_dir / video_path.name
            if video_path != video_path_final:
                video_path.rename(video_path_final)
                video_path = video_path_final
            print(f"Downloaded to: {video_path}")
        else:
            # Local file - copy to output directory
            source_path = Path(args.url_or_path)
            if not source_path.exists():
                print(f"Error: Video file not found: {source_path}", file=sys.stderr)
                sys.exit(1)

            video_path = args.output_dir / source_path.name
            if video_path.exists():
                print(f"Using existing video: {video_path}")
            else:
                print("Copying video to output directory...")
                args.output_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, video_path)
                print(f"Copied to: {video_path}")

        # Set up .tmp working directory
        work_dir = Path(str(video_path) + ".tmp")
        work_dir.mkdir(parents=True, exist_ok=True)
        timestamp_file = work_dir / "timestamps.json"

        # Step 2: Extract or load timestamps
        if args.use_timestamps:
            print(f"Loading timestamps from: {args.use_timestamps}")
            words = load_timestamps(args.use_timestamps)
        elif timestamp_file.exists():
            print(f"Found existing timestamps: {timestamp_file}")
            words = load_timestamps(timestamp_file)
            print(f"Loaded {len(words)} words")
        else:
            print(f"Transcribing video with Whisper model '{args.model}'...")
            words = extract_timestamps(video_path, args.model)
            print(f"Extracted {len(words)} words")

            # Always save timestamps
            save_timestamps(words, timestamp_file)
            print(f"Saved timestamps to: {timestamp_file}")

        # Step 3: Find gaps to speed up
        print(f"Analyzing gaps (min gap: {args.max_gap}s)...")
        video_duration = get_video_duration(video_path)
        gaps = find_gaps(words, args.max_gap)
        print(f"Found {len(gaps)} gaps to speed up")

        if not gaps:
            print("No gaps found - video already flows well!")
            sys.exit(0)

        total_gap_time = sum(end - start for start, end in gaps)
        total_compressed = len(gaps) * args.target_gap
        time_saved = total_gap_time - total_compressed
        new_duration = video_duration - time_saved

        print(f"Total gap time: {total_gap_time:.2f}s")
        print(f"Compressed to: {total_compressed:.2f}s")
        print(f"Time saved: {time_saved:.2f}s")
        print(f"Output will be {new_duration:.2f}s ({new_duration/video_duration*100:.1f}% of original)")

        # Step 4: Speed ramp the gaps
        output_path = args.output_dir / f"{video_path.stem}_dejensen{video_path.suffix}"

        # Save gaps info for debugging
        gaps_file = work_dir / "gaps.json"
        with open(gaps_file, "w") as f:
            json.dump([{"start": s, "end": e, "duration": e - s} for s, e in gaps], f, indent=2)

        print(f"Processing video with {args.speed_steps} speed steps per gap...")

        speed_ramp_gaps(
            video_path,
            gaps,
            output_path,
            video_duration,
            target_gap_duration=args.target_gap,
            speed_steps=args.speed_steps,
            work_dir=work_dir,
        )

        # Cleanup: remove .tmp directory unless --no-cleanup
        if not args.no_cleanup:
            print("Cleaning up temporary files...")
            shutil.rmtree(work_dir)
        else:
            print(f"Temporary files kept in: {work_dir}")

        print(f"\nSuccess! Output saved to: {output_path}")

    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
