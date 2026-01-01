from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import time
from PIL import Image
from pdf2image import convert_from_path
import logging

from model_manager import ModelManager
from license_extractor import LicenseExtractor
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from image_preprocessor import ImagePreprocessor
    OPENCV_AVAILABLE = True
    logger.info("OpenCV preprocessing: AVAILABLE")
except ImportError as e:
    OPENCV_AVAILABLE = False
    logger.warning(f"OpenCV preprocessing: DISABLED (missing dependencies: {e})")
    logger.warning("Install with: pip install opencv-python-headless numpy")

USE_PREPROCESSING = False
if USE_PREPROCESSING:
    logger.info("Image preprocessing: ENABLED")
else:
    logger.info("Image preprocessing: DISABLED (using original images for OCR)")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

model_manager = ModelManager()
license_extractor = LicenseExtractor()
db_manager = DatabaseManager()
image_preprocessor = ImagePreprocessor() if OPENCV_AVAILABLE else None

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'heif'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def convert_pdf_to_images(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=150)
        temp_image_paths = []

        for i, image in enumerate(images):
            if image.width > 2000 or image.height > 2000:
                ratio = min(2000/image.width, 2000/image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_page_{i}.png')
            image.save(temp_file.name, 'PNG', optimize=True)
            temp_image_paths.append(temp_file.name)

        return temp_image_paths
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise

def process_image_file(file_path):
    try:
        img = Image.open(file_path)
        if img.format == 'HEIC' or img.format == 'HEIF':
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.convert('RGB').save(temp_file.name, 'PNG')
            return temp_file.name
        return file_path
    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        raise

@app.route('/process-document', methods=['POST'])
def process_document():
    start_time = time.time()
    temp_files = []

    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No document file uploaded'}), 400

        file = request.files['document']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        is_pdf = file_ext in ALLOWED_DOCUMENT_EXTENSIONS
        is_image = file_ext in ALLOWED_IMAGE_EXTENSIONS

        if not is_pdf and not is_image:
            return jsonify({
                'error': f'Invalid file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS}'
            }), 400

        session_id = db_manager.create_session(filename, file_ext)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as input_temp:
            file.save(input_temp.name)
            temp_files.append(input_temp.name)

        image_paths = []

        if is_pdf:
            logger.info("Converting PDF to images...")
            pdf_images = convert_pdf_to_images(input_temp.name)
            temp_files.extend(pdf_images)
            image_paths = pdf_images
        else:
            logger.info("Processing image file...")
            processed_image = process_image_file(input_temp.name)
            if processed_image != input_temp.name:
                temp_files.append(processed_image)
            image_paths = [processed_image]

        if USE_PREPROCESSING and OPENCV_AVAILABLE:
            logger.info(f"Preprocessing {len(image_paths)} image(s) with OpenCV...")
            preprocessed_paths = []
            for img_path in image_paths:
                preprocessed_path = image_preprocessor.preprocess_for_ocr(img_path)
                preprocessed_paths.append(preprocessed_path)
                if preprocessed_path != img_path:
                    temp_files.append(preprocessed_path)
        else:
            logger.info("Using original images for OCR (preprocessing disabled)")
            preprocessed_paths = image_paths

        logger.info(f"Processing {len(preprocessed_paths)} image(s) with Surya + LLAMA...")

        results = model_manager.process_sequential(preprocessed_paths)

        if not results or len(results) == 0:
            raise Exception("No OCR results returned")

        result = results[0]
        raw_ocr_text = result['raw_ocr_text']
        extracted_data = result['extracted_data']

        normalized_data = license_extractor.validate_and_normalize(extracted_data)

        validation_report = license_extractor.validate_data(normalized_data)

        processing_time_ms = int((time.time() - start_time) * 1000)

        db_manager.update_session(
            session_id,
            status='completed',
            processing_time_ms=processing_time_ms,
            overall_confidence=0.0
        )

        license_id = db_manager.save_extracted_license(
            session_id,
            normalized_data.copy(),
            raw_ocr_text,
            validation_report
        )

        response = {
            'success': True,
            'session_id': session_id,
            'license_id': license_id,
            'raw_ocr_text': raw_ocr_text[:500],
            'extracted_data': extracted_data,
            'normalized_data': normalized_data,
            'validation_report': validation_report,
            'processing_time_ms': processing_time_ms
        }

        return jsonify(response), 200

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error processing document: {str(e)}")
        logger.error(f"Traceback: {error_trace}")

        if 'session_id' in locals() and session_id:
            db_manager.update_session(session_id, status='failed', error_message=str(e))

        return jsonify({
            'error': str(e),
            'traceback': error_trace
        }), 500

    finally:
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as cleanup_error:
                logger.warning(f"Could not cleanup temp file {temp_file}: {cleanup_error}")

@app.route('/process-pdf', methods=['POST'])
def process_pdf_legacy():
    if 'pdf' in request.files:
        file = request.files['pdf']

        form_data = {'document': file}
        request.files = form_data

        return process_document()
    else:
        return jsonify({'error': 'No PDF file uploaded'}), 400

@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    try:
        session = db_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        license_data = db_manager.get_extracted_license(session_id)

        return jsonify({
            'session': session,
            'license': license_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search/<license_number>', methods=['GET'])
def search_license(license_number):
    try:
        results = db_manager.search_by_license_number(license_number)
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recent-sessions', methods=['GET'])
def recent_sessions():
    try:
        limit = request.args.get('limit', default=10, type=int)
        sessions = db_manager.get_recent_sessions(limit)
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'DMV OCR Backend (Surya + LLAMA) is running',
        'device': model_manager.device,
        'opencv_available': OPENCV_AVAILABLE,
        'preprocessing_enabled': USE_PREPROCESSING
    }), 200

if __name__ == '__main__':
    port = 5001
    logger.info(f"Starting DMV OCR Backend Server (Surya + LLAMA) on http://localhost:{port}")
    logger.info(f"Using device: {model_manager.device}")
    logger.info("WARNING: First request will be slow as models are loaded into memory")
    logger.info("Install dependencies: pip install -r requirements.txt")
    app.run(debug=True, host='0.0.0.0', port=port)
