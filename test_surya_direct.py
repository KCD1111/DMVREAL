#!/usr/bin/env python3
"""
Direct Surya OCR Test
Tests if Surya is extracting text from images correctly
"""

import sys
from model_manager import ModelManager
from PIL import Image
import os

print("="*70)
print("SURYA OCR DIRECT TEST")
print("="*70)
print()

# Check for test image
test_images = ['test_license.jpg', 'license.jpg', 'sample.jpg', 'test.png']
test_image = None

for img in test_images:
    if os.path.exists(img):
        test_image = img
        break

if not test_image:
    print("ERROR: No test image found!")
    print("Please place a driver's license image as 'test_license.jpg'")
    sys.exit(1)

print(f"Using test image: {test_image}")
print()

# Check image properties
img = Image.open(test_image)
print(f"Image properties:")
print(f"  Size: {img.size}")
print(f"  Mode: {img.mode}")
print(f"  Format: {img.format}")
print()

# Initialize model manager
print("Initializing ModelManager...")
manager = ModelManager()
print(f"Using device: {manager.device}")
print()

# Run OCR
print("Running Surya OCR...")
try:
    predictions = manager.run_ocr([test_image])
    print(f"✓ OCR completed successfully")
    print()
except Exception as e:
    print(f"✗ OCR FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Analyze predictions
print("="*70)
print("PREDICTION ANALYSIS")
print("="*70)
print()

print(f"Number of predictions: {len(predictions)}")
print()

if len(predictions) == 0:
    print("ERROR: No predictions returned!")
    print("This means Surya OCR failed to process the image")
    sys.exit(1)

for pred_idx, pred in enumerate(predictions):
    print(f"Prediction #{pred_idx}")
    print("-" * 70)
    print(f"  Type: {type(pred)}")
    print(f"  Attributes: {[attr for attr in dir(pred) if not attr.startswith('_')]}")
    print()

    # Check for text_lines attribute
    if hasattr(pred, 'text_lines'):
        print(f"  ✓ Has 'text_lines' attribute")
        print(f"  Number of text lines: {len(pred.text_lines)}")
        print()

        if len(pred.text_lines) == 0:
            print("  ✗ ERROR: text_lines is EMPTY!")
            print("  This means Surya detected NO text in the image")
            print()
            print("  Possible causes:")
            print("    - Image is too blurry or low quality")
            print("    - Image contains no readable text")
            print("    - Image is upside down or rotated")
            print("    - Surya model failed to load properly")
        else:
            print("  ✓ Text lines extracted successfully")
            print()
            print("  Extracted text:")
            print("  " + "=" * 68)

            all_text = []
            for line_idx, text_line in enumerate(pred.text_lines):
                if hasattr(text_line, 'text'):
                    text = text_line.text
                    all_text.append(text)
                    print(f"  [{line_idx:3d}] {text}")
                else:
                    print(f"  [{line_idx:3d}] ERROR: No 'text' attribute")
                    print(f"         Type: {type(text_line)}")
                    print(f"         Attributes: {dir(text_line)}")

            print("  " + "=" * 68)
            print()

            # Combine all text
            combined_text = "\n".join(all_text)
            print(f"  Total characters extracted: {len(combined_text)}")
            print()

            if len(combined_text.strip()) == 0:
                print("  ✗ ERROR: All text lines are EMPTY!")
                print("  Surya returned lines but they contain no text")
            else:
                print("  ✓ SUCCESS: Text extraction working!")
                print()
                print("  Full extracted text:")
                print("  " + "-" * 68)
                print(combined_text)
                print("  " + "-" * 68)

    else:
        print(f"  ✗ ERROR: No 'text_lines' attribute found!")
        print()
        print("  This suggests Surya OCR API has changed!")
        print()
        print("  Available attributes:")
        for attr in dir(pred):
            if not attr.startswith('_'):
                print(f"    - {attr}: {type(getattr(pred, attr, None))}")
        print()
        print("  Attempting alternative access methods...")

        # Try alternative methods
        if hasattr(pred, 'text'):
            print(f"  ✓ Found 'text' attribute: {pred.text[:200]}")
        if hasattr(pred, 'bboxes'):
            print(f"  ✓ Found 'bboxes' attribute: {len(pred.bboxes)} boxes")
        if isinstance(pred, dict):
            print(f"  ✓ Prediction is a dict: {list(pred.keys())}")

print()
print("="*70)
print("TEST COMPLETE")
print("="*70)
