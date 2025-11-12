"""
Frame extraction processor for video files.
"""
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

from utils.video_utils import (
    get_video_info,
    extract_frames_at_timestamps,
    extract_frames_at_interval,
    extract_key_frames,
    timestamp_to_seconds,
    seconds_to_timestamp
)


class FrameExtractor:
    """Handles frame extraction from video files."""

    def __init__(self, quality: int = 2):
        """
        Initialize frame extractor.

        Args:
            quality: Frame extraction quality (1-31, lower is better)
        """
        self.quality = quality

    def extract_frames(
        self,
        video_path: Path,
        output_dir: Path,
        timestamps: Optional[List[float]] = None,
        interval: Optional[float] = None,
        extract_keyframes: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extract frames from video using specified method.

        Args:
            video_path: Path to video file
            output_dir: Output directory for frames
            timestamps: Specific timestamps to extract (in seconds)
            interval: Interval for regular frame extraction (in seconds)
            extract_keyframes: Extract key frames (scene changes)

        Returns:
            List of frame information dictionaries
        """
        logger.info(f"Extracting frames from {video_path.name}")

        # Get video info
        try:
            video_info = get_video_info(video_path)
            logger.info(f"Video duration: {video_info['duration']:.2f}s, FPS: {video_info['fps']:.2f}")
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return []

        # Determine extraction method
        extracted_frames = []

        if timestamps is not None:
            # Extract at specific timestamps
            logger.info(f"Extracting {len(timestamps)} frames at specific timestamps")
            extracted_frames = extract_frames_at_timestamps(
                video_path,
                timestamps,
                output_dir,
                self.quality,
                prefix=f"{video_path.stem}_frame"
            )

        elif interval is not None:
            # Extract at regular intervals
            logger.info(f"Extracting frames every {interval} seconds")
            extracted_frames = extract_frames_at_interval(
                video_path,
                interval,
                output_dir,
                self.quality,
                prefix=f"{video_path.stem}_frame"
            )

        elif extract_keyframes:
            # Extract key frames
            logger.info("Extracting key frames")
            extracted_frames = extract_key_frames(
                video_path,
                output_dir,
                self.quality,
                prefix=f"{video_path.stem}_keyframe"
            )

        else:
            logger.warning("No extraction method specified")
            return []

        # Format frame information
        frame_data = []
        for idx, (timestamp, frame_path) in enumerate(extracted_frames):
            frame_info = {
                'frame_id': idx,
                'frame_name': frame_path.name,
                'frame_path': str(frame_path),
                'timestamp': timestamp,
                'timestamp_str': seconds_to_timestamp(timestamp),
                'video_source': video_path.name,
                'video_path': str(video_path)
            }
            frame_data.append(frame_info)

        logger.info(f"Successfully extracted {len(frame_data)} frames")
        return frame_data

    def process_single_video(
        self,
        video_path: Path,
        output_dir: Path,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process single video file with given configuration.

        Args:
            video_path: Path to video file
            output_dir: Output directory
            config: Processing configuration

        Returns:
            List of frame information dictionaries
        """
        # Parse timestamps if provided
        timestamps = None
        if config.get('timestamps'):
            if isinstance(config['timestamps'], list):
                timestamps = []
                for ts in config['timestamps']:
                    if isinstance(ts, str):
                        timestamps.append(timestamp_to_seconds(ts))
                    else:
                        timestamps.append(float(ts))

        # Get interval
        interval = config.get('frame_interval')

        # Get keyframe option
        extract_keyframes = config.get('extract_keyframes', False)

        return self.extract_frames(
            video_path,
            output_dir,
            timestamps=timestamps,
            interval=interval,
            extract_keyframes=extract_keyframes
        )

    def process_video_folder(
        self,
        folder_path: Path,
        output_dir: Path,
        config: Dict[str, Any],
        allowed_formats: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process all videos in a folder.

        Args:
            folder_path: Path to folder containing videos
            output_dir: Output directory
            config: Processing configuration
            allowed_formats: List of allowed video formats

        Returns:
            Dictionary mapping video names to frame information lists
        """
        from utils.video_utils import get_videos_in_folder

        video_files = get_videos_in_folder(folder_path, allowed_formats)
        logger.info(f"Found {len(video_files)} video files in {folder_path}")

        results = {}

        for video_file in video_files:
            video_output_dir = output_dir / video_file.stem / "frames"
            video_output_dir.mkdir(parents=True, exist_ok=True)

            try:
                frame_data = self.process_single_video(
                    video_file,
                    video_output_dir,
                    config
                )
                results[video_file.name] = frame_data
                logger.info(f"Processed {video_file.name}: {len(frame_data)} frames")

            except Exception as e:
                logger.error(f"Failed to process {video_file.name}: {e}")
                results[video_file.name] = []

        return results
