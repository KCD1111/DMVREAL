import datetime
import re
import subprocess # Required to call the external OCRmyPDF command

# --- 1. Define Document Schema (Same as yours) ---

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


## 2. Simulate OCRmyPDF and Data Extraction

def run_ocrmypdf(input_pdf_path, output_pdf_path):
    """
    Simulates calling OCRmyPDF command line utility.
    NOTE: This requires OCRmyPDF to be installed and accessible via your system's PATH.
    """
    print(f"\n--- Simulating OCRmyPDF execution on {input_pdf_path} ---")
    try:
        # The actual command you'd run in your terminal:
        # ocrmypdf --output-type pdfa <input_path> <output_path>
        
        # We'll skip the actual execution for this environment, but this is the code:
        # subprocess.run(['ocrmypdf', '--output-type', 'pdfa', input_pdf_path, output_pdf_path], check=True)
        
        print(f"OCRmyPDF simulated successfully. Result saved to {output_pdf_path} (if run externally).")
        return True
    except FileNotFoundError:
        print("\nERROR: OCRmyPDF command not found. Ensure it is installed and in your system PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: OCRmyPDF failed with return code {e.returncode}. Output:\n{e.output}")
        return False

def extract_structured_data(ocr_pdf_path):
    """
    Simulates the AI/Plugin step that extracts structured key-value data 
    from the text layer created by OCRmyPDF.
    
    This function replaces your original 'ocr_data' dictionary creation.
    """
    print(f"\n--- Simulating AI extraction from OCR'd PDF: {ocr_pdf_path} ---")
    
    # This is the SIMULATED output data from the AI extraction
    # It includes the intentional errors from your original code for testing validation
    simulated_extracted_data = {
        'first_name': 'JOHN',
        'last_name': 'DOE',
        # Intentionally missing 'license_number' to test the missing_fields check
        'date_of_birth': '1990-01-01',
        'expiration_date': '2022/12/31', # Incorrect date format
        'address': '123 Main St, Anytown, USA',
        'gender': 'Male' # Invalid value (should be 'M', 'F', or 'X')
    }
    
    # Adding a missing field for a robust test
    del simulated_extracted_data['last_name']
    
    print("Simulated Structured Data Extracted for Validation:")
    print(simulated_extracted_data)
    return simulated_extracted_data


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
        'gender': 'sex',
        'sex': 'sex',
        'dob': 'date_of_birth',
        'birth_date': 'date_of_birth',
        'dateofbirth': 'date_of_birth',
        'expiry': 'expiration_date',
        'exp_date': 'expiration_date',
        'expiration': 'expiration_date',
        '4d DLN': 'license_number',
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
                # leave unknown keys as-is for now
                target = k_norm

        # handle combined name fields
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
            # remove spaces and non-alphanumeric characters
            v = re.sub(r'[^A-Za-z0-9]', '', v)

        # standard trimming for strings
        if isinstance(v, str):
            v = v.strip()

        normalized[target] = v

    # ensure canonical keys from schema exist (even if missing) so validation reports them
    for schema_key in document_schema.keys():
        if schema_key not in normalized:
            # keep None to indicate missing
            normalized[schema_key] = None

    print('\nNormalized OCR data (pre-validation):')
    print(normalized)
    return normalized

# --- 3. Implement AI API Plugin Logic (Your existing validation function) ---

def validate_ocr_data(ocr_data, document_schema):
    """Validates extracted OCR data against a defined schema."""
    validation_report = {
        'missing_fields': [],
        'type_mismatches': [],
        'format_errors': [],
        'value_out_of_range': [],
        'invalid_values': []
    }

    for field_name, schema_props in document_schema.items():
        field_value = ocr_data.get(field_name)

        # 1. Check for missing required fields
        # Treat None or empty strings as missing (normalization may add keys with None)
        if schema_props.get('required') and (field_value is None or (isinstance(field_value, str) and field_value.strip() == '')):
            validation_report['missing_fields'].append(field_name)
            continue
        
        # If field is not required and not present, skip further validation for it.
        if field_value is None and not schema_props.get('required'):
            continue

        # 2. Check for type mismatches (simplified for this example)
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
                        datetime.datetime.strptime(field_value, '%m/%d/%Y')
                except ValueError:
                    validation_report['format_errors'].append({'field': field_name, 'expected_format': date_format, 'actual_value': field_value})
                    continue

        # 4. Check for value constraints (e.g., allowed_values)
        allowed_values = schema_props.get('allowed_values')
        if allowed_values and field_value is not None and field_value not in allowed_values:
            validation_report['invalid_values'].append({'field': field_name, 'expected_one_of': allowed_values, 'actual_value': field_value})
            
        # Add simple alphanumeric check for license number (example of 'format')
        if field_name == 'license_number' and schema_props.get('format') == 'alphanumeric' and field_value is not None:
            if not re.match(r'^[a-zA-Z0-9]+$', field_value):
                validation_report['format_errors'].append({'field': field_name, 'expected_format': 'alphanumeric', 'actual_value': field_value})


    return validation_report

print("Validation function 'validate_ocr_data' finalized.")


## 4. Execution and Reporting

# 1. Define input/output paths (hypothetical)
INPUT_PDF = '/Users/octane.hinojosa/Downloads/OCR_Project.py/document_to_ocr.pdf'
OUTPUT_PDF = 'document_ocrd.pdf'

# 2. Run OCRmyPDF (Simulated here)
# The output is an OCR-enabled PDF with a searchable text layer.
ocr_data = run_ocrmypdf(INPUT_PDF, OUTPUT_PDF)

# 3. Extract Structured Data (Simulated AI/Plugin step)
#ocr_data = extract_structured_data(OUTPUT_PDF)

# 3.5 Normalize extracted data to match schema keys/formats
ocr_data_normalized = normalize_ocr_data(INPUT_PDF, document_schema)

# 4. Run your Validation Logic
report = validate_ocr_data(ocr_data_normalized, document_schema)

print("\n\n--- 📝 FINAL VALIDATION REPORT ---")

has_discrepancies = False
for category, findings in report.items():
    if findings:
        has_discrepancies = True
        print(f"\n🛑 **{category.replace('_', ' ').upper()}:**")
        for item in findings:
            if isinstance(item, dict):
                details = ", ".join([f"**{k}**: {v}" for k, v in item.items()])
                print(f"  - {details}")
            else:
                print(f"  - {item}")

if has_discrepancies:
    print("\n✅ **SUMMARY:** Validation completed with critical discrepancies found. Review required.")
else:
    print("\n✅ **SUMMARY:** Validation completed successfully. No discrepancies found.")
    