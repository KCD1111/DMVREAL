from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import re
import requests
import json
import numpy as np
from PIL import Image
import pdf2image
import pdfplumber
import tempfile
import os

# Try to import OCR libraries - use Tesseract as primary
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Surya is optional - only use if available
try:
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor
    from surya.foundation import FoundationPredictor
    SURYA_AVAILABLE = True
except ImportError:
    SURYA_AVAILABLE = False
    det_predictor = None
    rec_predictor = None
    foundation_predictor = None

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize OCR predictors once at startup
if SURYA_AVAILABLE:
    print("Loading Surya OCR models...")
    try:
        print("  Loading detection model...")
        det_predictor = DetectionPredictor()
        print("  Loading foundation model...")
        foundation_predictor = FoundationPredictor()
        print("  Loading recognition model...")
        rec_predictor = RecognitionPredictor(foundation_predictor=foundation_predictor)
        print("✓ Surya models loaded successfully!")
    except Exception as e:
        print(f"⚠️  Surya initialization failed: {e}")
        SURYA_AVAILABLE = False
        det_predictor = None
        rec_predictor = None
        foundation_predictor = None
else:
    det_predictor = None
    rec_predictor = None
    foundation_predictor = None

if TESSERACT_AVAILABLE:
    print("✓ Tesseract OCR available")
else:
    print("⚠️  Tesseract not available - install with: pip install pytesseract && brew install tesseract")

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


def run_tesseract_ocr(input_pdf_path):
    """Runs Tesseract OCR on PDF - reliable and fast."""
    if not TESSERACT_AVAILABLE:
        raise Exception("Tesseract not available")
    
    try:
        print("\n🔄 Converting PDF to images...")
        try:
            images = pdf2image.convert_from_path(input_pdf_path, dpi=300)
            print(f"✓ Converted to {len(images)} image(s)")
        except Exception as e:
            poppler_path = None
            possible_paths = ['/opt/homebrew/bin', '/usr/local/bin']
            for path_pattern in possible_paths:
                if os.path.exists(os.path.join(path_pattern, 'pdftoppm')):
                    poppler_path = path_pattern
                    break
            if poppler_path:
                images = pdf2image.convert_from_path(input_pdf_path, dpi=300, poppler_path=poppler_path)
                print(f"✓ Converted to {len(images)} image(s)")
            else:
                raise e
        
        if not images:
            raise Exception("No images could be extracted from PDF")
        
        print(f"\n🔍 Running Tesseract OCR on {len(images)} page(s)...")
        all_text = ""
        
        for page_num, pil_image in enumerate(images, 1):
            try:
                print(f"  Processing page {page_num}/{len(images)}...")
                page_text = pytesseract.image_to_string(pil_image, lang='eng')
                if page_text.strip():
                    all_text += page_text + "\n"
                    print(f"  ✓ Page {page_num}: Extracted {len(page_text)} characters")
                else:
                    print(f"  ⚠️  Page {page_num}: No text extracted")
            except Exception as page_error:
                print(f"  ❌ Error processing page {page_num}: {page_error}")
        
        del images
        import gc
        gc.collect()
        
        print(f"\n✓ Total text extracted: {len(all_text)} characters")
        return all_text
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Tesseract OCR failed: {str(e)}")


