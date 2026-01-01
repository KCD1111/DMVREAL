# OpenCV Preprocessing Fix

## Problem
The OpenCV preprocessing addition was breaking OCR output by applying aggressive image transformations (especially binarization) that destroyed visual features needed by Surya OCR.

**Symptoms:**
- OCR returned no text output
- Empty text_lines from Surya
- All extracted fields showing "Not found"
- Preprocessed images were pure black/white (binary) instead of natural RGB

## Root Cause
Version 2 (working): Images went directly to Surya OCR without preprocessing
Current version (broken): Images were preprocessed with aggressive pipeline:
- Denoise → Grayscale → Contrast → Sharpen → Deskew → **Binarize** → Border removal
- Binarization converted images to pure black/white
- Surya OCR expects natural color/grayscale images, not binary
- Visual features destroyed, text detection failed

## Solution Applied
Added `USE_PREPROCESSING` flag in `backend_surya_llama.py` (line 26):

```python
USE_PREPROCESSING = False  # Disabled by default to restore v2 behavior
```

**Changes made:**
1. Line 26: Added `USE_PREPROCESSING = False` flag
2. Line 27-30: Added status logging
3. Line 123: Changed condition from `if OPENCV_AVAILABLE:` to `if USE_PREPROCESSING and OPENCV_AVAILABLE:`
4. Line 132: Updated log message to clarify preprocessing is disabled
5. Line 252-253: Updated health endpoint to show both opencv_available and preprocessing_enabled status

## Result
- Images now go directly to Surya OCR (version 2 behavior restored)
- No binarization or aggressive transformations
- Surya receives natural RGB images with all visual features intact
- OCR output should now work properly

## How to Re-enable Preprocessing (if needed)
If you want to test preprocessing again in the future:

1. Edit `backend_surya_llama.py` line 26:
   ```python
   USE_PREPROCESSING = True  # Enable preprocessing
   ```

2. Restart the backend server

**Note:** Only enable preprocessing if you've modified the `image_preprocessor.py` pipeline to avoid binarization or if you're testing with specific image types that benefit from preprocessing.

## Alternative: Light Preprocessing
If you need some preprocessing without breaking OCR, consider using `preprocess_light()` instead of `preprocess_for_ocr()`:

In `backend_surya_llama.py` line 127, change:
```python
preprocessed_path = image_preprocessor.preprocess_light(img_path)  # Use light preprocessing
```

Light preprocessing only applies:
- Resize (if needed)
- Grayscale conversion
- Contrast enhancement (CLAHE)

It skips the aggressive steps: denoise, sharpen, deskew, binarize, border removal.

## Testing the Fix
1. Start the backend server
2. Check logs for: "Image preprocessing: DISABLED (using original images for OCR)"
3. Upload a license image
4. Verify OCR produces text output (check logs for "OCR extracted X characters" where X > 0)
5. Confirm extracted fields display properly (not "Not found")

## Version Comparison
| Aspect | Version 2 (Working) | Current (Fixed) | Previous (Broken) |
|--------|---------------------|-----------------|-------------------|
| Preprocessing | None | None (disabled) | Aggressive pipeline |
| Image format to Surya | RGB/Color | RGB/Color | Binary (black/white) |
| OCR output | Working | Working | Empty |
| Field extraction | Working | Working | All "Not found" |

## Conclusion
The fix restores version 2's working behavior by disabling OpenCV preprocessing. Images now go directly to Surya OCR without transformations, allowing proper text detection and field extraction.
