"""
Person detection processor using YOLO.
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.warning("Ultralytics YOLO not installed. Person detection will not work.")
    YOLO = None

from utils.bbox_utils import draw_person_boxes, crop_bbox


class PersonDetector:
    """Handles person detection using YOLO."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str = "cuda"
    ):
        """
        Initialize person detector.

        Args:
            model_path: Path to YOLO model
            confidence_threshold: Minimum confidence for detections
            device: Device to run model on ('cuda' or 'cpu')
        """
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None

        if YOLO is not None:
            try:
                logger.info(f"Loading YOLO model: {model_path}")
                self.model = YOLO(model_path)
                self.model.to(device)
                logger.info(f"YOLO model loaded successfully on {device}")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
        else:
            logger.error("YOLO not available")

    def detect_persons(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None
    ) -> Tuple[List[Tuple[int, int, int, int]], List[float]]:
        """
        Detect persons in image.

        Args:
            image: Input image (BGR format)
            conf_threshold: Confidence threshold (overrides default if provided)

        Returns:
            Tuple of (bounding boxes, confidence scores)
            Each box is (x, y, w, h)
        """
        if self.model is None:
            logger.error("YOLO model not initialized")
            return [], []

        threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold

        try:
            # Run inference
            results = self.model(image, verbose=False)

            boxes = []
            confidences = []

            # Process results
            for result in results:
                for box in result.boxes:
                    # Get class ID (0 is person in COCO dataset)
                    class_id = int(box.cls[0])
                    if class_id != 0:  # Only keep person class
                        continue

                    # Get confidence
                    conf = float(box.conf[0])
                    if conf < threshold:
                        continue

                    # Get bounding box (convert from xyxy to xywh)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x = int(x1)
                    y = int(y1)
                    w = int(x2 - x1)
                    h = int(y2 - y1)

                    boxes.append((x, y, w, h))
                    confidences.append(conf)

            logger.info(f"Detected {len(boxes)} persons")
            return boxes, confidences

        except Exception as e:
            logger.error(f"Person detection failed: {e}")
            return [], []

    def process_frame(
        self,
        frame_path: Path,
        output_dir: Path,
        save_annotated: bool = True,
        save_crops: bool = True
    ) -> Dict[str, Any]:
        """
        Process single frame for person detection.

        Args:
            frame_path: Path to frame image
            output_dir: Output directory for results
            save_annotated: Save annotated image with boxes
            save_crops: Save cropped person images

        Returns:
            Dictionary with detection results
        """
        logger.info(f"Processing frame: {frame_path.name}")

        # Load frame
        image = cv2.imread(str(frame_path))
        if image is None:
            logger.error(f"Failed to load frame: {frame_path}")
            return {'boxes': [], 'confidences': [], 'crops': []}

        # Detect persons
        boxes, confidences = self.detect_persons(image)

        result = {
            'frame_path': str(frame_path),
            'frame_name': frame_path.name,
            'boxes': boxes,
            'confidences': confidences,
            'crops': [],
            'annotated_path': None
        }

        if len(boxes) == 0:
            logger.info("No persons detected")
            return result

        # Create output directories
        if save_annotated:
            annotated_dir = output_dir / "annotated"
            annotated_dir.mkdir(parents=True, exist_ok=True)

        if save_crops:
            crops_dir = output_dir / "crops"
            crops_dir.mkdir(parents=True, exist_ok=True)

        # Save annotated image
        if save_annotated:
            annotated_image = draw_person_boxes(image, boxes, confidences)
            annotated_path = annotated_dir / f"{frame_path.stem}_persons.jpg"
            cv2.imwrite(str(annotated_path), annotated_image)
            result['annotated_path'] = str(annotated_path)
            logger.info(f"Saved annotated image: {annotated_path.name}")

        # Save person crops
        if save_crops:
            for idx, (box, conf) in enumerate(zip(boxes, confidences)):
                crop = crop_bbox(image, box)
                crop_path = crops_dir / f"person_{idx}_{frame_path.stem}.jpg"
                cv2.imwrite(str(crop_path), crop)
                result['crops'].append({
                    'person_id': idx,
                    'bbox': box,
                    'confidence': conf,
                    'crop_path': str(crop_path)
                })

            logger.info(f"Saved {len(boxes)} person crops")

        return result

    def process_frames(
        self,
        frame_data: List[Dict[str, Any]],
        output_dir: Path,
        save_annotated: bool = True,
        save_crops: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process multiple frames for person detection.

        Args:
            frame_data: List of frame information dictionaries
            output_dir: Output directory for results
            save_annotated: Save annotated images with boxes
            save_crops: Save cropped person images

        Returns:
            List of detection results for each frame
        """
        logger.info(f"Processing {len(frame_data)} frames for person detection")

        results = []
        for frame_info in frame_data:
            frame_path = Path(frame_info['frame_path'])

            # Create frame-specific output directory
            frame_output_dir = output_dir / "persons"

            result = self.process_frame(
                frame_path,
                frame_output_dir,
                save_annotated=save_annotated,
                save_crops=save_crops
            )

            # Merge with frame info
            result.update({
                'frame_id': frame_info['frame_id'],
                'timestamp': frame_info['timestamp'],
                'video_source': frame_info['video_source']
            })

            results.append(result)

        total_persons = sum(len(r['boxes']) for r in results)
        logger.info(f"Detected {total_persons} total persons across {len(frame_data)} frames")

        return results

    def save_metadata(
        self,
        results: List[Dict[str, Any]],
        output_path: Path
    ) -> None:
        """
        Save person detection metadata to CSV.

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
                person_id = crop_info['person_id']
                bbox = crop_info['bbox']
                confidence = crop_info['confidence']
                crop_path = crop_info['crop_path']

                rows.append({
                    'frame_id': frame_id,
                    'frame_name': frame_name,
                    'timestamp': timestamp,
                    'person_id': person_id,
                    'bbox_x': bbox[0],
                    'bbox_y': bbox[1],
                    'bbox_w': bbox[2],
                    'bbox_h': bbox[3],
                    'confidence': confidence,
                    'crop_path': crop_path
                })

        if rows:
            df = pd.DataFrame(rows)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Saved person metadata to {output_path}")
        else:
            logger.warning("No person detections to save")
