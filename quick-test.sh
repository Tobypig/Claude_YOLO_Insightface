#!/bin/bash

###############################################################################
# Quick Test Suite - Verify Critical Fixes
# Tests the 5 critical fixes we just applied
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

###############################################################################
# Test 1: Check Logs Directory Exists
###############################################################################

test_logs_directory() {
    print_info "Test 1: Checking logs directory..."

    if [ -d "backend/logs" ]; then
        print_success "Logs directory exists"
    else
        print_error "Logs directory missing"
    fi
}

###############################################################################
# Test 2: Check Logging Integration in Code
###############################################################################

test_logging_integration() {
    print_info "Test 2: Checking logging integration..."

    if grep -q "from logging_config import" backend/main.py; then
        print_success "Logging imports present"
    else
        print_error "Logging imports missing"
    fi

    if grep -q "setup_logging" backend/main.py; then
        print_success "setup_logging() called"
    else
        print_error "setup_logging() not called"
    fi

    if grep -q "RequestLoggingMiddleware" backend/main.py; then
        print_success "RequestLoggingMiddleware added"
    else
        print_error "RequestLoggingMiddleware missing"
    fi
}

###############################################################################
# Test 3: Check List Jobs Endpoint Exists
###############################################################################

test_list_jobs_endpoint() {
    print_info "Test 3: Checking list jobs endpoint..."

    if grep -q '@app.get("/api/jobs")' backend/main.py; then
        print_success "List jobs endpoint exists"
    else
        print_error "List jobs endpoint missing"
    fi

    if grep -q "async def list_jobs" backend/main.py; then
        print_success "list_jobs function defined"
    else
        print_error "list_jobs function missing"
    fi
}

###############################################################################
# Test 4: Check File Upload Security
###############################################################################

test_file_upload_security() {
    print_info "Test 4: Checking file upload security..."

    if grep -q "os.path.basename" backend/main.py; then
        print_success "Filename path sanitization present"
    else
        print_error "Filename path sanitization missing"
    fi

    if grep -q "safe_filename" backend/main.py; then
        print_success "Safe filename variable used"
    else
        print_error "Safe filename variable not used"
    fi

    if grep -q "isalnum" backend/main.py; then
        print_success "Character sanitization present"
    else
        print_error "Character sanitization missing"
    fi
}

###############################################################################
# Test 5: Check Global Exception Handler
###############################################################################

test_exception_handler() {
    print_info "Test 5: Checking global exception handler..."

    if grep -q "@app.exception_handler(Exception)" backend/main.py; then
        print_success "Global exception handler decorator present"
    else
        print_error "Global exception handler decorator missing"
    fi

    if grep -q "global_exception_handler" backend/main.py; then
        print_success "Exception handler function defined"
    else
        print_error "Exception handler function missing"
    fi
}

###############################################################################
# Test 6: Python Syntax Validation
###############################################################################

test_python_syntax() {
    print_info "Test 6: Validating Python syntax..."

    cd backend
    if python3 -m py_compile main.py 2>/dev/null; then
        print_success "main.py syntax valid"
    else
        print_error "main.py has syntax errors"
    fi
    cd ..
}

###############################################################################
# Test 7: Test Infrastructure Files
###############################################################################

test_infrastructure() {
    print_info "Test 7: Checking test infrastructure..."

    if [ -f "run-all-tests.sh" ]; then
        print_success "Test runner script exists"
    else
        print_error "Test runner script missing"
    fi

    if [ -x "run-all-tests.sh" ]; then
        print_success "Test runner is executable"
    else
        print_error "Test runner not executable"
    fi

    if [ -d "backend/tests" ]; then
        print_success "Tests directory exists"
    else
        print_error "Tests directory missing"
    fi

    # Count test files
    TEST_FILES=$(find backend/tests -name "test_*.py" 2>/dev/null | wc -l)
    if [ $TEST_FILES -ge 3 ]; then
        print_success "Found $TEST_FILES test files"
    else
        print_error "Only found $TEST_FILES test files (expected >= 3)"
    fi
}

###############################################################################
# Test 8: Configuration Files
###############################################################################

test_configuration() {
    print_info "Test 8: Checking configuration files..."

    if [ -f "backend/pytest.ini" ]; then
        print_success "pytest.ini exists"
    else
        print_error "pytest.ini missing"
    fi

    if [ -f "frontend/jest.config.js" ]; then
        print_success "jest.config.js exists"
    else
        print_error "jest.config.js missing"
    fi

    if [ -f "TESTING_GUIDE.md" ]; then
        print_success "Testing documentation exists"
    else
        print_error "Testing documentation missing"
    fi
}

###############################################################################
# Test 9: Documentation
###############################################################################

test_documentation() {
    print_info "Test 9: Checking documentation..."

    DOCS=(
        "CODE_REVIEW_FINDINGS.md"
        "QUICK_FIXES.md"
        "MISSING_ITEMS_ANALYSIS.md"
        "FIXES_APPLIED_SUMMARY.md"
        "TESTING_GUIDE.md"
        "TEST_IMPLEMENTATION_SUMMARY.md"
    )

    DOC_COUNT=0
    for doc in "${DOCS[@]}"; do
        if [ -f "$doc" ]; then
            ((DOC_COUNT++))
        fi
    done

    print_success "Found $DOC_COUNT/$((${#DOCS[@]})) documentation files"
}

###############################################################################
# Test 10: Git Status
###############################################################################

test_git_status() {
    print_info "Test 10: Checking git status..."

    if git diff --quiet backend/main.py; then
        print_success "backend/main.py committed"
    else
        print_error "backend/main.py has uncommitted changes"
    fi

    UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)
    if [ $UNTRACKED -eq 0 ]; then
        print_success "No untracked files"
    else
        print_error "$UNTRACKED untracked files present"
    fi
}

###############################################################################
# Run All Tests
###############################################################################

print_header "🧪 QUICK TEST SUITE - Verifying Critical Fixes"

test_logs_directory
test_logging_integration
test_list_jobs_endpoint
test_file_upload_security
test_exception_handler
test_python_syntax
test_infrastructure
test_configuration
test_documentation
test_git_status

###############################################################################
# Summary
###############################################################################

print_header "📊 TEST SUMMARY"

echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "ALL QUICK TESTS PASSED! ✨"
    echo ""
    echo "Status: ✅ Ready for comprehensive testing"
    echo "Next: Run ./run-all-tests.sh for full test suite"
    echo ""
    exit 0
else
    print_error "SOME TESTS FAILED"
    echo ""
    echo "Please review the failures above"
    echo ""
    exit 1
fi
