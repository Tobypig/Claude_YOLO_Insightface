"""
Face comparison processor for similarity matching.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import json

from processors.face_detector import FaceDetector


class FaceComparator:
    """Handles face comparison and similarity matching."""

    def __init__(self, face_detector: FaceDetector, similarity_threshold: float = 0.7):
        """
        Initialize face comparator.

        Args:
            face_detector: FaceDetector instance for processing reference images
            similarity_threshold: Minimum similarity score for matches
        """
        self.face_detector = face_detector
        self.similarity_threshold = similarity_threshold

    def extract_reference_embedding(
        self,
        reference_image_path: Path
    ) -> Optional[np.ndarray]:
        """
        Extract face embedding from reference image.

        Args:
            reference_image_path: Path to reference face image

        Returns:
            Face embedding or None if no face detected
        """
        logger.info(f"Extracting reference face from {reference_image_path.name}")

        # Load image
        image = cv2.imread(str(reference_image_path))
        if image is None:
            logger.error(f"Failed to load reference image: {reference_image_path}")
            return None

        # Detect faces
        boxes, confidences, landmarks, embeddings = self.face_detector.detect_faces(image)

        if len(embeddings) == 0:
            logger.error("No face detected in reference image")
            return None

        if len(embeddings) > 1:
            logger.warning(f"Multiple faces detected in reference image, using the first one")

        # Return the first (or only) face embedding
        return embeddings[0]

    def extract_reference_embedding_from_bytes(
        self,
        image_bytes: bytes
    ) -> Optional[np.ndarray]:
        """
        Extract face embedding from image bytes.

        Args:
            image_bytes: Image data as bytes

        Returns:
            Face embedding or None if no face detected
        """
        logger.info("Extracting reference face from uploaded image")

        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            logger.error("Failed to decode image bytes")
            return None

        # Detect faces
        boxes, confidences, landmarks, embeddings = self.face_detector.detect_faces(image)

        if len(embeddings) == 0:
            logger.error("No face detected in reference image")
            return None

        if len(embeddings) > 1:
            logger.warning("Multiple faces detected in reference image, using the first one")

        return embeddings[0]

    def compare_with_database(
        self,
        reference_embedding: np.ndarray,
        face_detection_results: List[Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Compare reference face with all detected faces in database.

        Args:
            reference_embedding: Reference face embedding
            face_detection_results: List of face detection results
            threshold: Similarity threshold (overrides default if provided)

        Returns:
            List of matches sorted by similarity (highest first)
        """
        sim_threshold = threshold if threshold is not None else self.similarity_threshold

        logger.info(f"Comparing reference face with database (threshold: {sim_threshold})")

        matches = []

        for result in face_detection_results:
            frame_id = result['frame_id']
            frame_name = result['frame_name']
            timestamp = result['timestamp']
            video_source = result.get('video_source', '')

            for crop_info in result['crops']:
                face_id = crop_info['face_id']
                embedding = crop_info['embedding']
                bbox = crop_info['bbox']
                crop_path = crop_info.get('crop_path')

                # Calculate similarity
                similarity = self.face_detector.calculate_similarity(
                    reference_embedding,
                    embedding
                )

                # Check if above threshold
                if similarity >= sim_threshold:
                    matches.append({
                        'frame_id': frame_id,
                        'frame_name': frame_name,
                        'face_id': face_id,
                        'similarity': float(similarity),
                        'timestamp': timestamp,
                        'video_source': video_source,
                        'bbox': bbox,
                        'crop_path': crop_path
                    })

        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        logger.info(f"Found {len(matches)} matching faces")

        return matches

    def compare_all_to_all(
        self,
        face_detection_results: List[Dict[str, Any]],
        threshold: Optional[float] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compare all faces against each other to find similar faces.

        Args:
            face_detection_results: List of face detection results
            threshold: Similarity threshold

        Returns:
            Dictionary mapping face IDs to their matches
        """
        sim_threshold = threshold if threshold is not None else self.similarity_threshold

        logger.info("Performing all-to-all face comparison")

        # Collect all faces with embeddings
        all_faces = []
        for result in face_detection_results:
            for crop_info in result['crops']:
                all_faces.append({
                    'frame_id': result['frame_id'],
                    'frame_name': result['frame_name'],
                    'face_id': crop_info['face_id'],
                    'embedding': crop_info['embedding'],
                    'bbox': crop_info['bbox'],
                    'crop_path': crop_info.get('crop_path'),
                    'timestamp': result['timestamp'],
                    'video_source': result.get('video_source', '')
                })

        logger.info(f"Comparing {len(all_faces)} faces")

        # Compare each face with all others
        similarity_groups = {}

        for i, face1 in enumerate(all_faces):
            face1_key = f"{face1['frame_id']}_{face1['face_id']}"
            matches = []

            for j, face2 in enumerate(all_faces):
                if i == j:
                    continue

                similarity = self.face_detector.calculate_similarity(
                    face1['embedding'],
                    face2['embedding']
                )

                if similarity >= sim_threshold:
                    face2_key = f"{face2['frame_id']}_{face2['face_id']}"
                    matches.append({
                        'face_key': face2_key,
                        'frame_id': face2['frame_id'],
                        'frame_name': face2['frame_name'],
                        'face_id': face2['face_id'],
                        'similarity': float(similarity),
                        'timestamp': face2['timestamp'],
                        'video_source': face2['video_source'],
                        'bbox': face2['bbox'],
                        'crop_path': face2['crop_path']
                    })

            if matches:
                matches.sort(key=lambda x: x['similarity'], reverse=True)
                similarity_groups[face1_key] = matches

        logger.info(f"Found {len(similarity_groups)} faces with matches")

        return similarity_groups

    def create_similarity_matrix(
        self,
        face_detection_results: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create similarity matrix for all faces.

        Args:
            face_detection_results: List of face detection results

        Returns:
            Tuple of (similarity matrix, face labels)
        """
        # Collect all faces
        all_faces = []
        face_labels = []

        for result in face_detection_results:
            for crop_info in result['crops']:
                all_faces.append(crop_info['embedding'])
                face_labels.append(
                    f"F{result['frame_id']}_Face{crop_info['face_id']}"
                )

        n_faces = len(all_faces)
        similarity_matrix = np.zeros((n_faces, n_faces))

        # Calculate pairwise similarities
        for i in range(n_faces):
            for j in range(n_faces):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    sim = self.face_detector.calculate_similarity(
                        all_faces[i],
                        all_faces[j]
                    )
                    similarity_matrix[i, j] = sim

        return similarity_matrix, face_labels

    def save_comparison_results(
        self,
        matches: List[Dict[str, Any]],
        output_path: Path,
        reference_image_path: Optional[Path] = None,
        threshold: float = None
    ) -> None:
        """
        Save comparison results to JSON file.

        Args:
            matches: List of matching faces
            output_path: Output JSON file path
            reference_image_path: Path to reference image (optional)
            threshold: Similarity threshold used
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result_data = {
            'reference_image': str(reference_image_path) if reference_image_path else None,
            'threshold': threshold if threshold else self.similarity_threshold,
            'total_matches': len(matches),
            'matches': matches
        }

        with open(output_path, 'w') as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"Saved comparison results to {output_path}")

    def save_matched_faces(
        self,
        matches: List[Dict[str, Any]],
        output_dir: Path
    ) -> None:
        """
        Copy matched face crops to output directory.

        Args:
            matches: List of matching faces
            output_dir: Output directory for matched faces
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for idx, match in enumerate(matches):
            crop_path = match.get('crop_path')
            if crop_path and Path(crop_path).exists():
                similarity = match['similarity']
                output_path = output_dir / f"match_{idx}_similarity_{similarity:.2f}.jpg"

                # Copy file
                import shutil
                shutil.copy(crop_path, output_path)

        logger.info(f"Saved {len(matches)} matched face crops to {output_dir}")

    def generate_comparison_report(
        self,
        matches: List[Dict[str, Any]],
        output_dir: Path,
        reference_image_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive comparison report.

        Args:
            matches: List of matching faces
            output_dir: Output directory
            reference_image_path: Path to reference image

        Returns:
            Report summary dictionary
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Calculate statistics
        if matches:
            similarities = [m['similarity'] for m in matches]
            avg_similarity = np.mean(similarities)
            max_similarity = np.max(similarities)
            min_similarity = np.min(similarities)
        else:
            avg_similarity = 0
            max_similarity = 0
            min_similarity = 0

        # Count unique frames and videos
        unique_frames = len(set(m['frame_id'] for m in matches))
        unique_videos = len(set(m.get('video_source', '') for m in matches))

        report = {
            'reference_image': str(reference_image_path) if reference_image_path else None,
            'threshold': self.similarity_threshold,
            'total_matches': len(matches),
            'unique_frames': unique_frames,
            'unique_videos': unique_videos,
            'statistics': {
                'avg_similarity': float(avg_similarity),
                'max_similarity': float(max_similarity),
                'min_similarity': float(min_similarity)
            },
            'matches': matches[:10]  # Top 10 matches
        }

        # Save report
        report_path = output_dir / "comparison_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Generated comparison report at {report_path}")

        return report
