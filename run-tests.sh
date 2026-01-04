#!/bin/bash

# Comprehensive test runner for AI Video Generation Platform
# This script runs all tests: backend, frontend, and E2E

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}AI Video Generation Platform${NC}"
echo -e "${BLUE}Comprehensive Test Suite${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Track overall status
FAILED=0

# Function to print section header
print_header() {
    echo -e "\n${YELLOW}======================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}======================================${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print failure
print_failure() {
    echo -e "${RED}✗ $1${NC}"
    FAILED=1
}

# Function to run command with error handling
run_test() {
    local name="$1"
    local command="$2"
    
    echo -e "${BLUE}Running: $name${NC}"
    if eval "$command"; then
        print_success "$name passed"
        return 0
    else
        print_failure "$name failed"
        return 1
    fi
}

# Parse command line arguments
SKIP_BACKEND=false
SKIP_FRONTEND=false
SKIP_E2E=false
COVERAGE=false
WATCH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backend)
            SKIP_BACKEND=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-e2e)
            SKIP_E2E=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --watch)
            WATCH=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-backend    Skip backend tests"
            echo "  --skip-frontend   Skip frontend tests"
            echo "  --skip-e2e        Skip E2E tests"
            echo "  --coverage        Generate coverage reports"
            echo "  --watch           Run tests in watch mode"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if services are running
print_header "Checking Services"

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Backend API is not running on http://localhost:8000${NC}"
    echo -e "${YELLOW}Some tests may fail. Start the backend with: cd backend && python -m app.main${NC}\n"
fi

if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Frontend is not running on http://localhost:3000${NC}"
    echo -e "${YELLOW}Some tests may fail. Start the frontend with: cd frontend && npm run dev${NC}\n"
fi

# Backend Tests
if [ "$SKIP_BACKEND" = false ]; then
    print_header "Backend Tests"
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating Python virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -q -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Run backend tests
    if [ "$COVERAGE" = true ]; then
        run_test "Backend Tests with Coverage" "pytest --cov=app --cov-report=html --cov-report=term-missing" || true
    else
        run_test "Backend Tests" "pytest -v" || true
    fi
    
    cd ..
fi

# Frontend Tests
if [ "$SKIP_FRONTEND" = false ]; then
    print_header "Frontend Tests"
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Run frontend tests
    if [ "$WATCH" = true ]; then
        echo -e "${YELLOW}Running tests in watch mode...${NC}"
        npm run test:watch
    elif [ "$COVERAGE" = true ]; then
        run_test "Frontend Tests with Coverage" "npm run test:coverage" || true
    else
        run_test "Frontend Tests" "npm test -- --run" || true
    fi
    
    cd ..
fi

# E2E Tests
if [ "$SKIP_E2E" = false ]; then
    print_header "E2E Tests"
    
    # Check if Playwright is installed
    if ! command -v npx &> /dev/null; then
        print_failure "npx not found. Please install Node.js"
        FAILED=1
    else
        # Install Playwright browsers if needed
        if [ ! -d "frontend/node_modules/playwright" ]; then
            echo -e "${YELLOW}Installing Playwright browsers...${NC}"
            npx playwright install --with-deps
        fi
        
        # Run E2E tests
        if [ "$COVERAGE" = true ]; then
            run_test "E2E Tests with Coverage" "npx playwright test" || true
        else
            run_test "E2E Tests" "npx playwright test" || true
        fi
    fi
fi

# Final Summary
print_header "Test Summary"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}\n"
    
    if [ "$COVERAGE" = true ]; then
        echo -e "${BLUE}Coverage Reports:${NC}"
        echo -e "  Backend:   backend/htmlcov/index.html"
        echo -e "  Frontend:  frontend/coverage/index.html"
        echo -e "  Playwright: playwright-report/index.html\n"
    fi
    
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}\n"
    echo -e "${BLUE}Tips for debugging:${NC}"
    echo -e "  1. Run specific test files to isolate failures"
    echo -e "  2. Check logs in backend/api.log and frontend.log"
    echo -e "  3. Ensure all services are running"
    echo -e "  4. Run tests with --watch mode for interactive debugging\n"
    exit 1
fi
