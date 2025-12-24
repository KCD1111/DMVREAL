@echo off
REM Startup script for DMV OCR Validator (Windows)

echo Starting DMV OCR Validator...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if Tesseract is installed
where tesseract >nul 2>&1
if errorlevel 1 (
    echo WARNING: Tesseract OCR is not installed!
    echo Please download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
)

REM Start backend server
echo Starting backend server on port 5001...
start "Flask Backend" python py

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start frontend HTTP server
echo Starting frontend server on port 8000...
start "HTTP Server" python -m http.server 8000

echo.
echo ==========================================
echo Servers started successfully!
echo ==========================================
echo Backend API:  http://localhost:5001
echo Frontend:     http://localhost:8000/web.html
echo.
echo Close this window to stop the servers
echo ==========================================
echo.

pause

