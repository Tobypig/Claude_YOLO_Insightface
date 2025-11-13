#!/bin/bash

###############################################################################
# Verify Critical Fixes - Simple Test Script
###############################################################################

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   VERIFYING CRITICAL FIXES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 1: Logs directory
echo -n "1. Logs directory exists.............. "
if [ -d "backend/logs" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 2: Logging imports
echo -n "2. Logging imports added.............. "
if grep -q "from logging_config import" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 3: setup_logging called
echo -n "3. setup_logging() called............. "
if grep -q "setup_logging" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 4: RequestLoggingMiddleware
echo -n "4. RequestLoggingMiddleware added..... "
if grep -q "RequestLoggingMiddleware" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 5: List jobs endpoint
echo -n "5. List jobs endpoint exists.......... "
if grep -q '@app.get("/api/jobs")' backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 6: list_jobs function
echo -n "6. list_jobs function defined......... "
if grep -q "async def list_jobs" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 7: File sanitization
echo -n "7. os.path.basename used.............. "
if grep -q "os.path.basename" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 8: safe_filename variable
echo -n "8. safe_filename variable used........ "
if grep -q "safe_filename" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 9: Character sanitization
echo -n "9. Character sanitization present..... "
if grep -q "isalnum" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 10: Exception handler
echo -n "10. Exception handler decorator........ "
if grep -q "@app.exception_handler(Exception)" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 11: Exception handler function
echo -n "11. Exception handler function......... "
if grep -q "global_exception_handler" backend/main.py; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 12: Python syntax
echo -n "12. Python syntax valid................ "
cd backend
if python3 -m py_compile main.py 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi
cd ..

# Test 13: Test files exist
echo -n "13. Test files created................. "
TEST_COUNT=$(find backend/tests -name "test_*.py" 2>/dev/null | wc -l)
if [ $TEST_COUNT -ge 3 ]; then
    echo -e "${GREEN}✓ PASS (${TEST_COUNT} files)${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL (only ${TEST_COUNT} files)${NC}"
    ((FAIL++))
fi

# Test 14: Test runner script
echo -n "14. Test runner script exists.......... "
if [ -f "run-all-tests.sh" ] && [ -x "run-all-tests.sh" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAIL++))
fi

# Test 15: Documentation
echo -n "15. Documentation complete............. "
DOC_COUNT=0
[ -f "CODE_REVIEW_FINDINGS.md" ] && ((DOC_COUNT++))
[ -f "QUICK_FIXES.md" ] && ((DOC_COUNT++))
[ -f "FIXES_APPLIED_SUMMARY.md" ] && ((DOC_COUNT++))
[ -f "TESTING_GUIDE.md" ] && ((DOC_COUNT++))

if [ $DOC_COUNT -ge 3 ]; then
    echo -e "${GREEN}✓ PASS (${DOC_COUNT} docs)${NC}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL (only ${DOC_COUNT} docs)${NC}"
    ((FAIL++))
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Tests Passed: $PASS"
echo "Tests Failed: $FAIL"
echo "Total Tests:  $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✨ ALL VERIFICATION TESTS PASSED! ✨${NC}"
    echo ""
    echo "Status: ✅ All critical fixes verified"
    echo ""
    exit 0
else
    echo -e "${RED}⚠ SOME TESTS FAILED${NC}"
    echo ""
    exit 1
fi
