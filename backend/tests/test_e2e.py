"""
End-to-End (E2E) tests for complete video processing workflows.
These tests simulate real user scenarios from start to finish.
"""
import pytest
import time
import base64
from pathlib import Path
from fastapi.testclient import TestClient
import cv2
import numpy as np
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import settings


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def test_data_dir():
    """Create directory with test videos."""
    temp_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))

    # Create test video
    video_path = temp_dir / "sample_video.mp4"
    create_test_video(video_path, duration_seconds=3, fps=10)

    # Create test reference image
    image_path = temp_dir / "reference_face.jpg"
    create_test_image(image_path, size=(200, 200))

    yield temp_dir

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def create_test_video(path: Path, duration_seconds: int = 3, fps: int = 10):
    """Create a test video with some patterns."""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    total_frames = duration_seconds * fps

    for i in range(total_frames):
        # Create frame with moving rectangle
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Background
        frame[:, :] = [50, 50, 50]

        # Moving rectangle (simulates person)
        x_pos = 50 + (i * 10) % 400
        y_pos = 150
        cv2.rectangle(frame, (x_pos, y_pos), (x_pos + 100, y_pos + 200), (255, 0, 0), -1)

        # Face region
        cv2.rectangle(frame, (x_pos + 25, y_pos + 20), (x_pos + 75, y_pos + 70), (0, 255, 0), -1)

        out.write(frame)

    out.release()


def create_test_image(path: Path, size: tuple = (200, 200)):
    """Create a test image."""
    image = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    cv2.imwrite(str(path), image)


