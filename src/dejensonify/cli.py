"""Command-line interface for dejensonify."""

import argparse
import sys
from pathlib import Path

from dejensonify.downloader import download_video
from dejensonify.transcriber import extract_timestamps, save_timestamps, load_timestamps
from dejensonify.gap_detector import calculate_keep_segments
from dejensonify.video_editor import cut_segments, get_video_duration


def main():
    """Main entry point for the dejensonify CLI."""
    parser = argparse.ArgumentParser(
        description="Remove annoying pauses from presentation videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a YouTube video with default settings
  dejensonify https://www.youtube.com/watch?v=VIDEO_ID

  # Use a custom max gap and output directory
  dejensonify https://www.youtube.com/watch?v=VIDEO_ID -g 2.0 -o ./output

  # Process a local video file
  dejensonify /path/to/video.mp4 --no-download

  # Use a larger Whisper model for better accuracy
  dejensonify URL -m small
        """,
    )

    parser.add_argument("url_or_path", help="YouTube URL or local video file path")
    parser.add_argument("-o", "--output-dir", type=Path, default=Path("./output"), help="Output directory (default: ./output)")
    parser.add_argument("-g", "--max-gap", type=float, default=0.2, help="Maximum allowed gap in seconds (default: 0.2)")
    parser.add_argument("-m", "--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model to use (default: base)")
    parser.add_argument("--no-download", action="store_true", help="Treat input as local file path instead of URL")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep intermediate files (timestamps, segments)")
    parser.add_argument("--use-timestamps", type=Path, help="Use existing timestamps JSON file instead of transcribing")

    args = parser.parse_args()

    try:
        # Step 1: Get the video file
        if args.no_download:
            video_path = Path(args.url_or_path)
            if not video_path.exists():
                print(f"Error: Video file not found: {video_path}", file=sys.stderr)
                sys.exit(1)
            print(f"Using local video: {video_path}")
        else:
            # Check if already downloaded
            download_dir = args.output_dir / "downloads"
            existing_videos = []
            if download_dir.exists():
                existing_videos = (
                    list(download_dir.glob("*.mp4")) +
                    list(download_dir.glob("*.webm")) +
                    list(download_dir.glob("*.mkv"))
                )
                # Filter out dejensonified files
                existing_videos = [v for v in existing_videos if "_dejensonified" not in v.name]

            if existing_videos:
                video_path = existing_videos[0]
                print(f"Found existing video: {video_path}")
            else:
                print(f"Downloading video from: {args.url_or_path}")
                video_path = download_video(args.url_or_path, download_dir)
                print(f"Downloaded to: {video_path}")

        # Set up working directory in the same location as the video
        work_dir = video_path.parent
        timestamp_file = work_dir / f"{video_path.stem}_timestamps.json"

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

        # Step 3: Find segments to keep
        print(f"Analyzing gaps (max gap: {args.max_gap}s)...")
        video_duration = get_video_duration(video_path)
        segments = calculate_keep_segments(words, args.max_gap, video_duration)
        print(f"Found {len(segments)} segments to keep")

        total_kept = sum(end - start for start, end in segments)
        total_removed = video_duration - total_kept
        print(f"Removing {total_removed:.2f}s of pauses from {video_duration:.2f}s video")
        print(f"Output will be {total_kept:.2f}s ({total_kept/video_duration*100:.1f}% of original)")

        # Step 4: Cut and reassemble video
        output_path = args.output_dir / f"{video_path.stem}_dejensonified.mp4"
        segments_dir = work_dir / "segments" if args.no_cleanup else None

        print(f"Processing video (this may take a while)...")
        if args.no_cleanup:
            print(f"Segments will be saved to: {segments_dir}")
            # Save segments info for debugging
            segments_file = work_dir / "segments_plan.json"
            import json
            with open(segments_file, "w") as f:
                json.dump([{"start": s, "end": e, "duration": e-s} for s, e in segments], f, indent=2)
            print(f"Segments plan saved to: {segments_file}")

        cut_segments(video_path, segments, output_path, work_dir=segments_dir)
        print(f"\nSuccess! Output saved to: {output_path}")

    except KeyboardInterrupt:
        print("\nCancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
