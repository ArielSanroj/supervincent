"""
Text extraction utilities for invoice parsing.
"""

import re
import logging
from typing import List, Optional

from ..models import InvoiceType, InvoiceItem
from .amount_parser import AmountParser

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extracts structured data from invoice text."""

    def __init__(self):
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

        self.amount_parser = AmountParser()

    def detect_invoice_type(self, text: str) -> InvoiceType:
        """Detect if invoice is purchase or sale."""
        text_lower = text.lower()

        strong_purchase_patterns = [
            'cuenta de cobro', 'servicios publicos',
            'acueducto', 'alcantarillado', 'aseo', 'energia',
            'electricidad', 'gas natural', 'gas domiciliario',
            'empresas publicas', 'codensa', 'enel',
            'epm', 'fidarta', 'rural', 'factura de servicios', 'debe a',
            'debea', 'factura de proveedor', 'factura proveedor',
            'bill', 'purchase', 'supplier', 'vendor bill'
        ]

        purchase_keywords = [
            'proveedor', 'proveedores', 'compra', 'compras',
            'orden de compra', 'oc', 'pedido', 'receipt',
            'pago a', 'pagamos a', 'gasto', 'egreso'
        ]

        sale_keywords = [
            'factura de venta', 'factura venta',
            'factura electronica de venta',
            'cliente', 'clientes', 'venta', 'ventas',
            'invoice', 'sale', 'customer', 'orden de venta', 'ov',
            'cotizacion', 'quote', 'debe pagar', 'debe cancelar',
            'vendedor', 'vendedores'
        ]

        for pattern in strong_purchase_patterns:
            if pattern in text_lower:
                logger.info(f"Detected PURCHASE from pattern: '{pattern}'")
                return InvoiceType.PURCHASE

        purchase_score = sum(1 for keyword in purchase_keywords if keyword in text_lower)
        sale_score = sum(1 for keyword in sale_keywords if keyword in text_lower)

        logger.info(f"Invoice type scores - Purchase: {purchase_score}, Sale: {sale_score}")

        if purchase_score > sale_score:
            return InvoiceType.PURCHASE
        elif sale_score > purchase_score:
            return InvoiceType.SALE
        else:
            logger.info("Ambiguous invoice type, defaulting to PURCHASE")
            return InvoiceType.PURCHASE

    def extract_date(self, text: str) -> str:
        """Extract date from text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self._normalize_date(date_str)

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

    def extract_vendor(self, text: str) -> str:
        """Extract vendor name from text."""
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                vendor = re.sub(r"^(?:\s*:\s*)", "", vendor)
                vendor = re.sub(r"\s*(cliente|customer|bill to|from)\s*$", "", vendor, flags=re.IGNORECASE)
                if vendor and len(vendor) > 2:
                    return vendor

        vendor = self._extract_vendor_from_cuenta_cobro(text)
        if vendor:
            return vendor

        vendor = self._extract_vendor_heuristic(text)
        if vendor:
            return vendor

        return "Proveedor Desconocido"

    def _extract_vendor_from_cuenta_cobro(self, text: str) -> Optional[str]:
        """Extract vendor from CUENTA DE COBRO format."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for i, ln in enumerate(lines[:20]):
            if re.search(r'cuenta\s*de\s*cobro', ln, re.IGNORECASE):
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    if re.search(r'^nit\s*:', candidate, re.IGNORECASE):
                        continue
                    if re.search(r'^debe\s+a', candidate, re.IGNORECASE):
                        continue
                    vendor = re.sub(r'\s*(nit|nit:)\s*.*$', '', candidate, flags=re.IGNORECASE).strip()
                    letter_count = len(re.sub(r'[^A-Za-z]', '', vendor))
                    if vendor and letter_count >= 3:
                        return vendor[:120]
        return None

    def _extract_vendor_heuristic(self, text: str) -> Optional[str]:
        """Extract vendor using heuristics."""
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        candidate_lines = lines[:60]

        blacklist_keywords = [
            'factura', 'invoice', 'nit', 'numero', 'fecha', 'address',
            'direccion', 'cliente', 'customer', 'proveedor', 'vendor', 'bill',
            'pagar', 'valor', 'subtotal', 'total', 'iva', 'impuesto', 'ref',
            'referencia', 'periodo', 'ruta', 'lectura', 'consumo', 'codigo',
            'payment', 'due', 'observaciones', 'cuenta de cobro', 'debe a',
            'la suma de'
        ]

        for ln in candidate_lines:
            if self._is_company_like(ln, blacklist_keywords) and len(ln) >= 3:
                return ln[:120]

        return None

    def _is_company_like(self, s: str, blacklist: List[str]) -> bool:
        """Check if string looks like a company name."""
        if any(k in s.lower() for k in blacklist):
            return False
        if re.search(r'^nit\s*:', s, re.IGNORECASE):
            return False
        letters = re.sub(r"[^A-Za-z\s]", "", s)
        if len(letters) < 3:
            return False
        letters_no_space = letters.replace(' ', '')
        if not letters_no_space:
            return False
        upper_ratio = sum(1 for c in letters_no_space if c.isupper()) / len(letters_no_space)
        return upper_ratio > 0.5 or s.isupper()

    def extract_items(self, text: str) -> List[InvoiceItem]:
        """Extract items from text."""
        items = []
        item_pattern = r'(\d+)\s*-\s*(.+?)\s*(?:Impuestos|Total|Subtotal|$)'
        matches = re.findall(item_pattern, text, re.DOTALL)

        for match in matches:
            code = match[0]
            description = match[1].strip()

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

        if not items:
            items.append(InvoiceItem(
                code="001",
                description="Producto no identificado",
                quantity=1.0,
                price=0.0
            ))

        return items

    def extract_totals(self, text: str):
        """Extract subtotal, taxes, and total from text."""
        return self.amount_parser.extract_totals(text)

    def parse_amount(self, raw: str) -> float:
        """Parse currency-like strings with dots/commas into float."""
        return self.amount_parser.parse_amount(raw)
