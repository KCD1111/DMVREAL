#!/usr/bin/env python3
"""
OCR Diagnostic Tool
Helps identify why OCR text extraction is failing
"""

import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("=" * 70)
print("DMV OCR DIAGNOSTIC TOOL")
print("=" * 70)
print()

def check_step(step_num, description):
    print(f"\n[STEP {step_num}] {description}")
    print("-" * 70)

def success(msg):
    print(f"  ✓ {msg}")

def error(msg):
    print(f"  ✗ {msg}")

def warning(msg):
    print(f"  ⚠ {msg}")

def info(msg):
    print(f"  → {msg}")

check_step(1, "Checking Python Version")
py_version = sys.version_info
info(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
if py_version.major == 3 and py_version.minor >= 9:
    success("Python version is compatible")
else:
    error(f"Python 3.9+ required, you have {py_version.major}.{py_version.minor}")

check_step(2, "Checking Required Dependencies")
dependencies = {
    'torch': 'PyTorch (Deep Learning)',
    'transformers': 'Hugging Face Transformers',
    'surya': 'Surya OCR',
    'PIL': 'Pillow (Image Processing)',
    'flask': 'Flask (Web Server)',
    'cv2': 'OpenCV (Optional - Image Preprocessing)'
}

missing_deps = []
optional_missing = []

for module, description in dependencies.items():
    try:
        if module == 'PIL':
            import PIL
        elif module == 'cv2':
            import cv2
        else:
            __import__(module)
        success(f"{description} - installed")
    except ImportError as e:
        if module == 'cv2':
            warning(f"{description} - NOT installed (optional)")
            optional_missing.append(module)
        else:
            error(f"{description} - NOT installed")
            missing_deps.append(module)

if missing_deps:
    print()
    error("CRITICAL: Missing required dependencies!")
    info("Install with: pip install -r requirements.txt")
    sys.exit(1)

check_step(3, "Checking PyTorch Device Support")
try:
    import torch
    info(f"PyTorch version: {torch.__version__}")

    if torch.backends.mps.is_available():
        success("Apple Silicon GPU (MPS) - available")
        device = "mps"
    elif torch.cuda.is_available():
        success("NVIDIA GPU (CUDA) - available")
        device = "cuda"
    else:
        warning("GPU not available - using CPU (will be slower)")
        device = "cpu"

    info(f"Using device: {device}")
except Exception as e:
    error(f"PyTorch check failed: {e}")
    device = "cpu"

check_step(4, "Testing Surya OCR Model Loading")
try:
    from surya.model.detection.model import load_model as load_det_model
    from surya.model.recognition.model import load_model as load_rec_model

    info("Loading Surya detection model...")
    det_model = load_det_model()
    success("Detection model loaded")

    info("Loading Surya recognition model...")
    rec_model = load_rec_model()
    success("Recognition model loaded")

    info("Model loading successful!")

except Exception as e:
    error(f"Failed to load Surya models: {e}")
    error("This is likely why OCR is failing!")
    print()
    info("Possible solutions:")
    info("1. Check internet connection (models download on first run)")
    info("2. Check disk space (~1GB needed for models)")
    info("3. Try: pip install --upgrade surya-ocr")
    sys.exit(1)

check_step(5, "Testing LLAMA Model Access")
try:
    from transformers import AutoTokenizer
    model_id = "meta-llama/Llama-3.2-1B-Instruct"

    info(f"Checking access to {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    success("LLAMA model accessible")

except Exception as e:
    error(f"LLAMA model access failed: {e}")
    warning("You may need to:")
    info("1. Accept Meta's license at https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct")
    info("2. Login: huggingface-cli login")
    info("OCR will work but field extraction may fail")

check_step(6, "Checking Test Image")
test_image_path = None
common_locations = [
    "test_license.jpg",
    "sample.jpg",
    "license.png",
    "test.png"
]

for loc in common_locations:
    if os.path.exists(loc):
        test_image_path = loc
        success(f"Found test image: {test_image_path}")
        break

if not test_image_path:
    warning("No test image found")
    info("To test OCR, place a driver's license image as 'test_license.jpg'")
    test_image = False
else:
    test_image = True

check_step(7, "Testing Complete OCR Pipeline")
if test_image:
    try:
        from model_manager import ModelManager
        info("Initializing ModelManager...")

        manager = ModelManager()
        success(f"ModelManager initialized (device: {manager.device})")

        info(f"Running OCR on: {test_image_path}")
        predictions = manager.run_ocr([test_image_path])

        if predictions and len(predictions) > 0:
            ocr_text = "\n".join([line.text for line in predictions[0].text_lines])
            success(f"OCR extracted {len(ocr_text)} characters")

            print()
            info("First 500 characters of OCR output:")
            print("-" * 70)
            print(ocr_text[:500])
            print("-" * 70)

            if len(ocr_text.strip()) < 50:
                warning("OCR output is very short - image may be low quality")
                info("Try:")
                info("1. Use higher resolution image (at least 1000px width)")
                info("2. Ensure image is clear and well-lit")
                info("3. Check if image is actually a driver's license")
            else:
                success("OCR is working and extracting text!")

        else:
            error("OCR returned no results")
            info("Possible issues:")
            info("1. Image is corrupted or invalid format")
            info("2. Image is blank or too dark")
            info("3. Image contains no text")

    except Exception as e:
        error(f"OCR pipeline failed: {e}")
        import traceback
        print()
        info("Full error trace:")
        print(traceback.format_exc())
else:
    warning("Skipping pipeline test (no test image)")

check_step(8, "Summary & Recommendations")
print()

if missing_deps:
    error("FAILED: Missing critical dependencies")
    info("Run: pip install -r requirements.txt")
elif not test_image:
    success("System is ready!")
    info("Add a test image (test_license.jpg) to verify OCR extraction")
else:
    success("All checks passed!")
    info("Your OCR system should be working")

print()
print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print()

if optional_missing:
    print("OPTIONAL ENHANCEMENTS:")
    if 'cv2' in optional_missing:
        print("  • Install OpenCV for image preprocessing:")
        print("    pip install opencv-python-headless numpy")
    print()

print("NEXT STEPS:")
print("  1. Start the backend: python backend_surya_llama.py")
print("  2. Test via API: curl http://localhost:5001/health")
print("  3. Upload a driver's license image through the web interface")
print()
