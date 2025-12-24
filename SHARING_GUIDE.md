# How to Share This Project

## Files to Share

Share these files with the other person:

### Essential Files:
- `web.html` - Frontend application
- `py` - Backend Flask server
- `requirements.txt` - Python dependencies
- `README.md` - Setup instructions
- `start_server.sh` - Startup script (macOS/Linux)
- `start_server.bat` - Startup script (Windows)

### Optional:
- `.gitignore` - Git ignore file (if using version control)

## Sharing Methods

### Option 1: ZIP Archive (Recommended)
1. Select all the files listed above
2. Create a ZIP archive
3. Share the ZIP file via email, cloud storage, etc.

### Option 2: Cloud Storage
Upload the files to:
- Google Drive
- Dropbox
- OneDrive
- GitHub (if using version control)

### Option 3: Git Repository
If both parties use Git:
```bash
git init
git add web.html py requirements.txt README.md start_server.* .gitignore
git commit -m "Initial commit"
# Push to GitHub/GitLab and share the repository link
```

## What the Recipient Needs

1. **Python 3.7+** installed
2. **Tesseract OCR** installed (see README.md for instructions)
3. **Internet connection** (for initial pip install)

## Quick Start for Recipient

1. Extract/unzip the files
2. Open terminal/command prompt in the project folder
3. Follow the instructions in `README.md`
4. Or run:
   - macOS/Linux: `./start_server.sh`
   - Windows: `start_server.bat`