def run_surya_ocr(input_pdf_path):
    """Runs Surya OCR on PDF - optional, falls back to Tesseract."""
    if not SURYA_AVAILABLE:
        raise Exception("Surya not available")
    
    try:
        print("\n🔄 Converting PDF to images...")
        try:
            images = pdf2image.convert_from_path(input_pdf_path, dpi=300)
            print(f"✓ Converted to {len(images)} image(s)")
        except Exception as e:
            poppler_path = None
            possible_paths = ['/opt/homebrew/bin', '/usr/local/bin']
            for path_pattern in possible_paths:
                if os.path.exists(os.path.join(path_pattern, 'pdftoppm')):
                    poppler_path = path_pattern
                    break
            if poppler_path:
                images = pdf2image.convert_from_path(input_pdf_path, dpi=300, poppler_path=poppler_path)
                print(f"✓ Converted to {len(images)} image(s)")
            else:
                raise e
        
        if not images:
            raise Exception("No images could be extracted from PDF")
        
        print(f"\n🔍 Running Surya OCR on {len(images)} page(s)...")
        
        all_text = ""
        # Process each image - run detection first, then recognition
        for page_num, pil_image in enumerate(images, 1):
            try:
                print(f"  Processing page {page_num}/{len(images)}...")
                
                # Step 1: Run detection to get bounding boxes
                print(f"    Step 1: Detecting text regions...")
                det_gen = det_predictor.batch_detection([pil_image], batch_size=1)
                det_predictions_list, image_sizes = next(det_gen)
                
                if not det_predictions_list or len(det_predictions_list) == 0:
                    print(f"    ⚠️  No text regions detected on page {page_num}")
                    continue
                
                bboxes_np = det_predictions_list[0]
                print(f"    ✓ Found {len(bboxes_np)} text regions")
                
                # Step 2: Convert bboxes to proper format
                bboxes = []
                for bbox_np in bboxes_np:
                    if isinstance(bbox_np, np.ndarray):
                        bbox_flat = bbox_np.flatten()
                        if len(bbox_flat) >= 4:
                            bboxes.append([float(bbox_flat[0]), float(bbox_flat[1]), 
                                         float(bbox_flat[2]), float(bbox_flat[3])])
                    else:
                        bbox_list = list(bbox_np)
                        if len(bbox_list) >= 4:
                            bboxes.append([float(bbox_list[0]), float(bbox_list[1]), 
                                         float(bbox_list[2]), float(bbox_list[3])])
                
                if not bboxes:
                    print(f"    ⚠️  No valid bounding boxes on page {page_num}")
                    continue
                
                # Step 3: Run recognition on detected regions
                print(f"    Step 2: Running OCR on {len(bboxes)} regions...")
                ocr_results = rec_predictor.slice_bboxes(
                    images=[pil_image],
                    task_names=["ocr"],
                    bboxes=[bboxes]
                )
                
                # Step 4: Extract text from results
                # slice_bboxes returns slices, we need to process them with recognition
                page_text = ""
                
                if ocr_results and isinstance(ocr_results, dict) and 'slices' in ocr_results:
                    slices = ocr_results['slices']
                    if slices and len(slices) > 0:
                        print(f"    Step 3: Processing {len(slices[0])} text regions...")
                        # Process each slice - run recognition on individual slices
                        text_parts = []
                        for slice_idx, slice_img in enumerate(slices[0]):
                            try:
                                # Run recognition on this slice
                                # Use the whole slice as one region
                                slice_bbox = [[0, 0, slice_img.width, slice_img.height]]
                                slice_result = rec_predictor.slice_bboxes(
                                    images=[slice_img],
                                    task_names=["ocr"],
                                    bboxes=[slice_bbox]
                                )
                                # Try to extract text from the result
                                if slice_result and 'input_text' in slice_result:
                                    slice_text_list = slice_result['input_text']
                                    if slice_text_list and len(slice_text_list) > 0:
                                        if isinstance(slice_text_list[0], list):
                                            slice_text = "\n".join([str(t) for t in slice_text_list[0] if t])
                                        else:
                                            slice_text = "\n".join([str(t) for t in slice_text_list if t])
                                        if slice_text:
                                            text_parts.append(slice_text)
                            except Exception as slice_error:
                                # Skip this slice and continue
                                continue
                        
                        if text_parts:
                            page_text = "\n".join(text_parts)
                
                # Fallback: Use Tesseract if available
                if not page_text:
                    print(f"    Step 3 (fallback): Trying Tesseract OCR...")
                    try:
                        import pytesseract
                        page_text = pytesseract.image_to_string(pil_image, lang='eng')
                        if page_text.strip():
                            print(f"    ✓ Tesseract extracted {len(page_text)} characters")
                    except ImportError:
                        print(f"    ⚠️  Tesseract not available (install: pip install pytesseract)")
                    except Exception as tesseract_error:
                        print(f"    ⚠️  Tesseract failed: {tesseract_error}")
                
                if page_text:
                    all_text += page_text + "\n"
                    print(f"  ✓ Page {page_num}: Extracted {len(page_text)} characters")
                else:
                    print(f"  ⚠️  Page {page_num}: No text extracted")
                    
            except Exception as page_error:
                print(f"  ❌ Error processing page {page_num}: {page_error}")
                import traceback
                traceback.print_exc()
                # Continue with next page
        
        # Clean up images to free memory
        del images
        import gc
        gc.collect()
        
        print(f"\n✓ Total text extracted: {len(all_text)} characters")
        
        if not all_text.strip():
            print("\n⚠️  WARNING: No text was extracted from any page!")
            print("This could mean:")
            print("  1. The PDF is an image without embedded text")
            print("  2. Surya OCR is not detecting text regions")
            print("  3. The image quality is too low")
        
        return all_text
        
    except Exception as e:
        # Log specifically if it's a poppler issue
        if "poppler" in str(e).lower() or "Unable to get page count" in str(e):
            raise Exception("Error: Poppler not installed or not in PATH. Install with 'brew install poppler' (macOS) or 'apt-get install poppler-utils' (Linux)")
        import traceback
        traceback.print_exc()
        raise Exception(f"Surya OCR failed: {str(e)}")

        
