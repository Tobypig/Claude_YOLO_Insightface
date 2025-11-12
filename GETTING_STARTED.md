# 🚀 Getting Started

This guide will help you set up and run the Video Frame Person & Face Detection System.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **ffmpeg** - For video processing
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: [Download](https://ffmpeg.org/download.html)
- **(Optional) CUDA** - For GPU acceleration

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Check system dependencies
- Create Python virtual environment
- Install all backend dependencies
- Install all frontend dependencies
- Create environment configuration files

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env if needed (optional)
nano .env
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local if needed (optional)
nano .env.local
```

## Running the Application

### Development Mode

#### Start Both Services Together

```bash
chmod +x start-dev.sh
./start-dev.sh
```

This will start both backend and frontend servers.

#### Start Services Separately

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Production Mode with Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Accessing the Application

Once running, you can access:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health

## First-Time Setup

### Model Downloads

The first time you run the application, it will automatically download:

1. **YOLOv8 Model** (~6 MB) - For person detection
2. **InsightFace buffalo_l Model** (~200 MB) - For face detection

This may take a few minutes depending on your internet connection.

### Test Video

You can test the system with any video file. Supported formats:
- MP4
- MOV
- AVI
- MKV

## Basic Usage

### 1. Process a Video

1. Go to http://localhost:3000/process
2. Choose an input method:
   - **Upload Video**: Drag & drop or select a video file
   - **Video Library**: Select from previously uploaded videos
   - **Video Folder**: Process multiple videos at once

3. Configure frame extraction:
   - **Regular Interval**: Extract frames every N seconds
   - **Specific Timestamps**: Enter comma-separated timestamps
   - **Key Frames**: Extract only scene changes

4. Select detection options:
   - ☑️ Enable Person Detection (YOLO)
   - ☑️ Enable Face Detection (InsightFace)

5. Click **Start Processing**

### 2. View Results

1. Go to http://localhost:3000/jobs
2. Click on a completed job
3. Click **View Results**
4. Browse extracted frames with detection overlays
5. Download metadata and crops

### 3. Compare Faces

1. Go to http://localhost:3000/compare/[job_id]
2. Upload a reference face image
3. Adjust similarity threshold (0.7 recommended)
4. Click **Compare Faces**
5. View matching faces with similarity scores

## Configuration

### Backend Configuration (`backend/.env`)

Key settings:

```env
# Device for inference (cuda or cpu)
DEVICE=cuda

# Model paths
YOLO_MODEL=yolov8n.pt
INSIGHTFACE_MODEL=buffalo_l

# Detection thresholds (0.0 - 1.0)
PERSON_CONFIDENCE_THRESHOLD=0.5
FACE_CONFIDENCE_THRESHOLD=0.5
FACE_SIMILARITY_THRESHOLD=0.7

# Processing settings
MAX_CONCURRENT_JOBS=3
FRAME_EXTRACTION_QUALITY=2  # 1-31, lower is better
```

### Frontend Configuration (`frontend/.env.local`)

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Maximum upload size (bytes)
NEXT_PUBLIC_MAX_UPLOAD_SIZE=2147483648  # 2GB

# Enable face comparison feature
NEXT_PUBLIC_ENABLE_FACE_COMPARISON=true
```

## GPU Support

### For Development

1. Install CUDA toolkit (version compatible with your GPU)
2. Install GPU-enabled dependencies:
```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```
3. Set `DEVICE=cuda` in `backend/.env`

### For Docker

1. Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
2. Uncomment the GPU sections in `docker-compose.yml`
3. Run: `docker-compose up -d`

## Troubleshooting

### Backend Issues

**Problem**: "CUDA out of memory"
```bash
# Solution: Use CPU mode
export DEVICE=cpu
```

**Problem**: "ffmpeg not found"
```bash
# Install ffmpeg (see Prerequisites section)
```

**Problem**: "No module named 'ultralytics'"
```bash
# Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Problem**: "Cannot connect to backend"
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Problem**: "Module not found"
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules
npm install
```

### Docker Issues

**Problem**: "Port already in use"
```bash
# Stop existing containers
docker-compose down

# Or change ports in docker-compose.yml
```

## Next Steps

- Read the full [README.md](README.md) for detailed features
- Check API documentation at http://localhost:8000/docs
- Explore example use cases in the README
- Configure advanced settings in `.env` files

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review [README.md](README.md)
- Open an issue on GitHub

## Development

### Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── config.py        # Configuration
│   ├── processors/      # Processing modules
│   └── utils/           # Utility functions
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Pages
│       ├── components/  # React components
│       ├── lib/         # API client & utils
│       └── types/       # TypeScript types
└── docker-compose.yml   # Docker orchestration
```

### Making Changes

1. Backend changes: Restart the uvicorn server (auto-reloads in dev mode)
2. Frontend changes: Hot reload is automatic
3. Configuration changes: Restart services

### Running Tests

```bash
# Backend tests (if available)
cd backend
pytest

# Frontend tests (if available)
cd frontend
npm test
```

Happy coding! 🎉
