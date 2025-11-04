"""
Invoice parsing modules for different file formats.
"""

import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber

# Optional OCR imports
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    # Try to set tesseract binary path on macOS (Homebrew) if available
    try:
        from shutil import which
        _candidates = [
            "/opt/homebrew/bin/tesseract",  # Apple Silicon default
            "/usr/local/bin/tesseract",    # Intel macOS default
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

from .models import InvoiceData, InvoiceItem, InvoiceType

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for invoice parsers."""
    
    @abstractmethod
    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice file and return structured data."""
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if parser can handle the file type."""
        pass


class PDFParser(BaseParser):
    """PDF invoice parser."""
    
    def __init__(self):
        """Initialize PDF parser with regex patterns."""
        self.date_patterns = [
            r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        self.vendor_patterns = [
            r'Proveedor[:\s]+(.+)',
            r'Vendor[:\s]+(.+)',
            r'From[:\s]+(.+)',
            r'Bill To[:\s]+(.+)',
        ]
        
        self.total_patterns = [
            r'LA\s*SUMA\s*DE[:\s]*[^0-9]*([\d\.,]+)',
            r'TOTAL\s*FACTURA[:\s]*\$?([\d\.,]+)',
            r'VALOR\s*A\s*PAGAR[:\s]*\$?([\d\.,]+)',
            r'Valor\s*a\s*Pagar[:\s]*\$?([\d\.,]+)',
            r'CUENTA\s*DE\s*COBRO[:\s]*\$?([\d\.,]+)',
            r'Cuenta\s*de\s*Cobro[:\s]*\$?([\d\.,]+)',
            r'TOTAL\s*[:\s]*\$?([\d\.,]+)',
            r'Total[:\s]+\$?([\d\.,]+)',
            r'Amount[:\s]+\$?([\d\.,]+)',
            r'Importe\s*Total[:\s]+\$?([\d\.,]+)'
        ]
        
        self.tax_patterns = [
            r'IVA[:\s]+\$?([\d,]+\.?\d*)',
            r'Impuesto[:\s]+\$?([\d,]+\.?\d*)',
            r'Tax[:\s]+\$?([\d,]+\.?\d*)',
        ]
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a PDF."""
        return file_path.lower().endswith('.pdf')
    
    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse PDF invoice."""
        logger.info(f"📄 Parsing PDF: {file_path}")
        
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
            
            if not text.strip():
                logger.error("No text extracted from PDF")
                return None
            
            return self.parse_text(text)
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return None
    
    def parse_text(self, text: str) -> Optional[InvoiceData]:
        """Parse already-extracted invoice text into structured data."""
        try:
            # Detect invoice type
            invoice_type = self._detect_invoice_type(text)
            
            # Extract data
            date = self._extract_date(text)
            vendor = self._extract_vendor(text)
            items = self._extract_items(text)
            subtotal, taxes, total = self._extract_totals(text)
            
            return InvoiceData(
                invoice_type=invoice_type,
                date=date,
                vendor=vendor,
                client="Cliente desde PDF" if invoice_type == InvoiceType.SALE else vendor,
                items=items,
                subtotal=subtotal,
                taxes=taxes,
                total=total,
                raw_text=text
            )
        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return None
    
    def _detect_invoice_type(self, text: str) -> InvoiceType:
        """Detect if invoice is purchase or sale based on Colombian invoice patterns."""
        text_lower = text.lower()
        
        # Strong purchase indicators (prioritize these)
        strong_purchase_patterns = [
            'cuenta de cobro',  # Cuenta de cobro = gasto reembolsable
            'servicios públicos', 'servicios publicos',
            'acueducto', 'alcantarillado', 'aseo',
            'energía', 'energia', 'electricidad',
            'gas natural', 'gas domiciliario',
            'empresas públicas', 'empresas publicas',
            'codensa', 'enel', 'epm', 'fidarta',
            'rural', 'factura de servicios',
            'debe a', 'debea',  # "DEBE A" indica que nosotros debemos (compra)
            'factura de proveedor', 'factura proveedor',
            'bill', 'purchase', 'supplier', 'vendor bill'
        ]
        
        # Purchase keywords (moderate weight)
        purchase_keywords = [
            'proveedor', 'proveedores', 'compra', 'compras',
            'orden de compra', 'oc', 'pedido', 'receipt',
            'pago a', 'pagamos a', 'gasto', 'egreso'
        ]
        
        # Sale keywords (strong indicators)
        sale_keywords = [
            'factura de venta', 'factura venta',
            'factura electrónica de venta',
            'factura electronica de venta',
            'cliente', 'clientes', 'venta', 'ventas',
            'invoice', 'sale', 'customer',
            'orden de venta', 'ov', 'cotización', 'quote',
            'debe pagar', 'debe cancelar',  # Cliente debe pagar = venta
            'vendedor', 'vendedores'
        ]
        
        # Check strong purchase patterns first (highest priority)
        for pattern in strong_purchase_patterns:
            if pattern in text_lower:
                logger.info(f"📋 Detected PURCHASE from pattern: '{pattern}'")
                return InvoiceType.PURCHASE
        
        # Score-based detection
        purchase_score = sum(1 for keyword in purchase_keywords if keyword in text_lower)
        sale_score = sum(1 for keyword in sale_keywords if keyword in text_lower)
        
        logger.info(f"📊 Invoice type scores - Purchase: {purchase_score}, Sale: {sale_score}")
        
        if purchase_score > sale_score:
            return InvoiceType.PURCHASE
        elif sale_score > purchase_score:
            return InvoiceType.SALE
        else:
            # Default to PURCHASE for PYMES (more common than sales)
            # Most invoices processed are expenses/purchases
            logger.info("⚠️ Ambiguous invoice type, defaulting to PURCHASE (common for PYMES)")
            return InvoiceType.PURCHASE
    
    def _extract_date(self, text: str) -> str:
        """Extract date from text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Normalize date format
                return self._normalize_date(date_str)
        
        # Return current date if not found
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to YYYY-MM-DD format."""
        try:
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = f"20{year}"
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    day, month, year = parts
                    if len(year) == 2:
                        year = f"20{year}"
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception:
            pass
        
        return date_str
    
    def _extract_vendor(self, text: str) -> str:
        """Extract vendor name from text."""
        # 1) Try labeled patterns first
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                # Remove trailing common labels
                vendor = re.sub(r"^(?:\s*:\s*)", "", vendor)
                vendor = re.sub(r"\s*(cliente|customer|bill to|from)\s*$", "", vendor, flags=re.IGNORECASE)
                if vendor and len(vendor) > 2:
                    return vendor

        # 2) Special case: "CUENTA DE COBRO" format - vendor is usually the line after
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        logger.info(f"🔍 Searching for vendor, total lines: {len(lines)}")
        for i, ln in enumerate(lines[:20]):
            if re.search(r'cuenta\s*de\s*cobro', ln, re.IGNORECASE):
                logger.info(f"🔍 Found 'CUENTA DE COBRO' at line {i}: {ln}")
                # Next non-empty line is likely the vendor (skip empty lines)
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    logger.info(f"🔍 Checking candidate line {j}: {candidate[:50]}")
                    # Skip empty, NIT lines, and "DEBE A" lines
                    if not candidate:
                        continue
                    if re.search(r'^nit\s*:', candidate, re.IGNORECASE):
                        logger.info(f"🔍 Skipping NIT line: {candidate}")
                        continue
                    if re.search(r'^debe\s+a', candidate, re.IGNORECASE):
                        logger.info(f"🔍 Skipping 'DEBE A' line: {candidate}")
                        continue
                    # Clean up the vendor name - remove any trailing NIT info
                    vendor = re.sub(r'\s*(nit|nit:)\s*.*$', '', candidate, flags=re.IGNORECASE)
                    vendor = vendor.strip()
                    # Must have at least 3 letters
                    letter_count = len(re.sub(r'[^A-Za-z]', '', vendor))
                    logger.info(f"🔍 Vendor candidate: '{vendor}', letters: {letter_count}")
                    if vendor and letter_count >= 3:
                        logger.info(f"📋 Found vendor from CUENTA DE COBRO: {vendor}")
                        return vendor[:120]

        # 3) Heuristic: take a prominent uppercase line near the top that looks like a company name
        candidate_lines = lines[:60]
        blacklist_keywords = [
            'factura', 'invoice', 'nit', 'n°', 'numero', 'fecha', 'address', 'dirección',
            'cliente', 'customer', 'proveedor', 'vendor', 'bill', 'pagar', 'valor',
            'subtotal', 'total', 'iva', 'impuesto', 'ref', 'referencia', 'periodo',
            'ruta', 'lectura', 'consumo', 'codigo', 'payment', 'due', 'observaciones',
            'cuenta de cobro', 'debe a', 'la suma de'
        ]
        def is_company_like(s: str) -> bool:
            if any(k in s.lower() for k in blacklist_keywords):
                return False
            # Skip NIT lines
            if re.search(r'^nit\s*:', s, re.IGNORECASE):
                return False
            # Remove numbers and punctuation for ratio
            letters = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]", "", s)
            if len(letters) < 3:
                return False
            # Uppercase ratio
            letters_no_space = letters.replace(' ', '')
            if not letters_no_space:
                return False
            upper_ratio = sum(1 for c in letters_no_space if c.isupper()) / len(letters_no_space)
            return upper_ratio > 0.5 or s.isupper()

        for ln in candidate_lines:
            if is_company_like(ln) and len(ln) >= 3:
                return ln[:120]

        return "Proveedor Desconocido"
    
    def _extract_items(self, text: str) -> List[InvoiceItem]:
        """Extract items from text."""
        items = []
        
        # Simple item extraction pattern
        item_pattern = r'(\d+)\s*-\s*(.+?)\s*(?:Impuestos|Total|Subtotal|$)'
        matches = re.findall(item_pattern, text, re.DOTALL)
        
        for match in matches:
            code = match[0]
            description = match[1].strip()
            
            # Extract quantity and price
            qty_match = re.search(rf'{code}.*?(\d+)\s+Unidad', text)
            quantity = float(qty_match.group(1)) if qty_match else 1.0
            
            price_match = re.search(rf'{code}.*?Precio unit\.\s*\$?([\d,]+\.?\d*)', text)
            price = float(price_match.group(1).replace(',', '')) if price_match else 0.0
            
            items.append(InvoiceItem(
                code=code,
                description=f"{code} - {description}",
                quantity=quantity,
                price=price
            ))
        
        # If no items found, create a generic one
        if not items:
            items.append(InvoiceItem(
                code="001",
                description="Producto no identificado",
                quantity=1.0,
                price=0.0
            ))
        
        return items
    
    def _parse_amount(self, raw: str) -> float:
        """Parse currency-like strings with dots/commas into float.
        Colombian format: dot = thousands, comma = decimals (e.g., 251.200 = 251200)
        """
        try:
            s = raw.strip()
            # Remove spaces and currency symbols
            s = re.sub(r"[^0-9\.,]", "", s)
            
            # Colombian format detection: if only dot and 3+ digits after, dot is thousands separator
            if "." in s and "," not in s:
                parts = s.split(".")
                if len(parts) == 2 and len(parts[1]) == 3:
                    # Format like "251.200" -> 251200 (Colombian thousands)
                    s = s.replace(".", "")
                elif len(parts) == 2 and len(parts[1]) <= 2:
                    # Format like "251.20" -> 251.20 (decimal)
                    s = s  # Keep as is
                else:
                    # Multiple dots, likely thousands separators
                    s = s.replace(".", "")
            
            # If both comma and dot exist
            elif "," in s and "." in s:
                # If last separator is comma, comma is decimal
                if s.rfind(",") > s.rfind("."):
                    # Format like "251.200,50" -> 251200.50
                    s = s.replace(".", "").replace(",", ".")
                else:
                    # Format like "251,200.50" -> 251200.50
                    s = s.replace(",", "")
            # If only comma
            elif "," in s:
                parts = s.split(",")
                if len(parts[-1]) == 3:
                    # Format like "251,200" -> 251200 (thousands)
                    s = s.replace(",", "")
                elif len(parts[-1]) <= 2:
                    # Format like "251,20" -> 251.20 (decimal)
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")
            
            return float(s)
        except Exception:
            try:
                return float(raw)
            except Exception:
                return 0.0

    def _extract_totals(self, text: str) -> Tuple[float, float, float]:
        """Extract subtotal, taxes, and total from text."""
        # Extract subtotal
        subtotal = 0.0
        for pattern in [r'Subtotal\s+\$?([\d\.,]+)', r'Sub\s*Total\s+\$?([\d\.,]+)']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subtotal = self._parse_amount(match.group(1))
                break
        
        # Extract taxes
        taxes = 0.0
        for pattern in self.tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                taxes = self._parse_amount(match.group(1))
                break
        
        # Extract total - special handling for "LA SUMA DE" format
        total = 0.0
        
        # First, try "LA SUMA DE" format - look for the pattern and extract number from same line or next lines
        if re.search(r'LA\s*SUMA\s*DE', text, re.IGNORECASE):
            logger.info("🔍 Found 'LA SUMA DE' pattern, extracting total...")
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if re.search(r'LA\s*SUMA\s*DE', line, re.IGNORECASE):
                    logger.info(f"🔍 Found LA SUMA DE in line {i}: {line[:100]}")
                    # Look for number in this line or next 2 lines
                    search_text = '\n'.join(lines[i:min(i+3, len(lines))])
                    logger.info(f"🔍 Searching in text: {search_text[:200]}")
                    # Find all numbers with dots/commas (4+ digits)
                    matches = re.findall(r'([\d\.,]{4,})', search_text)
                    logger.info(f"🔍 Found number matches: {matches}")
                    for match in matches:
                        parsed = self._parse_amount(match)
                        logger.info(f"🔍 Parsed amount from '{match}': {parsed}")
                        if parsed > 100:  # Reasonable minimum
                            total = parsed
                            logger.info(f"📊 Found total from LA SUMA DE: {total} (raw: {match})")
                            break
                    if total > 0:
                        break
        
        # If still zero, try standard patterns
        if total == 0.0:
            for pattern in self.total_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total = self._parse_amount(match.group(1))
                    if total > 0:
                        break
        
        # If still zero, try a fallback: scan lines containing total keywords
        if total == 0.0:
            for line in text.splitlines():
                # Look for lines with total/cobro/pagar keywords
                if re.search(r'(total|pagar|cobro|factura|valor)', line, re.IGNORECASE):
                    # Try to find largest number in the line (likely the total)
                    matches = re.findall(r'([\d\.,]{4,})', line)
                    for match in matches:
                        parsed = self._parse_amount(match)
                        if parsed > 100:  # Reasonable minimum for invoice total
                            total = parsed
                            logger.info(f"📊 Found total via fallback: {total} from line: {line[:100]}")
                            break
                    if total > 0:
                        break
        
        # If no subtotal found but total exists, calculate it
        if subtotal == 0.0 and total > 0:
            subtotal = total - taxes
        
        return subtotal, taxes, total


class ImageParser(BaseParser):
    """Image invoice parser using OCR."""
    
    def __init__(self):
        """Initialize image parser."""
        if not OCR_AVAILABLE:
            logger.warning("OCR libraries not available. Install pytesseract, Pillow, and opencv-python")
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is an image."""
        return file_path.lower().endswith(('.jpg', '.jpeg', '.png'))
    
    def parse(self, file_path: str) -> Optional[InvoiceData]:
        """Parse image invoice using OCR."""
        if not OCR_AVAILABLE:
            logger.error("OCR not available")
            return None
        
        logger.info(f"🖼️ Parsing image: {file_path}")
        
        try:
            # Load original image
            base_image = Image.open(file_path)

            # Define OCR strategies (preprocess, tesseract config)
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
                # like _preprocess but invert threshold
                try:
                    if img.mode != 'L':
                        img = img.convert('L')
                    cv_image = np.array(img)
                    cv_image = cv2.medianBlur(cv_image, 3)
                    cv_image = cv2.adaptiveThreshold(
                        cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
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

            pdf_parser = PDFParser()
            best_parsed: Optional[InvoiceData] = None
            for preprocess, cfg in strategies:
                try:
                    img = preprocess(base_image)
                    text = pytesseract.image_to_string(img, lang='spa+eng', config=cfg)
                    snippet = (text or '').strip()[:200]
                    logger.info(f"🧾 OCR snippet [{cfg}]: {snippet}")
                    if not text.strip():
                        continue
                    parsed = pdf_parser.parse_text(text)
                    if parsed:
                        logger.info(f"📄 Parsed result - Total: {parsed.total}, Subtotal: {parsed.subtotal}, Vendor: {parsed.vendor}")
                        if parsed.total > 0 or parsed.subtotal > 0:
                            best_parsed = parsed
                            logger.info(f"✅ Successfully extracted invoice with total: {parsed.total}")
                            break
                        # Keep the last parsed even if totals are zero as a fallback candidate
                        best_parsed = best_parsed or parsed
                    else:
                        logger.warning(f"⚠️ parse_text returned None for strategy {cfg}")
                except Exception as ocr_e:
                    logger.warning(f"OCR strategy failed ({cfg}): {ocr_e}")

            if best_parsed is None:
                logger.warning("No parsed result from OCR strategies; using minimal fallback")
                return self._fallback_minimal_invoice()
            return best_parsed
            
        except Exception as e:
            logger.error(f"Error parsing image {file_path}: {e}")
            return self._fallback_minimal_invoice()
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Convert to OpenCV format
            cv_image = np.array(image)
            
            # Apply image enhancement
            cv_image = cv2.medianBlur(cv_image, 3)
            cv_image = cv2.adaptiveThreshold(
                cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL
            return Image.fromarray(cv_image)
            
        except Exception as e:
            logger.warning(f"Error preprocessing image: {e}")
            return image

    def _fallback_minimal_invoice(self) -> InvoiceData:
        """Return a minimal valid InvoiceData to allow downstream processing."""
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


class InvoiceParserFactory:
    """Factory for creating appropriate invoice parsers."""
    
    _parsers = [
        PDFParser(),
        ImageParser(),
    ]
    
    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        """Get appropriate parser for file type."""
        for parser in cls._parsers:
            if parser.can_parse(file_path):
                return parser
        
        logger.error(f"No parser available for file: {file_path}")
        return None
    
    @classmethod
    def parse_invoice(cls, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice using appropriate parser."""
        parser = cls.get_parser(file_path)
        if parser:
            return parser.parse(file_path)
        return None
