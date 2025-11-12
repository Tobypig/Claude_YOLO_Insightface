"""
Face detection and recognition processor using InsightFace.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

try:
    from insightface.app import FaceAnalysis
except ImportError:
    logger.warning("InsightFace not installed. Face detection will not work.")
    FaceAnalysis = None

from utils.bbox_utils import draw_face_boxes, crop_bbox


class FaceDetector:
    """Handles face detection and embedding extraction using InsightFace."""

    def __init__(
        self,
        model_name: str = "buffalo_l",
        confidence_threshold: float = 0.5,
        device: str = "cuda"
    ):
        """
        Initialize face detector.

        Args:
            model_name: InsightFace model name
            confidence_threshold: Minimum confidence for detections
            device: Device to run model on ('cuda' or 'cpu')
        """
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None

        if FaceAnalysis is not None:
            try:
                logger.info(f"Loading InsightFace model: {model_name}")
                ctx_id = 0 if device == "cuda" else -1
                self.model = FaceAnalysis(name=model_name, providers=[
                    'CUDAExecutionProvider' if device == 'cuda' else 'CPUExecutionProvider'
                ])
                self.model.prepare(ctx_id=ctx_id, det_size=(640, 640))
                logger.info(f"InsightFace model loaded successfully on {device}")
            except Exception as e:
                logger.error(f"Failed to load InsightFace model: {e}")
        else:
            logger.error("InsightFace not available")

    def detect_faces(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> Tuple[List[Tuple[int, int, int, int]], List[float], List[np.ndarray], List[np.ndarray]]:
        """
        Detect faces in image and extract embeddings.

        Args:
            image: Input image (BGR format)
            conf_threshold: Confidence threshold (overrides default if provided)

        Returns:
            Tuple of (bounding boxes, confidence scores, landmarks, embeddings)
            Each box is (x, y, w, h)
        """
        if self.model is None:
            logger.error("InsightFace model not initialized")
            return [], [], [], []

        threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold

        try:
            # Run face detection and analysis
            faces = self.model.get(image)

            boxes = []
            confidences = []
            landmarks_list = []
            embeddings = []

            for face in faces:
                # Get confidence (detection score)
                conf = float(face.det_score)
                if conf < threshold:
                    continue

                # Get bounding box
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                x = int(x1)
                y = int(y1)
                w = int(x2 - x1)
                h = int(y2 - y1)

                # Get landmarks (5 facial keypoints)
                landmarks = face.kps.astype(int)

                # Get embedding (512-dim feature vector)
                embedding = face.normed_embedding

                boxes.append((x, y, w, h))
                confidences.append(conf)
                landmarks_list.append(landmarks)
                embeddings.append(embedding)

            logger.info(f"Detected {len(boxes)} faces")
            return boxes, confidences, landmarks_list, embeddings

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return [], [], [], []

    def process_frame(
        self,
        frame_path: Path,
        output_dir: Path,
        save_annotated: bool = True,
        save_crops: bool = True,
        save_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        Process single frame for face detection.

        Args:
            frame_path: Path to frame image
            output_dir: Output directory for results
            save_annotated: Save annotated image with boxes
            save_crops: Save cropped face images
            save_embeddings: Save face embeddings

        Returns:
            Dictionary with detection results
        """
        logger.info(f"Processing frame for faces: {frame_path.name}")

        # Load frame
        image = cv2.imread(str(frame_path))
        if image is None:
            logger.error(f"Failed to load frame: {frame_path}")
            return {'boxes': [], 'confidences': [], 'landmarks': [], 'embeddings': [], 'crops': []}

        # Detect faces
        boxes, confidences, landmarks_list, embeddings = self.detect_faces(image)

        result = {
            'frame_path': str(frame_path),
            'frame_name': frame_path.name,
            'boxes': boxes,
            'confidences': confidences,
            'landmarks': landmarks_list,
            'embeddings': embeddings,
            'crops': [],
            'annotated_path': None
        }

        if len(boxes) == 0:
            logger.info("No faces detected")
            return result

        # Create output directories
        if save_annotated:
            annotated_dir = output_dir / "annotated"
            annotated_dir.mkdir(parents=True, exist_ok=True)

        if save_crops:
            images_dir = output_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

        if save_embeddings:
            embeds_dir = output_dir / "embeds"
            embeds_dir.mkdir(parents=True, exist_ok=True)

        # Save annotated image
        if save_annotated:
            annotated_image = draw_face_boxes(
                image, boxes, confidences, landmarks_list,
                show_landmarks=True
            )
            annotated_path = annotated_dir / f"{frame_path.stem}_faces.jpg"
            cv2.imwrite(str(annotated_path), annotated_image)
            result['annotated_path'] = str(annotated_path)
            logger.info(f"Saved annotated image: {annotated_path.name}")

        # Save face crops and embeddings
        for idx, (box, conf, landmarks, embedding) in enumerate(
            zip(boxes, confidences, landmarks_list, embeddings)
        ):
            # Save crop
            if save_crops:
                crop = crop_bbox(image, box)
                crop_path = images_dir / f"face_{idx}_{frame_path.stem}.jpg"
                cv2.imwrite(str(crop_path), crop)
            else:
                crop_path = None

            # Save embedding
            if save_embeddings:
                embed_path = embeds_dir / f"face_{idx}_{frame_path.stem}.npy"
                np.save(str(embed_path), embedding)
            else:
                embed_path = None

            result['crops'].append({
                'face_id': idx,
                'bbox': box,
                'confidence': conf,
                'landmarks': landmarks.tolist(),
                'embedding': embedding,
                'crop_path': str(crop_path) if crop_path else None,
                'embedding_path': str(embed_path) if embed_path else None
            })

        logger.info(f"Saved {len(boxes)} face crops and embeddings")

        return result

    def process_frames(
        self,
        frame_data: List[Dict[str, Any]],
        output_dir: Path,
        save_annotated: bool = True,
        save_crops: bool = True,
        save_embeddings: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple frames for face detection.

        Args:
            frame_data: List of frame information dictionaries
            output_dir: Output directory for results
            save_annotated: Save annotated images with boxes
            save_crops: Save cropped face images
            save_embeddings: Save face embeddings

        Returns:
            List of detection results for each frame
        """
        logger.info(f"Processing {len(frame_data)} frames for face detection")

        results = []
        for frame_info in frame_data:
            frame_path = Path(frame_info['frame_path'])

            # Create frame-specific output directory
            frame_output_dir = output_dir / "faces"

            result = self.process_frame(
                frame_path,
                frame_output_dir,
                save_annotated=save_annotated,
                save_crops=save_crops,
                save_embeddings=save_embeddings
            )

            # Merge with frame info
            result.update({
                'frame_id': frame_info['frame_id'],
                'timestamp': frame_info['timestamp'],
                'video_source': frame_info['video_source']
            })

            results.append(result)

        total_faces = sum(len(r['boxes']) for r in results)
        logger.info(f"Detected {total_faces} total faces across {len(frame_data)} frames")

        return results

    def save_metadata(
        self,
        results: List[Dict[str, Any]],
        output_path: Path
    ) -> None:
        """
        Save face detection metadata to CSV.

        Args:
            results: List of detection results
            output_path: Output CSV file path
        """
        import pandas as pd

        rows = []
        for result in results:
            frame_id = result['frame_id']
            frame_name = result['frame_name']
            timestamp = result['timestamp']

            for crop_info in result['crops']:
                face_id = crop_info['face_id']
                bbox = crop_info['bbox']
                confidence = crop_info['confidence']
                landmarks = crop_info['landmarks']
                crop_path = crop_info['crop_path']
                embedding_path = crop_info['embedding_path']

                rows.append({
                    'frame_id': frame_id,
                    'frame_name': frame_name,
                    'timestamp': timestamp,
                    'face_id': face_id,
                    'bbox_x': bbox[0],
                    'bbox_y': bbox[1],
                    'bbox_w': bbox[2],
                    'bbox_h': bbox[3],
                    'confidence': confidence,
                    'landmarks': str(landmarks),
                    'crop_path': crop_path,
                    'embedding_path': embedding_path
                })

        if rows:
            df = pd.DataFrame(rows)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved face metadata to {output_path}")
        else:
            logger.warning("No face detections to save")

    @staticmethod
    def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two face embeddings.

        Args:
            embedding1: First face embedding
            embedding2: Second face embedding

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
