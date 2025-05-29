#!/usr/bin/env bash
# Run tests for the LaTeX compilation server

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo -e "${YELLOW}Warning: pdflatex not found. Integration tests will be skipped.${NC}"
fi

# Run unit tests only
run_unit_tests() {
    echo -e "${GREEN}Running unit tests...${NC}"
    python -m pytest tests/test_unit.py -v
}

# Run integration tests only
run_integration_tests() {
    echo -e "${GREEN}Running integration tests...${NC}"
    python -m pytest tests/test_integration.py -v
}

# Run all tests
run_all_tests() {
    echo -e "${GREEN}Running all tests with coverage report...${NC}"
    python -m pytest
}

# Process command line arguments
case "$1" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    *)
        run_all_tests
        ;;
esac
