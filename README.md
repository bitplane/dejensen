# dejenson

Remove annoying pauses from presentation videos.

## Why?

Nvidia... Nvidia presentations are... full of pauses... and I thought...
this was annoying ... so this fixes that

## How it works

1. Downloads a video using `yt-dlp` (or uses a local file)
2. Extracts word-level timestamps using OpenAI's Whisper
3. Identifies gaps between words that exceed a threshold (default 0.2 seconds)
4. Uses ffmpeg to cut out the gaps and reassemble the video

## Installation

```bash
make dev
```

This will create a virtual environment and install the package in development mode.

## Usage

```bash
# Activate the virtual environment
source .venv/bin/activate

# Process a YouTube video
dejensonify https://www.youtube.com/watch?v=VIDEO_ID

# Use a custom max gap (2 seconds)
dejensonify URL -g 2.0

# Process a local video file
dejensonify /path/to/video.mp4 --no-download

# Use a larger Whisper model for better accuracy
dejensonify URL -m small

# Save timestamps for later reuse
dejensonify URL --keep-timestamps

# Use existing timestamps to skip transcription
dejensonify URL --use-timestamps timestamps.json
```

## Options

- `-o, --output-dir`: Output directory (default: ./output)
- `-g, --max-gap`: Maximum allowed gap in seconds (default: 1.0)
- `-m, --model`: Whisper model to use: tiny, base, small, medium, large (default: base)
- `--no-download`: Treat input as local file path instead of URL
- `--keep-timestamps`: Save word timestamps to JSON file
- `--use-timestamps`: Use existing timestamps JSON file instead of transcribing

## Requirements

- Python 3.10+
- ffmpeg and ffprobe must be installed and in PATH

## Development

```bash
# Run tests
make test

# Run with coverage
make coverage

# Build distribution
make dist
```

## License

WTFPL + Warranty. Do whatever the fuck you want, just don't blame me.
