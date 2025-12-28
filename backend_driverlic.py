from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import re
import subprocess
import pdfplumber
import tempfile
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# --- Document Schema ---
document_schema = {
    'first_name': {'type': 'string', 'required': True},
    'last_name': {'type': 'string', 'required': True},
    'license_number': {'type': 'string', 'required': True, 'format': 'alphanumeric'},
    'date_of_birth': {'type': 'date', 'required': True, 'format': 'MM/DD/YYYY'},
    'expiration_date': {'type': 'date', 'required': True, 'format': 'MM/DD/YYYY'},
    'street_address': {'type': 'string', 'required': False},
    'city': {'type': 'string', 'required': False},
    'state': {'type': 'string', 'required': False},
    'zip_code': {'type': 'string', 'required': False},
    'sex': {'type': 'string', 'required': False, 'allowed_values': ['M', 'F']}
}

def run_ocrmypdf(input_pdf_path, output_pdf_path):
    """Calls OCRmyPDF to create a searchable PDF."""
    try:
        subprocess.run(
            ['ocrmypdf', '--output-type', 'pdfa', '--skip-text', input_pdf_path, output_pdf_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except FileNotFoundError:
        raise Exception("OCRmyPDF not found. Please install it first.")
    except subprocess.CalledProcessError as e:
        raise Exception(f"OCRmyPDF failed: {e.stderr}")
    except Exception as e:
        raise Exception(f"OCR error: {str(e)}")

def extract_structured_data(ocr_pdf_path):
    """Extracts structured data from OCR'd PDF using regex patterns."""
    full_text = ""
    data = {}

    try:
        with pdfplumber.open(ocr_pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Failed to read PDF: {str(e)}")

    if full_text.strip() == "":
        raise Exception("No text could be extracted from the PDF")
    print("\n=== RAW OCR TEXT ===")
    print(full_text[:1000])
    print("=" * 50)

    # Extract License Number
    license_match = re.search(r'(?:DLN|Driver(?:\'|\')?s?\s+License|License)\b[\s\S]*?([0-9]{3}-[0-9]{3}-[0-9]{3})', full_text, re.IGNORECASE)
    if license_match:
        data['license_number'] = 'S' + license_match.group(1)

    # Extract Date of Birth
    dob_match = re.search(r'(Date of Birth|DOB|3008)[:\s]*(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})', full_text, re.IGNORECASE)
    if dob_match:
        data['date_of_birth'] = dob_match.group(2)

    # Extract Sex
    sex_match = re.search(r'Sex[:\s]*(Male|Female|M|F)', full_text, re.IGNORECASE)
    if sex_match:
        data['sex'] = sex_match.group(1)

    # Extract Expiration Date
    exp_match = re.search(r'(Expiration Date|Expiry|exe)[:\s]*(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})', full_text, re.IGNORECASE)
    if exp_match:
        data['expiration_date'] = exp_match.group(2)

    # Extract Address (including City, State, and Zip)
    # Try comprehensive pattern first
# === ENHANCED ADDRESS EXTRACTION ===
    
    # Method 1: Try to extract complete address with city, state, zip
    full_address_pattern = re.compile(
        r'(\d{1,6}\s+[A-Z0-9\s]+?(?:ST|STREET|RD|ROAD|AVE|AVENUE|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|HWY|PKWY|PL|TER|WAY|CIR)\.?)' +  # Street
        r'\s*,?\s*' +  # Optional comma
        r'([A-Z][A-Za-z\s]+?)' +  # City
        r'\s*,?\s*' +  # Optional comma
        r'([A-Z]{2})' +  # State (2 letters)
        r'\s+' +
        r'(\d{5}(?:-\d{4})?)',  # Zip code
        re.IGNORECASE
    )
    
    full_match = full_address_pattern.search(full_text)
    if full_match:
        street = full_match.group(1).strip()
        city = full_match.group(2).strip()
        state = full_match.group(3).strip().upper()
        zip_code = full_match.group(4).strip()
        
        data['street_address'] = street
        data['city'] = city
        data['state'] = state
        data['zip_code'] = zip_code
        
        print(f"\n✓ Found complete address:")
        print(f"  Street: {street}")
        print(f"  City: {city}")
        print(f"  State: {state}")
        print(f"  Zip: {zip_code}")
    else:
        # Method 2: Try to extract components separately
        print("\n⚠ Complete address pattern not found, trying separate extraction...")
        
        # Extract street address
        street_pattern = re.compile(
            r'\b(\d{1,6}\s+(?:[NSEW]\s+)?[A-Z0-9]+(?:\s+[A-Z0-9]+)*\s+(?:ST|STREET|RD|ROAD|AVE|AVENUE|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|HWY|PKWY|PL|TER|WAY|CIR)\.?)\b',
            re.IGNORECASE
        )
        street_match = street_pattern.search(full_text)
        if street_match:
            data['street_address'] = street_match.group(1).strip()
            print(f"  ✓ Street: {data['street_address']}")
        
        # Extract city - look for pattern after street address
        if 'street_address' in data:
            # Try to find city after the street address
            street_pos = full_text.find(data['street_address'])
            if street_pos != -1:
                after_street = full_text[street_pos + len(data['street_address']):street_pos + len(data['street_address']) + 100]
                city_pattern = re.compile(r'[,\s]+([A-Z][A-Za-z\s]{2,25})[,\s]+([A-Z]{2})\s+(\d{5})', re.IGNORECASE)
                city_match = city_pattern.search(after_street)
                if city_match:
                    data['city'] = city_match.group(1).strip()
                    data['state'] = city_match.group(2).strip().upper()
                    data['zip_code'] = city_match.group(3).strip()
                    print(f"  ✓ City: {data['city']}")
                    print(f"  ✓ State: {data['state']}")
                    print(f"  ✓ Zip: {data['zip_code']}")
        
        # Last resort: look for standalone state and zip
        if 'state' not in data:
            state_zip_pattern = re.compile(r'\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b')
            state_zip_match = state_zip_pattern.search(full_text)
            if state_zip_match:
                data['state'] = state_zip_match.group(1).upper()
                data['zip_code'] = state_zip_match.group(2)
                print(f"  ✓ State: {data['state']}")
                print(f"  ✓ Zip: {data['zip_code']}")

    # Extract First Name
    first_name_match = re.search(r'~ \+([A-Z]+)', full_text)
    if first_name_match:
        data['first_name'] = first_name_match.group(1)

    # Extract Last Name
    last_name_match = re.search(r'(?:^|\n)[^A-Za-z]*([A-Z]+ [A-Z]+)(?!.*LICENSE)', full_text)
    if last_name_match:
        data['last_name'] = last_name_match.group(1)

    return data, full_text

def normalize_ocr_data(ocr_data, document_schema):
    """Normalize keys and values from OCR output."""
    normalized = {}

    key_map = {
        'gender': 'sex',
        'dob': 'date_of_birth',
        'birth_date': 'date_of_birth',
        'expiry': 'expiration_date',
        'exp_date': 'expiration_date',
        'DLN': 'license_number',
        # Keep address fields separate
        'street_address': 'street_address',
        'city': 'city',
        'state': 'state',
        'zip_code': 'zip_code',
        'sex': 'sex'
    }

    def normalize_date(val):
        if not isinstance(val, str): 
            return val
        val = val.strip()
        for fmt in ('%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                return dt.strftime('%m/%d/%Y')
            except Exception:
                continue
        return val

    def normalize_gender(val):
        if not isinstance(val, str): 
            return val
        v = val.strip().upper()
        if v in ('M', 'MALE'): 
            return 'M'
        if v in ('F', 'FEMALE'): 
            return 'F'
        return val

    for k, v in ocr_data.items():
        k_norm = k.strip().lower()
        target = key_map.get(k_norm, k_norm if k_norm in document_schema else None)

        if target:
            if target in ('date_of_birth', 'expiration_date'):
                v = normalize_date(v)
            elif target == 'sex':
                v = normalize_gender(v)
            elif target == 'license_number' and isinstance(v, str):
                v = re.sub(r'[^A-Za-z0-9]', '', v)

            if isinstance(v, str):
                v = v.strip()

            normalized[target] = v

    for schema_key in document_schema.keys():
        if schema_key not in normalized:
            normalized[schema_key] = None

    return normalized

def validate_ocr_data(ocr_data, document_schema):
    """Validates extracted OCR data against schema."""
    validation_report = {
        'missing_fields': [], 
        'type_mismatches': [], 
        'format_errors': [],
        'value_out_of_range': [], 
        'invalid_values': []
    }

    for field_name, schema_props in document_schema.items():
        field_value = ocr_data.get(field_name)

        is_missing = field_value is None or (isinstance(field_value, str) and field_value.strip() == '')
        if schema_props.get('required') and is_missing:
            validation_report['missing_fields'].append(field_name)
            continue

        if field_value is None: 
            continue

        expected_type = schema_props.get('type')

        if expected_type in ('string', 'date') and not isinstance(field_value, str):
            validation_report['type_mismatches'].append({
                'field': field_name, 
                'expected': expected_type, 
                'actual': type(field_value).__name__
            })
            continue

        if expected_type == 'date':
            date_format = schema_props.get('format')
            if date_format:
                try:
                    datetime.datetime.strptime(field_value, '%m/%d/%Y')
                except ValueError:
                    validation_report['format_errors'].append({
                        'field': field_name, 
                        'expected_format': date_format, 
                        'actual_value': field_value
                    })
                    continue

        if field_name == 'license_number' and schema_props.get('format') == 'alphanumeric':
            if not re.match(r'^[a-zA-Z0-9]+$', field_value):
                validation_report['format_errors'].append({
                    'field': field_name, 
                    'expected_format': 'alphanumeric', 
                    'actual_value': field_value
                })

        allowed_values = schema_props.get('allowed_values')
        if allowed_values and field_value not in allowed_values:
            validation_report['invalid_values'].append({
                'field': field_name, 
                'expected_one_of': allowed_values, 
                'actual_value': field_value
            })

    return validation_report

@app.route('/process-pdf', methods=['POST'])
def process_pdf():
    """Main endpoint to process uploaded PDF."""
    try:
        print(f"Received request: {request.method} {request.path}")
        print(f"Content-Type: {request.content_type}")
        print(f"Files in request: {list(request.files.keys())}")
    except Exception as e:
        print(f"Error logging request: {e}")
    
    # Debug: Print extracted data
    def debug_print_extracted(data_dict, label="Extracted"):
        print(f"\n=== {label} Data ===")
        for key, value in data_dict.items():
            if value:
                print(f"  {key}: {value}")
        print("=" * 30)
    
    if 'pdf' not in request.files:
        print("ERROR: No 'pdf' key in request.files")
        return jsonify({'error': 'No PDF file uploaded'}), 400

    pdf_file = request.files['pdf']
    
    if pdf_file.filename == '':
        print("ERROR: Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    print(f"Processing file: {pdf_file.filename}, size: {len(pdf_file.read())} bytes")
    pdf_file.seek(0)  # Reset file pointer after reading

    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as input_temp:
        pdf_file.save(input_temp.name)
        input_path = input_temp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix='_ocr.pdf') as output_temp:
        output_path = output_temp.name

    try:
        # Run OCR
        run_ocrmypdf(input_path, output_path)
        
        # Extract data
        extracted_data, raw_text = extract_structured_data(output_path)
        
        print("\n=== EXTRACTED DATA ===")
        for k, v in extracted_data.items():
            print(f"{k}: {v}")
        
        normalized_data = normalize_ocr_data(extracted_data, document_schema)
        
        print("\n=== NORMALIZED DATA ===")
        for k, v in normalized_data.items():
            if v:
                print(f"{k}: {v}")
        
        # Validate data
        validation_report = validate_ocr_data(normalized_data, document_schema)

        response = {
            'success': True,
            'raw_text': raw_text[:500],  # First 500 chars for debugging
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'validation_report': validation_report
        }

        return jsonify(response), 200

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR processing PDF: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': str(e), 'traceback': error_trace}), 500

    finally:
        # Cleanup temporary files
        try:
            if 'input_path' in locals():
                os.unlink(input_path)
            if 'output_path' in locals():
                os.unlink(output_path)
        except Exception as cleanup_error:
            print(f"Warning: Could not cleanup temp files: {cleanup_error}")
            pass

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'DMV OCR Backend is running'}), 200

if __name__ == '__main__':
    port = 5001  # Changed from 5000 to avoid macOS AirPlay conflict
    print(f"Starting DMV OCR Backend Server on http://localhost:{port}")
    print("Make sure OCRmyPDF is installed: pip install ocrmypdf")
    print("And install dependencies: pip install flask flask-cors pdfplumber")
    app.run(debug=True, host='0.0.0.0', port=port)