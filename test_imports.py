#!/usr/bin/env python3
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 60)
print("Testing imports and basic functionality")
print("=" * 60)

try:
    print("\n1. Testing Flask...")
    from flask import Flask
    print("   ✓ Flask imported successfully")
except Exception as e:
    print(f"   ✗ Flask import failed: {e}")
    sys.exit(1)

try:
    print("\n2. Testing Supabase...")
    from supabase import create_client
    print("   ✓ Supabase imported successfully")
except Exception as e:
    print(f"   ✗ Supabase import failed: {e}")

try:
    print("\n3. Testing database.py...")
    from database import DatabaseManager
    print("   ✓ DatabaseManager imported successfully")
    db = DatabaseManager()
    print(f"   ✓ DatabaseManager instantiated (supabase={'connected' if db.supabase else 'not available'})")
except Exception as e:
    print(f"   ✗ DatabaseManager failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. Testing license_extractor.py...")
    from license_extractor import LicenseExtractor
    print("   ✓ LicenseExtractor imported successfully")
    extractor = LicenseExtractor()
    print("   ✓ LicenseExtractor instantiated")
except Exception as e:
    print(f"   ✗ LicenseExtractor failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n5. Testing model_manager.py...")
    from model_manager import ModelManager
    print("   ✓ ModelManager imported successfully")
    manager = ModelManager()
    print(f"   ✓ ModelManager instantiated (device={manager.device})")
except Exception as e:
    print(f"   ✗ ModelManager failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n6. Testing backend_surya_llama.py...")
    import backend_surya_llama
    print("   ✓ Backend module imported successfully")
except Exception as e:
    print(f"   ✗ Backend module failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Diagnostic test complete!")
print("=" * 60)
