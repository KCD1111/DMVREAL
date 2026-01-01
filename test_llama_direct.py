#!/usr/bin/env python3
"""
Direct LLAMA Extraction Test
Tests if LLAMA is extracting fields from OCR text correctly
"""

from model_manager import ModelManager

print("="*70)
print("LLAMA FIELD EXTRACTION DIRECT TEST")
print("="*70)
print()

# Sample OCR text from a Kentucky driver's license
test_text = """
1 JOHN
2 DOE SMITH
3 DOB 01/15/1985
4d DLN D123-456-789-000
4b EXP 01/15/2028
8 123 E MAIN ST
LEXINGTON KY 40508
15 SEX M
"""

print("Test OCR Input:")
print("-" * 70)
print(test_text)
print("-" * 70)
print()

# Initialize model manager
print("Initializing ModelManager...")
manager = ModelManager()
print(f"Using device: {manager.device}")
print()

# Run LLAMA extraction
print("Running LLAMA field extraction...")
try:
    extracted = manager.extract_fields_with_llama(test_text)
    print("✓ Extraction completed successfully")
    print()
except Exception as e:
    print(f"✗ LLAMA EXTRACTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Display results
print("="*70)
print("EXTRACTION RESULTS")
print("="*70)
print()

all_null = True
for key, value in extracted.items():
    status = "✓" if value is not None else "✗"
    print(f"{status} {key:20s}: {value}")
    if value is not None:
        all_null = False

print()

if all_null:
    print("="*70)
    print("ERROR: ALL FIELDS ARE NULL!")
    print("="*70)
    print()
    print("This means LLAMA is NOT extracting any data from the OCR text.")
    print()
    print("Possible causes:")
    print("  1. LLAMA model not loaded correctly")
    print("  2. Prompt format incompatible with model")
    print("  3. Model not understanding the instruction")
    print("  4. JSON parsing failing")
    print()
    print("Expected values from test text:")
    print("  first_name: JOHN")
    print("  last_name: DOE SMITH")
    print("  dln: D123-456-789-000")
    print("  date_of_birth: 01/15/1985")
    print("  expiration_date: 01/15/2028")
    print("  street_address: 123 E MAIN ST")
    print("  city: LEXINGTON")
    print("  state: KY")
    print("  zip_code: 40508")
    print("  sex: M")
else:
    print("="*70)
    print("SUCCESS: LLAMA extracted at least some fields")
    print("="*70)
    print()

    # Validate extracted data
    expected = {
        'first_name': 'John',
        'last_name': 'Doe Smith',
        'dln': 'D123-456-789-000',
        'date_of_birth': '01/15/1985',
        'expiration_date': '01/15/2028',
        'street_address': '123 E Main St',
        'city': 'Lexington',
        'state': 'KY',
        'zip_code': '40508',
        'sex': 'M'
    }

    print("Validation:")
    print("-" * 70)

    correct = 0
    total = 0

    for field, expected_value in expected.items():
        actual_value = extracted.get(field)
        total += 1

        if actual_value is None:
            print(f"✗ {field:20s}: Missing (expected: {expected_value})")
        elif str(actual_value).lower() == str(expected_value).lower():
            print(f"✓ {field:20s}: Correct")
            correct += 1
        else:
            print(f"⚠ {field:20s}: Mismatch")
            print(f"     Expected: {expected_value}")
            print(f"     Got:      {actual_value}")

    print("-" * 70)
    print(f"Accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
    print()

print("="*70)
print("TEST COMPLETE")
print("="*70)
