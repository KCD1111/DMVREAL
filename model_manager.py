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

        inputs = tokenizer(prompt, return_tensors="pt")

        if self.device == "mps":
            inputs = {k: v.to("mps") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                early_stopping=True
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        extracted_data = self._parse_llama_response(response)

        return extracted_data

    def _build_extraction_prompt(self, ocr_text):
        ocr_text_trimmed = ocr_text[:800] if len(ocr_text) > 800 else ocr_text
        return f"""Extract US driver's license info from OCR text as JSON:

{ocr_text_trimmed}

Required fields: first_name, last_name, license_number, date_of_birth (MM/DD/YYYY), expiration_date (MM/DD/YYYY), street_address, city, state (2-letter), zip_code, sex (M/F), confidence (0.0-1.0 per field).

Return only valid JSON. Use null if not found.

JSON:"""

    def _parse_llama_response(self, response):
        import json
        import re

        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from LLAMA response")
                return {}
        return {}

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
