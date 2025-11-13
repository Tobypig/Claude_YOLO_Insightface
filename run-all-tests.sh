#!/bin/bash

#############################################################################
# Comprehensive Test Runner for Video Frame Person & Face Detection System
# Runs all 5 categories of tests: Unit, Integration, E2E, Frontend, Load
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TEST_START_TIME=$(date +%s)

# Print colored output
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if backend server is running
check_backend() {
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if frontend server is running
check_frontend() {
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

#############################################################################
# Parse command line arguments
#############################################################################

RUN_UNIT=true
RUN_INTEGRATION=true
RUN_E2E=true
RUN_FRONTEND=true
RUN_LOAD=false  # Load tests disabled by default
VERBOSE=false
COVERAGE=false
HEADLESS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            RUN_E2E=false
            RUN_FRONTEND=false
            RUN_LOAD=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            RUN_E2E=false
            RUN_FRONTEND=false
            RUN_LOAD=false
            shift
            ;;
        --e2e-only)
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_FRONTEND=false
            RUN_LOAD=false
            shift
            ;;
        --frontend-only)
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_E2E=false
            RUN_LOAD=false
            shift
            ;;
        --load-only)
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_E2E=false
            RUN_FRONTEND=false
            RUN_LOAD=true
            shift
            ;;
        --with-load)
            RUN_LOAD=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --help)
            echo "Usage: ./run-all-tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit-only         Run only unit tests"
            echo "  --integration-only  Run only integration tests"
            echo "  --e2e-only          Run only E2E tests"
            echo "  --frontend-only     Run only frontend tests"
            echo "  --load-only         Run only load tests"
            echo "  --with-load         Include load tests (default: disabled)"
            echo "  --verbose           Show detailed output"
            echo "  --coverage          Generate coverage reports"
            echo "  --headless          Run tests in headless mode"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run-all-tests.sh                    # Run all tests except load"
            echo "  ./run-all-tests.sh --with-load        # Run all tests including load"
            echo "  ./run-all-tests.sh --unit-only        # Run only unit tests"
            echo "  ./run-all-tests.sh --coverage         # Run with coverage"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

#############################################################################
# Main Test Execution
#############################################################################

print_header "🧪 COMPREHENSIVE TEST SUITE"
print_info "Starting comprehensive test execution..."
echo ""

# Check dependencies
print_info "Checking dependencies..."

if [ ! -d "backend/venv" ]; then
    print_warning "Virtual environment not found. Creating..."
    cd backend && python3 -m venv venv && cd ..
fi

# Activate virtual environment
source backend/venv/bin/activate

# Install test dependencies
print_info "Installing test dependencies..."
pip install -q pytest pytest-asyncio pytest-cov httpx locust 2>/dev/null || true

print_success "Dependencies checked"

#############################################################################
# 1. PROCESSOR UNIT TESTS
#############################################################################

if [ "$RUN_UNIT" = true ]; then
    print_header "1. PROCESSOR UNIT TESTS"
    print_info "Testing individual processor modules..."

    cd backend

    if [ "$COVERAGE" = true ]; then
        if pytest tests/test_processors.py -v --cov=processors --cov-report=html --cov-report=term; then
            print_success "Processor unit tests PASSED"
            ((TESTS_PASSED++))
            print_info "Coverage report generated: backend/htmlcov/index.html"
        else
            print_error "Processor unit tests FAILED"
            ((TESTS_FAILED++))
        fi
    else
        if [ "$VERBOSE" = true ]; then
            pytest tests/test_processors.py -v -s
        else
            pytest tests/test_processors.py -v
        fi

        if [ $? -eq 0 ]; then
            print_success "Processor unit tests PASSED"
            ((TESTS_PASSED++))
        else
            print_error "Processor unit tests FAILED"
            ((TESTS_FAILED++))
        fi
    fi

    cd ..
fi

#############################################################################
# 2. INTEGRATION TESTS
#############################################################################

if [ "$RUN_INTEGRATION" = true ]; then
    print_header "2. INTEGRATION TESTS"
    print_info "Testing API endpoints and workflows..."

    # Check if backend is running
    if ! check_backend; then
        print_warning "Backend not running. Starting test server..."
        cd backend
        uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
        BACKEND_PID=$!
        cd ..

        # Wait for server to start
        sleep 3

        if ! check_backend; then
            print_error "Failed to start backend server"
            kill $BACKEND_PID 2>/dev/null || true
            ((TESTS_FAILED++))
        else
            STARTED_BACKEND=true
        fi
    fi

    if check_backend; then
        cd backend

        if [ "$COVERAGE" = true ]; then
            pytest tests/test_integration.py -v --cov=. --cov-report=html --cov-report=term
        elif [ "$VERBOSE" = true ]; then
            pytest tests/test_integration.py -v -s
        else
            pytest tests/test_integration.py -v
        fi

        if [ $? -eq 0 ]; then
            print_success "Integration tests PASSED"
            ((TESTS_PASSED++))
        else
            print_error "Integration tests FAILED"
            ((TESTS_FAILED++))
        fi

        cd ..

        # Stop backend if we started it
        if [ "$STARTED_BACKEND" = true ]; then
            print_info "Stopping test backend server..."
            kill $BACKEND_PID 2>/dev/null || true
        fi
    fi
