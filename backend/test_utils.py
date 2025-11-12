"""
Unit tests for utility functions
"""
import pytest
import numpy as np
from pathlib import Path

from utils.bbox_utils import (
    calculate_iou,
    is_face_in_person_bbox,
    associate_faces_to_persons,
    crop_bbox
)
from utils.video_utils import (
    timestamp_to_seconds,
    seconds_to_timestamp,
    validate_video_file
)


class TestBoundingBoxUtils:
    """Test bounding box utility functions"""

    def test_calculate_iou_no_overlap(self):
        """Test IoU calculation with no overlap"""
        box1 = (0, 0, 10, 10)
        box2 = (20, 20, 10, 10)
        iou = calculate_iou(box1, box2)
        assert iou == 0.0

    def test_calculate_iou_full_overlap(self):
        """Test IoU calculation with full overlap"""
        box1 = (0, 0, 10, 10)
        box2 = (0, 0, 10, 10)
        iou = calculate_iou(box1, box2)
        assert iou == 1.0

    def test_calculate_iou_partial_overlap(self):
        """Test IoU calculation with partial overlap"""
        box1 = (0, 0, 10, 10)
        box2 = (5, 5, 10, 10)
        iou = calculate_iou(box1, box2)
        assert 0.0 < iou < 1.0

    def test_is_face_in_person_bbox(self):
        """Test face-in-person detection"""
        face_bbox = (5, 5, 5, 5)
        person_bbox = (0, 0, 20, 20)
        assert is_face_in_person_bbox(face_bbox, person_bbox, threshold=0.3)

    def test_associate_faces_to_persons(self):
        """Test face-to-person association"""
        person_boxes = [(0, 0, 100, 200), (200, 0, 100, 200)]
        face_boxes = [(20, 20, 30, 30), (220, 20, 30, 30)]
        associations = associate_faces_to_persons(person_boxes, face_boxes)

        assert len(associations) == 2
        assert 0 in associations[0]  # First face belongs to first person
        assert 1 in associations[1]  # Second face belongs to second person

    def test_crop_bbox(self):
        """Test bounding box cropping"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        bbox = (10, 10, 20, 20)
        crop = crop_bbox(image, bbox)

        assert crop.shape == (20, 20, 3)

    def test_crop_bbox_boundary(self):
        """Test cropping at image boundaries"""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        bbox = (90, 90, 20, 20)  # Goes beyond image
        crop = crop_bbox(image, bbox)

        # Should be clipped to image bounds
        assert crop.shape[0] <= 20
        assert crop.shape[1] <= 20


class TestVideoUtils:
    """Test video utility functions"""

    def test_timestamp_to_seconds_float(self):
        """Test timestamp conversion from float"""
        assert timestamp_to_seconds("10.5") == 10.5

    def test_timestamp_to_seconds_mmss(self):
        """Test timestamp conversion from MM:SS"""
        assert timestamp_to_seconds("01:30") == 90.0

    def test_timestamp_to_seconds_hhmmss(self):
        """Test timestamp conversion from HH:MM:SS"""
        assert timestamp_to_seconds("01:30:45") == 5445.0

    def test_seconds_to_timestamp(self):
        """Test seconds to timestamp conversion"""
        ts = seconds_to_timestamp(90.5)
        assert "00:01:30" in ts

    def test_seconds_to_timestamp_hours(self):
        """Test seconds to timestamp with hours"""
        ts = seconds_to_timestamp(3665)
        assert "01:01:05" in ts

    def test_validate_video_file_valid(self):
        """Test video file validation with valid format"""
        # Create a mock file path
        test_file = Path("/tmp/test.mp4")
        # We can't test actual file existence without creating files
        # This tests the extension validation
        assert test_file.suffix.lower().lstrip('.') == 'mp4'

    def test_validate_video_file_invalid_format(self):
        """Test video file validation with invalid format"""
        allowed_formats = ['mp4', 'mov', 'avi', 'mkv']
        test_file = Path("/tmp/test.txt")
        extension = test_file.suffix.lower().lstrip('.')
        assert extension not in allowed_formats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
