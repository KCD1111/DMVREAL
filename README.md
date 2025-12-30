# DMV License OCR Validator

A high-performance web application that extracts and validates driver's license information from PDF and image files using advanced OCR and AI models.

## Architecture

This application uses a two-stage AI pipeline:

1. **Surya OCR** - State-of-the-art optical character recognition for text extraction
   - Detection model: `vikp/surya_det3`
   - Recognition model: `vikp/surya_rec2`
   - Optimized for document processing with high accuracy

2. **Llama 3.2 1B Instruct** - Lightweight language model for field extraction
   - Model: `meta-llama/Llama-3.2-1B-Instruct`
   - Optimized for 8GB M1/M2 Macs
   - Extracts structured data from OCR text
   - Provides confidence scores for each field

3. **Supabase Database** - Cloud database for persistence
   - Stores OCR sessions and processing history
   - Tracks extracted license data with validation reports
   - Enables search by license number

## Features

- Upload PDF documents or images (PNG, JPG, JPEG, HEIC, HEIF) via drag-and-drop
- Automatic OCR processing using Surya OCR
- AI-powered field extraction using Llama 3.2
- Data validation and normalization
- Confidence scoring for extracted fields
- Session tracking and history
- Search by license number
- RESTful API endpoints
- Beautiful, responsive web interface

## System Requirements

### Minimum Requirements
- **RAM:** 8GB (recommended for 1B model)
- **Python:** 3.9 or higher
- **Disk Space:** ~5GB for models and dependencies
- **OS:** macOS, Linux, or Windows

### Recommended for Best Performance
- **RAM:** 16GB or more
- **GPU:** Apple Silicon (M1/M2/M3) with MPS support, or NVIDIA GPU with CUDA
- **CPU:** Multi-core processor (4+ cores)

### Hardware Acceleration
- **macOS:** Automatic MPS (Metal Performance Shaders) acceleration on Apple Silicon
- **Linux/Windows:** Automatic CUDA acceleration if NVIDIA GPU is available
- **Fallback:** CPU mode (slower but functional)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd dmv-ocr-validator
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all Python dependencies
pip install -r requirements.txt
```

This will install:
- Flask and Flask-CORS (web server)
- PyTorch (ML framework)
- Transformers and Accelerate (Llama model)
- Surya OCR (document OCR)
- Supabase (database client)
- Pillow and pdf2image (image processing)
- Additional dependencies for model optimization

### 4. Configure Environment Variables

Create a `.env` file in the project root (or verify it exists):

```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Note:** The Supabase database is pre-configured. If you need to set up a new instance, see the Database Setup section below.

## Running the Application

### Quick Start

Use the provided startup script:

```bash
# Make the script executable (first time only)
chmod +x start_server.sh

# Run the server
./start_server.sh
```

### Manual Start

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate      # Windows

# Start the backend server
python backend_surya_llama.py
```

The server will start on `http://localhost:5001`

**Important Notes:**
- First request will be slow (5-10 seconds) as models load into memory
- Subsequent requests will be much faster (2-4 seconds)
- Models are loaded on-demand and unloaded after processing to save memory

### Access the Web Interface

Open your browser and navigate to:
```
http://localhost:5001
```

Or access `web.html` directly through a local server:

```bash
# In a separate terminal
python3 -m http.server 8000
# Then open: http://localhost:8000/web.html
```

## Usage

### Processing a Document

1. Open the web interface in your browser
2. Click the upload area or drag and drop a PDF or image file
3. Click "Process & Validate Document"
4. Wait for processing (2-10 seconds depending on hardware)
5. View extracted data, confidence scores, and validation results

### API Endpoints

#### POST `/process-document`
Process a PDF or image file and extract license data.

**Request:**
```bash
curl -X POST http://localhost:5001/process-document \
  -F "document=@license.pdf"
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "license_id": "uuid",
  "extracted_data": {
    "first_name": "John",
    "last_name": "Doe",
    "license_number": "D1234567",
    ...
  },
  "normalized_data": { ... },
  "validation_report": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "overall_confidence": 0.92,
  "processing_time_ms": 3450
}
```

#### GET `/session/<session_id>`
Retrieve a previous OCR session and its results.

#### GET `/search/<license_number>`
Search for licenses by license number.

#### GET `/recent-sessions?limit=10`
Get recent processing sessions.

#### GET `/health`
Check server health and model status.

## Database Setup

The application uses Supabase for data persistence. The database schema includes:

### Tables

**ocr_sessions**
- Tracks each processing session
- Stores file metadata and processing status
- Records processing time and confidence scores

**extracted_licenses**
- Stores extracted license information
- Contains all parsed fields (name, address, dates, etc.)
- Includes confidence scores and validation reports
- Links to parent session

### Applying Migrations

If you need to set up a new Supabase instance:

1. Create a new Supabase project at https://supabase.com
2. Go to SQL Editor in your Supabase dashboard
3. Run the migration files in order:
   - `database_migration.sql` (creates tables and indexes)
   - `supabase/migrations/add_anonymous_access_policies.sql` (adds access policies)

### Row Level Security (RLS)

The database uses RLS policies that allow:
- Anonymous users to read/write (for demo purposes)
- Authenticated users to read/write their own data

**Production Note:** For production use, implement proper authentication and restrict RLS policies to authenticated users only.

## Project Structure

```
dmv-ocr-validator/
├── backend_surya_llama.py      # Main Flask server
├── model_manager.py            # AI model loading and orchestration
├── license_extractor.py        # Data validation and normalization
├── database.py                 # Supabase database operations
├── web.html                    # Frontend web interface
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (Supabase config)
├── start_server.sh             # Startup script
├── database_migration.sql      # Database schema
├── supabase/migrations/        # Additional migrations
├── MODEL_COMPARISON.md         # Guide for choosing Llama model size
└── README.md                   # This file
```

## Model Management

### Memory-Efficient Sequential Processing

The application uses a memory-efficient approach:

1. **Load Surya OCR** → Extract text → **Unload Surya**
2. **Load Llama** → Extract fields → **Unload Llama**

This ensures:
- Only one model in memory at a time
- Stable performance on 8GB systems
- Automatic GPU memory management

### Model Selection

The application uses Llama 3.2 1B Instruct by default. This model is:
- Optimized for 8GB M1/M2 Macs
- 2-3x faster than the 3B model
- 94% accuracy vs 95% for 3B (negligible difference for structured data)
- Uses ~1GB RAM instead of ~3GB

See `MODEL_COMPARISON.md` for detailed analysis.

### Changing Models

To use a different Llama model, edit `model_manager.py`:

```python
# Line 68
model_id = "meta-llama/Llama-3.2-3B-Instruct"  # For 3B model
```

## Troubleshooting

### Port Already in Use

Change the port in `backend_surya_llama.py`:
```python
# Line 232
port = 5002  # Change from 5001
```

### Out of Memory Errors

Solutions:
1. Close other applications to free up RAM
2. Ensure models are being unloaded properly (check logs)
3. Consider using the 1B model instead of 3B
4. Reduce image resolution in `model_manager.py` (line 139-144)

### Models Not Loading

First run downloads models (~2-3GB):
- Ensure stable internet connection
- Check available disk space
- Models cache in `~/.cache/huggingface/`

### Database Connection Errors

Verify `.env` configuration:
```bash
# Check environment variables are set
python test_db_connection.py
```

If Supabase is unavailable:
- Application will still work but won't save data
- Check logs for "Supabase not available" warnings

### CORS Errors

Always access through HTTP server:
```bash
python3 -m http.server 8000
```
Then open: `http://localhost:8000/web.html`

### Slow Processing

Optimize performance:
- First request is always slow (model loading)
- Use GPU acceleration (MPS on Mac, CUDA on NVIDIA)
- Reduce PDF resolution if needed
- Process multiple documents in sequence (models stay warm)

## Performance Benchmarks

### On 8GB M1 Mac with 1B Model:

| Stage | Time | Notes |
|-------|------|-------|
| PDF to Image | 0.5s | Per page |
| Surya OCR | 2-3s | Text extraction |
| Llama Extraction | 2-3s | Field parsing |
| **Total** | **4-7s** | Per document |

### Memory Usage:

```
Peak Memory: ~4-5GB
├── macOS System: 2GB
├── Surya OCR: 1-2GB (when loaded)
├── Llama 1B: 1GB (when loaded)
└── Python + Flask: 500MB
```

## Development

### Testing Database Connection

```bash
python test_db_connection.py
```

### Testing Imports

```bash
python test_imports.py
```

### Running in Debug Mode

The Flask server runs in debug mode by default:
- Auto-reloads on code changes
- Provides detailed error messages
- Shows stack traces in responses

For production, disable debug mode in `backend_surya_llama.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

## Security Considerations

### Current Setup (Development)
- Anonymous database access enabled
- CORS allows all origins
- Debug mode enabled

### Production Recommendations
1. Enable Supabase authentication
2. Restrict RLS policies to authenticated users only
3. Disable debug mode
4. Configure CORS for specific domains only
5. Use environment variables for all secrets
6. Enable HTTPS/SSL
7. Add rate limiting
8. Implement input validation and sanitization

## License

[Add your license here]

## Support

For issues, questions, or contributions:
- Check existing issues and documentation
- Review `MODEL_COMPARISON.md` for model selection guidance
- Test database connectivity with `test_db_connection.py`
- Check logs for detailed error messages

## Acknowledgments

- **Surya OCR** by Vik Paruchuri - High-quality document OCR
- **Llama 3.2** by Meta - Efficient language model
- **Supabase** - Open-source Firebase alternative
- **Hugging Face** - Model hosting and transformers library