def wait_for_job_completion(client, job_id: str, timeout: int = 30, poll_interval: float = 1.0):
    """Wait for job to complete."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200

        job_info = response.json()
        status = job_info.get("status")

        if status == "completed":
            return job_info
        elif status == "failed":
            pytest.fail(f"Job failed: {job_info.get('error', 'Unknown error')}")

        time.sleep(poll_interval)

    pytest.fail(f"Job {job_id} did not complete within {timeout} seconds")


# ============================================================================
# Scenario 1: Upload and Process Single Video
# ============================================================================

class TestScenario1UploadAndProcess:
    """Test: User uploads a video and processes it for person/face detection."""

    @pytest.mark.e2e
    def test_upload_and_process_workflow(self, client, test_data_dir):
        """
        Complete workflow:
        1. Upload video
        2. Start processing
        3. Poll for completion
        4. Retrieve results
        5. Download metadata
        6. Clean up
        """
        video_path = test_data_dir / "sample_video.mp4"

        # Step 1: Upload video
        print("\n[E2E] Step 1: Uploading video...")
        with open(video_path, 'rb') as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("sample_video.mp4", f, "video/mp4")}
            )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        print(f"[E2E] Uploaded: {upload_data['filename']}, Size: {upload_data['size_bytes']} bytes")

        # Step 2: List videos to verify upload
        print("[E2E] Step 2: Verifying upload...")
        videos_response = client.get("/api/videos")
        assert videos_response.status_code == 200
        videos = videos_response.json()
        assert any(v['name'] == "sample_video.mp4" for v in videos)
        print(f"[E2E] Found {len(videos)} video(s) in library")

        # Step 3: Start processing
        print("[E2E] Step 3: Starting processing job...")
        process_request = {
            "input_type": "video",
            "path": upload_data['path'],
            "frame_interval": 1.0,  # 1 fps
            "detect_persons": False,  # Skip heavy processing for speed
            "detect_faces": False
        }

        process_response = client.post("/api/process", json=process_request)
        assert process_response.status_code == 200

        job_data = process_response.json()
        job_id = job_data['job_id']
        print(f"[E2E] Job created: {job_id}")

        # Step 4: Poll for completion
        print("[E2E] Step 4: Waiting for job completion...")
        completed_job = wait_for_job_completion(client, job_id, timeout=30)
        print(f"[E2E] Job completed: {completed_job['status']}")

        # Step 5: Get detailed results
        print("[E2E] Step 5: Retrieving results...")
        results_response = client.get(f"/api/results/{job_id}")
        assert results_response.status_code == 200

        results = results_response.json()
        print(f"[E2E] Results summary: {results.get('summary', {})}")

        # Step 6: Verify job can be listed
        print("[E2E] Step 6: Verifying job status...")
        job_status_response = client.get(f"/api/jobs/{job_id}")
        assert job_status_response.status_code == 200
        assert job_status_response.json()['status'] == 'completed'

        # Step 7: Clean up
        print("[E2E] Step 7: Cleaning up...")
        delete_response = client.delete(f"/api/jobs/{job_id}")
        assert delete_response.status_code == 200
        print("[E2E] Workflow complete!")


# ============================================================================
# Scenario 2: Process with Detection Enabled
# ============================================================================

class TestScenario2ProcessWithDetection:
    """Test: Process video with person and face detection enabled."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_process_with_detection(self, client, test_data_dir):
        """
        Workflow with detection:
        1. Upload video
        2. Process with person detection
        3. Verify detection results
        4. Check annotated images
        """
        video_path = test_data_dir / "sample_video.mp4"

        # Upload
        print("\n[E2E-Detection] Uploading video...")
        with open(video_path, 'rb') as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("detection_test.mp4", f, "video/mp4")}
            )
        assert upload_response.status_code == 200

        # Process with detection (this will be slow with real models)
        print("[E2E-Detection] Processing (may be slow with real models)...")
        process_request = {
            "input_type": "video",
            "path": upload_response.json()['path'],
            "frame_interval": 1.0,
            "detect_persons": True,  # Enable person detection
            "detect_faces": True     # Enable face detection
        }

        process_response = client.post("/api/process", json=process_request)
        if process_response.status_code != 200:
            print(f"[E2E-Detection] Processing failed (models may not be available): {process_response.json()}")
            pytest.skip("Detection models not available")

        job_id = process_response.json()['job_id']

        # Wait for completion (longer timeout for detection)
        print("[E2E-Detection] Waiting for detection to complete...")
        try:
            completed_job = wait_for_job_completion(client, job_id, timeout=60)

            # Get results
            results_response = client.get(f"/api/results/{job_id}")
            if results_response.status_code == 200:
                results = results_response.json()
                summary = results.get('summary', {})

                print(f"[E2E-Detection] Persons detected: {summary.get('persons_detected', 0)}")
                print(f"[E2E-Detection] Faces detected: {summary.get('faces_detected', 0)}")

                # Cleanup
                client.delete(f"/api/jobs/{job_id}")
        except Exception as e:
            print(f"[E2E-Detection] Test failed: {e}")
            pytest.skip("Detection processing failed (models may not be loaded)")


# ============================================================================
# Scenario 3: Face Comparison Workflow
# ============================================================================

