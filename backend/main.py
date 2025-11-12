"""
FastAPI main application for Video Frame Person & Face Detection System.
"""
import base64
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
import json
import os

from config import settings
from processors.video_processor import VideoProcessor
from utils.video_utils import validate_video_file, get_videos_in_folder
from logging_config import setup_logging, RequestLoggingMiddleware, performance_monitor

# Initialize FastAPI app
app = FastAPI(
    title="Video Frame Person & Face Detection API",
    description="REST API for video frame extraction, person detection, and face recognition",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "path": str(request.url.path)
        }
    )

# Initialize video processor
video_processor = None

# Job storage (in production, use a database)
jobs_db: Dict[str, Dict[str, Any]] = {}


# Pydantic models
class ProcessRequest(BaseModel):
    """Request model for video processing."""
    input_type: str = Field(..., description="'video' or 'folder'")
    path: str = Field(..., description="Path to video file or folder")
    timestamps: Optional[List[float]] = Field(None, description="Specific timestamps in seconds")
    frame_interval: Optional[float] = Field(None, description="Frame extraction interval in seconds")
    extract_keyframes: bool = Field(False, description="Extract key frames")
    detect_persons: bool = Field(True, description="Enable person detection")
    detect_faces: bool = Field(True, description="Enable face detection")


class CompareRequest(BaseModel):
    """Request model for face comparison."""
    job_id: str = Field(..., description="Job ID to compare against")
    reference_image: str = Field(..., description="Base64 encoded reference image")
    threshold: float = Field(0.7, description="Similarity threshold (0.0-1.0)")


class JobResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    message: str


class VideoInfo(BaseModel):
    """Video file information."""
    name: str
    path: str
    size_bytes: int
    format: str


@app.on_event("startup")
async def startup_event():
    """Initialize video processor on startup."""
    global video_processor

    # Setup logging
    setup_logging(log_dir="logs", log_level="INFO")

    logger.info("Starting Video Frame Person & Face Detection API")
    logger.info(f"Device: {settings.DEVICE}")
    logger.info(f"YOLO Model: {settings.YOLO_MODEL}")
    logger.info(f"InsightFace Model: {settings.INSIGHTFACE_MODEL}")

    video_processor = VideoProcessor(
        yolo_model=settings.YOLO_MODEL,
        insightface_model=settings.INSIGHTFACE_MODEL,
        person_threshold=settings.PERSON_CONFIDENCE_THRESHOLD,
        face_threshold=settings.FACE_CONFIDENCE_THRESHOLD,
        device=settings.DEVICE,
        frame_quality=settings.FRAME_EXTRACTION_QUALITY
    )

    logger.info("API startup complete")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Video Frame Person & Face Detection API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device": settings.DEVICE,
        "models": {
            "yolo": settings.YOLO_MODEL,
            "insightface": settings.INSIGHTFACE_MODEL
        }
    }


@app.get("/api/videos", response_model=List[VideoInfo])
async def list_videos():
    """List available video files."""
    video_files = get_videos_in_folder(settings.VIDEO_DIR, settings.allowed_formats)

    videos = []
    for video_path in video_files:
        videos.append(VideoInfo(
            name=video_path.name,
            path=str(video_path.relative_to(settings.VIDEO_DIR)),
            size_bytes=video_path.stat().st_size,
            format=video_path.suffix.lstrip('.')
        ))

    return videos


