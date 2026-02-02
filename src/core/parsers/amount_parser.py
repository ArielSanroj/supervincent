"""
Amount parsing utilities for invoice extraction.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class AmountParser:
    """Parses currency amounts from invoice text."""

    def __init__(self):
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

    def extract_totals(self, text: str) -> Tuple[float, float, float]:
        """Extract subtotal, taxes, and total from text."""
        subtotal = self._extract_subtotal(text)
        taxes = self._extract_taxes(text)
        total = self._extract_total(text)

        if subtotal == 0.0 and total > 0:
            subtotal = total - taxes

        return subtotal, taxes, total

    def _extract_subtotal(self, text: str) -> float:
        """Extract subtotal from text."""
        for pattern in [r'Subtotal\s+\$?([\d\.,]+)', r'Sub\s*Total\s+\$?([\d\.,]+)']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_amount(match.group(1))
        return 0.0

    def _extract_taxes(self, text: str) -> float:
        """Extract taxes from text."""
        for pattern in self.tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_amount(match.group(1))
        return 0.0

    def _extract_total(self, text: str) -> float:
        """Extract total from text."""
        total = 0.0

        if re.search(r'LA\s*SUMA\s*DE', text, re.IGNORECASE):
            total = self._extract_total_from_suma(text)

        if total == 0.0:
            for pattern in self.total_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    total = self.parse_amount(match.group(1))
                    if total > 0:
                        break

        if total == 0.0:
            total = self._extract_total_fallback(text)

        return total

    def _extract_total_from_suma(self, text: str) -> float:
        """Extract total from LA SUMA DE format."""
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.search(r'LA\s*SUMA\s*DE', line, re.IGNORECASE):
                search_text = '\n'.join(lines[i:min(i+3, len(lines))])
                matches = re.findall(r'([\d\.,]{4,})', search_text)
                for match in matches:
                    parsed = self.parse_amount(match)
                    if parsed > 100:
                        return parsed
        return 0.0

    def _extract_total_fallback(self, text: str) -> float:
        """Fallback total extraction method."""
        for line in text.splitlines():
            if re.search(r'(total|pagar|cobro|factura|valor)', line, re.IGNORECASE):
                matches = re.findall(r'([\d\.,]{4,})', line)
                for match in matches:
                    parsed = self.parse_amount(match)
                    if parsed > 100:
                        return parsed
        return 0.0

    def parse_amount(self, raw: str) -> float:
        """Parse currency-like strings with dots/commas into float.

        Colombian format: dot = thousands, comma = decimals (e.g., 251.200 = 251200)
        """
        try:
            s = raw.strip()
            s = re.sub(r"[^0-9\.,]", "", s)

            if "." in s and "," not in s:
                parts = s.split(".")
                if len(parts) == 2 and len(parts[1]) == 3:
                    s = s.replace(".", "")
                elif len(parts) == 2 and len(parts[1]) <= 2:
                    pass
                else:
                    s = s.replace(".", "")
            elif "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s:
                parts = s.split(",")
                if len(parts[-1]) == 3:
                    s = s.replace(",", "")
                elif len(parts[-1]) <= 2:
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")

            return float(s)
        except Exception:
            try:
                return float(raw)
            except Exception:
                return 0.0
