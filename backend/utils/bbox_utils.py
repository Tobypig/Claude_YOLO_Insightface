"""
Bounding box utilities for drawing and processing detection boxes.
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any


def draw_person_boxes(
    image: np.ndarray,
    boxes: List[Tuple[int, int, int, int]],
    confidences: List[float],
    color: Tuple[int, int, int] = (255, 0, 0),  # Blue for persons
    thickness: int = 2,
    show_confidence: bool = True
) -> np.ndarray:
    """
    Draw person detection bounding boxes on image.

    Args:
        image: Input image (BGR format)
        boxes: List of bounding boxes (x, y, w, h)
        confidences: List of confidence scores
        color: Box color in BGR format
        thickness: Line thickness
        show_confidence: Whether to show confidence scores

    Returns:
        Image with drawn boxes
    """
    img_copy = image.copy()

    for box, conf in zip(boxes, confidences):
        x, y, w, h = box
        x, y, w, h = int(x), int(y), int(w), int(h)

        # Draw rectangle
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, thickness)

        # Draw label
        if show_confidence:
            label = f"Person: {conf:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                img_copy,
                (x, y - label_h - baseline - 5),
                (x + label_w, y),
                color,
                -1
            )
            cv2.putText(
                img_copy,
                label,
                (x, y - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

    return img_copy


def draw_face_boxes(
    image: np.ndarray,
    boxes: List[Tuple[int, int, int, int]],
    confidences: List[float],
    landmarks: List[np.ndarray] = None,
    color: Tuple[int, int, int] = (0, 255, 0),  # Green for faces
    thickness: int = 2,
    show_confidence: bool = True,
    show_landmarks: bool = True
) -> np.ndarray:
    """
    Draw face detection bounding boxes on image.

    Args:
        image: Input image (BGR format)
        boxes: List of bounding boxes (x, y, w, h)
        confidences: List of confidence scores
        landmarks: List of facial landmarks
        color: Box color in BGR format
        thickness: Line thickness
        show_confidence: Whether to show confidence scores
        show_landmarks: Whether to draw facial landmarks

    Returns:
        Image with drawn boxes and landmarks
    """
    img_copy = image.copy()

    for idx, (box, conf) in enumerate(zip(boxes, confidences)):
        x, y, w, h = box
        x, y, w, h = int(x), int(y), int(w), int(h)

        # Draw rectangle
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, thickness)

        # Draw label
        if show_confidence:
            label = f"Face: {conf:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                img_copy,
                (x, y - label_h - baseline - 5),
                (x + label_w, y),
                color,
                -1
            )
            cv2.putText(
                img_copy,
                label,
                (x, y - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )

        # Draw landmarks
        if show_landmarks and landmarks is not None and idx < len(landmarks):
            landmark_points = landmarks[idx]
            for point in landmark_points:
                cv2.circle(img_copy, (int(point[0]), int(point[1])), 2, (0, 0, 255), -1)

    return img_copy


def draw_combined_boxes(
    image: np.ndarray,
    person_data: Dict[str, Any],
    face_data: Dict[str, Any],
    show_confidence: bool = True
) -> np.ndarray:
    """
    Draw both person and face bounding boxes on the same image.

    Args:
        image: Input image (BGR format)
        person_data: Dictionary with 'boxes' and 'confidences' for persons
        face_data: Dictionary with 'boxes', 'confidences', and optionally 'landmarks' for faces
        show_confidence: Whether to show confidence scores

    Returns:
        Image with all boxes drawn
    """
    img_copy = image.copy()

    # Draw person boxes (blue)
    if person_data.get('boxes'):
        img_copy = draw_person_boxes(
            img_copy,
            person_data['boxes'],
            person_data['confidences'],
            color=(255, 0, 0),
            show_confidence=show_confidence
        )

    # Draw face boxes (green)
    if face_data.get('boxes'):
        img_copy = draw_face_boxes(
            img_copy,
            face_data['boxes'],
            face_data['confidences'],
            landmarks=face_data.get('landmarks'),
            color=(0, 255, 0),
            show_confidence=show_confidence
        )

    return img_copy


def crop_bbox(image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Crop bounding box region from image.

    Args:
        image: Input image
        bbox: Bounding box (x, y, w, h)

    Returns:
        Cropped image region
    """
    x, y, w, h = bbox
    x, y, w, h = int(x), int(y), int(w), int(h)

    # Ensure coordinates are within image bounds
    h_img, w_img = image.shape[:2]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_img, x + w)
    y2 = min(h_img, y + h)

    return image[y1:y2, x1:x2]


def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.

    Args:
        box1: First bounding box (x, y, w, h)
        box2: Second bounding box (x, y, w, h)

    Returns:
        IoU value between 0 and 1
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # Calculate intersection coordinates
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)

    # Calculate intersection area
    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    inter_area = inter_width * inter_height

    # Calculate union area
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    # Calculate IoU
    if union_area == 0:
        return 0.0

    return inter_area / union_area


def is_face_in_person_bbox(
    face_bbox: Tuple[int, int, int, int],
    person_bbox: Tuple[int, int, int, int],
    threshold: float = 0.5
) -> bool:
    """
    Check if a face bounding box is inside a person bounding box.

    Args:
        face_bbox: Face bounding box (x, y, w, h)
        person_bbox: Person bounding box (x, y, w, h)
        threshold: IoU threshold to consider face inside person

    Returns:
        True if face is inside person bbox
    """
    iou = calculate_iou(face_bbox, person_bbox)
    return iou >= threshold


def associate_faces_to_persons(
    person_boxes: List[Tuple[int, int, int, int]],
    face_boxes: List[Tuple[int, int, int, int]],
    iou_threshold: float = 0.3
) -> Dict[int, List[int]]:
    """
    Associate detected faces to detected persons based on spatial overlap.

    Args:
        person_boxes: List of person bounding boxes
        face_boxes: List of face bounding boxes
        iou_threshold: IoU threshold for association

    Returns:
        Dictionary mapping person_id to list of face_ids
    """
    associations = {i: [] for i in range(len(person_boxes))}

    for face_id, face_box in enumerate(face_boxes):
        best_person_id = -1
        best_iou = 0

        for person_id, person_box in enumerate(person_boxes):
            iou = calculate_iou(face_box, person_box)
            if iou > best_iou and iou >= iou_threshold:
                best_iou = iou
                best_person_id = person_id

        if best_person_id >= 0:
            associations[best_person_id].append(face_id)

    return associations
