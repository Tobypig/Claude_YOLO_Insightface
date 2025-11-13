"""
Load tests for Video Frame Person & Face Detection API.
Using Locust for performance and stress testing.

Run with:
    locust -f tests/locustfile.py --host=http://localhost:8000
"""
import base64
import json
import random
import time
from pathlib import Path
from locust import HttpUser, task, between, events
import tempfile
import cv2
import numpy as np


# Global test video path
TEST_VIDEO_PATH = None


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize test data before load test starts."""
    global TEST_VIDEO_PATH

    # Create a small test video
    temp_dir = Path(tempfile.mkdtemp())
    video_path = temp_dir / "load_test_video.mp4"

    # Create minimal video (10 frames, 320x240)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 10.0, (320, 240))

    for i in range(10):
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        out.write(frame)

    out.release()

    TEST_VIDEO_PATH = video_path
    print(f"[Load Test] Test video created at: {video_path}")


class VideoProcessingUser(HttpUser):
    """Simulates a user interacting with the video processing API."""

    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts."""
        self.uploaded_videos = []
        self.job_ids = []

    @task(10)
    def health_check(self):
        """Test health check endpoint (most frequent)."""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data}")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)
    def list_videos(self):
        """Test listing videos."""
        with self.client.get("/api/videos", catch_response=True) as response:
            if response.status_code == 200:
                videos = response.json()
                response.success()
            else:
                response.failure(f"Failed to list videos: {response.status_code}")

    @task(3)
    def list_folders(self):
        """Test listing folders."""
        with self.client.get("/api/folders", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list folders: {response.status_code}")

    @task(2)
    def upload_video(self):
        """Test video upload."""
        if TEST_VIDEO_PATH is None or not TEST_VIDEO_PATH.exists():
            return

        filename = f"load_test_{random.randint(1000, 9999)}.mp4"

        with open(TEST_VIDEO_PATH, 'rb') as video_file:
            files = {'file': (filename, video_file, 'video/mp4')}

            with self.client.post("/api/upload", files=files, catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.uploaded_videos.append(data['path'])
                    response.success()
                else:
                    response.failure(f"Upload failed: {response.status_code}")

    @task(2)
    def process_video(self):
        """Test video processing (lightweight - no detection)."""
        # Use a previously uploaded video or skip
        if not self.uploaded_videos:
            return

        video_path = random.choice(self.uploaded_videos)

        payload = {
            "input_type": "video",
            "path": video_path,
            "frame_interval": 2.0,  # Less frames for faster processing
            "detect_persons": False,  # Skip heavy processing in load test
            "detect_faces": False
        }

        with self.client.post("/api/process", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.job_ids.append(data['job_id'])
                response.success()
            else:
                response.failure(f"Process failed: {response.status_code}")

    @task(4)
    def check_job_status(self):
        """Test checking job status."""
        if not self.job_ids:
            return

        job_id = random.choice(self.job_ids)

        with self.client.get(f"/api/jobs/{job_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Job might have been deleted
                self.job_ids.remove(job_id)
                response.success()
            else:
                response.failure(f"Status check failed: {response.status_code}")

    @task(1)
    def get_job_results(self):
        """Test getting job results."""
        if not self.job_ids:
            return

        job_id = random.choice(self.job_ids)

        with self.client.get(f"/api/results/{job_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                # 404 is OK if job not completed or deleted
                response.success()
            else:
                response.failure(f"Results fetch failed: {response.status_code}")


class HeavyProcessingUser(HttpUser):
    """
    Simulates users doing heavy processing (person/face detection).
    Use sparingly in load tests.
    """

    wait_time = between(5, 10)

    def on_start(self):
        self.uploaded_videos = []

    @task(1)
    def upload_and_process_with_detection(self):
        """Upload and process with detection enabled."""
        if TEST_VIDEO_PATH is None or not TEST_VIDEO_PATH.exists():
            return

        filename = f"heavy_test_{random.randint(1000, 9999)}.mp4"

        # Upload
        with open(TEST_VIDEO_PATH, 'rb') as video_file:
            files = {'file': (filename, video_file, 'video/mp4')}
            upload_response = self.client.post("/api/upload", files=files)

            if upload_response.status_code != 200:
                return

            video_path = upload_response.json()['path']

        # Process with detection
        payload = {
            "input_type": "video",
            "path": video_path,
            "frame_interval": 2.0,
            "detect_persons": True,
            "detect_faces": True
        }

        with self.client.post("/api/process", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Heavy processing failed: {response.status_code}")


class ReadOnlyUser(HttpUser):
    """
    Simulates users only reading data (no uploads/processing).
    Good for testing read performance.
    """

    wait_time = between(0.5, 2)

    @task(20)
    def health_check(self):
        self.client.get("/api/health")

    @task(10)
    def list_videos(self):
        self.client.get("/api/videos")

    @task(10)
    def list_folders(self):
        self.client.get("/api/folders")

    @task(5)
    def check_root(self):
        self.client.get("/")


# ============================================================================
# Custom Load Test Scenarios
# ============================================================================

class SpikeTestUser(HttpUser):
    """
    Simulate spike in traffic (sudden burst of requests).
    """

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_health_checks(self):
        """Rapid-fire health checks."""
        self.client.get("/api/health")


class StressTestUser(HttpUser):
    """
    Simulate stress conditions (sustained high load).
    """

    wait_time = between(0.1, 1)

    @task(5)
    def continuous_video_listing(self):
        self.client.get("/api/videos")

    @task(3)
    def continuous_folder_listing(self):
        self.client.get("/api/folders")

    @task(2)
    def continuous_health_checks(self):
        self.client.get("/api/health")


# ============================================================================
# Load Test Configurations
# ============================================================================

"""
Example load test commands:

1. Basic load test (10 users):
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --users 10 --spawn-rate 2 --run-time 60s

2. Heavy load test (100 users):
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --users 100 --spawn-rate 10 --run-time 300s

3. Spike test:
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --user-classes SpikeTestUser \\
          --users 500 --spawn-rate 100 --run-time 30s

4. Stress test:
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --user-classes StressTestUser \\
          --users 200 --spawn-rate 20 --run-time 600s

5. Read-only test:
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --user-classes ReadOnlyUser \\
          --users 50 --spawn-rate 10 --run-time 120s

6. Headless mode (no web UI):
   locust -f tests/locustfile.py --host=http://localhost:8000 \\
          --headless --users 50 --spawn-rate 5 --run-time 120s \\
          --html report.html --csv results

Performance targets:
- Health check: < 100ms p95
- List videos: < 500ms p95
- Upload (small video): < 2s p95
- Process (no detection): < 5s p95
- Job status: < 200ms p95
"""
