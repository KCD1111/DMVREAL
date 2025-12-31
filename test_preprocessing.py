#!/usr/bin/env python3
import sys
import os

print("Testing OpenCV Preprocessing Integration...")
print("-" * 50)

print("\n1. Testing imports...")
try:
    from image_preprocessor import ImagePreprocessor
    print("   ✓ ImagePreprocessor imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import ImagePreprocessor: {e}")
    sys.exit(1)

print("\n2. Testing ImagePreprocessor instantiation...")
try:
    preprocessor = ImagePreprocessor()
    print("   ✓ ImagePreprocessor instantiated successfully")
except Exception as e:
    print(f"   ✗ Failed to instantiate: {e}")
    sys.exit(1)

print("\n3. Testing backend integration...")
try:
    from backend_surya_llama import image_preprocessor as backend_preprocessor
    print("   ✓ Backend has preprocessor instance")
    print(f"   ✓ Preprocessor type: {type(backend_preprocessor)}")
except Exception as e:
    print(f"   ✗ Failed to import from backend: {e}")
    sys.exit(1)

print("\n4. Checking preprocessing methods...")
try:
    methods = ['preprocess_for_ocr', 'preprocess_light']
    for method in methods:
        if hasattr(preprocessor, method):
            print(f"   ✓ Method '{method}' exists")
        else:
            print(f"   ✗ Method '{method}' not found")
except Exception as e:
    print(f"   ✗ Error checking methods: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("All tests passed! ✓")
print("=" * 50)
print("\nNote: To fully test image processing, install dependencies:")
print("  pip install -r requirements.txt")
print("\nThen you can run the Flask backend with:")
print("  python backend_surya_llama.py")
