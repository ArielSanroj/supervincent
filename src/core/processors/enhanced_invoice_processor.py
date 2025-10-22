#!/usr/bin/env python3
"""
Enhanced invoice processor with Ollama OCR and supplier validation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from ..ocr.ollama_enhanced_ocr import OllamaEnhancedOCR, ExtractedData
from ..database.supplier_database import SupplierDatabase
from ..validators.tax_validator import TaxValidator, InvoiceType
from ..validators.input_validator import InputValidator
from ...utils.config import ConfigManager

class EnhancedInvoiceProcessor:
    """
    Enhanced invoice processor with improved OCR and validation
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.ocr = OllamaEnhancedOCR()
        self.supplier_db = SupplierDatabase()
        self.tax_validator = TaxValidator(config)
        self.input_validator = InputValidator()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'supplier_validations': 0,
            'ocr_improvements': 0
        }
    
    def process_invoice(self, image_path: str) -> Dict[str, Any]:
        """
        Process invoice with enhanced OCR and validation
        
        Args:
            image_path: Path to invoice image
            
        Returns:
            Processed invoice data with enhanced accuracy
        """
        try:
            self.logger.info(f"🔄 Processing invoice: {image_path}")
            self.stats['total_processed'] += 1
            
            # Step 1: Enhanced OCR extraction
            extracted_data = self.ocr.extract_structured_data(image_path)
            
            if not extracted_data.supplier_name and not extracted_data.total_amount:
                self.logger.error("❌ Failed to extract basic information")
                return self._create_error_response("OCR extraction failed")
            
            # Step 2: Supplier validation and correction
            supplier_info = self._validate_and_correct_supplier(
                extracted_data.supplier_name,
                extracted_data.supplier_phone,
                extracted_data.supplier_bank
            )
            
            # Step 3: Amount validation and correction
            validated_amounts = self._validate_and_correct_amounts(
                extracted_data.total_amount,
                extracted_data.items
            )
            
            # Step 4: Create structured invoice data
            invoice_data = self._create_invoice_data(
                extracted_data,
                supplier_info,
                validated_amounts
            )
            
            # Step 5: Tax calculation and validation
            invoice_type = InvoiceType.PURCHASE if "compra" in invoice_data.get('tipo', '') else InvoiceType.SALE
            enriched_data = self.tax_validator.validate_and_enrich(invoice_data, invoice_type)
            
            # Step 6: Final validation
            validation_errors = self.input_validator.validate_invoice_data(enriched_data)
            
            if validation_errors:
                self.logger.warning(f"⚠️ Validation warnings: {validation_errors}")
            
            # Update statistics
            self.stats['successful_extractions'] += 1
            if supplier_info['corrected']:
                self.stats['supplier_validations'] += 1
            if validated_amounts['corrected']:
                self.stats['ocr_improvements'] += 1
            
            # Create response
            response = {
                'success': True,
                'invoice_data': enriched_data,
                'extraction_confidence': extracted_data.confidence_score,
                'supplier_info': supplier_info,
                'amount_validation': validated_amounts,
                'validation_errors': validation_errors,
                'processing_stats': self.stats.copy()
            }
            
            self.logger.info(f"✅ Invoice processed successfully: {enriched_data.get('total', 0)}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error processing invoice: {e}")
            return self._create_error_response(str(e))
    
    def _validate_and_correct_supplier(self, name: str, phone: str, bank: str) -> Dict[str, Any]:
        """Validate and correct supplier information"""
        try:
            # Validate supplier
            is_valid, corrected_name, confidence = self.supplier_db.validate_supplier(name, phone)
            
            # If not found, try to add new supplier
            if not is_valid and name:
                supplier_id = self.supplier_db.add_supplier(name, phone, bank)
                if supplier_id > 0:
                    is_valid = True
                    corrected_name = name
                    confidence = 0.6
            
            return {
                'original_name': name,
                'corrected_name': corrected_name,
                'phone': phone,
                'bank_account': bank,
                'is_valid': is_valid,
                'confidence': confidence,
                'corrected': name != corrected_name
            }
            
        except Exception as e:
            self.logger.error(f"Error validating supplier: {e}")
            return {
                'original_name': name,
                'corrected_name': name,
                'phone': phone,
                'bank_account': bank,
                'is_valid': False,
                'confidence': 0.0,
                'corrected': False
            }
    
    def _validate_and_correct_amounts(self, total: float, items: List[Dict]) -> Dict[str, Any]:
        """Validate and correct monetary amounts"""
        try:
            corrected = False
            
            # Validate total amount
            if total <= 0:
                self.logger.warning("⚠️ Invalid total amount, attempting correction")
                # Try to recalculate from items
                if items:
                    recalculated_total = sum(item.get('amount', 0) for item in items)
                    if recalculated_total > 0:
                        total = recalculated_total
                        corrected = True
                        self.logger.info(f"✅ Corrected total amount: {total}")
            
            # Validate items
            validated_items = []
            for item in items:
                if item.get('amount', 0) > 0:
                    validated_items.append(item)
            
            # If no valid items but we have a total, create a generic item
            if not validated_items and total > 0:
                validated_items = [{
                    'description': 'Servicio/Producto',
                    'amount': total,
                    'quantity': 1
                }]
                corrected = True
            
            return {
                'original_total': total,
                'corrected_total': total,
                'items': validated_items,
                'corrected': corrected
            }
            
        except Exception as e:
            self.logger.error(f"Error validating amounts: {e}")
            return {
                'original_total': total,
                'corrected_total': total,
                'items': items,
                'corrected': False
            }
    
    def _create_invoice_data(self, extracted: ExtractedData, supplier_info: Dict, amounts: Dict) -> Dict[str, Any]:
        """Create structured invoice data"""
        return {
            'fecha': extracted.date or datetime.now().strftime('%Y-%m-%d'),
            'tipo': 'compra',  # Default to purchase
            'proveedor': supplier_info['corrected_name'],
            'telefono': supplier_info['phone'],
            'cuenta_bancaria': supplier_info['bank_account'],
            'total': amounts['corrected_total'],
            'items': amounts['items'],
            'numero_factura': extracted.invoice_number,
            'confidence_score': extracted.confidence_score,
            'supplier_confidence': supplier_info['confidence']
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'error': error_message,
            'invoice_data': {},
            'processing_stats': self.stats.copy()
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_processed': self.stats['total_processed'],
            'successful_extractions': self.stats['successful_extractions'],
            'supplier_validations': self.stats['supplier_validations'],
            'ocr_improvements': self.stats['ocr_improvements'],
            'success_rate': (
                self.stats['successful_extractions'] / max(self.stats['total_processed'], 1) * 100
            )
        }
    
    def get_supplier_database_stats(self) -> Dict[str, Any]:
        """Get supplier database statistics"""
        try:
            suppliers = self.supplier_db.get_all_suppliers()
            return {
                'total_suppliers': len(suppliers),
                'recent_suppliers': len([s for s in suppliers if s.last_used > datetime.now().replace(day=1)]),
                'high_confidence_suppliers': len([s for s in suppliers if s.confidence_score > 0.8])
            }
        except Exception as e:
            self.logger.error(f"Error getting supplier stats: {e}")
            return {'error': str(e)}

# Example usage
if __name__ == "__main__":
    from src.utils.config import ConfigManager
    
    config = ConfigManager()
    processor = EnhancedInvoiceProcessor(config)
    
    result = processor.process_invoice("/Users/arielsanroj/downloads/test3factura.jpg")
    
    if result['success']:
        print("✅ Processing successful!")
        print(f"Supplier: {result['invoice_data'].get('proveedor', 'Unknown')}")
        print(f"Total: ${result['invoice_data'].get('total', 0):,.2f}")
        print(f"Confidence: {result['extraction_confidence']:.2f}")
    else:
        print(f"❌ Processing failed: {result['error']}")