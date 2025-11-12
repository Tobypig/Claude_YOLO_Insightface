#!/bin/bash

# Test runner script for Video Frame Person & Face Detection System

set -e

echo "🧪 Running Tests for Video Frame Person & Face Detection System"
echo "================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend tests
echo "📦 Backend Tests"
echo "----------------"
cd backend

if [ ! -d "venv" ]; then
    echo -e "${RED}✗${NC} Virtual environment not found. Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}ℹ${NC} Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov httpx
fi

echo ""
echo "Running unit tests..."
python -m pytest test_utils.py -v

echo ""
echo "Running API integration tests..."
python -m pytest test_api.py -v

echo ""
echo "Running all tests with coverage..."
python -m pytest test_*.py --cov=. --cov-report=term-missing --cov-report=html

cd ..

echo ""
echo "================================================================"
echo -e "${GREEN}✓ All tests completed!${NC}"
echo "================================================================"
echo ""
echo "Coverage report generated at: backend/htmlcov/index.html"
echo ""
