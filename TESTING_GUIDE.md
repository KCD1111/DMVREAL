# Testing Guide - DMV OCR Validator

## Prerequisites Checklist

Before testing, make sure you have:

- [ ] Python 3.7+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] **Ollama installed and running**
- [ ] **Llama3:8b model downloaded**

## Step 1: Install and Start Ollama

### Install Ollama:
```bash
# macOS
brew install ollama

# Or download from: https://ollama.ai/download
```

### Start Ollama:
```bash
ollama serve
```
Keep this terminal window open - Ollama must be running!

### Download Llama3 Model (in a new terminal):
```bash
ollama pull llama3:8b
```

This will download the model (about 4.7GB). Wait for it to complete.

### Verify Ollama is Running:
```bash
curl http://localhost:11434/api/tags
```

You should see JSON with available models.

## Step 2: Start the Backend Server

In a **new terminal window**:

```bash
cd /Users/octane.hinojosa/WEB
source .venv/bin/activate
python backend_driverlic.py
```

You should see:
```
Loading Surya OCR models...
Surya models loaded successfully!
Starting DMV OCR Backend Server on http://localhost:5001
```

**Note:** First time loading Surya models may take 2-5 minutes. Be patient!

## Step 3: Start the Frontend Server

In **another new terminal window**:

```bash
cd /Users/octane.hinojosa/WEB
python3 -m http.server 8000
```

You should see:
```
Serving HTTP on 0.0.0.0 port 8000 ...
```

## Step 4: Open the Web Interface

Open your browser and go to:
```
http://localhost:8000/web.html
```

## Step 5: Test the Application

1. **Upload a PDF**:
   - Click the upload area or drag & drop a PDF file
   - The file should be a driver's license or similar document

2. **Click "Process & Validate Document"**

3. **Watch the Processing**:
   - You'll see "Processing document..." spinner
   - Check the backend terminal for progress:
     - `[Step 1/2] Running Surya OCR...`
     - `✓ Surya OCR completed, memory released`
     - `[Step 2/2] Running Ollama/Llama3 extraction...`
     - `✓ Ollama extraction completed`

4. **View Results**:
   - If successful: Green banner "Validation Successful"
   - Extracted Data section shows all fields
   - If issues: Red banner with validation errors

## Troubleshooting

### "Cannot connect to server"
- Make sure backend is running on port 5001
- Check: `curl http://localhost:5001/health`

### "Ollama API error"
- Make sure Ollama is running: `ollama serve`
- Check: `curl http://localhost:11434/api/tags`
- Make sure llama3:8b is installed: `ollama list`

### "Surya OCR failed"
- First run downloads models (wait 2-5 minutes)
- Check you have enough disk space
- Check terminal for specific error messages

### "No text extracted"
- PDF might be image-only
- Try a different PDF
- Check if PDF has selectable text

### Memory Issues
- Close other applications
- Surya uses GPU/memory - ensure you have enough RAM
- The code now explicitly releases memory between steps

## Quick Test Commands

### Test Backend Health:
```bash
curl http://localhost:5001/health
```

### Test Ollama:
```bash
curl http://localhost:11434/api/tags
```

### Test Frontend:
```bash
curl http://localhost:8000/web.html | head -5
```

## Expected Output

### Successful Processing:
- Backend terminal shows:
  ```
  [Step 1/2] Running Surya OCR...
  Processing page 1/1
  ✓ Surya OCR completed, memory released
  === RAW OCR TEXT ===
  [extracted text...]
  [Step 2/2] Running Ollama/Llama3 extraction...
  === LLAMA3 EXTRACTED DATA ===
  first_name: John
  last_name: Doe
  ...
  ✓ Ollama extraction completed
  ```

- Browser shows:
  - Green "Validation Successful" banner
  - Extracted Data cards with all fields
  - No validation issues

## Using the Startup Script

For easier testing, you can use the startup script:

```bash
cd /Users/octane.hinojosa/WEB
./start_server.sh
```

This starts both servers automatically. **But you still need Ollama running separately!**

## Production Ready Checklist

✅ Surya OCR extracts text successfully  
✅ Memory is released before Ollama starts  
✅ Ollama extracts structured data  
✅ Data is normalized correctly  
✅ Validation works  
✅ Frontend displays results with green checkmark  
✅ All address fields (street, city, state, zip) are extracted  

If all these work, you have a production-ready DMV prototype! 🎉

