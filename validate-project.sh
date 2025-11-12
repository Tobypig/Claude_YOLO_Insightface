#!/bin/bash

# Project validation script for Video Frame Person & Face Detection System

set -e

echo "🔍 Project Validation & Health Check"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Helper functions
print_check() {
    echo -e "${BLUE}Checking:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# 1. Check Project Structure
print_section "1. Project Structure"

print_check "Backend directory structure"
if [ -d "backend" ] && [ -d "backend/processors" ] && [ -d "backend/utils" ] && [ -d "backend/data" ]; then
    print_success "Backend structure exists"
else
    print_error "Backend structure incomplete"
fi

print_check "Frontend directory structure"
if [ -d "frontend" ] && [ -d "frontend/src" ] && [ -d "frontend/src/app" ]; then
    print_success "Frontend structure exists"
else
    print_error "Frontend structure incomplete"
fi

# 2. Check Configuration Files
print_section "2. Configuration Files"

print_check "Backend .env file"
if [ -f "backend/.env" ]; then
    print_success "backend/.env exists"
else
    print_error "backend/.env not found - run setup.sh"
fi

print_check "Backend .env.example"
if [ -f "backend/.env.example" ]; then
    print_success "backend/.env.example exists"
else
    print_warning "backend/.env.example not found"
fi

print_check "Frontend environment template"
if [ -f "frontend/.env.local.example" ]; then
    print_success "frontend/.env.local.example exists"
else
    print_warning "frontend/.env.local.example not found"
fi

# 3. Check Backend Files
print_section "3. Backend Files"

BACKEND_FILES=(
    "backend/config.py"
    "backend/main.py"
    "backend/requirements.txt"
    "backend/Dockerfile"
    "backend/processors/frame_extractor.py"
    "backend/processors/person_detector.py"
    "backend/processors/face_detector.py"
    "backend/processors/face_comparator.py"
    "backend/processors/video_processor.py"
    "backend/utils/bbox_utils.py"
    "backend/utils/video_utils.py"
    "backend/test_api.py"
    "backend/test_utils.py"
    "backend/logging_config.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file"
    else
        print_error "$file missing"
    fi
done

# 4. Check Frontend Files
print_section "4. Frontend Files"

FRONTEND_FILES=(
    "frontend/package.json"
    "frontend/tsconfig.json"
    "frontend/next.config.js"
    "frontend/tailwind.config.js"
    "frontend/Dockerfile"
    "frontend/src/app/page.tsx"
    "frontend/src/app/layout.tsx"
    "frontend/src/app/process/page.tsx"
    "frontend/src/app/jobs/page.tsx"
    "frontend/src/app/results/[id]/page.tsx"
    "frontend/src/app/compare/[id]/page.tsx"
    "frontend/src/lib/api.ts"
    "frontend/src/lib/utils.ts"
    "frontend/src/types/index.ts"
)

for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file"
    else
        print_error "$file missing"
    fi
done

# 5. Check Documentation
print_section "5. Documentation"

DOCS=(
    "README.md"
    "GETTING_STARTED.md"
    "DEPLOYMENT.md"
    "PROJECT_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        print_success "$doc"
    else
        print_warning "$doc missing"
    fi
done

# 6. Check Docker Configuration
print_section "6. Docker Configuration"

if [ -f "docker-compose.yml" ]; then
    print_success "docker-compose.yml exists"
else
    print_error "docker-compose.yml missing"
fi

if [ -f "backend/Dockerfile" ]; then
    print_success "backend/Dockerfile exists"
else
    print_error "backend/Dockerfile missing"
fi

if [ -f "frontend/Dockerfile" ]; then
    print_success "frontend/Dockerfile exists"
else
    print_error "frontend/Dockerfile missing"
fi

# 7. Check Scripts
print_section "7. Automation Scripts"

SCRIPTS=(
    "setup.sh"
    "start-dev.sh"
    "run-tests.sh"
    "validate-project.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            print_success "$script (executable)"
        else
            print_warning "$script (not executable - run: chmod +x $script)"
        fi
    else
        print_error "$script missing"
    fi
done

# 8. Check CI/CD
print_section "8. CI/CD Configuration"

if [ -f ".github/workflows/ci.yml" ]; then
    print_success "GitHub Actions workflow exists"
else
    print_warning "GitHub Actions workflow missing"
fi

if [ -f "prometheus.yml" ]; then
    print_success "Prometheus config exists"
else
    print_warning "Prometheus config missing"
fi

# 9. Check Python Syntax
print_section "9. Python Syntax Check"

if command -v python3 &> /dev/null; then
    print_check "Checking Python files for syntax errors"
    PYTHON_FILES=$(find backend -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*")
    SYNTAX_ERRORS=0

    for file in $PYTHON_FILES; do
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            print_error "Syntax error in $file"
            ((SYNTAX_ERRORS++))
        fi
    done

    if [ $SYNTAX_ERRORS -eq 0 ]; then
        print_success "All Python files have valid syntax"
    fi
else
    print_warning "Python3 not installed - skipping syntax check"
fi

# 10. Check Git Status
print_section "10. Git Repository"

if [ -d ".git" ]; then
    print_success "Git repository initialized"

    BRANCH=$(git branch --show-current)
    print_success "Current branch: $BRANCH"

    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Uncommitted changes exist"
    else
        print_success "Working directory clean"
    fi
else
    print_error "Not a git repository"
fi

# 11. Check Data Directories
print_section "11. Data Directories"

DATA_DIRS=(
    "backend/data/videos"
    "backend/data/clips"
    "backend/data/output"
    "backend/models"
)

for dir in "${DATA_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_success "$dir exists"
    else
        print_warning "$dir not found (will be created on setup)"
    fi
done

# 12. Summary
print_section "12. Validation Summary"

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ PROJECT VALIDATION PASSED${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}All critical checks passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Warnings: $WARNINGS${NC} (non-critical)"
    fi
    echo ""
    echo "✓ Project is ready to use!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./setup.sh (if not done yet)"
    echo "  2. Run: ./start-dev.sh (to start development)"
    echo "  3. Or: docker-compose up -d (for Docker)"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗ PROJECT VALIDATION FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${RED}Errors: $ERRORS${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo ""
    echo "Please fix the errors above before proceeding."
    echo ""
    exit 1
fi
