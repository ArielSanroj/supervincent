"""
Service to integrate with a local Ollama server for invoice parsing.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from ..core.models import InvoiceData, InvoiceItem, InvoiceType
from ..core.config import Settings

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.text_model = settings.ollama_text_model
        self.vision_model = settings.ollama_vision_model

    def _post(self, path: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        # Some Ollama endpoints stream; assume non-stream for simplicity
        data = resp.json()
        return data

    def parse_text_to_invoice(self, text: str) -> Optional[InvoiceData]:
        """Use LLM to extract structured invoice data from raw text."""
        system = (
            "Eres un extractor de datos de facturas. Devuelve SOLO JSON válido con esta forma:\n"
            "{\n  \"invoice_type\": \"purchase|sale\",\n  \"date\": \"YYYY-MM-DD\",\n  \"vendor\": \"string\",\n  \"client\": \"string\",\n  \"items\": [{\n    \"code\": \"string\", \"description\": \"string\", \"quantity\": number, \"price\": number\n  }],\n  \"subtotal\": number, \"taxes\": number, \"total\": number\n}"
        )
        prompt = (
            "Extrae y normaliza los campos desde el siguiente texto de factura. "
            "Si faltan datos, estima razonablemente. Responde SOLO el JSON.\n\n" + text
        )
        payload = {
            "model": self.text_model,
            "prompt": f"{system}\n\n{prompt}",
            "stream": False,
            "options": {"temperature": 0}
        }
        try:
            data = self._post("/api/generate", payload)
            content = data.get("response") or data.get("message") or ""
            json_str = self._extract_json(content)
            if not json_str:
                return None
            obj = json.loads(json_str)
            return self._to_invoice_data(obj, raw_text=text)
        except Exception as e:
            logger.warning(f"Ollama text parse failed: {e}")
            return None

    def parse_image_to_invoice(self, image_path: str) -> Optional[InvoiceData]:
        """Use a vision model to parse an image invoice (if available)."""
        try:
            b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
            messages = [
                {"role": "system", "content": "Extrae datos de factura y responde SOLO JSON con los campos definidos."},
                {"role": "user", "content": "Analiza la imagen y devuelve el JSON de la factura." , "images": [b64]},
            ]
            payload = {"model": self.vision_model, "messages": messages, "stream": False}
            data = self._post("/api/chat", payload)
            content = data.get("message", {}).get("content", "") or data.get("response", "")
            json_str = self._extract_json(content)
            if not json_str:
                return None
            obj = json.loads(json_str)
            return self._to_invoice_data(obj, raw_text=None)
        except Exception as e:
            logger.warning(f"Ollama vision parse failed: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[str]:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return text[start:end+1]
            return None
        except Exception:
            return None

    def _to_invoice_data(self, obj: Dict[str, Any], raw_text: Optional[str]) -> InvoiceData:
        t = (obj.get("invoice_type") or "purchase").strip().lower()
        inv_type = InvoiceType.SALE if t in ("sale", "venta") else InvoiceType.PURCHASE
        items = []
        for it in obj.get("items", []) or []:
            items.append(InvoiceItem(
                code=str(it.get("code") or "001"),
                description=str(it.get("description") or "Item"),
                quantity=float(it.get("quantity") or 1.0),
                price=float(it.get("price") or 0.0),
            ))
        return InvoiceData(
            invoice_type=inv_type,
            date=str(obj.get("date") or ""),
            vendor=str(obj.get("vendor") or "Proveedor Desconocido"),
            client=str(obj.get("client") or ""),
            items=items or [InvoiceItem(code="001", description="Item", quantity=1.0, price=0.0)],
            subtotal=float(obj.get("subtotal") or 0.0),
            taxes=float(obj.get("taxes") or 0.0),
            total=float(obj.get("total") or 0.0),
            raw_text=raw_text,
        )


