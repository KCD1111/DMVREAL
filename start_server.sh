#!/bin/bash
# Startup script for DMV OCR Validator

echo "Starting DMV OCR Validator..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR is not installed!"
    echo "Please install it:"
    echo "  macOS: brew install tesseract"
    echo "  Linux: sudo apt-get install tesseract-ocr"
    echo ""
fi

# Start backend server in background
echo "Starting backend server on port 5001..."
python py > flask_server.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for server to start
sleep 2

# Start frontend HTTP server
echo "Starting frontend server on port 8000..."
python3 -m http.server 8000 > http_server.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "Servers started successfully!"
echo "=========================================="
echo "Backend API:  http://localhost:5001"
echo "Frontend:     http://localhost:8000/web.html"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait

