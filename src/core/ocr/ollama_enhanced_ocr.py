#!/usr/bin/env python3
"""
Enhanced OCR system using Ollama for better Colombian invoice processing
"""

import logging
import requests
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PIL import Image
import cv2
import numpy as np
from pathlib import Path

@dataclass
class ExtractedData:
    """Structured data extracted from invoice"""
    supplier_name: str
    supplier_phone: str
    supplier_bank: str
    total_amount: float
    items: List[Dict[str, Any]]
    invoice_number: str
    date: str
    confidence_score: float

class OllamaEnhancedOCR:
    """
    Enhanced OCR system using Ollama for Colombian invoice processing
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.logger = logging.getLogger(__name__)
        
        # Colombian invoice patterns
        self.colombian_patterns = {
            'supplier_name': [
                r'(?:Proveedor|Supplier|Vendedor)[:\s]+([A-ZÁÉÍÓÚÑ\s]+)',
                r'(?:Nombre|Name)[:\s]+([A-ZÁÉÍÓÚÑ\s]+)',
                r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{10,50})(?:\s+[0-9]{7,11})',
                r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{10,50})(?:\s+CEL:)',
            ],
            'phone': [
                r'(?:Tel|Cel|Phone)[:\s]*(\d{10,11})',
                r'(\d{10,11})',
                r'CEL:(\d{10,11})',
            ],
            'bank_account': [
                r'(?:Cuenta|Account|Nequi|Bancolombia)[:\s]*(\d{10,15})',
                r'(\d{10,15})',
            ],
            'total_amount': [
                r'(?:Total|TOTAL|Valor|VALOR)[:\s]*\$?([0-9.,]+)',
                r'(?:Pesos|pesos)[:\s]*([0-9.,]+)',
                r'\$([0-9.,]+)',
                r'([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)',
            ],
            'items': [
                r'([A-ZÁÉÍÓÚÑ][^0-9]{10,50})\s+([0-9.,]+)',
                r'([A-ZÁÉÍÓÚÑ][^0-9]{10,50})\s+\$([0-9.,]+)',
            ]
        }
        
        # Initialize Ollama model
        self._initialize_ollama()
    
    def _initialize_ollama(self):
        """Initialize Ollama with appropriate model"""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.logger.info(f"Ollama models available: {[m['name'] for m in models]}")
                
                # Use llama3.2 or similar for text processing
                self.model_name = "llama3.2:latest"
                if not any(self.model_name in m['name'] for m in models):
                    self.logger.warning(f"Model {self.model_name} not found, using first available")
                    self.model_name = models[0]['name'] if models else "llama3.2:latest"
            else:
                self.logger.error("Ollama not running, falling back to basic OCR")
                self.model_name = None
        except Exception as e:
            self.logger.error(f"Error initializing Ollama: {e}")
            self.model_name = None
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Enhanced image preprocessing for better OCR"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Resize if too small
            height, width = cleaned.shape
            if height < 1000:
                scale = 1000 / height
                new_width = int(width * scale)
                cleaned = cv2.resize(cleaned, (new_width, 1000))
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            return None
    
    def extract_text_with_ollama(self, image_path: str) -> str:
        """Extract text using Ollama vision model"""
        try:
            if not self.model_name:
                return self._fallback_ocr(image_path)
            
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return self._fallback_ocr(image_path)
            
            # Save processed image temporarily
            temp_path = "/tmp/processed_invoice.png"
            cv2.imwrite(temp_path, processed_image)
            
            # Convert image to base64
            import base64
            with open(temp_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create prompt for Colombian invoice processing
            prompt = """
            Analiza esta factura colombiana y extrae la siguiente información de manera precisa:
            
            1. Nombre del proveedor/supplier (busca nombres como "Juan Hernando Bejarano")
            2. Teléfono del proveedor (formato: 10-11 dígitos)
            3. Cuenta bancaria (Nequi, Bancolombia, etc.)
            4. Monto total de la factura (busca "Total", "Valor", "Pesos")
            5. Desglose de items (Combustible, Peajes, Comida, etc.)
            6. Número de factura
            7. Fecha
            
            Responde en formato JSON con esta estructura:
            {
                "supplier_name": "nombre exacto del proveedor",
                "supplier_phone": "teléfono",
                "supplier_bank": "cuenta bancaria",
                "total_amount": 251200,
                "items": [
                    {"description": "Combustible", "amount": 100000},
                    {"description": "Peajes", "amount": 61200},
                    {"description": "Comida", "amount": 90000}
                ],
                "invoice_number": "número de factura",
                "date": "fecha",
                "raw_text": "texto completo extraído"
            }
            """
            
            # Call Ollama API
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        extracted_data = json.loads(json_match.group())
                        return extracted_data
                    except json.JSONDecodeError:
                        self.logger.warning("Could not parse JSON from Ollama response")
                        return {"raw_text": response_text}
                else:
                    return {"raw_text": response_text}
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_ocr(image_path)
                
        except Exception as e:
            self.logger.error(f"Error in Ollama OCR: {e}")
            return self._fallback_ocr(image_path)
    
    def _fallback_ocr(self, image_path: str) -> Dict[str, Any]:
        """Fallback OCR using pytesseract"""
        try:
            import pytesseract
            from PIL import Image
            
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return {"raw_text": "", "error": "Could not process image"}
            
            # Convert to PIL Image
            pil_image = Image.fromarray(processed_image)
            
            # Extract text
            raw_text = pytesseract.image_to_string(pil_image, lang='spa')
            
            return {"raw_text": raw_text}
            
        except Exception as e:
            self.logger.error(f"Fallback OCR error: {e}")
            return {"raw_text": "", "error": str(e)}
    
    def extract_structured_data(self, image_path: str) -> ExtractedData:
        """Extract structured data from invoice image"""
        try:
            # Get data from Ollama
            ollama_data = self.extract_text_with_ollama(image_path)
            
            if "raw_text" in ollama_data and not ollama_data.get("supplier_name"):
                # Fallback to pattern matching
                return self._extract_with_patterns(ollama_data["raw_text"])
            
            # Use Ollama data if available
            return ExtractedData(
                supplier_name=ollama_data.get("supplier_name", ""),
                supplier_phone=ollama_data.get("supplier_phone", ""),
                supplier_bank=ollama_data.get("supplier_bank", ""),
                total_amount=float(ollama_data.get("total_amount", 0)),
                items=ollama_data.get("items", []),
                invoice_number=ollama_data.get("invoice_number", ""),
                date=ollama_data.get("date", ""),
                confidence_score=0.9  # High confidence for Ollama
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting structured data: {e}")
            return ExtractedData(
                supplier_name="",
                supplier_phone="",
                supplier_bank="",
                total_amount=0.0,
                items=[],
                invoice_number="",
                date="",
                confidence_score=0.0
            )
    
    def _extract_with_patterns(self, text: str) -> ExtractedData:
        """Extract data using regex patterns"""
        try:
            # Extract supplier name
            supplier_name = ""
            for pattern in self.colombian_patterns['supplier_name']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    supplier_name = match.group(1).strip()
                    break
            
            # Extract phone
            supplier_phone = ""
            for pattern in self.colombian_patterns['phone']:
                match = re.search(pattern, text)
                if match:
                    supplier_phone = match.group(1).strip()
                    break
            
            # Extract bank account
            supplier_bank = ""
            for pattern in self.colombian_patterns['bank_account']:
                match = re.search(pattern, text)
                if match:
                    supplier_bank = match.group(1).strip()
                    break
            
            # Extract total amount
            total_amount = 0.0
            for pattern in self.colombian_patterns['total_amount']:
                match = re.search(pattern, text)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    try:
                        total_amount = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            # Extract items
            items = []
            for pattern in self.colombian_patterns['items']:
                matches = re.findall(pattern, text)
                for match in matches:
                    description = match[0].strip()
                    amount_str = match[1].replace(',', '').replace('.', '')
                    try:
                        amount = float(amount_str)
                        items.append({
                            "description": description,
                            "amount": amount
                        })
                    except ValueError:
                        continue
            
            return ExtractedData(
                supplier_name=supplier_name,
                supplier_phone=supplier_phone,
                supplier_bank=supplier_bank,
                total_amount=total_amount,
                items=items,
                invoice_number="",
                date="",
                confidence_score=0.6  # Medium confidence for pattern matching
            )
            
        except Exception as e:
            self.logger.error(f"Error in pattern extraction: {e}")
            return ExtractedData(
                supplier_name="",
                supplier_phone="",
                supplier_bank="",
                total_amount=0.0,
                items=[],
                invoice_number="",
                date="",
                confidence_score=0.0
            )

# Example usage
if __name__ == "__main__":
    ocr = OllamaEnhancedOCR()
    result = ocr.extract_structured_data("/Users/arielsanroj/downloads/test3factura.jpg")
    print(f"Supplier: {result.supplier_name}")
    print(f"Total: ${result.total_amount:,.2f}")
    print(f"Items: {result.items}")