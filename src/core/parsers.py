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
            r'Total[:\s]+\$?([\d,]+\.?\d*)',
            r'Amount[:\s]+\$?([\d,]+\.?\d*)',
            r'Importe Total[:\s]+\$?([\d,]+\.?\d*)',
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
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return None
    
    def _detect_invoice_type(self, text: str) -> InvoiceType:
        """Detect if invoice is purchase or sale."""
        text_lower = text.lower()
        
        purchase_keywords = [
            'proveedor', 'compra', 'bill', 'purchase', 'supplier'
        ]
        
        sale_keywords = [
            'cliente', 'venta', 'invoice', 'sale', 'customer'
        ]
        
        purchase_score = sum(1 for keyword in purchase_keywords if keyword in text_lower)
        sale_score = sum(1 for keyword in sale_keywords if keyword in text_lower)
        
        if purchase_score > sale_score:
            return InvoiceType.PURCHASE
        elif sale_score > purchase_score:
            return InvoiceType.SALE
        else:
            # Default to sale if unclear
            return InvoiceType.SALE
    
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
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                if vendor and len(vendor) > 2:
                    return vendor
        
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
    
    def _extract_totals(self, text: str) -> Tuple[float, float, float]:
        """Extract subtotal, taxes, and total from text."""
        # Extract subtotal
        subtotal = 0.0
        for pattern in [r'Subtotal\s+\$?([\d,]+\.?\d*)', r'Sub Total\s+\$?([\d,]+\.?\d*)']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subtotal = float(match.group(1).replace(',', ''))
                break
        
        # Extract taxes
        taxes = 0.0
        for pattern in self.tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                taxes = float(match.group(1).replace(',', ''))
                break
        
        # Extract total
        total = 0.0
        for pattern in self.total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total = float(match.group(1).replace(',', ''))
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
            # Load and preprocess image
            image = Image.open(file_path)
            processed_image = self._preprocess_image(image)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(processed_image, lang='spa+eng')
            
            if not text.strip():
                logger.error("No text extracted from image")
                return None
            
            # Use PDF parser logic for text processing
            pdf_parser = PDFParser()
            return pdf_parser.parse_text(text)
            
        except Exception as e:
            logger.error(f"Error parsing image {file_path}: {e}")
            return None
    
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
