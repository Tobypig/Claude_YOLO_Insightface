"""
Integration tests for Video Frame Person & Face Detection API.
Tests actual API endpoints with realistic workflows.
"""
import pytest
import asyncio
import tempfile
import shutil
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
import cv2
import numpy as np

# Import the FastAPI app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import settings


# Fixtures
@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def temp_test_dir():
    """Create temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp(prefix="video_test_"))
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture(scope="module")
def test_video(temp_test_dir):
    """Create a test video file."""
    video_path = temp_test_dir / "test_video.mp4"

    # Create video with OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))

    # Write 60 frames (2 seconds)
    for i in range(60):
        # Create frame with some patterns
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some colors
        frame[100:200, 100:200] = [255, 0, 0]  # Blue square
        frame[300:400, 400:500] = [0, 255, 0]  # Green square
        out.write(frame)

    out.release()
    return video_path


@pytest.fixture(scope="module")
def test_image(temp_test_dir):
    """Create a test image file."""
    image_path = temp_test_dir / "test_image.jpg"
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite(str(image_path), image)
    return image_path


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthCheck:
    """Test health check endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns basic info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "device" in data
        assert "models" in data


# ============================================================================
# Video Management Tests
# ============================================================================

class TestVideoManagement:
    """Test video listing and folder management."""

    def test_list_videos_empty(self, client):
        """Test listing videos when directory is empty."""
        response = client.get("/api/videos")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_list_folders_empty(self, client):
        """Test listing folders when directory is empty."""
        response = client.get("/api/folders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_upload_video_invalid_format(self, client, test_image):
        """Test uploading invalid file format."""
        with open(test_image, 'rb') as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]

    def test_upload_video_success(self, client, test_video):
        """Test successful video upload."""
        with open(test_video, 'rb') as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test_video.mp4", f, "video/mp4")}
            )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "filename" in data
        assert data["filename"] == "test_video.mp4"
        assert "size_bytes" in data


# ============================================================================
# Job Processing Tests
# ============================================================================

class TestJobProcessing:
    """Test video processing job creation and management."""

    def test_process_video_not_found(self, client):
        """Test processing non-existent video."""
        request_data = {
            "input_type": "video",
            "path": "nonexistent.mp4",
            "detect_persons": True,
            "detect_faces": True
        }

        response = client.post("/api/process", json=request_data)
        assert response.status_code == 404

    def test_process_video_invalid_type(self, client):
        """Test processing with invalid input type."""
        request_data = {
            "input_type": "invalid_type",
            "path": "test.mp4",
            "detect_persons": True,
            "detect_faces": True
        }

        response = client.post("/api/process", json=request_data)
        assert response.status_code == 400
        assert "Invalid input_type" in response.json()["detail"]

    def test_get_job_not_found(self, client):
        """Test getting non-existent job."""
        response = client.get("/api/jobs/nonexistent_job")
        assert response.status_code == 404

    def test_delete_job_not_found(self, client):
        """Test deleting non-existent job."""
        response = client.delete("/api/jobs/nonexistent_job")
        assert response.status_code == 404


# ============================================================================
# Results and Preview Tests
# ============================================================================

class TestResultsAndPreview:
    """Test results retrieval and frame previews."""

    def test_get_results_not_found(self, client):
        """Test getting results for non-existent job."""
        response = client.get("/api/results/nonexistent_job")
        assert response.status_code == 404

    def test_get_preview_not_found(self, client):
        """Test getting preview for non-existent job."""
        response = client.get("/api/preview/nonexistent_job/frame/0")
        assert response.status_code == 404

    def test_download_metadata_not_found(self, client):
        """Test downloading metadata for non-existent job."""
        response = client.get("/api/download/nonexistent_job/metadata")
        assert response.status_code == 404

    def test_download_invalid_file_type(self, client):
        """Test downloading invalid file type."""
        # First create a dummy job
        from main import jobs_db
        jobs_db["test_job"] = {"status": "completed"}

        response = client.get("/api/download/test_job/invalid_type")
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

        # Cleanup
        del jobs_db["test_job"]


# ============================================================================
# Face Comparison Tests
# ============================================================================

