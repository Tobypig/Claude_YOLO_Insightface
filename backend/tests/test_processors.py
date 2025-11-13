"""
Unit tests for processor modules.
Tests: FrameExtractor, PersonDetector, FaceDetector, FaceComparator, VideoProcessor
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from processors.frame_extractor import FrameExtractor
from processors.person_detector import PersonDetector
from processors.face_detector import FaceDetector
from processors.face_comparator import FaceComparator
from processors.video_processor import VideoProcessor


# Fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image():
    """Create sample test image."""
    # Create 640x480 RGB image
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return image


@pytest.fixture
def sample_video(temp_dir):
    """Create a sample test video file."""
    video_path = temp_dir / "test_video.mp4"

    # Create a simple video using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

    # Write 90 frames (3 seconds at 30fps)
    for i in range(90):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)

    out.release()
    return video_path


@pytest.fixture
def mock_yolo_model():
    """Mock YOLO model for testing."""
    mock_model = MagicMock()

    # Mock detection results
    mock_box = MagicMock()
    mock_box.cls = [0]  # Person class
    mock_box.conf = [0.85]
    mock_box.xyxy = [np.array([100, 100, 200, 300])]  # x1, y1, x2, y2

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]

    mock_model.return_value = [mock_result]
    return mock_model


@pytest.fixture
def mock_insightface_model():
    """Mock InsightFace model for testing."""
    mock_model = MagicMock()

    # Mock face detection
    mock_face = MagicMock()
    mock_face.det_score = 0.95
    mock_face.bbox = np.array([150, 150, 250, 250])
    mock_face.kps = np.array([[160, 170], [180, 170], [170, 190], [165, 200], [185, 200]])
    mock_face.normed_embedding = np.random.randn(512).astype(np.float32)

    mock_model.get.return_value = [mock_face]
    return mock_model


# ============================================================================
# FrameExtractor Tests
# ============================================================================

class TestFrameExtractor:
    """Test suite for FrameExtractor."""

    def test_init(self):
        """Test FrameExtractor initialization."""
        extractor = FrameExtractor(quality=5)
        assert extractor.quality == 5

    def test_init_default_quality(self):
        """Test FrameExtractor with default quality."""
        extractor = FrameExtractor()
        assert extractor.quality == 2

    @patch('processors.frame_extractor.get_video_info')
    @patch('processors.frame_extractor.extract_frames_at_timestamps')
    def test_extract_frames_with_timestamps(self, mock_extract, mock_info, temp_dir):
        """Test frame extraction at specific timestamps."""
        # Setup mocks
        mock_info.return_value = {'duration': 10.0, 'fps': 30.0}
        mock_extract.return_value = [
            (1.0, temp_dir / "frame_1.jpg"),
            (2.0, temp_dir / "frame_2.jpg")
        ]

        extractor = FrameExtractor()
        result = extractor.extract_frames(
            Path("test.mp4"),
            temp_dir,
            timestamps=[1.0, 2.0]
        )

        assert len(result) == 2
        assert result[0]['timestamp'] == 1.0
        assert result[1]['timestamp'] == 2.0
        mock_extract.assert_called_once()

    @patch('processors.frame_extractor.get_video_info')
    @patch('processors.frame_extractor.extract_frames_at_interval')
    def test_extract_frames_with_interval(self, mock_extract, mock_info, temp_dir):
        """Test frame extraction at regular intervals."""
        mock_info.return_value = {'duration': 10.0, 'fps': 30.0}
        mock_extract.return_value = [
            (0.0, temp_dir / "frame_0.jpg"),
            (1.0, temp_dir / "frame_1.jpg"),
            (2.0, temp_dir / "frame_2.jpg")
        ]

        extractor = FrameExtractor()
        result = extractor.extract_frames(
            Path("test.mp4"),
            temp_dir,
            interval=1.0
        )

        assert len(result) == 3
        mock_extract.assert_called_once()

    @patch('processors.frame_extractor.get_video_info')
    def test_extract_frames_no_method(self, mock_info, temp_dir):
        """Test extraction with no method specified returns empty."""
        mock_info.return_value = {'duration': 10.0, 'fps': 30.0}

        extractor = FrameExtractor()
        result = extractor.extract_frames(Path("test.mp4"), temp_dir)

        assert len(result) == 0


# ============================================================================
# PersonDetector Tests
# ============================================================================

class TestPersonDetector:
    """Test suite for PersonDetector."""

    def test_init(self):
        """Test PersonDetector initialization."""
        with patch('processors.person_detector.YOLO') as mock_yolo:
            detector = PersonDetector(
                model_path="yolov8n.pt",
                confidence_threshold=0.6,
                device="cpu"
            )

            assert detector.confidence_threshold == 0.6
            assert detector.device == "cpu"

    def test_detect_persons_success(self, sample_image, mock_yolo_model):
        """Test successful person detection."""
        with patch('processors.person_detector.YOLO') as mock_yolo:
            mock_yolo.return_value = mock_yolo_model

            detector = PersonDetector(device="cpu")
            detector.model = mock_yolo_model

            boxes, confidences = detector.detect_persons(sample_image)

            assert len(boxes) == 1
            assert len(confidences) == 1
            assert boxes[0] == (100, 100, 100, 200)  # x, y, w, h
            assert confidences[0] == 0.85

    def test_detect_persons_no_model(self, sample_image):
        """Test detection with no model loaded."""
        detector = PersonDetector(device="cpu")
        detector.model = None

        boxes, confidences = detector.detect_persons(sample_image)

        assert len(boxes) == 0
        assert len(confidences) == 0

    def test_detect_persons_confidence_threshold(self, sample_image):
        """Test confidence threshold filtering."""
        with patch('processors.person_detector.YOLO') as mock_yolo:
            # Create mock with low confidence
            mock_box = MagicMock()
            mock_box.cls = [0]
            mock_box.conf = [0.3]  # Below default 0.5 threshold
            mock_box.xyxy = [np.array([100, 100, 200, 300])]

            mock_result = MagicMock()
            mock_result.boxes = [mock_box]

            mock_model = MagicMock()
            mock_model.return_value = [mock_result]
            mock_yolo.return_value = mock_model

            detector = PersonDetector(confidence_threshold=0.5, device="cpu")
            detector.model = mock_model

            boxes, confidences = detector.detect_persons(sample_image)

            # Should be filtered out due to low confidence
            assert len(boxes) == 0

    def test_process_frame(self, temp_dir, sample_image, mock_yolo_model):
        """Test processing single frame."""
        # Save sample image
        frame_path = temp_dir / "test_frame.jpg"
        cv2.imwrite(str(frame_path), sample_image)

        output_dir = temp_dir / "output"

        with patch('processors.person_detector.YOLO') as mock_yolo:
            mock_yolo.return_value = mock_yolo_model

            detector = PersonDetector(device="cpu")
            detector.model = mock_yolo_model

            result = detector.process_frame(
                frame_path,
                output_dir,
                save_annotated=True,
                save_crops=True
            )

            assert len(result['boxes']) == 1
            assert len(result['confidences']) == 1
            assert len(result['crops']) == 1


# ============================================================================
# FaceDetector Tests
# ============================================================================

class TestFaceDetector:
    """Test suite for FaceDetector."""

    def test_init(self):
        """Test FaceDetector initialization."""
        with patch('processors.face_detector.FaceAnalysis'):
            detector = FaceDetector(
                model_name="buffalo_l",
                confidence_threshold=0.6,
                device="cpu"
            )

            assert detector.confidence_threshold == 0.6
            assert detector.device == "cpu"

    def test_detect_faces_success(self, sample_image, mock_insightface_model):
        """Test successful face detection."""
        with patch('processors.face_detector.FaceAnalysis'):
            detector = FaceDetector(device="cpu")
            detector.model = mock_insightface_model

            boxes, confs, landmarks, embeddings = detector.detect_faces(sample_image)

            assert len(boxes) == 1
            assert len(confs) == 1
            assert len(landmarks) == 1
            assert len(embeddings) == 1
            assert boxes[0] == (150, 150, 100, 100)  # x, y, w, h
            assert confs[0] == 0.95
            assert embeddings[0].shape == (512,)

    def test_detect_faces_no_model(self, sample_image):
        """Test detection with no model."""
        detector = FaceDetector(device="cpu")
        detector.model = None

        boxes, confs, landmarks, embeddings = detector.detect_faces(sample_image)

        assert len(boxes) == 0
        assert len(confs) == 0
        assert len(landmarks) == 0
        assert len(embeddings) == 0

    def test_calculate_similarity(self):
        """Test cosine similarity calculation."""
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([1.0, 0.0, 0.0])
        emb3 = np.array([0.0, 1.0, 0.0])

        # Same embeddings
        sim1 = FaceDetector.calculate_similarity(emb1, emb2)
        assert sim1 == pytest.approx(1.0)

        # Orthogonal embeddings
        sim2 = FaceDetector.calculate_similarity(emb1, emb3)
        assert sim2 == pytest.approx(0.0)

    def test_process_frame(self, temp_dir, sample_image, mock_insightface_model):
        """Test processing single frame for faces."""
        frame_path = temp_dir / "test_frame.jpg"
        cv2.imwrite(str(frame_path), sample_image)

        output_dir = temp_dir / "output"

        with patch('processors.face_detector.FaceAnalysis'):
            detector = FaceDetector(device="cpu")
            detector.model = mock_insightface_model

            result = detector.process_frame(
                frame_path,
                output_dir,
                save_annotated=True,
                save_crops=True,
                save_embeddings=True
            )

            assert len(result['boxes']) == 1
            assert len(result['confidences']) == 1
            assert len(result['landmarks']) == 1
            assert len(result['embeddings']) == 1
            assert len(result['crops']) == 1


# ============================================================================
# FaceComparator Tests
# ============================================================================

class TestFaceComparator:
    """Test suite for FaceComparator."""

    @pytest.fixture
    def mock_face_detector(self, mock_insightface_model):
        """Create mock FaceDetector."""
        with patch('processors.face_detector.FaceAnalysis'):
            detector = FaceDetector(device="cpu")
            detector.model = mock_insightface_model
            return detector

    def test_init(self, mock_face_detector):
        """Test FaceComparator initialization."""
        comparator = FaceComparator(
            face_detector=mock_face_detector,
            similarity_threshold=0.8
        )

        assert comparator.similarity_threshold == 0.8
        assert comparator.face_detector == mock_face_detector

    def test_extract_reference_embedding_from_bytes(self, mock_face_detector, sample_image):
        """Test extracting embedding from image bytes."""
        # Encode image to bytes
        _, buffer = cv2.imencode('.jpg', sample_image)
        image_bytes = buffer.tobytes()

        comparator = FaceComparator(mock_face_detector)
        embedding = comparator.extract_reference_embedding_from_bytes(image_bytes)

        assert embedding is not None
        assert embedding.shape == (512,)

    def test_compare_with_database(self, mock_face_detector):
        """Test comparing face with database."""
        comparator = FaceComparator(mock_face_detector, similarity_threshold=0.7)

        # Create reference embedding
        ref_embedding = np.random.randn(512).astype(np.float32)
        ref_embedding = ref_embedding / np.linalg.norm(ref_embedding)

        # Create database results
        database = [
            {
                'frame_id': 0,
                'frame_name': 'frame_0.jpg',
                'timestamp': 1.0,
                'video_source': 'test.mp4',
                'crops': [
                    {
                        'face_id': 0,
                        'embedding': ref_embedding,  # Exact match
                        'bbox': (100, 100, 50, 50),
                        'crop_path': '/path/to/crop.jpg'
                    },
                    {
                        'face_id': 1,
                        'embedding': np.random.randn(512).astype(np.float32),  # Random
                        'bbox': (200, 200, 50, 50),
                        'crop_path': '/path/to/crop2.jpg'
                    }
                ]
            }
        ]

        matches = comparator.compare_with_database(ref_embedding, database, threshold=0.7)

        # Should match the first face
        assert len(matches) >= 1
        assert matches[0]['similarity'] > 0.99  # Nearly perfect match

    def test_compare_all_to_all(self, mock_face_detector):
        """Test all-to-all face comparison."""
        comparator = FaceComparator(mock_face_detector, similarity_threshold=0.8)

        # Create embeddings
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.99, 0.1, 0.0])  # Similar to emb1
        emb3 = np.array([0.0, 1.0, 0.0])  # Different

        database = [
            {
                'frame_id': 0,
                'frame_name': 'frame_0.jpg',
                'timestamp': 1.0,
                'video_source': 'test.mp4',
                'crops': [
                    {'face_id': 0, 'embedding': emb1, 'bbox': (0, 0, 10, 10), 'crop_path': 'c1.jpg'},
                    {'face_id': 1, 'embedding': emb2, 'bbox': (0, 0, 10, 10), 'crop_path': 'c2.jpg'}
                ]
            },
            {
                'frame_id': 1,
                'frame_name': 'frame_1.jpg',
                'timestamp': 2.0,
                'video_source': 'test.mp4',
                'crops': [
                    {'face_id': 0, 'embedding': emb3, 'bbox': (0, 0, 10, 10), 'crop_path': 'c3.jpg'}
                ]
            }
        ]

        groups = comparator.compare_all_to_all(database, threshold=0.8)

        # Should find similarity between emb1 and emb2
        assert len(groups) > 0


# ============================================================================
# VideoProcessor Tests
# ============================================================================

class TestVideoProcessor:
    """Test suite for VideoProcessor."""

    @patch('processors.video_processor.FaceComparator')
    @patch('processors.video_processor.FaceDetector')
    @patch('processors.video_processor.PersonDetector')
    @patch('processors.video_processor.FrameExtractor')
    def test_init(self, mock_frame, mock_person, mock_face, mock_comp):
        """Test VideoProcessor initialization."""
        processor = VideoProcessor(
            yolo_model="yolov8n.pt",
            insightface_model="buffalo_l",
            person_threshold=0.6,
            face_threshold=0.7,
            device="cpu",
            frame_quality=3
        )

        # Verify sub-processors were initialized
        mock_frame.assert_called_once_with(quality=3)
        mock_person.assert_called_once()
        mock_face.assert_called_once()

    def test_serialize_result(self):
        """Test result serialization for JSON."""
        processor = VideoProcessor(
            yolo_model="yolov8n.pt",
            insightface_model="buffalo_l",
            person_threshold=0.5,
            face_threshold=0.5,
            device="cpu"
        )

        # Create test result with embeddings
        result = {
            'frame_id': 0,
            'boxes': [(100, 100, 50, 50)],
            'embeddings': [np.array([1.0, 2.0, 3.0])],
            'crops': [
                {
                    'crop_id': 0,
                    'embedding': np.array([4.0, 5.0, 6.0])
                }
            ]
        }

        serialized = processor._serialize_result(result)

        # Embeddings should be removed
        assert 'embeddings' not in serialized
        assert 'embedding' not in serialized['crops'][0]
        assert 'frame_id' in serialized


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
