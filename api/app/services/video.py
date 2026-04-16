"""
Video utility service — wraps FFmpeg/FFprobe operations.
These are placeholders that will be filled with real FFmpeg calls
when the recorder service is built.
"""

from app.core.logging import get_logger

logger = get_logger("video")


async def probe_stream(rtsp_url: str) -> dict | None:
    """Probe an RTSP stream and return codec/resolution info."""
    # Placeholder for: ffprobe -v quiet -print_format json -show_streams <url>
    logger.info("Probing stream: %s", rtsp_url)
    return {
        "codec": "h264",
        "width": 1920,
        "height": 1080,
        "fps": 15,
    }


async def generate_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """Extract a single frame as a JPEG thumbnail."""
    # Placeholder for: ffmpeg -ss <ts> -i <input> -vframes 1 -q:v 2 <output>
    logger.info("Generating thumbnail: %s → %s", video_path, output_path)
    return True


async def generate_clip(
    source_path: str,
    output_path: str,
    start_seconds: float,
    duration_seconds: float,
) -> bool:
    """Extract a clip from a recording segment."""
    # Placeholder for: ffmpeg -ss <start> -i <input> -t <dur> -c copy <output>
    logger.info(
        "Generating clip: %s → %s (start=%.1f, dur=%.1f)",
        source_path,
        output_path,
        start_seconds,
        duration_seconds,
    )
    return True