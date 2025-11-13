"""
Configuration management for the Video Frame Person & Face Detection System.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Directories
    VIDEO_DIR: Path = Field(default=Path("./data/videos"))
    CLIPS_DIR: Path = Field(default=Path("./data/clips"))
    OUTPUT_DIR: Path = Field(default=Path("./data/output"))
    MODELS_DIR: Path = Field(default=Path("./models"))

    # Upload settings
    MAX_UPLOAD_SIZE: int = Field(default=2147483648)  # 2GB
    ALLOWED_VIDEO_FORMATS: str = Field(default="mp4,mov,avi,mkv")

    # Model settings
    YOLO_MODEL: str = Field(default="yolov8n.pt")
    INSIGHTFACE_MODEL: str = Field(default="buffalo_l")
    DEVICE: str = Field(default="cuda")

    # Detection thresholds
    PERSON_CONFIDENCE_THRESHOLD: float = Field(default=0.5)
    FACE_CONFIDENCE_THRESHOLD: float = Field(default=0.5)
    FACE_SIMILARITY_THRESHOLD: float = Field(default=0.7)

    # Processing settings
    MAX_CONCURRENT_JOBS: int = Field(default=3)
    FRAME_EXTRACTION_QUALITY: int = Field(default=2)

    # API settings
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_RELOAD: bool = Field(default=True)

    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:3001")

    # Redis settings
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def allowed_formats(self) -> List[str]:
        """Get list of allowed video formats."""
        return [fmt.strip() for fmt in self.ALLOWED_VIDEO_FORMATS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.VIDEO_DIR, self.CLIPS_DIR, self.OUTPUT_DIR, self.MODELS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on startup
settings.ensure_directories()
