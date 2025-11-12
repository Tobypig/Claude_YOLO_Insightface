"""
Main video processor that orchestrates frame extraction, person detection, and face detection.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from processors.frame_extractor import FrameExtractor
from processors.person_detector import PersonDetector
from processors.face_detector import FaceDetector
from processors.face_comparator import FaceComparator
from utils.bbox_utils import draw_combined_boxes
from utils.video_utils import load_frame, save_frame
import cv2


class VideoProcessor:
    """Main processor for video analysis pipeline."""

    def __init__(
        self,
        yolo_model: str,
        insightface_model: str,
        person_threshold: float,
        face_threshold: float,
        device: str,
        frame_quality: int = 2
    ):
        """
        Initialize video processor with all sub-processors.

        Args:
            yolo_model: Path to YOLO model
            insightface_model: InsightFace model name
            person_threshold: Person detection confidence threshold
            face_threshold: Face detection confidence threshold
            device: Device to run models on ('cuda' or 'cpu')
            frame_quality: Frame extraction quality (1-31)
        """
        logger.info("Initializing VideoProcessor")

        self.frame_extractor = FrameExtractor(quality=frame_quality)
        self.person_detector = PersonDetector(
            model_path=yolo_model,
            confidence_threshold=person_threshold,
            device=device
        )
        self.face_detector = FaceDetector(
            model_name=insightface_model,
            confidence_threshold=face_threshold,
            device=device
        )
        self.face_comparator = FaceComparator(face_detector=self.face_detector)

        logger.info("VideoProcessor initialized successfully")

    def process_job(
        self,
        job_id: str,
        input_type: str,
        input_path: Path,
        output_dir: Path,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a complete job (single video or folder).

        Args:
            job_id: Unique job identifier
            input_type: 'video' or 'folder'
            input_path: Path to video file or folder
            output_dir: Output directory for results
            config: Processing configuration

        Returns:
            Job results dictionary
        """
        logger.info(f"Starting job {job_id}: {input_type} - {input_path}")

        start_time = datetime.now()

        # Create job output directory
        job_output_dir = output_dir / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)

        # Extract frames
        logger.info("Step 1: Extracting frames")
        frames_dir = job_output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        if input_type == "video":
            frame_data = self.frame_extractor.process_single_video(
                input_path,
                frames_dir,
                config
            )
        elif input_type == "folder":
            frame_results = self.frame_extractor.process_video_folder(
                input_path,
                job_output_dir,
                config,
                config.get('allowed_formats', ['mp4', 'mov', 'avi', 'mkv'])
            )
            # Flatten frame data from all videos
            frame_data = []
            for video_name, frames in frame_results.items():
                frame_data.extend(frames)
        else:
            raise ValueError(f"Invalid input_type: {input_type}")

        logger.info(f"Extracted {len(frame_data)} frames")

        # Initialize results
        person_results = []
        face_results = []

        # Detect persons
        if config.get('detect_persons', False):
            logger.info("Step 2: Detecting persons")
            person_results = self.person_detector.process_frames(
                frame_data,
                job_output_dir,
                save_annotated=True,
                save_crops=True
            )
            # Save person metadata
            person_meta_path = job_output_dir / "persons" / "person_meta.csv"
            self.person_detector.save_metadata(person_results, person_meta_path)

        # Detect faces
        if config.get('detect_faces', False):
            logger.info("Step 3: Detecting faces")
            face_results = self.face_detector.process_frames(
                frame_data,
                job_output_dir,
                save_annotated=True,
                save_crops=True,
                save_embeddings=True
            )
            # Save face metadata
            face_meta_path = job_output_dir / "faces" / "face_meta.csv"
            self.face_detector.save_metadata(face_results, face_meta_path)

        # Create combined visualizations
        if config.get('detect_persons', False) and config.get('detect_faces', False):
            logger.info("Step 4: Creating combined visualizations")
            self._create_combined_visualizations(
                frame_data,
                person_results,
                face_results,
                job_output_dir
            )

        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Create summary
        summary = {
            'job_id': job_id,
            'input_type': input_type,
            'input_path': str(input_path),
            'status': 'completed',
            'processing_time': f"{processing_time:.2f}s",
            'total_frames': len(frame_data),
            'persons_detected': sum(len(r['boxes']) for r in person_results),
            'faces_detected': sum(len(r['boxes']) for r in face_results),
            'output_dir': str(job_output_dir)
        }

        # Save metadata
        metadata_path = job_output_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({
                'summary': summary,
                'frames': frame_data,
                'person_results': [self._serialize_result(r) for r in person_results],
                'face_results': [self._serialize_result(r) for r in face_results]
            }, f, indent=2, default=str)

        logger.info(f"Job {job_id} completed in {processing_time:.2f}s")

        return summary

    def _create_combined_visualizations(
        self,
        frame_data: List[Dict[str, Any]],
        person_results: List[Dict[str, Any]],
        face_results: List[Dict[str, Any]],
        output_dir: Path
    ) -> None:
        """
        Create visualizations with both person and face boxes.

        Args:
            frame_data: Frame information
            person_results: Person detection results
            face_results: Face detection results
            output_dir: Output directory
        """
        combined_dir = output_dir / "combined"
        combined_dir.mkdir(exist_ok=True)

        # Match results by frame_id
        person_by_frame = {r['frame_id']: r for r in person_results}
        face_by_frame = {r['frame_id']: r for r in face_results}

        for frame_info in frame_data:
            frame_id = frame_info['frame_id']
            frame_path = Path(frame_info['frame_path'])

            # Load frame
            image = load_frame(frame_path)
            if image is None:
                continue

            # Get detections
            person_data = person_by_frame.get(frame_id, {'boxes': [], 'confidences': []})
            face_data = face_by_frame.get(frame_id, {
                'boxes': [],
                'confidences': [],
                'landmarks': []
            })

            # Draw combined boxes
            combined_image = draw_combined_boxes(
                image,
                {
                    'boxes': person_data['boxes'],
                    'confidences': person_data['confidences']
                },
                {
                    'boxes': face_data['boxes'],
                    'confidences': face_data['confidences'],
                    'landmarks': face_data.get('landmarks', [])
                }
            )

            # Save combined image
            output_path = combined_dir / f"{frame_path.stem}_all_boxes.jpg"
            save_frame(combined_image, output_path)

        logger.info(f"Created {len(frame_data)} combined visualizations")

    def _serialize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize result for JSON output (remove numpy arrays).

        Args:
            result: Result dictionary

        Returns:
            Serialized result
        """
        serialized = result.copy()

        # Remove embeddings (too large for JSON)
        if 'embeddings' in serialized:
            del serialized['embeddings']

        # Remove embedding arrays from crops
        if 'crops' in serialized:
            for crop in serialized['crops']:
                if 'embedding' in crop:
                    del crop['embedding']

        return serialized

    def compare_faces(
        self,
        job_id: str,
        reference_image: Any,
        threshold: float,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Compare reference face against detected faces in a job.

        Args:
            job_id: Job ID to compare against
            reference_image: Reference image (path or bytes)
            threshold: Similarity threshold
            output_dir: Output directory for comparison results

        Returns:
            Comparison results
        """
        logger.info(f"Starting face comparison for job {job_id}")

        # Load job metadata to get face results
        job_dir = output_dir / job_id
        metadata_path = job_dir / "metadata.json"

        if not metadata_path.exists():
            raise ValueError(f"Job {job_id} not found")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        face_results = metadata.get('face_results', [])

        # Load face embeddings
        face_results_with_embeddings = self._load_face_embeddings(face_results, job_dir)

        # Extract reference embedding
        if isinstance(reference_image, (str, Path)):
            ref_embedding = self.face_comparator.extract_reference_embedding(Path(reference_image))
        else:
            ref_embedding = self.face_comparator.extract_reference_embedding_from_bytes(
                reference_image
            )

        if ref_embedding is None:
            raise ValueError("Failed to extract reference face embedding")

        # Compare
        matches = self.face_comparator.compare_with_database(
            ref_embedding,
            face_results_with_embeddings,
            threshold=threshold
        )

        # Save results
        comparison_dir = job_dir / "comparisons"
        comparison_dir.mkdir(exist_ok=True)

        results_path = comparison_dir / "comparison_results.json"
        self.face_comparator.save_comparison_results(
            matches,
            results_path,
            threshold=threshold
        )

        # Save matched faces
        matched_dir = comparison_dir / "matched_faces"
        self.face_comparator.save_matched_faces(matches, matched_dir)

        # Generate report
        report = self.face_comparator.generate_comparison_report(
            matches,
            comparison_dir
        )

        logger.info(f"Face comparison completed: {len(matches)} matches found")

        return report

    def _load_face_embeddings(
        self,
        face_results: List[Dict[str, Any]],
        job_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Load face embeddings from saved .npy files.

        Args:
            face_results: Face detection results
            job_dir: Job directory

        Returns:
            Face results with loaded embeddings
        """
        import numpy as np

        results_with_embeddings = []

        for result in face_results:
            result_copy = result.copy()
            crops_with_embeddings = []

            for crop_info in result.get('crops', []):
                crop_copy = crop_info.copy()
                embedding_path = crop_info.get('embedding_path')

                if embedding_path:
                    full_path = job_dir / Path(embedding_path).relative_to(
                        Path(embedding_path).parts[0]
                    ) if not Path(embedding_path).is_absolute() else Path(embedding_path)

                    if full_path.exists():
                        embedding = np.load(str(full_path))
                        crop_copy['embedding'] = embedding

                crops_with_embeddings.append(crop_copy)

            result_copy['crops'] = crops_with_embeddings
            results_with_embeddings.append(result_copy)

        return results_with_embeddings
