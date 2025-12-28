import datetime
import re
import os
import sys
import subprocess  # Required to call the external OCRmyPDF command

# Try importing PyPDF2, fallback to pypdf if needed
try:
    import PyPDF2
except ImportError:
        print("ERROR: Neither PyPDF2 nor pypdf is installed. Please install one with: pip install PyPDF2")
        raise

# --- 1. Define Document Schema ---
document_schema = {
    'first_name': {
        'type': 'string',
        'required': True
    },
    'last_name': {
        'type': 'string',
        'required': True
    },
    'license_number': {
        'type': 'string',
        'required': True,
        'format': 'alphanumeric'
    },
    'date_of_birth': {
        'type': 'date',
        'required': True,
        'format': 'MM/DD/YYYY'
    },
    'expiration_date': {
        'type': 'date',
        'required': True,
        'format': 'MM/DD/YYYY'
    },
    'address': {
        'type': 'string',
        'required': False
    },
    'sex': {
        'type': 'string',
        'required': False,
        'allowed_values': ['M', 'F']
    }
}
print("Document Schema Defined.")

## 2. OCRmyPDF and Data Extraction
def run_ocrmypdf(input_pdf_path, output_pdf_path):
    """
    Calls OCRmyPDF command line utility to add a text layer.
    NOTE: This requires OCRmyPDF to be installed and accessible via your system's PATH.
    """
    print(f"\n--- Running OCRmyPDF on {input_pdf_path} ---")
    try:
        subprocess.run(['ocrmypdf', '--output-type', 'pdfa', input_pdf_path, output_pdf_path], check=True)
        print(f"OCRmyPDF executed successfully. Result saved to {output_pdf_path}.")
        return True
    except FileNotFoundError:
        print("\nERROR: OCRmyPDF command not found. Ensure it is installed and in your system PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: OCRmyPDF failed with return code {e.returncode}. Output:\n{e.output}")
        return False

