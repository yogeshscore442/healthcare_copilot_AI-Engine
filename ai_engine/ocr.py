"""
ocr.py — Document ingestion: PDF → page images, Tesseract fallback text.
Never raises; returns a result dict on all paths.

Preprocessing pipeline (PHASE 2):
  1. EXIF auto-orient
  2. Convert to RGB
  3. 2× upscale for small images (<1200px wide) using LANCZOS
  4. Contrast enhancement (factor 1.4) via ImageEnhance
  5. Unsharp mask sharpening for edge clarity
  6. Adaptive deskew (rotate by detected skew angle if |angle|>0.3°)
Each step is independently wrapped — failure in one step never crashes the pipeline.
"""
from __future__ import annotations

import base64
import io
import logging
import math
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── PIL import (required) ──────────────────────────────────────────────────────
try:
    from PIL import Image, ImageFilter, ImageOps, ImageEnhance
    _PIL_OK = True
except ImportError:
    _PIL_OK = False
    logger.error("Pillow not installed — OCR will be unavailable.")

# ── numpy (optional — used for deskew) ────────────────────────────────────────
try:
    import numpy as np
    _NP_OK = True
except ImportError:
    _NP_OK = False

# ── pdf2image (optional — needs poppler) ──────────────────────────────────────
try:
    from pdf2image import convert_from_path
    _PDF2IMAGE_OK = True
except ImportError:
    _PDF2IMAGE_OK = False
    logger.warning("pdf2image not available — PDFs will use text fallback only.")

# ── Tesseract (optional) ───────────────────────────────────────────────────────
try:
    import pytesseract
    _TESSERACT_OK = True
except ImportError:
    _TESSERACT_OK = False
    logger.warning("pytesseract not available — text fallback disabled.")


# ── Public API ─────────────────────────────────────────────────────────────────

def load_document(file_path: str, mime: str) -> dict:
    """
    Load a medical document and return:
        {
          "pages":         list[PIL.Image],   # may be empty on failure
          "fallback_text": str,               # Tesseract text (may be "")
          "page_count":    int,
          "error":         str | None
        }
    Never raises.
    """
    result = {"pages": [], "fallback_text": "", "page_count": 0, "error": None}
    path = Path(file_path)

    if not path.exists():
        result["error"] = f"File not found: {file_path}"
        return result

    if path.stat().st_size == 0:
        result["error"] = "File is empty"
        return result

    if not _PIL_OK:
        result["error"] = "Pillow not installed"
        return result

    try:
        mime_lc = mime.lower()
        if "pdf" in mime_lc:
            images = _load_pdf(path)
        else:
            images = _load_image(path)

        # Preprocess for OCR quality
        images = [_preprocess(img) for img in images]
        result["pages"] = images
        result["page_count"] = len(images)

        # Tesseract fallback text
        if _TESSERACT_OK and images:
            texts = []
            for img in images:
                try:
                    txt = pytesseract.image_to_string(img, lang="eng+tam", timeout=20)
                    texts.append(txt)
                except Exception as e:
                    logger.warning("Tesseract failed on a page: %s", e)
            result["fallback_text"] = "\n".join(texts).strip()

    except Exception as e:
        logger.exception("load_document failed for %s", file_path)
        result["error"] = str(e)

    return result


def encode_image_b64(image: "Image.Image", fmt: str = "JPEG") -> str:
    """Convert a PIL Image to a base64-encoded string for LLM vision APIs."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format=fmt, quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def get_image_bytes(image: "Image.Image", fmt: str = "JPEG") -> bytes:
    """Return raw bytes of a PIL Image."""
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format=fmt, quality=85)
    return buf.getvalue()


# ── Internal helpers ───────────────────────────────────────────────────────────

def _load_pdf(path: Path) -> list:
    if _PDF2IMAGE_OK:
        try:
            return convert_from_path(str(path), dpi=250)  # PHASE 2: bumped for quality
        except Exception as e:
            logger.warning("pdf2image failed (%s), trying text extraction", e)

    # Fallback: try PyMuPDF if available
    try:
        import fitz  # type: ignore
        doc = fitz.open(str(path))
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        return pages
    except ImportError:
        pass
    except Exception as e:
        logger.warning("PyMuPDF failed: %s", e)

    return []


def _load_image(path: Path) -> list:
    try:
        img = Image.open(str(path))
        img.load()  # force read
        return [img]
    except Exception as e:
        logger.error("Image load failed for %s: %s", path, e)
        return []


def _deskew(img: "Image.Image") -> "Image.Image":
    """
    Detect and correct skew by finding the dominant line angle in a
    binarised thumbnail. Rotates only when |angle| > 0.3°.
    Requires numpy; if unavailable returns image unchanged.
    """
    if not _NP_OK:
        return img
    try:
        # Downsample for speed
        thumb = img.convert("L").resize((800, int(800 * img.height / max(img.width, 1))), Image.LANCZOS)
        arr = np.array(thumb)
        # Binarise
        thresh = arr.mean()
        binary = (arr < thresh).astype(np.uint8) * 255

        # Project-profile skew detection: sum rows for each rotation angle
        best_angle = 0.0
        best_score = -1.0
        for angle in range(-10, 11):  # −10° to +10° in 1° steps
            rotated = np.array(
                Image.fromarray(binary).rotate(angle, expand=False, fillcolor=0)
            )
            row_sums = rotated.sum(axis=1).astype(float)
            score = float(row_sums.var())
            if score > best_score:
                best_score = score
                best_angle = float(angle)

        if abs(best_angle) > 0.3:
            img = img.rotate(best_angle, expand=True, fillcolor=(255, 255, 255))
            logger.debug("Deskewed by %.1f°", best_angle)
    except Exception as e:
        logger.debug("Deskew failed (non-critical): %s", e)
    return img


def _preprocess(img: "Image.Image") -> "Image.Image":
    """
    Multi-step preprocessing pipeline (PHASE 2):
    1. EXIF auto-orient
    2. RGB conversion
    3. 2× upscale for small images (<1200px wide)
    4. Contrast enhancement
    5. Unsharp mask sharpening
    6. Adaptive deskew
    Each step is independently safe — exceptions are swallowed.
    """
    # Step 1: EXIF orientation
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Step 2: RGB
    try:
        img = img.convert("RGB")
    except Exception:
        pass

    # Step 3: Upscale small images
    try:
        if img.width < 1200:
            scale = max(2, math.ceil(1200 / img.width))
            img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    except Exception:
        pass

    # Step 4: Contrast enhancement
    try:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)
    except Exception:
        pass

    # Step 5: Unsharp mask (sharpen edges for OCR)
    try:
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    except Exception:
        pass

    # Step 6: Deskew
    img = _deskew(img)

    return img