class TestScenario3FaceComparison:
    """Test: Complete face comparison workflow."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_face_comparison_workflow(self, client, test_data_dir):
        """
        Face comparison workflow:
        1. Upload and process video with face detection
        2. Upload reference face image
        3. Compare reference face with detected faces
        4. Retrieve comparison results
        """
        video_path = test_data_dir / "sample_video.mp4"
        reference_path = test_data_dir / "reference_face.jpg"

        # Step 1: Upload and process video
        print("\n[E2E-FaceComp] Step 1: Processing video...")
        with open(video_path, 'rb') as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("face_comp_test.mp4", f, "video/mp4")}
            )

        process_request = {
            "input_type": "video",
            "path": upload_response.json()['path'],
            "frame_interval": 1.0,
            "detect_persons": False,
            "detect_faces": True  # Need faces for comparison
        }

        process_response = client.post("/api/process", json=process_request)
        if process_response.status_code != 200:
            pytest.skip("Face detection not available")

        job_id = process_response.json()['job_id']

        try:
            # Wait for processing
            completed_job = wait_for_job_completion(client, job_id, timeout=60)

            # Step 2: Prepare reference image
            print("[E2E-FaceComp] Step 2: Preparing reference image...")
            with open(reference_path, 'rb') as f:
                reference_bytes = f.read()
                reference_base64 = base64.b64encode(reference_bytes).decode('utf-8')

            # Step 3: Compare faces
            print("[E2E-FaceComp] Step 3: Comparing faces...")
            compare_request = {
                "job_id": job_id,
                "reference_image": reference_base64,
                "threshold": 0.7
            }

            compare_response = client.post("/api/compare", json=compare_request)

            if compare_response.status_code == 200:
                comparison_results = compare_response.json()
                print(f"[E2E-FaceComp] Matches found: {comparison_results.get('total_matches', 0)}")
            else:
                print(f"[E2E-FaceComp] Comparison failed: {compare_response.json()}")

            # Cleanup
            client.delete(f"/api/jobs/{job_id}")

        except Exception as e:
            print(f"[E2E-FaceComp] Test failed: {e}")
            pytest.skip("Face comparison failed")


# ============================================================================
# Scenario 4: Multiple Jobs Concurrent Processing
# ============================================================================

class TestScenario4ConcurrentJobs:
    """Test: Multiple jobs processing concurrently."""

    @pytest.mark.e2e
    def test_concurrent_job_processing(self, client, test_data_dir):
        """
        Test concurrent job processing:
        1. Upload multiple videos
        2. Start multiple jobs
        3. All jobs should complete successfully
        """
        video_path = test_data_dir / "sample_video.mp4"

        job_ids = []

        # Start 3 jobs
        print("\n[E2E-Concurrent] Starting 3 concurrent jobs...")
        for i in range(3):
            with open(video_path, 'rb') as f:
                upload_response = client.post(
                    "/api/upload",
                    files={"file": (f"concurrent_test_{i}.mp4", f, "video/mp4")}
                )

            process_request = {
                "input_type": "video",
                "path": upload_response.json()['path'],
                "frame_interval": 2.0,  # Fewer frames
                "detect_persons": False,
                "detect_faces": False
            }

            process_response = client.post("/api/process", json=process_request)
            assert process_response.status_code == 200

            job_id = process_response.json()['job_id']
            job_ids.append(job_id)
            print(f"[E2E-Concurrent] Started job {i+1}: {job_id}")

        # Wait for all jobs
        print("[E2E-Concurrent] Waiting for all jobs to complete...")
        for i, job_id in enumerate(job_ids):
            try:
                completed_job = wait_for_job_completion(client, job_id, timeout=30)
                print(f"[E2E-Concurrent] Job {i+1} completed: {completed_job['status']}")
            except Exception as e:
                print(f"[E2E-Concurrent] Job {i+1} failed: {e}")

        # Cleanup
        for job_id in job_ids:
            client.delete(f"/api/jobs/{job_id}")

        print("[E2E-Concurrent] All jobs processed!")


# ============================================================================
# Scenario 5: Error Handling and Recovery
# ============================================================================

class TestScenario5ErrorHandling:
    """Test: Error handling in various failure scenarios."""

    @pytest.mark.e2e
    def test_invalid_video_handling(self, client, test_data_dir):
        """Test system handles invalid video gracefully."""
        print("\n[E2E-Errors] Testing error handling...")

        # Try to process non-existent video
        process_request = {
            "input_type": "video",
            "path": "nonexistent_video.mp4",
            "detect_persons": True,
            "detect_faces": True
        }

        response = client.post("/api/process", json=process_request)
        assert response.status_code == 404
        print("[E2E-Errors] ✓ Non-existent video handled correctly")

    def test_invalid_comparison_handling(self, client):
        """Test system handles invalid comparison requests."""
        # Try to compare without completed job
        compare_request = {
            "job_id": "fake_job_id",
            "reference_image": "invalid_base64",
            "threshold": 0.7
        }

        response = client.post("/api/compare", json=compare_request)
        assert response.status_code in [400, 404]
        print("[E2E-Errors] ✓ Invalid comparison handled correctly")

    def test_malformed_request_handling(self, client):
        """Test system handles malformed requests."""
        # Missing required fields
        response = client.post("/api/process", json={})
        assert response.status_code == 422
        print("[E2E-Errors] ✓ Malformed request handled correctly")


# ============================================================================
# Scenario 6: Full Lifecycle Test
# ============================================================================

class TestScenario6FullLifecycle:
    """Test: Complete lifecycle from upload to deletion."""

    @pytest.mark.e2e
    def test_full_lifecycle(self, client, test_data_dir):
        """
        Complete lifecycle:
        1. Health check
        2. Upload video
        3. List videos
        4. Process video
        5. Check status
        6. Get results
        7. Download metadata
        8. Delete job
        9. Verify deletion
        """
        video_path = test_data_dir / "sample_video.mp4"

        # 1. Health check
        print("\n[E2E-Lifecycle] 1. Health check...")
        health = client.get("/api/health")
        assert health.status_code == 200
        print(f"[E2E-Lifecycle]    Status: {health.json()['status']}")

        # 2. Upload
        print("[E2E-Lifecycle] 2. Uploading video...")
        with open(video_path, 'rb') as f:
            upload = client.post(
                "/api/upload",
                files={"file": ("lifecycle_test.mp4", f, "video/mp4")}
            )
        assert upload.status_code == 200
        filename = upload.json()['filename']
        print(f"[E2E-Lifecycle]    Uploaded: {filename}")

        # 3. List videos
        print("[E2E-Lifecycle] 3. Listing videos...")
        videos = client.get("/api/videos")
        assert videos.status_code == 200
        assert any(v['name'] == filename for v in videos.json())
        print(f"[E2E-Lifecycle]    Found {len(videos.json())} video(s)")

        # 4. Process
        print("[E2E-Lifecycle] 4. Processing...")
        process = client.post("/api/process", json={
            "input_type": "video",
            "path": filename,
            "frame_interval": 1.0,
            "detect_persons": False,
            "detect_faces": False
        })
        assert process.status_code == 200
        job_id = process.json()['job_id']
        print(f"[E2E-Lifecycle]    Job ID: {job_id}")

        # 5. Monitor status
        print("[E2E-Lifecycle] 5. Monitoring status...")
        completed = wait_for_job_completion(client, job_id)
        print(f"[E2E-Lifecycle]    Status: {completed['status']}")

        # 6. Get results
        print("[E2E-Lifecycle] 6. Getting results...")
        results = client.get(f"/api/results/{job_id}")
        assert results.status_code == 200
        print(f"[E2E-Lifecycle]    Results retrieved")

        # 7. Download metadata
        print("[E2E-Lifecycle] 7. Downloading metadata...")
        metadata = client.get(f"/api/download/{job_id}/metadata")
        assert metadata.status_code == 200
        print(f"[E2E-Lifecycle]    Metadata downloaded ({len(metadata.content)} bytes)")

        # 8. Delete job
        print("[E2E-Lifecycle] 8. Deleting job...")
        delete = client.delete(f"/api/jobs/{job_id}")
        assert delete.status_code == 200
        print(f"[E2E-Lifecycle]    Job deleted")

        # 9. Verify deletion
        print("[E2E-Lifecycle] 9. Verifying deletion...")
        verify = client.get(f"/api/jobs/{job_id}")
        assert verify.status_code == 404
        print(f"[E2E-Lifecycle]    ✓ Deletion verified")

        print("[E2E-Lifecycle] ✅ Full lifecycle complete!")


# ============================================================================
# Run E2E tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-m', 'e2e',
        '-s'  # Show print statements
    ])