def extract_structured_data(ocr_pdf_path):
    """
    Extracts structured key-value data from the text layer in the OCR'd PDF.
    Uses PyPDF2 to read text, then regex tailored to Kentucky driver's license numbered layout.
    """
    print(f"\n--- Extracting from OCR'd PDF: {ocr_pdf_path} ---")
    extracted_data = {}
    try:
        # Check if file exists before trying to open it
        if not os.path.exists(ocr_pdf_path):
            print(f"ERROR: File not found: {ocr_pdf_path}")
            return extracted_data
        
        with open(ocr_pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        
        if not text.strip():
            print("WARNING: No text extracted from PDF. OCR may have failed or PDF is empty.")
            return extracted_data
        
        # Kentucky-specific parsing (adjust if needed for other states)
        # Last name (after '1')
        last_name_match = re.search(r'1\s+([A-Z\s]+)', text, re.I | re.M)
        if last_name_match:
            extracted_data['last_name'] = last_name_match.group(1).strip()
        
        # First name (and middle, after '2')
        first_name_match = re.search(r'2\s+([A-Z\s]+)', text, re.I | re.M)
        if first_name_match:
            extracted_data['first_name'] = first_name_match.group(1).strip()
        
        # Address (lines between '2' name and '3 DOB')
        address_match = re.search(r'2\s+[A-Z\s]+\n\s*(.+?)\n\s*(.+?)\n\s*3 DOB', text, re.I | re.S)
        if address_match:
            extracted_data['address'] = address_match.group(1).strip() + ', ' + address_match.group(2).strip()
        
        # License number
        license_match = re.search(r'DLN\s+([A-Z0-9\-]+)', text, re.I | re.M)
        if license_match:
            extracted_data['license_number'] = license_match.group(1).strip()
        
        # Date of birth
        dob_match = re.search(r'DOB\s+(\d{2}/\d{2}/\d{4})', text, re.I | re.M)
        if dob_match:
            extracted_data['date_of_birth'] = dob_match.group(1).strip()
        
        # Expiration date
        exp_match = re.search(r'EXP\s+(\d{2}/\d{2}/\d{4})', text, re.I | re.M)
        if exp_match:
            extracted_data['expiration_date'] = exp_match.group(1).strip()
        
        # Sex
        sex_match = re.search(r'SEX\s+([MF])', text, re.I | re.M)
        if sex_match:
            extracted_data['sex'] = sex_match.group(1).strip()
        
        print("Extracted Structured Data:")
        print(extracted_data)
        return extracted_data
    except Exception as e:
        print(f"ERROR during extraction: {e}")
        return extracted_data

def normalize_ocr_data(ocr_data, document_schema):
    """
    Normalize keys and values from OCR output to better match the document schema.
    - Map common synonyms to canonical field names (e.g., 'gender' -> 'sex')
    - Normalize gender values to single-letter codes
    - Normalize dates into MM/DD/YYYY when possible
    - Clean license numbers to alphanumeric only
    """
    normalized = {}
    # common synonyms mapping
    key_map = {
        'sex': 'sex',
        'dob': 'date_of_birth',
        'EXP': 'expiration_date',
        'DLN': 'license_number',
        'full_name': None,  # handled specially
        'name': None
    }
    # helper to parse dates in common formats and convert to MM/DD/YYYY
    def normalize_date(val):
        if not isinstance(val, str):
            return val
        val = val.strip()
        # try common date formats
        for fmt in ('%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                return dt.strftime('%m/%d/%Y')
            except Exception:
                continue
        return val
    # helper to normalize gender values
    def normalize_gender(val):
        if not isinstance(val, str):
            return val
        v = val.strip().upper()
        if v in ('M', 'MALE'):
            return 'M'
        if v in ('F', 'FEMALE'):
            return 'F'
        if v in ('X', 'OTHER'):
            return 'X'
        return val
    # iterate input keys and map them
    for k, v in ocr_data.items():
        k_norm = k.strip().lower()
        target = key_map.get(k_norm, None)
        if target is None:
            # if key not in map but matches a schema key, use it
            if k_norm in document_schema:
                target = k_norm
            else:
                target = k_norm
        # handle combined name fields (if extracted as 'full_name')
        if k_norm in ('full_name', 'name') and isinstance(v, str):
            parts = v.strip().split()
            if len(parts) >= 2:
                normalized.setdefault('first_name', parts[0])
                normalized.setdefault('last_name', ' '.join(parts[1:]))
            else:
                normalized.setdefault('first_name', parts[0])
            continue
        # normalize specific value types
        if target == 'date_of_birth' or target == 'expiration_date':
            v = normalize_date(v)
        if target == 'sex':
            v = normalize_gender(v)
        if target == 'license_number' and isinstance(v, str):
            v = re.sub(r'[^A-Za-z0-9]', '', v)
        # standard trimming for strings
        if isinstance(v, str):
            v = v.strip()
        normalized[target] = v
    # ensure canonical keys from schema exist (even if missing) so validation reports them
    for schema_key in document_schema.keys():
        if schema_key not in normalized:
            normalized[schema_key] = None
    print('\nNormalized OCR data (pre-validation):')
    print(normalized)
    return normalized

# --- 3. Validation Function ---
def validate_ocr_data(ocr_data, document_schema):
    """Validates extracted OCR data against a defined schema."""
    validation_report = {
        'missing_fields': [],
        'type_mismatches': [],
        'format_errors': [],
        'value_out_of_range': [],
        'invalid_values': []
    }
    today = datetime.date.today()
    for field_name, schema_props in document_schema.items():
        field_value = ocr_data.get(field_name)
        # 1. Check for missing required fields
        if schema_props.get('required') and (field_value is None or (isinstance(field_value, str) and field_value.strip() == '')):
            validation_report['missing_fields'].append(field_name)
            continue
        # If field is not required and not present, skip further validation for it.
        if field_value is None and not schema_props.get('required'):
            continue
        # 2. Check for type mismatches
        expected_type = schema_props.get('type')
        has_type_mismatch = False
        if expected_type and field_value is not None:
            if expected_type == 'string':
                if not isinstance(field_value, str):
                    validation_report['type_mismatches'].append({'field': field_name, 'expected': expected_type, 'actual': type(field_value).__name__})
                    has_type_mismatch = True
            elif expected_type == 'date':
                if not isinstance(field_value, str):
                    validation_report['type_mismatches'].append({'field': field_name, 'expected': expected_type, 'actual': type(field_value).__name__})
                    has_type_mismatch = True
        if has_type_mismatch:
            continue
        # 3. Check for format errors (e.g., date formats)
        if expected_type == 'date' and field_value is not None:
            date_format = schema_props.get('format')
            if date_format:
                try:
                    if date_format == 'MM/DD/YYYY':
                        dt = datetime.datetime.strptime(field_value, '%m/%d/%Y').date()
                        # Optional: Check if expiration is in the future
                        if field_name == 'expiration_date' and dt < today:
                            validation_report['value_out_of_range'].append({'field': field_name, 'issue': 'Expired', 'actual_value': field_value})
                except ValueError:
                    validation_report['format_errors'].append({'field': field_name, 'expected_format': date_format, 'actual_value': field_value})
        # 4. Check for value constraints (e.g., allowed_values)
        allowed_values = schema_props.get('allowed_values')
        if allowed_values and field_value is not None and field_value not in allowed_values:
            validation_report['invalid_values'].append({'field': field_name, 'expected_one_of': allowed_values, 'actual_value': field_value})
        # Add simple alphanumeric check for license number
        if field_name == 'license_number' and schema_props.get('format') == 'alphanumeric' and field_value is not None:
            if not re.match(r'^[a-zA-Z0-9]+$', field_value):
                validation_report['format_errors'].append({'field': field_name, 'expected_format': 'alphanumeric', 'actual_value': field_value})
    return validation_report
print("Validation function 'validate_ocr_data' finalized.")

## 4. Execution and Reporting
# 1. Define input/output paths
INPUT_PDF = '/Users/octane.hinojosa/Downloads/OCR_Project copy 2.py/sampleREAL-ID.pdf' # Update this path if needed

# Verify input file exists
if not os.path.exists(INPUT_PDF):
    print(f"ERROR: Input PDF not found: {INPUT_PDF}")
    print("Please check the file path and ensure the PDF file exists.")
    sys.exit(1)

# Make output path absolute (in same directory as input)
input_dir = os.path.dirname(INPUT_PDF)
OUTPUT_PDF = os.path.join(input_dir, 'document_ocrd.pdf')

# 2. Run OCRmyPDF (actual)
ocr_success = run_ocrmypdf(INPUT_PDF, OUTPUT_PDF)

# 3. Extract Structured Data (actual)
# If OCR failed, try extracting from original PDF as fallback
if ocr_success and os.path.exists(OUTPUT_PDF):
    ocr_data = extract_structured_data(OUTPUT_PDF)
else:
    print("\n--- OCR failed or output not found. Attempting extraction from original PDF ---")
    ocr_data = extract_structured_data(INPUT_PDF)

# 3.5 Normalize extracted data
ocr_data_normalized = normalize_ocr_data(ocr_data, document_schema)

# 4. Run Validation Logic
report = validate_ocr_data(ocr_data_normalized, document_schema)

print("\n\n--- FINAL VALIDATION REPORT ---")
has_discrepancies = False
for category, findings in report.items():
    if findings:
        has_discrepancies = True
        print(f"\n **{category.replace('_', ' ').upper()}:**")
        for item in findings:
            if isinstance(item, dict):
                details = ", ".join([f"**{k}**: {v}" for k, v in item.items()])
                print(f" - {details}")
            else:
                print(f" - {item}")
if has_discrepancies:
    print("\n **SUMMARY:** Validation completed with critical discrepancies found. Review required.")
else:
    print("\n **SUMMARY:** Validation completed successfully. No discrepancies found.")