fi

#############################################################################
# 3. END-TO-END TESTS
#############################################################################

if [ "$RUN_E2E" = true ]; then
    print_header "3. END-TO-END TESTS"
    print_info "Testing complete user workflows..."

    # Ensure backend is running
    if ! check_backend; then
        print_warning "Backend required for E2E tests. Starting..."
        cd backend
        uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
        BACKEND_PID=$!
        cd ..
        sleep 3
        STARTED_BACKEND=true
    fi

    if check_backend; then
        cd backend

        if [ "$VERBOSE" = true ]; then
            pytest tests/test_e2e.py -v -s -m e2e
        else
            pytest tests/test_e2e.py -v -m e2e
        fi

        if [ $? -eq 0 ]; then
            print_success "E2E tests PASSED"
            ((TESTS_PASSED++))
        else
            print_error "E2E tests FAILED"
            ((TESTS_FAILED++))
        fi

        cd ..

        if [ "$STARTED_BACKEND" = true ]; then
            kill $BACKEND_PID 2>/dev/null || true
        fi
    else
        print_error "Backend not available for E2E tests"
        ((TESTS_FAILED++))
    fi
fi

#############################################################################
# 4. FRONTEND TESTS
#############################################################################

if [ "$RUN_FRONTEND" = true ]; then
    print_header "4. FRONTEND TESTS"
    print_info "Testing React components and pages..."

    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "Dependencies not installed. Running npm install..."
        npm install
    fi

    # Install test dependencies
    print_info "Installing frontend test dependencies..."
    npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest jest-environment-jsdom @types/jest 2>/dev/null || true

    # Run frontend tests
    if [ "$COVERAGE" = true ]; then
        npm test -- --coverage --watchAll=false
    else
        npm test -- --watchAll=false
    fi

    if [ $? -eq 0 ]; then
        print_success "Frontend tests PASSED"
        ((TESTS_PASSED++))
    else
        print_error "Frontend tests FAILED"
        ((TESTS_FAILED++))
    fi

    cd ..
fi

#############################################################################
# 5. LOAD TESTS
#############################################################################

if [ "$RUN_LOAD" = true ]; then
    print_header "5. LOAD TESTS"
    print_info "Running performance and load tests..."

    # Ensure backend is running
    if ! check_backend; then
        print_warning "Backend required for load tests. Starting..."
        cd backend
        uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
        BACKEND_PID=$!
        cd ..
        sleep 3
        STARTED_BACKEND=true
    fi

    if check_backend; then
        print_info "Running load test: 20 users, 60 seconds"
        print_info "Locust web UI: http://localhost:8089"

        cd backend

        # Run load test
        locust -f tests/locustfile.py \\
            --host=http://localhost:8000 \\
            --headless \\
            --users 20 \\
            --spawn-rate 5 \\
            --run-time 60s \\
            --html tests/load_test_report.html \\
            --csv tests/load_test_results

        if [ $? -eq 0 ]; then
            print_success "Load tests PASSED"
            ((TESTS_PASSED++))
            print_info "Load test report: backend/tests/load_test_report.html"
        else
            print_error "Load tests FAILED"
            ((TESTS_FAILED++))
        fi

        cd ..

        if [ "$STARTED_BACKEND" = true ]; then
            kill $BACKEND_PID 2>/dev/null || true
        fi
    else
        print_error "Backend not available for load tests"
        ((TESTS_FAILED++))
    fi
fi

#############################################################################
# Test Summary
#############################################################################

TEST_END_TIME=$(date +%s)
TEST_DURATION=$((TEST_END_TIME - TEST_START_TIME))

print_header "📊 TEST SUMMARY"

echo "Total Categories Passed: $TESTS_PASSED"
echo "Total Categories Failed: $TESTS_FAILED"
echo "Total Duration: ${TEST_DURATION}s"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "ALL TESTS PASSED! ✨"
    echo ""
    exit 0
else
    print_error "SOME TESTS FAILED"
    echo ""
    print_info "Review the output above for details"
    echo ""
    exit 1
fi