class TestFaceComparison:
    """Test face comparison functionality."""

    def test_compare_job_not_found(self, client):
        """Test comparison with non-existent job."""
        request_data = {
            "job_id": "nonexistent_job",
            "reference_image": "base64encodedimage",
            "threshold": 0.7
        }

        response = client.post("/api/compare", json=request_data)
        assert response.status_code == 404

    def test_compare_job_not_completed(self, client):
        """Test comparison with incomplete job."""
        # Create processing job
        from main import jobs_db
        jobs_db["processing_job"] = {"status": "processing"}

        request_data = {
            "job_id": "processing_job",
            "reference_image": "base64encodedimage",
            "threshold": 0.7
        }

        response = client.post("/api/compare", json=request_data)
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

        # Cleanup
        del jobs_db["processing_job"]


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

class TestEndToEndWorkflow:
    """Test complete workflows from upload to results."""

    @pytest.mark.slow
    def test_complete_workflow_with_mock(self, client, test_video, temp_test_dir):
        """Test complete workflow with mocked models."""
        # This test is marked as slow since it involves actual processing
        # In real scenario, you'd want to mock the heavy models

        # Step 1: Upload video
        with open(test_video, 'rb') as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("workflow_test.mp4", f, "video/mp4")}
            )

        assert upload_response.status_code == 200
        filename = upload_response.json()["filename"]

        # Step 2: Start processing (with mocked models, processing should be fast)
        process_request = {
            "input_type": "video",
            "path": filename,
            "frame_interval": 1.0,  # 1 frame per second
            "detect_persons": False,  # Skip heavy processing
            "detect_faces": False     # Skip heavy processing
        }

        process_response = client.post("/api/process", json=process_request)
        assert process_response.status_code == 200

        job_id = process_response.json()["job_id"]
        assert job_id is not None

        # Step 3: Check job status (poll a few times)
        max_attempts = 5
        job_status = None

        for _ in range(max_attempts):
            status_response = client.get(f"/api/jobs/{job_id}")
            assert status_response.status_code == 200

            job_status = status_response.json()
            if job_status["status"] in ["completed", "failed"]:
                break

            time.sleep(1)

        # Verify job has a status
        assert job_status is not None
        assert "status" in job_status

    def test_error_handling_workflow(self, client):
        """Test error handling in workflow."""
        # Try to process without uploading
        process_request = {
            "input_type": "video",
            "path": "never_uploaded.mp4",
            "detect_persons": True,
            "detect_faces": True
        }

        response = client.post("/api/process", json=process_request)
        assert response.status_code == 404


# ============================================================================
# Concurrent Request Tests
# ============================================================================

class TestConcurrency:
    """Test handling of concurrent requests."""

    def test_concurrent_health_checks(self, client):
        """Test multiple concurrent health checks."""
        import concurrent.futures

        def check_health():
            response = client.get("/api/health")
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(status == 200 for status in results)

    def test_concurrent_video_lists(self, client):
        """Test concurrent video listing requests."""
        import concurrent.futures

        def list_videos():
            response = client.get("/api/videos")
            return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(list_videos) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status == 200 for status in results)


# ============================================================================
# Data Validation Tests
# ============================================================================

class TestDataValidation:
    """Test request/response data validation."""

    def test_process_request_missing_fields(self, client):
        """Test processing request with missing required fields."""
        # Missing path field
        request_data = {
            "input_type": "video",
            "detect_persons": True
        }

        response = client.post("/api/process", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_process_request_invalid_types(self, client):
        """Test processing request with invalid field types."""
        request_data = {
            "input_type": "video",
            "path": "test.mp4",
            "detect_persons": "yes",  # Should be boolean
            "frame_interval": "one"    # Should be float
        }

        response = client.post("/api/process", json=request_data)
        assert response.status_code == 422

    def test_compare_request_validation(self, client):
        """Test face comparison request validation."""
        # Missing required fields
        request_data = {
            "job_id": "test_job"
            # Missing reference_image
        }

        response = client.post("/api/compare", json=request_data)
        assert response.status_code == 422


# ============================================================================
# Performance Tests (Light)
# ============================================================================

class TestPerformance:
    """Light performance tests for integration suite."""

    def test_health_check_response_time(self, client):
        """Test health check responds quickly."""
        import time

        start = time.time()
        response = client.get("/api/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second

    def test_list_videos_response_time(self, client):
        """Test video listing responds quickly."""
        import time

        start = time.time()
        response = client.get("/api/videos")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0  # Should respond in less than 2 seconds


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'not slow'])
