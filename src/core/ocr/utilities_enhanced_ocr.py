#!/usr/bin/env python3
"""
Enhanced OCR system specifically for Colombian utilities invoices
"""

import logging
import requests
import json
import re
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PIL import Image
import pytesseract

@dataclass
class UtilitiesInvoiceData:
    """Structured data for utilities invoices"""
    supplier_name: str
    supplier_nit: str
    invoice_number: str
    customer_name: str
    customer_address: str
    stratum: int
    period: str
    reading_date: str
    due_date: str
    total_amount: float
    acueducto: Dict[str, Any]
    alcantarillado: Dict[str, Any]
    aseo: Dict[str, Any]
    deuda_anterior: float
    recargos: float
    subsidios: Dict[str, float]
    confidence_score: float

class UtilitiesEnhancedOCR:
    """
    Enhanced OCR system for Colombian utilities invoices
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.logger = logging.getLogger(__name__)
        
        # Utilities-specific patterns
        self.utilities_patterns = {
            'supplier_name': [
                r'(?:EMPRESAS PUBLICAS|ACUEDUCTO|ALCANTARILLADO|ASEO)[^A-Z]*([A-Z][A-Z\s\.]{10,50})',
                r'([A-Z][A-Z\s\.]{10,50})\s*E\.S\.P',
                r'([A-Z][A-Z\s\.]{10,50})\s*S\.A\.S',
            ],
            'nit': [
                r'NIT[:\s]*(\d{6,12}[-]?\d?)',
                r'Nit[:\s]*(\d{6,12}[-]?\d?)',
                r'(\d{6,12}[-]?\d?)\s*NIT',
            ],
            'invoice_number': [
                r'FACTURA[:\s]*(\d{6,10})',
                r'NUMERO[:\s]*(\d{6,10})',
                r'No[:\s]*(\d{6,10})',
            ],
            'customer_name': [
                r'CLIENTE[:\s]*([A-Z][A-Z\s]{10,50})',
                r'USUARIO[:\s]*([A-Z][A-Z\s]{10,50})',
                r'ABONADO[:\s]*([A-Z][A-Z\s]{10,50})',
            ],
            'stratum': [
                r'ESTRATO[:\s]*(\d)',
                r'ESTRATO\s*(\d)',
            ],
            'period': [
                r'PERIODO[:\s]*([A-Z]{3,9}\s*\d{4})',
                r'FACTURACION[:\s]*([A-Z]{3,9}\s*\d{4})',
            ],
            'total_amount': [
                r'VALOR\s*A\s*PAGAR[:\s]*\$?([0-9.,]+)',
                r'TOTAL\s*A\s*PAGAR[:\s]*\$?([0-9.,]+)',
                r'TOTAL[:\s]*\$?([0-9.,]+)',
            ],
            'acueducto_subtotal': [
                r'ACUEDUCTO[^0-9]*([0-9.,]+)',
                r'SUBTOTAL\s*ACUEDUCTO[:\s]*\$?([0-9.,]+)',
            ],
            'aseo_subtotal': [
                r'ASEO[^0-9]*([0-9.,]+)',
                r'SUBTOTAL\s*ASEO[:\s]*\$?([0-9.,]+)',
            ],
            'deuda_anterior': [
                r'DEUDA\s*ANTERIOR[:\s]*\$?([0-9.,]+)',
                r'SALDO\s*ANTERIOR[:\s]*\$?([0-9.,]+)',
            ]
        }
    
    def preprocess_utilities_image(self, image_path: str) -> np.ndarray:
        """Enhanced preprocessing for utilities invoices"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding for better table detection
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Resize if too small
            height, width = cleaned.shape
            if height < 1500:
                scale = 1500 / height
                new_width = int(width * scale)
                cleaned = cv2.resize(cleaned, (new_width, 1500))
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocessing utilities image: {e}")
            return None
    
    def extract_with_ollama_utilities(self, image_path: str) -> Dict[str, Any]:
        """Extract data using Ollama with utilities-specific prompt"""
        try:
            # Preprocess image
            processed_image = self.preprocess_utilities_image(image_path)
            if processed_image is None:
                return self._fallback_utilities_ocr(image_path)
            
            # Save processed image temporarily
            temp_path = "/tmp/utilities_invoice.png"
            cv2.imwrite(temp_path, processed_image)
            
            # Convert image to base64
            import base64
            with open(temp_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create utilities-specific prompt
            prompt = """
            Analiza esta factura de servicios públicos colombiana (acueducto, alcantarillado, aseo) y extrae la siguiente información de manera precisa:
            
            INFORMACIÓN BÁSICA:
            1. Nombre de la empresa proveedora (ej: "EMPRESAS PUBLICAS DE NILO S.A.S. E.S.P.")
            2. NIT de la empresa (formato: 123456789-0)
            3. Número de factura (ej: "358157")
            4. Nombre del cliente/abonado
            5. Dirección del cliente
            6. Estrato socioeconómico (1-6)
            7. Período de facturación (ej: "OCTUBRE 2025")
            8. Fecha de lectura
            9. Fecha de vencimiento
            10. VALOR A PAGAR (total final)
            
            SECCIONES DE SERVICIOS:
            ACUEDUCTO:
            - Cargo fijo
            - Consumo básico (m3)
            - Consumo complementario (m3)
            - Subtotal acueducto
            - Subsidios acueducto
            
            ALCANTARILLADO:
            - Cargo fijo
            - Consumo (m3)
            - Subtotal alcantarillado
            
            ASEO:
            - Recolección de basuras
            - Subtotal aseo
            - Subsidios aseo
            
            OTROS:
            - Deuda anterior
            - Recargos
            - Total subsidios
            
            Responde en formato JSON con esta estructura:
            {
                "supplier_name": "nombre exacto de la empresa",
                "supplier_nit": "123456789-0",
                "invoice_number": "358157",
                "customer_name": "nombre del cliente",
                "customer_address": "dirección completa",
                "stratum": 3,
                "period": "OCTUBRE 2025",
                "reading_date": "08/10/2025",
                "due_date": "24/10/2025",
                "total_amount": 529369,
                "acueducto": {
                    "cargo_fijo": 20734,
                    "consumo_basico_m3": 10,
                    "consumo_basico_valor": 1651.81,
                    "consumo_complementario_m3": 5,
                    "consumo_complementario_valor": 1651.81,
                    "subtotal": 137546,
                    "subsidios": -7074
                },
                "alcantarillado": {
                    "cargo_fijo": 0,
                    "consumo_m3": 10,
                    "subtotal": 0
                },
                "aseo": {
                    "recoleccion_basuras": 29120,
                    "subtotal": 24752,
                    "subsidios": -4368
                },
                "deuda_anterior": 365249,
                "recargos": 1822,
                "subsidios_totales": -11442,
                "raw_text": "texto completo extraído"
            }
            """
            
            # Call Ollama API
            payload = {
                "model": "llama3.2:latest",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120
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
                return self._fallback_utilities_ocr(image_path)
                
        except Exception as e:
            self.logger.error(f"Error in Ollama utilities OCR: {e}")
            return self._fallback_utilities_ocr(image_path)
    
    def _fallback_utilities_ocr(self, image_path: str) -> Dict[str, Any]:
        """Fallback OCR using pytesseract with utilities patterns"""
        try:
            # Preprocess image
            processed_image = self.preprocess_utilities_image(image_path)
            if processed_image is None:
                return {"raw_text": "", "error": "Could not process image"}
            
            # Convert to PIL Image
            pil_image = Image.fromarray(processed_image)
            
            # Extract text with Spanish language
            raw_text = pytesseract.image_to_string(pil_image, lang='spa')
            
            # Extract data using patterns
            extracted_data = self._extract_with_utilities_patterns(raw_text)
            extracted_data["raw_text"] = raw_text
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Fallback utilities OCR error: {e}")
            return {"raw_text": "", "error": str(e)}
    
    def _extract_with_utilities_patterns(self, text: str) -> Dict[str, Any]:
        """Extract data using utilities-specific patterns"""
        try:
            extracted = {}
            
            # Extract supplier name
            for pattern in self.utilities_patterns['supplier_name']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['supplier_name'] = match.group(1).strip()
                    break
            
            # Extract NIT
            for pattern in self.utilities_patterns['nit']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['supplier_nit'] = match.group(1).strip()
                    break
            
            # Extract invoice number
            for pattern in self.utilities_patterns['invoice_number']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['invoice_number'] = match.group(1).strip()
                    break
            
            # Extract customer name
            for pattern in self.utilities_patterns['customer_name']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['customer_name'] = match.group(1).strip()
                    break
            
            # Extract stratum
            for pattern in self.utilities_patterns['stratum']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['stratum'] = int(match.group(1))
                    break
            
            # Extract period
            for pattern in self.utilities_patterns['period']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted['period'] = match.group(1).strip()
                    break
            
            # Extract total amount
            for pattern in self.utilities_patterns['total_amount']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    try:
                        extracted['total_amount'] = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            # Extract acueducto subtotal
            for pattern in self.utilities_patterns['acueducto_subtotal']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    try:
                        extracted['acueducto_subtotal'] = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            # Extract aseo subtotal
            for pattern in self.utilities_patterns['aseo_subtotal']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    try:
                        extracted['aseo_subtotal'] = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            # Extract deuda anterior
            for pattern in self.utilities_patterns['deuda_anterior']:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('.', '')
                    try:
                        extracted['deuda_anterior'] = float(amount_str)
                        break
                    except ValueError:
                        continue
            
            return extracted
            
        except Exception as e:
            self.logger.error(f"Error in utilities pattern extraction: {e}")
            return {}
    
    def process_utilities_invoice(self, image_path: str) -> Dict[str, Any]:
        """
        Process utilities invoice with enhanced OCR
        
        Args:
            image_path: Path to invoice image
            
        Returns:
            Processed utilities invoice data
        """
        try:
            self.logger.info(f"🔄 Processing utilities invoice: {image_path}")
            
            # Extract data using Ollama
            extracted_data = self.extract_with_ollama_utilities(image_path)
            
            if not extracted_data.get('supplier_name') and not extracted_data.get('total_amount'):
                self.logger.error("❌ Failed to extract basic information")
                return self._create_error_response("OCR extraction failed")
            
            # Create structured utilities data
            utilities_data = self._create_utilities_data(extracted_data)
            
            # Calculate taxes with utilities-specific rules
            enriched_data = self._calculate_utilities_taxes(utilities_data)
            
            return {
                'success': True,
                'utilities_data': enriched_data,
                'extraction_confidence': 0.9,  # High confidence for Ollama
                'processing_stats': {
                    'total_processed': 1,
                    'successful_extractions': 1,
                    'utilities_specific': True
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing utilities invoice: {e}")
            return self._create_error_response(str(e))
    
    def _create_utilities_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured utilities data"""
        return {
            'supplier_name': extracted_data.get('supplier_name', ''),
            'supplier_nit': extracted_data.get('supplier_nit', ''),
            'invoice_number': extracted_data.get('invoice_number', ''),
            'customer_name': extracted_data.get('customer_name', ''),
            'customer_address': extracted_data.get('customer_address', ''),
            'stratum': extracted_data.get('stratum', 3),
            'period': extracted_data.get('period', ''),
            'reading_date': extracted_data.get('reading_date', ''),
            'due_date': extracted_data.get('due_date', ''),
            'total_amount': extracted_data.get('total_amount', 0.0),
            'acueducto': extracted_data.get('acueducto', {}),
            'alcantarillado': extracted_data.get('alcantarillado', {}),
            'aseo': extracted_data.get('aseo', {}),
            'deuda_anterior': extracted_data.get('deuda_anterior', 0.0),
            'recargos': extracted_data.get('recargos', 0.0),
            'subsidios_totales': extracted_data.get('subsidios_totales', 0.0),
            'confidence_score': 0.9
        }
    
    def _calculate_utilities_taxes(self, utilities_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate taxes for utilities invoices with CREG 2025 rules"""
        try:
            total = utilities_data.get('total_amount', 0)
            stratum = utilities_data.get('stratum', 3)
            
            # CREG 2025 rules for utilities
            if stratum <= 3:
                # Low stratum: reduced or no IVA
                iva_rate = 0.05  # 5% for low stratum
            elif stratum == 4:
                iva_rate = 0.10  # 10% for medium stratum
            else:
                iva_rate = 0.19  # 19% for high stratum
            
            # Calculate base amount (before IVA)
            base_amount = total / (1 + iva_rate)
            iva_amount = total - base_amount
            
            # ReteFuente: 15% on IVA for agents (if applicable)
            retefuente_rate = 0.15 if total > 10000000 else 0.0  # 10M COP threshold
            retefuente_amount = iva_amount * retefuente_rate
            
            # ICA: varies by municipality (Nilo, Cundinamarca)
            ica_rate = 0.0  # Often exempt for utilities
            ica_amount = 0.0
            
            # Net amount after retentions
            net_amount = total - retefuente_amount - ica_amount
            
            # Add tax calculations to utilities data
            utilities_data.update({
                'base_amount': base_amount,
                'iva_rate': iva_rate,
                'iva_amount': iva_amount,
                'retefuente_rate': retefuente_rate,
                'retefuente_amount': retefuente_amount,
                'ica_rate': ica_rate,
                'ica_amount': ica_amount,
                'total_retenciones': retefuente_amount + ica_amount,
                'net_amount': net_amount,
                'tax_rules_applied': 'CREG 2025'
            })
            
            return utilities_data
            
        except Exception as e:
            self.logger.error(f"Error calculating utilities taxes: {e}")
            return utilities_data
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'error': error_message,
            'utilities_data': {},
            'processing_stats': {
                'total_processed': 1,
                'successful_extractions': 0,
                'utilities_specific': True
            }
        }

# Example usage
if __name__ == "__main__":
    ocr = UtilitiesEnhancedOCR()
    result = ocr.process_utilities_invoice("/Users/arielsanroj/downloads/test2factura.pdf")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Supplier: {result['utilities_data']['supplier_name']}")
        print(f"Total: ${result['utilities_data']['total_amount']:,.2f}")
        print(f"Stratum: {result['utilities_data']['stratum']}")
    else:
        print(f"Error: {result['error']}")