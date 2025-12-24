# DMV Document OCR Validator

A web application that processes PDF documents (driver's licenses) using OCR technology to extract and validate information.

## Features

- Upload PDF documents via drag-and-drop or file selection
- Automatic OCR processing using OCRmyPDF
- Data extraction and normalization
- Field validation against schema
- Beautiful, responsive web interface

## Requirements

- Python 3.7 or higher
- Tesseract OCR (required for OCRmyPDF)
- Virtual environment (recommended)

## Installation

### 1. Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Set up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

## Running the Application

### 1. Start the Backend Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate      # Windows

# Start the Flask server
python py
```

The server will start on `http://localhost:5001`

### 2. Start the Frontend Server (Optional but Recommended)

In a new terminal window:

```bash
# Navigate to the project directory
cd /path/to/WEB

# Start a simple HTTP server
python3 -m http.server 8000
```

### 3. Open the Application

Open your browser and navigate to:
- **If using HTTP server:** `http://localhost:8000/web.html`
- **If opening file directly:** Open `web.html` in your browser (may have CORS issues)

## Usage

1. Open the web interface in your browser
2. Click the upload area or drag and drop a PDF file
3. Click "Process & Validate Document"
4. View the extracted data and validation results

## Project Structure

```
WEB/
├── web.html          # Frontend HTML/JavaScript application
├── py               # Backend Flask server
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Troubleshooting

### Port Already in Use

If port 5001 is already in use, you can change it:
1. Edit `py` file, line 307: Change `port = 5001` to another port (e.g., `5002`)
2. Edit `web.html` file, line 113: Change `const API_BASE_URL = 'http://localhost:5001'` to match

### OCR Errors

- Make sure Tesseract is installed: `tesseract --version`
- Check that OCRmyPDF is installed: `pip install ocrmypdf`

### CORS Errors

Always access the HTML file through an HTTP server (`http://localhost:8000/web.html`) rather than opening it directly from the file system.

## Notes

- The application processes PDFs locally on your machine
- OCR processing can take 10-30 seconds depending on PDF size
- Temporary files are automatically cleaned up after processing

