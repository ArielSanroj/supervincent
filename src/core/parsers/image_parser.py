"""
Image invoice parser using OCR.
"""

import logging
from pathlib import Path
from typing import Optional

from ..models import InvoiceData, InvoiceItem, InvoiceType
from .base import BaseParser

logger = logging.getLogger(__name__)

# Optional OCR imports
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np

    try:
        from shutil import which
        _candidates = [
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract",
            which("tesseract") or ""
        ]
        for _path in _candidates:
            if _path and Path(_path).exists():
                pytesseract.pytesseract.tesseract_cmd = _path
                break
    except Exception:
        pass
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class ImageParser(BaseParser):
    """Image invoice parser using OCR."""

    def __init__(self):
        """Initialize image parser."""
        if not OCR_AVAILABLE:
            logger.warning("OCR libraries not available")

    def can_parse(self, file_path: str) -> bool:
        """Check if file is an image."""
        return file_path.lower().endswith(('.jpg', '.jpeg', '.png'))

    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse image invoice using OCR."""
        if not OCR_AVAILABLE:
            logger.error("OCR not available")
            return None

        logger.info(f"Parsing image: {file_path}")

        try:
            base_image = Image.open(file_path)
            strategies = self._get_ocr_strategies()

            from .pdf_parser import PDFParser
            pdf_parser = PDFParser()
            best_parsed: Optional[InvoiceData] = None

            for preprocess, cfg in strategies:
                try:
                    img = preprocess(base_image)
                    text = pytesseract.image_to_string(img, lang='spa+eng', config=cfg)
                    snippet = (text or '').strip()[:200]
                    logger.info(f"OCR snippet [{cfg}]: {snippet}")

                    if not text.strip():
                        continue

                    parsed = pdf_parser.parse_text(text)
                    if parsed:
                        if parsed.total > 0 or parsed.subtotal > 0:
                            best_parsed = parsed
                            logger.info(f"Successfully extracted invoice with total: {parsed.total}")
                            break
                        best_parsed = best_parsed or parsed
                except Exception as ocr_e:
                    logger.warning(f"OCR strategy failed ({cfg}): {ocr_e}")

            if best_parsed is None:
                logger.warning("No parsed result from OCR strategies")
                return self._fallback_minimal_invoice()
            return best_parsed

        except Exception as e:
            logger.error(f"Error parsing image {file_path}: {e}")
            return self._fallback_minimal_invoice()

    def _get_ocr_strategies(self):
        """Get list of OCR preprocessing strategies."""
        strategies = []

        def as_is(img: Image.Image) -> Image.Image:
            return img

        def upscale_gray(img: Image.Image) -> Image.Image:
            if img.mode != 'L':
                img = img.convert('L')
            w, h = img.size
            return img.resize((int(w * 1.5), int(h * 1.5)))

        def binarize(img: Image.Image) -> Image.Image:
            return self._preprocess_image(img)

        def invert_binarize(img: Image.Image) -> Image.Image:
            try:
                if img.mode != 'L':
                    img = img.convert('L')
                cv_image = np.array(img)
                cv_image = cv2.medianBlur(cv_image, 3)
                cv_image = cv2.adaptiveThreshold(
                    cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, 11, 2
                )
                return Image.fromarray(cv_image)
            except Exception:
                return img

        strategies.append((as_is, '--psm 6 --oem 3'))
        strategies.append((upscale_gray, '--psm 6 --oem 3'))
        strategies.append((binarize, '--psm 6 --oem 3'))
        strategies.append((invert_binarize, '--psm 6 --oem 3'))
        strategies.append((upscale_gray, '--psm 4 --oem 3'))
        strategies.append((binarize, '--psm 11 --oem 3'))

        return strategies

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        try:
            if image.mode != 'L':
                image = image.convert('L')

            cv_image = np.array(image)
            cv_image = cv2.medianBlur(cv_image, 3)
            cv_image = cv2.adaptiveThreshold(
                cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            return Image.fromarray(cv_image)

        except Exception as e:
            logger.warning(f"Error preprocessing image: {e}")
            return image

    def _fallback_minimal_invoice(self) -> InvoiceData:
        """Return a minimal valid InvoiceData."""
        return InvoiceData(
            invoice_type=InvoiceType.PURCHASE,
            date="",
            vendor="Proveedor Desconocido",
            client="Proveedor Desconocido",
            items=[InvoiceItem(code="001", description="Producto no identificado", quantity=1.0, price=0.0)],
            subtotal=0.0,
            taxes=0.0,
            total=0.0,
            raw_text=None
        )
