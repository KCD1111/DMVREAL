import cv2
import numpy as np
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImagePreprocessor:

    def __init__(self):
        pass

    def preprocess_for_ocr(self, image_path: str, output_path: str = None) -> str:
        try:
            img = cv2.imread(image_path)

            if img is None:
                logger.warning(f"Could not read image with OpenCV, using PIL fallback: {image_path}")
                pil_img = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)

            processed_img = self._apply_preprocessing_pipeline(img)

            if output_path is None:
                output_path = image_path.replace('.', '_preprocessed.')

            cv2.imwrite(output_path, processed_img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            logger.info(f"Preprocessed image saved to: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image_path

    def _apply_preprocessing_pipeline(self, img: np.ndarray) -> np.ndarray:
        img = self._resize_if_needed(img)
        img = self._denoise(img)
        img = self._convert_to_grayscale(img)
        img = self._enhance_contrast(img)
        img = self._sharpen(img)
        img = self._deskew(img)
        img = self._binarize(img)
        img = self._remove_borders(img)

        return img

    def _resize_if_needed(self, img: np.ndarray, max_dimension: int = 3000) -> np.ndarray:
        height, width = img.shape[:2]

        if height > max_dimension or width > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

        return img

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    def _convert_to_grayscale(self, img: np.ndarray) -> np.ndarray:
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(img)

    def _sharpen(self, img: np.ndarray) -> np.ndarray:
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        return cv2.filter2D(img, -1, kernel)

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        try:
            coords = np.column_stack(np.where(img > 0))
            if len(coords) < 3:
                return img

            angle = cv2.minAreaRect(coords)[-1]

            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) < 0.5:
                return img

            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)

            logger.info(f"Deskewed image by {angle:.2f} degrees")
            return rotated

        except Exception as e:
            logger.warning(f"Deskewing failed: {e}")
            return img

    def _binarize(self, img: np.ndarray) -> np.ndarray:
        binary = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return binary

    def _remove_borders(self, img: np.ndarray) -> np.ndarray:
        try:
            contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return img

            x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))

            padding = 10
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(img.shape[1] - x, w + 2 * padding)
            h = min(img.shape[0] - y, h + 2 * padding)

            cropped = img[y:y+h, x:x+w]

            return cropped

        except Exception as e:
            logger.warning(f"Border removal failed: {e}")
            return img

    def preprocess_light(self, image_path: str, output_path: str = None) -> str:
        try:
            img = cv2.imread(image_path)

            if img is None:
                logger.warning(f"Could not read image with OpenCV: {image_path}")
                return image_path

            img = self._resize_if_needed(img)
            img = self._convert_to_grayscale(img)
            img = self._enhance_contrast(img)

            if output_path is None:
                output_path = image_path.replace('.', '_light.')

            cv2.imwrite(output_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            logger.info(f"Light preprocessed image saved to: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Error in light preprocessing: {e}")
            return image_path