@app.get("/api/folders")
async def list_folders():
    """List available video folders."""
    if not settings.CLIPS_DIR.exists():
        return []

    folders = []
    for folder_path in settings.CLIPS_DIR.iterdir():
        if folder_path.is_dir():
            video_files = get_videos_in_folder(folder_path, settings.allowed_formats)
            folders.append({
                'name': folder_path.name,
                'path': str(folder_path.relative_to(settings.CLIPS_DIR)),
                'video_count': len(video_files)
            })

    return folders


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file."""
    # Sanitize filename to prevent path traversal attacks
    safe_filename = os.path.basename(file.filename)  # Remove any path components
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._- ")  # Remove dangerous chars

    # Validate file extension
    file_ext = Path(safe_filename).suffix.lstrip('.').lower()
    if file_ext not in settings.allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(settings.allowed_formats)}"
        )

    # Check file size (read in chunks to avoid memory issues)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    # Save file with sanitized filename
    file_path = settings.VIDEO_DIR / safe_filename
    with open(file_path, 'wb') as f:
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE:
                file_path.unlink()  # Delete partial file
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
                )
            f.write(chunk)

    logger.info(f"Uploaded video: {safe_filename} ({file_size} bytes)")

    return {
        "message": "Video uploaded successfully",
        "filename": safe_filename,
        "size_bytes": file_size,
        "path": safe_filename  # Return just the filename, not full path
    }


@app.post("/api/process", response_model=JobResponse)
async def process_video(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """Process video or folder for frame extraction and detection."""
    # Generate job ID
    job_id = f"{Path(request.path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Validate input path
    if request.input_type == "video":
        input_path = settings.VIDEO_DIR / request.path
        if not validate_video_file(input_path, settings.allowed_formats):
            raise HTTPException(status_code=404, detail="Video file not found or invalid")
    elif request.input_type == "folder":
        input_path = settings.CLIPS_DIR / request.path
        if not input_path.exists() or not input_path.is_dir():
            raise HTTPException(status_code=404, detail="Folder not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid input_type. Must be 'video' or 'folder'")

    # Store job info
    jobs_db[job_id] = {
        'job_id': job_id,
        'status': 'processing',
        'input_type': request.input_type,
        'input_path': str(input_path),
        'created_at': datetime.now().isoformat(),
        'config': request.dict()
    }

    # Process in background
    background_tasks.add_task(
        process_job_background,
        job_id,
        request.input_type,
        input_path,
        request.dict()
    )

    logger.info(f"Job {job_id} queued for processing")

    return JobResponse(
        job_id=job_id,
        status="processing",
        message="Processing started"
    )


async def process_job_background(
    job_id: str,
    input_type: str,
    input_path: Path,
    config: Dict[str, Any]
):
    """Background task for processing job."""
    try:
        logger.info(f"Starting background processing for job {job_id}")

        result = video_processor.process_job(
            job_id=job_id,
            input_type=input_type,
            input_path=input_path,
            output_dir=settings.OUTPUT_DIR,
            config=config
        )

        # Update job status
        jobs_db[job_id].update({
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'result': result
        })

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        jobs_db[job_id].update({
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })


@app.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status: processing, completed, failed"),
    limit: int = Query(50, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip for pagination")
):
    """
    List all jobs with optional filtering and pagination.

    Args:
        status: Filter by job status (optional)
        limit: Maximum number of jobs to return (default 50, max 100)
        offset: Number of jobs to skip for pagination (default 0)

    Returns:
        Dictionary with total count and list of jobs
    """
    jobs = list(jobs_db.values())

    # Filter by status if provided
    if status:
        jobs = [j for j in jobs if j.get('status') == status]

    # Sort by created_at (newest first)
    jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # Pagination
    total = len(jobs)
    paginated_jobs = jobs[offset:offset+limit]

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'jobs': paginated_jobs
    }


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and results."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs_db[job_id]


@app.get("/api/results/{job_id}")
async def get_job_results(job_id: str):
    """Get detailed job results with frame data."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = jobs_db[job_id]

    if job_info['status'] != 'completed':
        return {
            'job_id': job_id,
            'status': job_info['status'],
            'message': 'Job not completed yet'
        }

    # Load metadata file
    metadata_path = settings.OUTPUT_DIR / job_id / "metadata.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Results metadata not found")

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    return metadata


@app.get("/api/preview/{job_id}/frame/{frame_id}")
async def get_frame_preview(
    job_id: str,
    frame_id: int,
    show_persons: bool = Query(True),
    show_faces: bool = Query(True),
    person_threshold: Optional[float] = Query(None),
    face_threshold: Optional[float] = Query(None)
):
    """Get frame with overlaid bounding boxes."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    # Determine which image to return
    job_dir = settings.OUTPUT_DIR / job_id

    if show_persons and show_faces:
        # Return combined visualization
        image_path = job_dir / "combined" / f"frame_{frame_id}_all_boxes.jpg"
    elif show_persons:
        # Return person-only visualization
        image_path = job_dir / "persons" / "annotated" / f"frame_{frame_id}_persons.jpg"
    elif show_faces:
        # Return face-only visualization
        image_path = job_dir / "faces" / "annotated" / f"frame_{frame_id}_faces.jpg"
    else:
        # Return original frame
        image_path = job_dir / "frames" / f"frame_{frame_id}.jpg"

    # Find the actual file (frame_id might be part of filename)
    if not image_path.exists():
        # Try to find file with frame_id in name
        parent_dir = image_path.parent
        if parent_dir.exists():
            matches = list(parent_dir.glob(f"*frame_{frame_id}*.jpg"))
            if matches:
                image_path = matches[0]

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Frame preview not found")

    return FileResponse(image_path, media_type="image/jpeg")


@app.post("/api/compare")
async def compare_faces(request: CompareRequest):
    """Compare reference face against detected faces."""
    if request.job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = jobs_db[request.job_id]
    if job_info['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed yet")

    try:
        # Decode base64 image
        image_data = base64.b64decode(request.reference_image)

        # Perform comparison
        result = video_processor.compare_faces(
            job_id=request.job_id,
            reference_image=image_data,
            threshold=request.threshold,
            output_dir=settings.OUTPUT_DIR
        )

        logger.info(f"Face comparison completed for job {request.job_id}")

        return result

    except Exception as e:
        logger.error(f"Face comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{job_id}/{file_type}")
async def download_results(job_id: str, file_type: str):
    """Download job results (metadata, crops, etc.)."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dir = settings.OUTPUT_DIR / job_id

    if file_type == "metadata":
        file_path = job_dir / "metadata.json"
    elif file_type == "person_meta":
        file_path = job_dir / "persons" / "person_meta.csv"
    elif file_type == "face_meta":
        file_path = job_dir / "faces" / "face_meta.csv"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete job and its results."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete output directory
    job_dir = settings.OUTPUT_DIR / job_id
    if job_dir.exists():
        import shutil
        shutil.rmtree(job_dir)

    # Remove from database
    del jobs_db[job_id]

    logger.info(f"Job {job_id} deleted")

    return {"message": "Job deleted successfully", "job_id": job_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
