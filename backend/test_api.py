"""
Integration tests for the Video Frame Person & Face Detection API
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "device" in data
        assert "models" in data


class TestVideoEndpoints:
    """Test video listing endpoints"""

    def test_list_videos(self):
        """Test listing available videos"""
        response = client.get("/api/videos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_folders(self):
        """Test listing available folders"""
        response = client.get("/api/folders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestJobEndpoints:
    """Test job processing endpoints"""

    def test_process_invalid_input_type(self):
        """Test processing with invalid input type"""
        response = client.post(
            "/api/process",
            json={
                "input_type": "invalid",
                "path": "test.mp4",
                "detect_persons": True,
                "detect_faces": True
            }
        )
        assert response.status_code == 400

    def test_process_nonexistent_video(self):
        """Test processing with non-existent video"""
        response = client.post(
            "/api/process",
            json={
                "input_type": "video",
                "path": "nonexistent.mp4",
                "detect_persons": True,
                "detect_faces": True
            }
        )
        assert response.status_code == 404

    def test_get_nonexistent_job(self):
        """Test getting status of non-existent job"""
        response = client.get("/api/jobs/nonexistent_job_id")
        assert response.status_code == 404


class TestComparisonEndpoints:
    """Test face comparison endpoints"""

    def test_compare_nonexistent_job(self):
        """Test comparison with non-existent job"""
        response = client.post(
            "/api/compare",
            json={
                "job_id": "nonexistent",
                "reference_image": "base64encodedimage",
                "threshold": 0.7
            }
        )
        assert response.status_code == 404


class TestDownloadEndpoints:
    """Test download endpoints"""

    def test_download_invalid_file_type(self):
        """Test download with invalid file type"""
        response = client.get("/api/download/test_job/invalid_type")
        assert response.status_code in [400, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
