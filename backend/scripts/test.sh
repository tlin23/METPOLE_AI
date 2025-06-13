#!/bin/bash

# MetPol AI Backend Test Runner
# Usage: ./scripts/test.sh [OPTIONS] [TEST_TYPE]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE="false"
VERBOSE="false"
FAST="false"
LINT="false"
SECURITY="false"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

print_usage() {
    echo "Usage: $0 [OPTIONS] [TEST_TYPE]"
    echo ""
    echo "TEST_TYPE:"
    echo "  unit        Run unit tests only"
    echo "  integration Run integration tests only"
    echo "  security    Run security tests only"
    echo "  load        Run load tests (slow)"
    echo "  all         Run all tests (default)"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help      Show this help message"
    echo "  -c, --coverage  Generate coverage report"
    echo "  -v, --verbose   Verbose output"
    echo "  -f, --fast      Skip slow tests"
    echo "  -l, --lint      Run linting checks"
    echo "  -s, --security  Run security scans"
    echo "  --ci            CI mode (coverage + lint + security)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 unit -c           # Run unit tests with coverage"
    echo "  $0 --ci              # Full CI pipeline"
    echo "  $0 load              # Run load tests"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v python &> /dev/null; then
        log_error "Python is not installed"
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi

    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        log_warning "Virtual environment not detected. Consider activating venv."
    fi

    log_success "Dependencies check passed"
}

setup_environment() {
    log_info "Setting up test environment..."

    # Set test environment variables
    export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"
    export GOOGLE_CLIENT_ID="test_client_id"
    export ADMIN_EMAILS="admin@example.com"
    export OPENAI_API_KEY="test_key"
    export DATABASE_PATH="/tmp/test_$(date +%s).db"
    export ENV="test"

    # Create temporary database directory
    mkdir -p "$(dirname "$DATABASE_PATH")"

    log_success "Environment setup complete"
}

run_linting() {
    if [ "$LINT" = "true" ]; then
        log_info "Running linting checks..."

        # Black formatting check
        log_info "Checking code formatting with Black..."
        if ! black --check --diff server/; then
            log_error "Code formatting issues found. Run: black server/"
            return 1
        fi

        # Flake8 linting
        log_info "Running Flake8 linting..."
        if ! flake8 server/ --count --statistics; then
            log_error "Linting issues found"
            return 1
        fi

        # Import sorting check
        log_info "Checking import sorting with isort..."
        if ! isort --check-only --diff server/; then
            log_error "Import sorting issues found. Run: isort server/"
            return 1
        fi

        log_success "All linting checks passed"
    fi
}

run_security_scans() {
    if [ "$SECURITY" = "true" ]; then
        log_info "Running security scans..."

        # Bandit security scan
        log_info "Running Bandit security scan..."
        if ! bandit -r server/ -ll; then
            log_warning "Security issues found (see above)"
        fi

        # Safety dependency check
        log_info "Checking dependencies for known vulnerabilities..."
        if ! safety check; then
            log_warning "Vulnerable dependencies found (see above)"
        fi

        log_success "Security scans completed"
    fi
}

run_tests() {
    log_info "Running tests (type: $TEST_TYPE)..."

    # Build pytest command
    PYTEST_CMD="python -m pytest"

    # Add test directory based on type
    case $TEST_TYPE in
        "unit")
            PYTEST_CMD="$PYTEST_CMD server/tests/unit/"
            ;;
        "integration")
            PYTEST_CMD="$PYTEST_CMD server/tests/integration/"
            ;;
        "security")
            PYTEST_CMD="$PYTEST_CMD server/tests/security/"
            ;;
        "load")
            PYTEST_CMD="$PYTEST_CMD server/tests/load/ -m slow"
            ;;
        "all")
            PYTEST_CMD="$PYTEST_CMD server/tests/"
            ;;
        *)
            log_error "Unknown test type: $TEST_TYPE"
            exit 1
            ;;
    esac

    # Add coverage if requested
    if [ "$COVERAGE" = "true" ]; then
        PYTEST_CMD="$PYTEST_CMD --cov=server --cov-report=xml --cov-report=html --cov-report=term-missing"
    fi

    # Add verbose output if requested
    if [ "$VERBOSE" = "true" ]; then
        PYTEST_CMD="$PYTEST_CMD -v"
    else
        PYTEST_CMD="$PYTEST_CMD -q"
    fi

    # Skip slow tests if fast mode
    if [ "$FAST" = "true" ] && [ "$TEST_TYPE" != "load" ]; then
        PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
    fi

    # Add test markers for organization
    PYTEST_CMD="$PYTEST_CMD --strict-markers"

    # Execute tests
    log_info "Executing: $PYTEST_CMD"

    if ! eval $PYTEST_CMD; then
        log_error "Tests failed"
        return 1
    fi

    log_success "Tests completed successfully"
}

generate_reports() {
    if [ "$COVERAGE" = "true" ]; then
        log_info "Generating test reports..."

        # Coverage report
        if [ -f "coverage.xml" ]; then
            log_success "Coverage report generated: coverage.xml"
        fi

        if [ -d "htmlcov" ]; then
            log_success "HTML coverage report: htmlcov/index.html"
        fi
    fi
}

cleanup() {
    log_info "Cleaning up..."

    # Remove temporary database
    if [ -n "$DATABASE_PATH" ] && [ -f "$DATABASE_PATH" ]; then
        rm -f "$DATABASE_PATH"
    fi

    # Clean up pytest cache
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true

    log_success "Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -f|--fast)
            FAST="true"
            shift
            ;;
        -l|--lint)
            LINT="true"
            shift
            ;;
        -s|--security)
            SECURITY="true"
            shift
            ;;
        --ci)
            COVERAGE="true"
            LINT="true"
            SECURITY="true"
            VERBOSE="true"
            shift
            ;;
        unit|integration|security|load|all)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting MetPol AI Backend Test Suite"
    log_info "Python version: $(python --version)"
    log_info "Test type: $TEST_TYPE"

    check_dependencies
    setup_environment

    # Run linting first (fail fast)
    if ! run_linting; then
        exit 1
    fi

    # Run security scans
    run_security_scans

    # Run tests
    if ! run_tests; then
        exit 1
    fi

    # Generate reports
    generate_reports

    log_success "All checks completed successfully! 🎉"
}

# Change to project directory
cd "$PROJECT_DIR"

# Run main function
main
