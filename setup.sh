#!/bin/bash

# Setup script for Video Frame Person & Face Detection System

set -e  # Exit on error

echo "🎥 Video Frame Person & Face Detection System - Setup"
echo "===================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print colored message
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check system dependencies
echo "1. Checking system dependencies..."
echo ""

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm found: v$NPM_VERSION"
else
    print_error "npm not found. Please install npm"
    exit 1
fi

if command_exists ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
    print_success "ffmpeg found: $FFMPEG_VERSION"
else
    print_error "ffmpeg not found. Please install ffmpeg"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi

echo ""

# Setup backend
echo "2. Setting up backend..."
echo ""

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
else
    print_info ".env file already exists"
fi

# Download models (optional - they will auto-download on first run)
print_info "Models will be downloaded automatically on first run"

cd ..

echo ""

# Setup frontend
echo "3. Setting up frontend..."
echo ""

cd frontend

# Install dependencies
print_info "Installing npm dependencies..."
npm install
print_success "npm dependencies installed"

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    print_info "Creating .env.local file from template..."
    cp .env.local.example .env.local
    print_success ".env.local file created"
else
    print_info ".env.local file already exists"
fi

cd ..

echo ""

# Summary
echo "===================================================="
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo "===================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "For Docker setup:"
echo "   docker-compose up -d"
echo ""
