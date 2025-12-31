import torch
import gc
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from transformers import BitsAndBytesConfig
    import platform
    if platform.processor() == 'arm' or 'Apple' in platform.processor():
        QUANTIZATION_AVAILABLE = False
        logger.warning("M1/M2 Mac detected - bitsandbytes not supported on Apple Silicon")
        logger.warning("Using standard model loading with optimizations")
    else:
        QUANTIZATION_AVAILABLE = True
        logger.info("4-bit quantization available (bitsandbytes detected)")
except ImportError:
    QUANTIZATION_AVAILABLE = False
    logger.warning("bitsandbytes not available - using standard model loading (will use more memory)")

class ModelManager:
    def __init__(self):
        self.surya_det_model = None
        self.surya_det_processor = None
        self.surya_rec_model = None
        self.surya_rec_processor = None
        self.llama_model = None
        self.llama_tokenizer = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

    def clear_gpu_memory(self):
        if self.device == "mps":
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        logger.info("Cleared GPU memory")

    def load_surya_models(self):
        if self.surya_det_model is None:
            logger.info("Loading Surya detection model...")
            self.surya_det_model = load_det_model()
            self.surya_det_processor = load_det_processor()
            logger.info("Loading Surya recognition model...")
            self.surya_rec_model = load_rec_model()
            self.surya_rec_processor = load_rec_processor()
            logger.info("Surya models loaded successfully")
        return self.surya_det_model, self.surya_det_processor, self.surya_rec_model, self.surya_rec_processor

    def unload_surya_models(self):
        logger.info("Unloading Surya models to free memory...")
        self.surya_det_model = None
        self.surya_det_processor = None
        self.surya_rec_model = None
        self.surya_rec_processor = None
        self.clear_gpu_memory()

    def load_llama_model(self):
        if self.llama_model is None:
            model_id = "meta-llama/Llama-3.2-1B-Instruct"
            logger.info(f"Loading LLAMA model: {model_id}")
            logger.info("Using 1B model - optimized for 8GB M1 Macs")

            if QUANTIZATION_AVAILABLE:
                logger.info("Loading LLAMA 3.2 1B model with 4-bit quantization...")
                logger.info("This reduces memory usage from 2GB to ~500MB")

                if self.device == "mps":
                    logger.info("M1/M2 Mac detected - optimizing for 8GB RAM")

                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    llm_int8_enable_fp32_cpu_offload=True
                )

                self.llama_tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    use_fast=True
                )
                if self.llama_tokenizer.pad_token is None:
                    self.llama_tokenizer.pad_token = self.llama_tokenizer.eos_token

                self.llama_model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    max_memory={0: "5GB", "cpu": "3GB"}
                )
            else:
                logger.info("Loading LLAMA 3.2 1B model with M1-optimized settings")
                logger.info("Memory usage: ~1GB (perfect for 8GB M1)")

                if self.device == "mps":
                    logger.info("Using float16 precision for Apple Silicon GPU")
                    dtype = torch.float16
                else:
                    logger.warning("Loading without quantization - will use more memory")
                    dtype = torch.float32

                self.llama_tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    use_fast=True
                )
                if self.llama_tokenizer.pad_token is None:
                    self.llama_tokenizer.pad_token = self.llama_tokenizer.eos_token

                self.llama_model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=dtype,
                    low_cpu_mem_usage=True,
                    device_map={"": self.device} if self.device == "mps" else "auto"
                )

            logger.info("LLAMA model loaded successfully")
        return self.llama_model, self.llama_tokenizer

    def unload_llama_model(self):
        logger.info("Unloading LLAMA model to free memory...")
        self.llama_model = None
        self.llama_tokenizer = None
        self.clear_gpu_memory()

    def run_ocr(self, image_paths, languages=["en"]):
        det_model, det_processor, rec_model, rec_processor = self.load_surya_models()

        if any(x is None for x in [det_model, det_processor, rec_model, rec_processor]):
            raise RuntimeError("One or more Surya models failed to load")

        images = []
        for img_path in image_paths:
            img = Image.open(img_path).convert("RGB")
            original_size = img.size
            if img.width > 2000 or img.height > 2000:
                ratio = min(2000/img.width, 2000/img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {img.size}")
            images.append(img)

        predictions = run_ocr(
            images,
            [languages] * len(images),
            det_model,
            det_processor,
            rec_model,
            rec_processor
        )

        return predictions

    def extract_fields_with_llama(self, ocr_text):
        model, tokenizer = self.load_llama_model()

        if model is None or tokenizer is None:
            raise RuntimeError("LLAMA model or tokenizer failed to load")

        prompt = self._build_extraction_prompt(ocr_text)

        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=1024)

        if self.device == "mps":
            inputs = {k: v.to("mps") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=700,
                temperature=0.05,
                do_sample=True,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        extracted_data = self._parse_llama_response(response)

        # Apply fallback extraction for validation
        extracted_data = self._apply_fallback_extraction(ocr_text, extracted_data)

        return extracted_data

    def _build_extraction_prompt(self, ocr_text):
        ocr_text_trimmed = ocr_text[:1500] if len(ocr_text) > 1500 else ocr_text

        # Log the OCR text being sent to the model
        logger.info(f"Building prompt with OCR text: {ocr_text_trimmed[:200]}...")

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Extract data from driver's license OCR text and return JSON.<|eot_id|><|start_header_id|>user<|end_header_id|>
OCR text from driver's license:

{ocr_text_trimmed}

Find these values in the text above:
- First name (look for "1" label, extract the name after it)
- Last name (look for "2" label, extract all words after it - may be multiple words)
- License number (look for "4d DLN" label, extract only the number after it)
- Birth date (look for "3 DOB" label, format MM/DD/YYYY)
- Expiration date (look for "4b EXP" or "4bEXP" label, format MM/DD/YYYY)
- Street address (look for "8" label)
- City (city name before state)
- State (2-letter code like KY)
- Zip code (5 digits)
- Sex (look for "15 SEX" label - carefully extract M or F)

Return JSON with this exact structure:
{{
  "first_name": null,
  "last_name": null,
  "license_number": null,
  "date_of_birth": null,
  "expiration_date": null,
  "street_address": null,
  "city": null,
  "state": null,
  "zip_code": null,
  "sex": null,
  "confidence": {{"first_name": 0.9, "last_name": 0.9, "license_number": 0.9, "date_of_birth": 0.9, "expiration_date": 0.9, "street_address": 0.9, "city": 0.9, "state": 0.9, "zip_code": 0.9, "sex": 0.9}}
}}

Replace null with actual values from the OCR text. Keep the exact same JSON structure.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{{"""

    def _parse_llama_response(self, response):
        import json
        import re

        logger.info(f"LLAMA raw response length: {len(response)} characters")
        logger.info(f"LLAMA response preview: {response[:200]}...")

        if len(response) > 300:
            logger.info(f"LLAMA response end: ...{response[-200:]}")

        # Extract JSON from assistant's response
        # The prompt ends with '{' so the model should continue from there
        assistant_marker = "<|start_header_id|>assistant<|end_header_id|>"
        if assistant_marker in response:
            response = response.split(assistant_marker)[-1].strip()
            logger.info(f"Extracted assistant portion: {response[:200]}...")

        # Find ALL JSON objects in the response
        # The model may output the template first, then the actual data
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        all_json_matches = re.findall(json_pattern, response, re.DOTALL)

        logger.info(f"Found {len(all_json_matches)} potential JSON blocks")

        # Try to parse each JSON block and score them
        valid_jsons = []
        for idx, json_str in enumerate(all_json_matches):
            # Clean up the JSON string
            json_str = json_str.strip()
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays

            logger.info(f"Attempting to parse JSON block {idx+1}: {json_str[:150]}...")

            try:
                data = json.loads(json_str)

                # Count non-null values (excluding confidence)
                non_null_count = sum(1 for k, v in data.items()
                                    if k != 'confidence' and v is not None and v != "")

                logger.info(f"✓ Block {idx+1} parsed successfully - {non_null_count} non-null fields")
                valid_jsons.append((data, non_null_count, idx))
            except json.JSONDecodeError as e:
                logger.warning(f"✗ Block {idx+1} failed to parse: {e}")
                continue

        # Sort by non-null count (descending) - prefer the one with most actual data
        valid_jsons.sort(key=lambda x: x[1], reverse=True)

        # Try each valid JSON, starting with the one with most non-null values
        for data, non_null_count, idx in valid_jsons:
            logger.info(f"Validating block {idx+1} with {non_null_count} non-null fields")
            logger.info(f"Extracted fields: {list(data.keys())}")

            # Validate JSON structure - must be flat with expected field names
            expected_fields = {'first_name', 'last_name', 'license_number', 'date_of_birth',
                             'expiration_date', 'street_address', 'city', 'state', 'zip_code', 'sex'}
            actual_fields = set(data.keys()) - {'confidence'}

            # Check if structure is wrong (nested objects instead of flat)
            if 'name' in data or 'driver_info' in data or 'address' in data:
                logger.warning("Model returned nested JSON structure instead of flat structure!")
                logger.warning(f"Wrong structure detected: {list(data.keys())}")
                continue

            # Check if any field is a dict/list (should all be strings or null)
            has_nested = False
            for field, value in data.items():
                if field != 'confidence' and value is not None and not isinstance(value, (str, int, float)):
                    logger.warning(f"Field '{field}' has nested structure (type: {type(value)}), expecting flat string!")
                    has_nested = True
                    break
            if has_nested:
                continue

            # Validate that we have actual data, not placeholder text or example data
            if data.get('first_name') and isinstance(data['first_name'], str):
                first_name_lower = data['first_name'].lower()
                if 'string' in first_name_lower or 'null' in first_name_lower:
                    logger.warning("Model returned placeholder text instead of actual data!")
                    continue
                if '<extract' in first_name_lower or 'extract from' in first_name_lower:
                    logger.warning("Model returned template placeholder instead of extracting!")
                    continue
                # Check if model returned the example data instead of extracting from OCR
                if first_name_lower == 'john' and data.get('last_name', '').lower() == 'smith':
                    logger.warning("Model returned example data (John Smith) instead of extracting from OCR text!")
                    continue

            # Ensure all expected fields exist
            default_structure = {
                "first_name": None,
                "last_name": None,
                "license_number": None,
                "date_of_birth": None,
                "expiration_date": None,
                "street_address": None,
                "city": None,
                "state": None,
                "zip_code": None,
                "sex": None,
                "confidence": {
                    "first_name": 0.5,
                    "last_name": 0.5,
                    "license_number": 0.5,
                    "date_of_birth": 0.5,
                    "expiration_date": 0.5,
                    "street_address": 0.5,
                    "city": 0.5,
                    "state": 0.5,
                    "zip_code": 0.5,
                    "sex": 0.5
                }
            }
            default_structure.update(data)

            # Ensure confidence is a dict
            if not isinstance(default_structure.get('confidence'), dict):
                default_structure['confidence'] = {
                    "first_name": 0.5,
                    "last_name": 0.5,
                    "license_number": 0.5,
                    "date_of_birth": 0.5,
                    "expiration_date": 0.5,
                    "street_address": 0.5,
                    "city": 0.5,
                    "state": 0.5,
                    "zip_code": 0.5,
                    "sex": 0.5
                }

            logger.info(f"✓ Using block {idx+1} with {non_null_count} non-null values")
            return default_structure

        logger.error("✗ Failed to parse valid JSON from LLAMA response after all attempts")
        logger.error(f"Full response: {response}")

        return {
            "first_name": None,
            "last_name": None,
            "license_number": None,
            "date_of_birth": None,
            "expiration_date": None,
            "street_address": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "sex": None,
            "confidence": {
                "first_name": 0.0,
                "last_name": 0.0,
                "license_number": 0.0,
                "date_of_birth": 0.0,
                "expiration_date": 0.0,
                "street_address": 0.0,
                "city": 0.0,
                "state": 0.0,
                "zip_code": 0.0,
                "sex": 0.0
            }
        }

    def _apply_fallback_extraction(self, ocr_text, extracted_data):
        """Use regex patterns as a fallback to validate/correct extracted fields"""
        import re

        logger.info("Applying fallback extraction validation...")

        # Create a copy to modify
        corrected = extracted_data.copy()

        # Fallback for Sex field (common issue)
        sex_match = re.search(r'15\s*SEX\s+([MF])', ocr_text, re.IGNORECASE)
        if sex_match:
            fallback_sex = sex_match.group(1).upper()
            if extracted_data.get('sex') != fallback_sex:
                logger.info(f"Correcting sex: '{extracted_data.get('sex')}' -> '{fallback_sex}' (from regex)")
                corrected['sex'] = fallback_sex
                if isinstance(corrected.get('confidence'), dict):
                    corrected['confidence']['sex'] = 0.95

        # Fallback for License Number (should not contain address parts)
        license_num = extracted_data.get('license_number', '')
        if license_num and ('E' in license_num and 'ST' in license_num):
            # Likely extracted street address instead
            logger.warning(f"License number appears to be street address: '{license_num}'")
            # Try to find the actual license number
            dln_match = re.search(r'4d\s*DLN\s+([A-Z0-9-]+)', ocr_text, re.IGNORECASE)
            if dln_match:
                fallback_license = dln_match.group(1)
                logger.info(f"Correcting license number: '{license_num}' -> '{fallback_license}'")
                corrected['license_number'] = fallback_license
                if isinstance(corrected.get('confidence'), dict):
                    corrected['confidence']['license_number'] = 0.85

        # Fallback for Last Name (field "2" - may have multiple words)
        last_name = extracted_data.get('last_name', '')
        if last_name and len(last_name.split()) == 1:
            # Try to find multi-word last name
            name_match = re.search(r'2\s+([A-Z][A-Z\s]+?)(?:\n|3\s|$)', ocr_text)
            if name_match:
                fallback_name = name_match.group(1).strip()
                if len(fallback_name.split()) > 1:
                    logger.info(f"Correcting last name: '{last_name}' -> '{fallback_name}' (multi-word)")
                    corrected['last_name'] = fallback_name.title()
                    if isinstance(corrected.get('confidence'), dict):
                        corrected['confidence']['last_name'] = 0.80

        # Fallback for DOB - should be in 1900s/early 2000s for most licenses
        dob = extracted_data.get('date_of_birth', '')
        if dob and '/2020' in dob:
            # Very unlikely - probably parsing error
            dob_match = re.search(r'3\s*DOB\s+(\d{2}/\d{2}/\d{4})', ocr_text)
            if dob_match:
                fallback_dob = dob_match.group(1)
                logger.info(f"Correcting DOB: '{dob}' -> '{fallback_dob}' (suspicious year)")
                corrected['date_of_birth'] = fallback_dob
                if isinstance(corrected.get('confidence'), dict):
                    corrected['confidence']['date_of_birth'] = 0.85

        # Fallback for Expiration - should typically be future date
        exp_date = extracted_data.get('expiration_date', '')
        if exp_date and '/2020' in exp_date:
            # Likely wrong or expired
            exp_match = re.search(r'4b\s*EXP\s+(\d{2}/\d{2}/\d{4})', ocr_text)
            if exp_match:
                fallback_exp = exp_match.group(1)
                logger.info(f"Correcting expiration: '{exp_date}' -> '{fallback_exp}'")
                corrected['expiration_date'] = fallback_exp
                if isinstance(corrected.get('confidence'), dict):
                    corrected['confidence']['expiration_date'] = 0.85

        return corrected

    def process_sequential(self, image_paths):
        logger.info("Processing with sequential model loading (memory-efficient mode)")

        logger.info("Step 1: Running Surya OCR...")
        predictions = self.run_ocr(image_paths)

        ocr_texts = []
        for pred in predictions:
            text_lines = []
            for text_line in pred.text_lines:
                text_lines.append(text_line.text)
            ocr_texts.append("\n".join(text_lines))

        self.unload_surya_models()

        logger.info("Step 2: Extracting fields with LLAMA...")
        results = []
        for ocr_text in ocr_texts:
            extracted_data = self.extract_fields_with_llama(ocr_text)
            results.append({
                'raw_ocr_text': ocr_text,
                'extracted_data': extracted_data
            })

        self.unload_llama_model()

        logger.info("Processing complete")
        return results
