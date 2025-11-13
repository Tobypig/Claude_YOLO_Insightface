"""
Logging configuration for the application.
"""
import sys
from loguru import logger
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Configure logging for the application.

    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # Add file handler for all logs
    logger.add(
        log_path / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    # Add file handler for errors only
    logger.add(
        log_path / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="90 days",
        compression="zip"
    )

    # Add file handler for API requests
    logger.add(
        log_path / "api_requests.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[request_id]} | {message}",
        level="INFO",
        rotation="20 MB",
        retention="14 days",
        compression="zip",
        filter=lambda record: "request_id" in record["extra"]
    )

    logger.info("Logging configured successfully")


# Middleware for request logging
class RequestLoggingMiddleware:
    """Middleware to log all API requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            import uuid
            from time import time

            request_id = str(uuid.uuid4())
            start_time = time()

            # Log request
            logger.bind(request_id=request_id).info(
                f"Request: {scope['method']} {scope['path']}"
            )

            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time() - start_time
                    status_code = message["status"]

                    # Log response
                    logger.bind(request_id=request_id).info(
                        f"Response: {status_code} - Duration: {duration:.3f}s"
                    )

                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# Performance monitoring
class PerformanceMonitor:
    """Monitor and log performance metrics"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "total_processing_time": 0,
            "total_frames_processed": 0,
            "total_persons_detected": 0,
            "total_faces_detected": 0,
        }

    def log_request(self, duration: float):
        """Log API request metrics"""
        self.metrics["total_requests"] += 1
        self.metrics["total_processing_time"] += duration

        if self.metrics["total_requests"] % 100 == 0:
            avg_time = self.metrics["total_processing_time"] / self.metrics["total_requests"]
            logger.info(
                f"Performance: {self.metrics['total_requests']} requests, "
                f"avg time: {avg_time:.3f}s"
            )

    def log_job_completion(self, frames: int, persons: int, faces: int, duration: float):
        """Log job completion metrics"""
        self.metrics["total_frames_processed"] += frames
        self.metrics["total_persons_detected"] += persons
        self.metrics["total_faces_detected"] += faces

        logger.info(
            f"Job completed: {frames} frames, {persons} persons, {faces} faces "
            f"in {duration:.2f}s"
        )

    def get_metrics(self):
        """Get current metrics"""
        return self.metrics.copy()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
