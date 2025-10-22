#!/usr/bin/env python3
"""
Enhanced OCR system for PDF files using Ollama
"""

import logging
import fitz  # PyMuPDF
import tempfile
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import cv2
import numpy as np

from .ollama_enhanced_ocr import OllamaEnhancedOCR, ExtractedData

class PDFEnhancedOCR:
    """
    Enhanced OCR system specifically for PDF files
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.logger = logging.getLogger(__name__)
        self.image_ocr = OllamaEnhancedOCR(ollama_base_url)
        
    def pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[np.ndarray]:
        """Convert PDF pages to images"""
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                # Get page
                page = doc.load_page(page_num)
                
                # Convert to image with high DPI
                mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to numpy array
                img_data = pix.tobytes("ppm")
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                
                if img is not None:
                    images.append(img)
                    self.logger.info(f"Converted page {page_num + 1} to image")
            
            doc.close()
            return images
            
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {e}")
            return []
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text directly from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n"  # Add page break
            
            doc.close()
            return text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def process_pdf_invoice(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF invoice with enhanced OCR
        
        Args:
            pdf_path: Path to PDF invoice
            
        Returns:
            Processed invoice data
        """
        try:
            self.logger.info(f"🔄 Processing PDF invoice: {pdf_path}")
            
            # Step 1: Try direct text extraction first
            pdf_text = self.extract_text_from_pdf(pdf_path)
            
            if pdf_text and len(pdf_text.strip()) > 50:
                self.logger.info("📄 Using direct PDF text extraction")
                return self._process_text_data(pdf_text, pdf_path)
            
            # Step 2: Convert PDF to images and use OCR
            self.logger.info("🖼️ Converting PDF to images for OCR")
            images = self.pdf_to_images(pdf_path)
            
            if not images:
                return self._create_error_response("Could not convert PDF to images")
            
            # Process each page
            all_extracted_data = []
            for i, image in enumerate(images):
                self.logger.info(f"Processing page {i + 1}/{len(images)}")
                
                # Save image temporarily
                temp_path = f"/tmp/pdf_page_{i}.png"
                cv2.imwrite(temp_path, image)
                
                # Extract data using image OCR
                extracted_data = self.image_ocr.extract_structured_data(temp_path)
                all_extracted_data.append(extracted_data)
                
                # Clean up temp file
                os.unlink(temp_path)
            
            # Combine results from all pages
            return self._combine_extracted_data(all_extracted_data, pdf_path)
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            return self._create_error_response(str(e))
    
    def _process_text_data(self, text: str, pdf_path: str) -> Dict[str, Any]:
        """Process extracted text data"""
        try:
            # Use pattern matching on the text
            extracted_data = self.image_ocr._extract_with_patterns(text)
            
            # Create invoice data
            invoice_data = {
                'fecha': extracted_data.date or '2025-10-22',
                'tipo': 'compra',
                'proveedor': extracted_data.supplier_name,
                'telefono': extracted_data.supplier_phone,
                'cuenta_bancaria': extracted_data.supplier_bank,
                'total': extracted_data.total_amount,
                'items': extracted_data.items,
                'numero_factura': extracted_data.invoice_number,
                'confidence_score': extracted_data.confidence_score,
                'source': 'pdf_text_extraction'
            }
            
            return {
                'success': True,
                'invoice_data': invoice_data,
                'extraction_confidence': extracted_data.confidence_score,
                'supplier_info': {
                    'original_name': extracted_data.supplier_name,
                    'corrected_name': extracted_data.supplier_name,
                    'phone': extracted_data.supplier_phone,
                    'bank_account': extracted_data.supplier_bank,
                    'is_valid': True,
                    'confidence': 0.8,
                    'corrected': False
                },
                'amount_validation': {
                    'original_total': extracted_data.total_amount,
                    'corrected_total': extracted_data.total_amount,
                    'items': extracted_data.items,
                    'corrected': False
                },
                'processing_stats': {
                    'total_processed': 1,
                    'successful_extractions': 1,
                    'supplier_validations': 0,
                    'ocr_improvements': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing text data: {e}")
            return self._create_error_response(str(e))
    
    def _combine_extracted_data(self, all_data: List[ExtractedData], pdf_path: str) -> Dict[str, Any]:
        """Combine extracted data from multiple pages"""
        try:
            # Find the best extraction (highest confidence)
            best_data = max(all_data, key=lambda x: x.confidence_score)
            
            # Create invoice data
            invoice_data = {
                'fecha': best_data.date or '2025-10-22',
                'tipo': 'compra',
                'proveedor': best_data.supplier_name,
                'telefono': best_data.supplier_phone,
                'cuenta_bancaria': best_data.supplier_bank,
                'total': best_data.total_amount,
                'items': best_data.items,
                'numero_factura': best_data.invoice_number,
                'confidence_score': best_data.confidence_score,
                'source': 'pdf_image_ocr'
            }
            
            return {
                'success': True,
                'invoice_data': invoice_data,
                'extraction_confidence': best_data.confidence_score,
                'supplier_info': {
                    'original_name': best_data.supplier_name,
                    'corrected_name': best_data.supplier_name,
                    'phone': best_data.supplier_phone,
                    'bank_account': best_data.supplier_bank,
                    'is_valid': True,
                    'confidence': 0.8,
                    'corrected': False
                },
                'amount_validation': {
                    'original_total': best_data.total_amount,
                    'corrected_total': best_data.total_amount,
                    'items': best_data.items,
                    'corrected': False
                },
                'processing_stats': {
                    'total_processed': 1,
                    'successful_extractions': 1,
                    'supplier_validations': 0,
                    'ocr_improvements': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error combining extracted data: {e}")
            return self._create_error_response(str(e))
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'error': error_message,
            'invoice_data': {},
            'processing_stats': {
                'total_processed': 1,
                'successful_extractions': 0,
                'supplier_validations': 0,
                'ocr_improvements': 0
            }
        }

# Example usage
if __name__ == "__main__":
    ocr = PDFEnhancedOCR()
    result = ocr.process_pdf_invoice("/Users/arielsanroj/downloads/test2factura.pdf")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Supplier: {result['invoice_data']['proveedor']}")
        print(f"Total: ${result['invoice_data']['total']:,.2f}")
    else:
        print(f"Error: {result['error']}")