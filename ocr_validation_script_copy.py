import datetime
import re
import subprocess
from PyPDF2 import PdfReader
from PyPDF2.errors import EmptyFileError, PdfReadError

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
        'format': 'alphanumeric' # This expects ONLY letters/numbers (no dashes)
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


# --- 2. Simulate OCRmyPDF and Data Extraction ---

def run_ocrmypdf(input_pdf_path, output_pdf_path):
    """
    Simulates calling OCRmyPDF.
    """
    print(f"\n--- Simulating OCRmyPDF execution on {input_pdf_path} ---")
    # In a real scenario, subprocess.run would happen here.
    print(f"OCRmyPDF simulated successfully. Result saved to {output_pdf_path}.")
    return True

def extract_structured_data_from_pdf_content(pdf_path):
    """
    Extracts raw data from the actual PDF file.
    """
    print(f"\n--- Extracting data from PDF: {pdf_path} ---")
    
    try:
        # Open and read the PDF
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            # Extract text from all pages
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
        
        print(f"Raw PDF Text Extracted:\n{extracted_text}\n")
        
        # Parse the extracted text to get structured data
        # This is a basic parser - you may need to adjust based on your PDF format
        raw_extracted_data = {
            'first_name': '',
            'last_name': '',
            'license_number': '',
            'date_of_birth': '',
            'expiration_date': '',
            'address': '',
            'sex': ''
        }
        
        lines = extracted_text.split('\n')
        for line in lines:
            line = line.strip()
            if 'DOB' in line.upper() or 'DATE OF BIRTH' in line.upper():
                # Extract date of birth
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if match:
                    raw_extracted_data['date_of_birth'] = match.group(1)
            elif 'EXP' in line.upper() or 'EXPIRATION' in line.upper():
                # Extract expiration date
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                if match:
                    raw_extracted_data['expiration_date'] = match.group(1)
            elif 'SEX' in line.upper():
                # Extract sex
                match = re.search(r'([MF])', line.upper())
                if match:
                    raw_extracted_data['sex'] = match.group(1)
            elif 'DLN' in line.upper():
                # Extract license number
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'DLN' in part.upper() and i + 1 < len(parts):
                        raw_extracted_data['license_number'] = parts[i + 1]
        
        print("Extracted Data:")
        print(raw_extracted_data)
        return raw_extracted_data
        
    except FileNotFoundError:
        print(f"Error: PDF file '{pdf_path}' not found.")
        return {
            'first_name': '',
            'last_name': '',
            'license_number': '',
            'date_of_birth': '',
            'expiration_date': '',
            'address': '',
            'sex': ''
        }
    except EmptyFileError:
        print(f"Error: PDF file '{pdf_path}' is empty or corrupted.")
        return {
            'first_name': '',
            'last_name': '',
            'license_number': '',
            'date_of_birth': '',
            'expiration_date': '',
            'address': '',
            'sex': ''
        }
    except (PdfReadError, Exception) as e:
        print(f"Error reading PDF file '{pdf_path}': {str(e)}")
        return {
            'first_name': '',
            'last_name': '',
            'license_number': '',
            'date_of_birth': '',
            'expiration_date': '',
            'address': '',
            'sex': ''
        }


def normalize_ocr_data(ocr_data, document_schema):
    """
    Clean and Normalize data before validation.
    """
    normalized = {}
    print('\n--- Normalizing Data ---')

    # Iterate over the raw data and clean it up
    for key, val in ocr_data.items():
        clean_val = val
        
        # 1. Normalize Dates
        if key in ['date_of_birth', 'expiration_date']:
            # Ensure it is a string and stripped
            if isinstance(val, str):
                clean_val = val.strip()

        # 2. Normalize License Number (Remove dashes)
        if key == 'license_number' and isinstance(val, str):
            # This regex replaces anything that is NOT a letter or number with empty string
            clean_val = re.sub(r'[^A-Za-z0-9]', '', val)
            print(f"  > Cleaned License Number: '{val}' -> '{clean_val}'")

        # 3. Normalize Gender/Sex
        if key == 'sex' and isinstance(val, str):
            clean_val = val.upper().strip()

        normalized[key] = clean_val

    # Ensure all schema keys exist (fill with None if missing)
    for schema_key in document_schema.keys():
        if schema_key not in normalized:
            normalized[schema_key] = None

    return normalized

# --- 3. Validation Logic ---

def validate_ocr_data(ocr_data, document_schema):
    """Validates normalized data against schema."""
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
        if schema_props.get('required') and (field_value is None or field_value == ''):
            validation_report['missing_fields'].append(field_name)
            continue
        
        # Skip validation for optional fields that are None or empty
        if not schema_props.get('required') and (field_value is None or field_value == ''):
            continue

        # 2. Check for type mismatches
        expected_type = schema_props.get('type')
        if expected_type == 'string' and not isinstance(field_value, str):
            validation_report['type_mismatches'].append({'field': field_name, 'expected': 'string', 'actual': type(field_value).__name__})
            continue

        # 3. Check for format errors
        # Date Check
        if expected_type == 'date' and isinstance(field_value, str):
            date_format = schema_props.get('format')
            if date_format == 'MM/DD/YYYY':
                try:
                    datetime.datetime.strptime(field_value, '%m/%d/%Y')
                except (ValueError, TypeError):
                    validation_report['format_errors'].append({'field': field_name, 'expected_format': date_format, 'actual_value': field_value})

        # Alphanumeric Check
        if schema_props.get('format') == 'alphanumeric' and isinstance(field_value, str):
            if not re.match(r'^[a-zA-Z0-9]+$', field_value):
                validation_report['format_errors'].append({'field': field_name, 'expected_format': 'alphanumeric', 'actual_value': field_value})

        # 4. Check for allowed values (Sex/Gender)
        allowed_values = schema_props.get('allowed_values')
        if allowed_values and isinstance(field_value, str) and field_value.strip() and field_value not in allowed_values:
            validation_report['invalid_values'].append({'field': field_name, 'expected_one_of': allowed_values, 'actual_value': field_value})

    return validation_report

print("Validation function finalized.")


# --- 4. Execution ---

INPUT_PDF = 'sample,REAL-ID.pdf'
OUTPUT_PDF = 'sample,REAL-ID_ocrd.pdf'

# 1. Simulate OCR execution
run_ocrmypdf(INPUT_PDF, OUTPUT_PDF)

# 2. Extract Data from the actual PDF file
raw_ocr_data = extract_structured_data_from_pdf_content(INPUT_PDF)

# 3. Normalize Data (Crucial step to fix the dashes in license number)
ocr_data_normalized = normalize_ocr_data(raw_ocr_data, document_schema)

# 4. Validate
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
    print("\n✅ **SUMMARY:** Validation completed with critical discrepancies found.")
else:
    print("\n✅ **SUMMARY:** Validation completed successfully. No discrepancies found.")