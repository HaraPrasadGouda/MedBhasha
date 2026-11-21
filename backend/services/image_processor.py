"""
MedBhasha - Image Preprocessing Service
Specialized for vernacular handwritten prescriptions, doctor notes, and printed lab reports.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("medbhasha.image_processor")

# Quality assessment thresholds
LAPLACIAN_BLUR_THRESHOLD = 100.0  # Variance below this indicates potential blur
BRIGHTNESS_MIN_THRESHOLD = 45.0    # Mean pixel value below this is severely underexposed
BRIGHTNESS_MAX_THRESHOLD = 254.5    # Mean pixel value above this is essentially blank/clipped
MAX_IMAGE_WIDTH = 1600             # Max proportional width in pixels


def _extract_pdf_first_page_image(file_bytes: bytes) -> Optional[np.ndarray]:
    """
    Attempts to extract or render the first page of a PDF file using pdf2image or pypdf.
    Returns a BGR numpy array if successful, or None.
    """
    # Attempt 1: pdf2image (highest quality rasterization of PDF page)
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(file_bytes, first_page=1, last_page=1)
        if pages:
            pil_image = pages[0].convert("RGB")
            # Convert RGB (PIL) to BGR (OpenCV)
            bgr_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return bgr_img
    except Exception as exc:
        logger.debug(f"pdf2image conversion skipped or failed: {exc}")

    # Attempt 2: pypdf (extract first embedded raster image)
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if len(pdf_reader.pages) > 0:
            first_page = pdf_reader.pages[0]
            if first_page.images:
                # Extract first embedded image on the page
                first_img = first_page.images[0]
                pil_image = Image.open(io.BytesIO(first_img.data)).convert("RGB")
                bgr_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                return bgr_img
    except Exception as exc:
        logger.debug(f"pypdf extraction failed: {exc}")

    return None


def _decode_image_bytes(file_bytes: bytes) -> np.ndarray:
    """
    Decodes raw bytes into an OpenCV BGR numpy array.
    Supports PNG, JPG, JPEG, WEBP, and PDF first-page extraction.
    """
    if not file_bytes:
        raise ValueError("Provided file bytes are empty.")

    # Check for PDF header (%PDF)
    if file_bytes.startswith(b"%PDF"):
        pdf_img = _extract_pdf_first_page_image(file_bytes)
        if pdf_img is not None:
            return pdf_img
        raise ValueError("Could not extract or render an image from the provided PDF file.")

    # Direct decode with OpenCV (fastest for standard image formats)
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is not None:
        return img

    # Fallback to Pillow for WEBP or uncommon formats/color profiles
    try:
        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as err:
        raise ValueError(
            f"Unable to decode image. Supported formats: PNG, JPG, JPEG, WEBP, PDF. Error: {err}"
        ) from err


def preprocess_medical_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Preprocess medical prescriptions and lab reports for vernacular OCR and AI decoding.

    Steps:
    1. Decodes uploaded image bytes (or converts first page if PDF).
    2. Proportionally resizes to a max width of 1600px while preserving aspect ratio.
    3. Converts to grayscale, applies CLAHE (clipLimit=2.0, tileGridSize=(8,8)) to fix
       uneven lighting/glare, and applies cv2.fastNlMeansDenoising to clean phone camera noise.
    4. Computes image quality metrics (Laplacian blur variance and brightness score) and returns
       enhanced PNG bytes, preview base64 data URI, and warnings.

    Returns:
        Dict containing:
            - enhanced_image_bytes: Raw PNG bytes for downstream multimodal LLM / OCR inference.
            - preview_base64: Data URI string for immediate UI rendering.
            - raw_base64: Plain base64 string without data URI prefix.
            - metrics: Image quality indicators (blur variance, brightness, warnings).
            - dimensions: Original and processed image dimensions.
    """
    # 1. Decode image
    bgr_img = _decode_image_bytes(file_bytes)
    orig_h, orig_w = bgr_img.shape[:2]

    # 2. Proportionally resize to max width of 1600px
    if orig_w > MAX_IMAGE_WIDTH:
        scale = MAX_IMAGE_WIDTH / float(orig_w)
        new_w = MAX_IMAGE_WIDTH
        new_h = int(round(orig_h * scale))
        resized = cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        resized = bgr_img
        new_w, new_h = orig_w, orig_h

    # 3. Grayscale conversion
    if len(resized.shape) == 3 and resized.shape[2] == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized

    # Compute blur variance via Laplacian on original grayscale before denoising
    # (cv2.CV_64F provides higher precision for variance calculation)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))

    # Evaluate quality flags & human-readable warnings
    warnings: List[str] = []
    is_blurry = laplacian_var < LAPLACIAN_BLUR_THRESHOLD
    is_too_dark = brightness < BRIGHTNESS_MIN_THRESHOLD
    is_too_bright = brightness > BRIGHTNESS_MAX_THRESHOLD

    if is_blurry:
        warnings.append(
            f"Image appears blurry (sharpness score: {laplacian_var:.1f}). "
            "Handwritten prescriptions may be hard to decode. Please ensure sharp focus."
        )
    if is_too_dark:
        warnings.append(
            f"Image is underexposed (brightness: {brightness:.1f}/255). "
            "Please capture under adequate lighting or turn on flash."
        )
    elif is_too_bright:
        warnings.append(
            f"Image has severe glare or overexposure (brightness: {brightness:.1f}/255). "
            "Avoid direct flashlight reflections on glossy prescription pads."
        )

    quality_status = "good"
    if is_blurry and (is_too_dark or is_too_bright):
        quality_status = "critical"
    elif is_blurry or is_too_dark or is_too_bright:
        quality_status = "warning"

    # Apply CLAHE to resolve uneven shadows, paper creases, and phone glare
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_enhanced = clahe.apply(gray)

    # Apply Non-Local Means Denoising to clean low-light sensor noise from phone cameras
    denoised = cv2.fastNlMeansDenoising(
        clahe_enhanced,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )

    # 4. Encode enhanced image as PNG bytes
    success, buffer = cv2.imencode(".png", denoised)
    if not success:
        raise RuntimeError("Failed to encode processed medical image into PNG format.")

    enhanced_bytes = buffer.tobytes()
    raw_b64 = base64.b64encode(enhanced_bytes).decode("utf-8")
    preview_b64 = f"data:image/png;base64,{raw_b64}"

    return {
        "enhanced_image_bytes": enhanced_bytes,
        "preview_base64": preview_b64,
        "raw_base64": raw_b64,
        "metrics": {
            "blur_variance": round(laplacian_var, 2),
            "brightness_score": round(brightness, 2),
            "is_blurry": is_blurry,
            "is_too_dark": is_too_dark,
            "is_too_bright": is_too_bright,
            "quality_status": quality_status,
            "warnings": warnings,
        },
        "dimensions": {
            "original_width": orig_w,
            "original_height": orig_h,
            "processed_width": new_w,
            "processed_height": new_h,
        },
    }


def extract_pdf_text(file_bytes: bytes) -> Optional[str]:
    """
    Extracts plain text from a PDF using pypdf. Returns None if the PDF has
    no meaningful text (e.g. it is a scanned image) or if extraction fails.
    """
    if not file_bytes or not file_bytes.startswith(b"%PDF"):
        return None
    try:
        import io
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        chunks: List[str] = []
        for page in reader.pages[:3]:
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(text)
        combined = "\n".join(chunks).strip()
        return combined if len(combined) >= 20 else None
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"PDF text extraction failed: {exc}")
        return None

