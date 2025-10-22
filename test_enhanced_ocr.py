#!/usr/bin/env python3
"""
Test script for enhanced OCR system
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.processors.enhanced_invoice_processor import EnhancedInvoiceProcessor
from src.utils.config import ConfigManager
import json

def test_enhanced_ocr():
    """Test the enhanced OCR system"""
    print("🧪 Testing Enhanced OCR System")
    print("=" * 50)
    
    try:
        # Initialize processor
        config = ConfigManager()
        processor = EnhancedInvoiceProcessor(config)
        
        # Test with the problematic invoice
        image_path = "/Users/arielsanroj/downloads/test3factura.jpg"
        
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return False
        
        print(f"📄 Processing: {image_path}")
        print("-" * 30)
        
        # Process the invoice
        result = processor.process_invoice(image_path)
        
        if result['success']:
            print("✅ Processing successful!")
            print()
            
            # Display results
            invoice_data = result['invoice_data']
            print("📊 EXTRACTED DATA:")
            print(f"  Supplier: {invoice_data.get('proveedor', 'Unknown')}")
            print(f"  Phone: {invoice_data.get('telefono', 'Unknown')}")
            print(f"  Bank Account: {invoice_data.get('cuenta_bancaria', 'Unknown')}")
            print(f"  Total Amount: ${invoice_data.get('total', 0):,.2f}")
            print(f"  Invoice Number: {invoice_data.get('numero_factura', 'Unknown')}")
            print(f"  Date: {invoice_data.get('fecha', 'Unknown')}")
            print()
            
            # Display items
            items = invoice_data.get('items', [])
            if items:
                print("📦 ITEMS BREAKDOWN:")
                for i, item in enumerate(items, 1):
                    print(f"  {i}. {item.get('description', 'Unknown')}: ${item.get('amount', 0):,.2f}")
                print()
            
            # Display confidence scores
            print("🎯 CONFIDENCE SCORES:")
            print(f"  OCR Extraction: {result['extraction_confidence']:.2f}")
            print(f"  Supplier Validation: {result['supplier_info']['confidence']:.2f}")
            print()
            
            # Display corrections made
            if result['supplier_info']['corrected']:
                print("🔧 CORRECTIONS MADE:")
                print(f"  Supplier Name: '{result['supplier_info']['original_name']}' → '{result['supplier_info']['corrected_name']}'")
            
            if result['amount_validation']['corrected']:
                print(f"  Amount: {result['amount_validation']['original_total']} → {result['amount_validation']['corrected_total']}")
            
            print()
            
            # Display processing stats
            stats = result['processing_stats']
            print("📈 PROCESSING STATISTICS:")
            print(f"  Total Processed: {stats['total_processed']}")
            print(f"  Successful Extractions: {stats['successful_extractions']}")
            print(f"  Supplier Validations: {stats['supplier_validations']}")
            print(f"  OCR Improvements: {stats['ocr_improvements']}")
            print()
            
            # Display tax calculations
            print("💰 TAX CALCULATIONS:")
            print(f"  Base Amount: ${invoice_data.get('base_amount', 0):,.2f}")
            print(f"  IVA (19%): ${invoice_data.get('iva_amount', 0):,.2f}")
            print(f"  ReteFuente (3.5%): ${invoice_data.get('retefuente_amount', 0):,.2f}")
            print(f"  ICA (0.414%): ${invoice_data.get('ica_amount', 0):,.2f}")
            print(f"  Total Tax: ${invoice_data.get('total_retenciones', 0):,.2f}")
            print(f"  Net Amount: ${invoice_data.get('net_amount', 0):,.2f}")
            print()
            
            return True
            
        else:
            print(f"❌ Processing failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_supplier_database():
    """Test supplier database functionality"""
    print("🗄️ Testing Supplier Database")
    print("=" * 50)
    
    try:
        from src.core.database.supplier_database import SupplierDatabase
        
        db = SupplierDatabase()
        
        # Add test suppliers
        print("Adding test suppliers...")
        db.add_supplier("Juan Hernando Bejarano", "3112062261", "3112062261")
        db.add_supplier("VEGA RODRIGUEZ MARIA CLEMENCIA", "3108824736")
        
        # Test validation
        print("Testing supplier validation...")
        is_valid, corrected_name, confidence = db.validate_supplier("JUAN HERNANDO BEJARANO", "3112062261")
        print(f"  Validation result: {is_valid}")
        print(f"  Corrected name: {corrected_name}")
        print(f"  Confidence: {confidence}")
        
        # Get all suppliers
        suppliers = db.get_all_suppliers()
        print(f"  Total suppliers in database: {len(suppliers)}")
        
        print("✅ Supplier database test completed")
        return True
        
    except Exception as e:
        print(f"❌ Supplier database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Enhanced OCR System Test")
    print("=" * 50)
    
    # Test 1: Supplier database
    if not test_supplier_database():
        print("❌ Supplier database test failed")
        return False
    
    print()
    
    # Test 2: Enhanced OCR
    if not test_enhanced_ocr():
        print("❌ Enhanced OCR test failed")
        return False
    
    print("=" * 50)
    print("✅ All tests completed successfully!")
    print("\n🎉 The enhanced OCR system is ready to use!")
    print("\n📋 To use the system:")
    print("1. Run: python test_enhanced_ocr.py")
    print("2. Process invoices with improved accuracy")
    print("3. Check supplier database for validation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)