def extract_structured_data(pdf_path):
    """Extracts structured data from PDF using OCR and Ollama/Llama3."""
    full_text = ""
    
    # Step 1: Try Tesseract first (most reliable)
    if TESSERACT_AVAILABLE:
        print("\n[Step 1/2] Running Tesseract OCR...")
        try:
            full_text = run_tesseract_ocr(pdf_path)
            if full_text and full_text.strip():
                print(f"✓ Tesseract OCR extracted {len(full_text)} characters")
            else:
                print("⚠️  Tesseract returned empty text")
        except Exception as e:
            print(f"⚠️  Tesseract OCR failed: {str(e)}")
    
    # Step 2: Fallback to pdfplumber (for text-based PDFs)
    if not full_text or not full_text.strip():
        print("Trying pdfplumber (for text-based PDFs)...")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                if full_text.strip():
                    print(f"✓ pdfplumber extracted {len(full_text)} characters")
        except Exception as fallback_error:
            print(f"⚠️  pdfplumber failed: {str(fallback_error)}")
    
    # Step 3: Try Surya as last resort (if available)
    if (not full_text or not full_text.strip()) and SURYA_AVAILABLE:
        print("Trying Surya OCR as last resort...")
        try:
            surya_text = run_surya_ocr(pdf_path)
            if surya_text and surya_text.strip():
                full_text = surya_text
                print(f"✓ Surya OCR extracted {len(full_text)} characters")
        except Exception as surya_error:
            print(f"⚠️  Surya OCR failed: {str(surya_error)}")

    if not full_text or not full_text.strip():
        raise Exception("No text could be extracted. Make sure Tesseract is installed: brew install tesseract && pip install pytesseract")
    
    print("\n=== RAW OCR TEXT ===")
    print(full_text[:1000])
    print("=" * 50)

    # Step 2: Use Ollama with Llama3 to extract structured data
    print("\n[Step 2/2] Running Ollama/Llama3 extraction...")
    extracted_data = extract_with_llama(full_text)
    print("✓ Ollama extraction completed")
    
    return extracted_data, full_text


def extract_with_llama(ocr_text):
    """Uses Ollama/Llama3 to extract structured data from OCR text."""
    
    prompt = f"""Extract the following information from this driver's license OCR text. Return ONLY a JSON object with these exact keys:

- first_name
- last_name
- license_number
- date_of_birth (format: MM/DD/YYYY)
- expiration_date (format: MM/DD/YYYY)
- street_address
- city
- state
- zip_code
- sex (M or F)

OCR Text:
{ocr_text}

Return ONLY the JSON object, no other text or markdown:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        response_text = result.get("response", "")
        
        # Clean up response - remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        print("\n=== LLAMA3 EXTRACTED DATA ===")
        for k, v in extracted_data.items():
            print(f"{k}: {v}")
        print("=" * 50)
        
        return extracted_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        print("Falling back to regex extraction...")
        return extract_with_regex(ocr_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing Ollama response: {e}")
        print(f"Raw response: {response_text[:200]}")
        print("Falling back to regex extraction...")
        return extract_with_regex(ocr_text)


def extract_with_regex(full_text):
    """Fallback regex extraction (original regex code)."""
    data = {}
    
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

    # Extract Address
    full_address_pattern = re.compile(
        r'(\d{1,6}\s+[A-Z0-9\s]+?(?:ST|STREET|RD|ROAD|AVE|AVENUE|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|HWY|PKWY|PL|TER|WAY|CIR)\.?)' +
        r'\s*,?\s*' +
        r'([A-Z][A-Za-z\s]+?)' +
        r'\s*,?\s*' +
        r'([A-Z]{2})' +
        r'\s+' +
        r'(\d{5}(?:-\d{4})?)',
        re.IGNORECASE
    )
    
    full_match = full_address_pattern.search(full_text)
    if full_match:
        data['street_address'] = full_match.group(1).strip()
        data['city'] = full_match.group(2).strip()
        data['state'] = full_match.group(3).strip().upper()
        data['zip_code'] = full_match.group(4).strip()

    # Extract First Name
    first_name_match = re.search(r'~ \+([A-Z]+)', full_text)
    if first_name_match:
        data['first_name'] = first_name_match.group(1)

    # Extract Last Name
    last_name_match = re.search(r'(?:^|\n)[^A-Za-z]*([A-Z]+ [A-Z]+)(?!.*LICENSE)', full_text)
    if last_name_match:
        data['last_name'] = last_name_match.group(1)

    return data

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

    try:
        # Extract data using Surya OCR + Ollama
        # input_path contains the uploaded PDF
        extracted_data, raw_text = extract_structured_data(input_path)
        
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
        except Exception as cleanup_error:
            print(f"Warning: Could not cleanup temp files: {cleanup_error}")
            pass

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'DMV OCR Backend is running'}), 200

if __name__ == '__main__':
    port = 5001
    print(f"Starting DMV OCR Backend Server on http://localhost:{port}")
    print("Make sure Ollama is running: ollama serve")
    print("And Llama3 is installed: ollama run llama3:8b")
    app.run(debug=True, host='0.0.0.0', port=port)