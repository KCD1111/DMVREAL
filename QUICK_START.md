# Quick Start - Test Your DMV OCR Validator

## ✅ Current Status

- ✅ Ollama is running with llama3:8b installed
- ✅ Frontend server running on port 8000
- ⏳ Backend server starting...

## 🚀 Quick Test Steps

### 1. Open the Web Interface

Open your browser and go to:
```
http://localhost:8000/web.html
```

### 2. Upload a PDF

- Click the upload area or drag & drop a PDF file
- Click "Process & Validate Document"

### 3. Watch the Progress

**In the browser:**
- You'll see "Processing document..." spinner
- Wait for results (may take 30-60 seconds)

**In the backend terminal:**
- `[Step 1/2] Running Surya OCR...`
- `Processing page 1/1`
- `✓ Surya OCR completed, memory released`
- `[Step 2/2] Running Ollama/Llama3 extraction...`
- `✓ Ollama extraction completed`

### 4. View Results

**Success looks like:**
- ✅ Green banner: "Validation Successful"
- ✅ Extracted Data section with all fields
- ✅ Address fields: street_address, city, state, zip_code

**If there are issues:**
- ⚠️ Red banner with validation errors
- Check the browser console (F12) for details

## 🔍 Check Server Status

### Backend Health:
```bash
curl http://localhost:5001/health
```

### Ollama Status:
```bash
curl http://localhost:11434/api/tags
```

### View Backend Logs:
```bash
tail -f /tmp/flask_server.log
```

## 📝 What to Expect

**First Run:**
- Surya models download (2-5 minutes) - be patient!
- After that, processing is faster

**Normal Processing Time:**
- Surya OCR: 10-30 seconds
- Ollama extraction: 5-15 seconds
- Total: ~30-60 seconds per PDF

## 🐛 Troubleshooting

### Backend not responding?
```bash
# Check if it's running
lsof -ti:5001

# Restart it
cd /Users/octane.hinojosa/WEB
source .venv/bin/activate
python backend_driverlic.py
```

### Ollama errors?
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, verify model
ollama list
```

### Frontend not loading?
```bash
# Restart frontend server
python3 -m http.server 8000
```

## ✨ Success Indicators

You'll know it's working when you see:

1. **Backend terminal shows:**
   ```
   ✓ Surya OCR completed, memory released
   ✓ Ollama extraction completed
   ```

2. **Browser shows:**
   - Green "Validation Successful" banner
   - All extracted data fields displayed
   - No validation errors

3. **Extracted Data includes:**
   - First Name
   - Last Name
   - License Number
   - Date of Birth
   - Expiration Date
   - Street Address
   - City
   - State
   - Zip Code
   - Sex

**If you see all of this, your DMV prototype is production-ready! 🎉**

