"""
Video processing utilities for frame extraction and video information.
"""
import cv2
import ffmpeg
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import timedelta


def get_video_info(video_path: Path) -> Dict[str, Any]:
    """
    Get video metadata information.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video information (duration, fps, resolution, etc.)
    """
    try:
        probe = ffmpeg.probe(str(video_path))
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

        duration = float(probe['format']['duration'])
        fps = eval(video_info['r_frame_rate'])
        width = int(video_info['width'])
        height = int(video_info['height'])
        total_frames = int(video_info.get('nb_frames', duration * fps))

        return {
            'duration': duration,
            'fps': fps,
            'width': width,
            'height': height,
            'total_frames': total_frames,
            'format': probe['format']['format_name'],
            'size_bytes': int(probe['format']['size'])
        }
    except Exception as e:
        raise ValueError(f"Failed to get video info: {str(e)}")


def timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert timestamp string to seconds.

    Args:
        timestamp: Timestamp in format HH:MM:SS or MM:SS or seconds

    Returns:
        Time in seconds
    """
    try:
        # Try parsing as float (seconds)
        return float(timestamp)
    except ValueError:
        # Parse as time format
        parts = timestamp.split(':')
        if len(parts) == 3:  # HH:MM:SS
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:  # MM:SS
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds to timestamp string.

    Args:
        seconds: Time in seconds

    Returns:
        Timestamp in format HH:MM:SS.mmm
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = td.total_seconds() % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def extract_frame_at_timestamp(
    video_path: Path,
    timestamp: float,
    output_path: Optional[Path] = None,
    quality: int = 2
) -> Optional[Path]:
    """
    Extract a single frame from video at specified timestamp using ffmpeg.

    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds
        output_path: Output path for extracted frame
        quality: Quality parameter (1-31, lower is better)

    Returns:
        Path to extracted frame or None if failed
    """
    try:
        if output_path is None:
            output_path = video_path.parent / f"frame_{timestamp:.3f}.jpg"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        (
            ffmpeg
            .input(str(video_path), ss=timestamp)
            .output(str(output_path), vframes=1, q=quality)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        return output_path if output_path.exists() else None

    except ffmpeg.Error as e:
        print(f"ffmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return None


def extract_frames_at_timestamps(
    video_path: Path,
    timestamps: List[float],
    output_dir: Path,
    quality: int = 2,
    prefix: str = "frame"
) -> List[Tuple[float, Path]]:
    """
    Extract multiple frames from video at specified timestamps.

    Args:
        video_path: Path to video file
        timestamps: List of timestamps in seconds
        output_dir: Output directory for frames
        quality: Quality parameter (1-31, lower is better)
        prefix: Prefix for output filenames

    Returns:
        List of tuples (timestamp, frame_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_frames = []

    for idx, timestamp in enumerate(timestamps):
        timestamp_str = seconds_to_timestamp(timestamp)
        safe_timestamp = timestamp_str.replace(':', '-')
        output_path = output_dir / f"{prefix}_{idx}_{safe_timestamp}.jpg"

        frame_path = extract_frame_at_timestamp(
            video_path,
            timestamp,
            output_path,
            quality
        )

        if frame_path:
            extracted_frames.append((timestamp, frame_path))

    return extracted_frames


def extract_frames_at_interval(
    video_path: Path,
    interval_seconds: float,
    output_dir: Path,
    quality: int = 2,
    start_time: float = 0,
    end_time: Optional[float] = None,
    prefix: str = "frame"
) -> List[Tuple[float, Path]]:
    """
    Extract frames at regular intervals from video.

    Args:
        video_path: Path to video file
        interval_seconds: Interval between frames in seconds
        output_dir: Output directory for frames
        quality: Quality parameter (1-31, lower is better)
        start_time: Start time in seconds
        end_time: End time in seconds (None for end of video)
        prefix: Prefix for output filenames

    Returns:
        List of tuples (timestamp, frame_path)
    """
    video_info = get_video_info(video_path)
    duration = end_time if end_time else video_info['duration']

    # Generate timestamps
    timestamps = []
    current_time = start_time
    while current_time <= duration:
        timestamps.append(current_time)
        current_time += interval_seconds

    return extract_frames_at_timestamps(
        video_path,
        timestamps,
        output_dir,
        quality,
        prefix
    )


def extract_key_frames(
    video_path: Path,
    output_dir: Path,
    quality: int = 2,
    prefix: str = "keyframe"
) -> List[Tuple[float, Path]]:
    """
    Extract key frames (scene changes) from video.

    Args:
        video_path: Path to video file
        output_dir: Output directory for frames
        quality: Quality parameter (1-31, lower is better)
        prefix: Prefix for output filenames

    Returns:
        List of tuples (timestamp, frame_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Use ffmpeg scene detection
        output_pattern = str(output_dir / f"{prefix}_%04d.jpg")

        (
            ffmpeg
            .input(str(video_path))
            .filter('select', 'gt(scene,0.3)')
            .output(output_pattern, vsync='vfr', q=quality)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        # Get extracted frames
        extracted_frames = []
        for frame_file in sorted(output_dir.glob(f"{prefix}_*.jpg")):
            # Estimate timestamp based on file order
            # Note: This is approximate. For precise timestamps, use a different approach
            extracted_frames.append((0.0, frame_file))

        return extracted_frames

    except ffmpeg.Error as e:
        print(f"ffmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return []


def load_frame(frame_path: Path) -> Optional[cv2.Mat]:
    """
    Load frame from file.

    Args:
        frame_path: Path to frame image

    Returns:
        Frame as numpy array or None if failed
    """
    if not frame_path.exists():
        return None

    frame = cv2.imread(str(frame_path))
    return frame


def save_frame(frame: cv2.Mat, output_path: Path, quality: int = 95) -> bool:
    """
    Save frame to file.

    Args:
        frame: Frame as numpy array
        output_path: Output path
        quality: JPEG quality (0-100)

    Returns:
        True if successful
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])


def validate_video_file(file_path: Path, allowed_formats: List[str]) -> bool:
    """
    Validate video file format and existence.

    Args:
        file_path: Path to video file
        allowed_formats: List of allowed file extensions

    Returns:
        True if valid video file
    """
    if not file_path.exists():
        return False

    if not file_path.is_file():
        return False

    extension = file_path.suffix.lower().lstrip('.')
    if extension not in allowed_formats:
        return False

    return True


def get_videos_in_folder(folder_path: Path, allowed_formats: List[str]) -> List[Path]:
    """
    Get all valid video files in a folder.

    Args:
        folder_path: Path to folder
        allowed_formats: List of allowed file extensions

    Returns:
        List of video file paths
    """
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    video_files = []
    for ext in allowed_formats:
        video_files.extend(folder_path.glob(f"*.{ext}"))
        video_files.extend(folder_path.glob(f"*.{ext.upper()}"))

    return sorted(video_files)
