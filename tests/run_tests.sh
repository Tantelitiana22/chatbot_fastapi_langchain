#!/bin/bash

# ChatGPT-like Chatbot Test Runner Script
# This script provides an easy way to run tests

set -e

echo "🧪 ChatGPT-like Chatbot Test Runner"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "run_tests.py" ]; then
    echo "❌ run_tests.py not found. Please run this script from the tests directory."
    exit 1
fi

# Check if server is running
echo "🔍 Checking if server is running..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Server is running on http://localhost:8000"
else
    echo "❌ Server is not running on http://localhost:8000"
    echo "Please start the server first:"
    echo "  uv run uvicorn backend.app:app --reload --port 8000"
    exit 1
fi

# Run the tests
echo ""
echo "🚀 Running tests..."
python3 run_tests.py "$@"
