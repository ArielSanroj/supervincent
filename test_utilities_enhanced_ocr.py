#!/usr/bin/env python3
"""
Test script for enhanced utilities OCR system
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.ocr.utilities_enhanced_ocr import UtilitiesEnhancedOCR
import json

def test_utilities_enhanced_ocr():
    """Test the enhanced utilities OCR system"""
    print("🧪 Testing Enhanced Utilities OCR System")
    print("=" * 60)
    
    try:
        # Initialize utilities OCR processor
        utilities_ocr = UtilitiesEnhancedOCR()
        
        # Test with the problematic PDF invoice
        pdf_path = "/Users/arielsanroj/downloads/test2factura.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            return False
        
        print(f"📄 Processing: {pdf_path}")
        print("-" * 60)
        
        # Process the utilities invoice
        result = utilities_ocr.process_utilities_invoice(pdf_path)
        
        if result['success']:
            print("✅ Processing successful!")
            print()
            
            # Display results
            utilities_data = result['utilities_data']
            print("📊 EXTRACTED UTILITIES DATA:")
            print(f"  🏢 Supplier: {utilities_data.get('supplier_name', 'Unknown')}")
            print(f"  🆔 NIT: {utilities_data.get('supplier_nit', 'Unknown')}")
            print(f"  📄 Invoice Number: {utilities_data.get('invoice_number', 'Unknown')}")
            print(f"  👤 Customer: {utilities_data.get('customer_name', 'Unknown')}")
            print(f"  📍 Address: {utilities_data.get('customer_address', 'Unknown')}")
            print(f"  🏘️  Stratum: {utilities_data.get('stratum', 'Unknown')}")
            print(f"  📅 Period: {utilities_data.get('period', 'Unknown')}")
            print(f"  📖 Reading Date: {utilities_data.get('reading_date', 'Unknown')}")
            print(f"  ⏰ Due Date: {utilities_data.get('due_date', 'Unknown')}")
            print(f"  💰 Total Amount: ${utilities_data.get('total_amount', 0):,.2f}")
            print()
            
            # Display service sections
            print("🔧 SERVICE SECTIONS:")
            print("-" * 40)
            
            # Acueducto
            acueducto = utilities_data.get('acueducto', {})
            if acueducto:
                print("💧 ACUEDUCTO:")
                print(f"  Cargo Fijo: ${acueducto.get('cargo_fijo', 0):,.2f}")
                print(f"  Consumo Básico: {acueducto.get('consumo_basico_m3', 0)} m³ (${acueducto.get('consumo_basico_valor', 0):,.2f})")
                print(f"  Consumo Complementario: {acueducto.get('consumo_complementario_m3', 0)} m³ (${acueducto.get('consumo_complementario_valor', 0):,.2f})")
                print(f"  Subtotal: ${acueducto.get('subtotal', 0):,.2f}")
                print(f"  Subsidios: ${acueducto.get('subsidios', 0):,.2f}")
                print()
            
            # Alcantarillado
            alcantarillado = utilities_data.get('alcantarillado', {})
            if alcantarillado:
                print("🚰 ALCANTARILLADO:")
                print(f"  Cargo Fijo: ${alcantarillado.get('cargo_fijo', 0):,.2f}")
                print(f"  Consumo: {alcantarillado.get('consumo_m3', 0)} m³")
                print(f"  Subtotal: ${alcantarillado.get('subtotal', 0):,.2f}")
                print()
            
            # Aseo
            aseo = utilities_data.get('aseo', {})
            if aseo:
                print("🗑️  ASEO:")
                print(f"  Recolección Basuras: ${aseo.get('recoleccion_basuras', 0):,.2f}")
                print(f"  Subtotal: ${aseo.get('subtotal', 0):,.2f}")
                print(f"  Subsidios: ${aseo.get('subsidios', 0):,.2f}")
                print()
            
            # Other charges
            print("📋 OTHER CHARGES:")
            print(f"  Deuda Anterior: ${utilities_data.get('deuda_anterior', 0):,.2f}")
            print(f"  Recargos: ${utilities_data.get('recargos', 0):,.2f}")
            print(f"  Total Subsidios: ${utilities_data.get('subsidios_totales', 0):,.2f}")
            print()
            
            # Display tax calculations
            print("💰 TAX CALCULATIONS (CREG 2025):")
            print("-" * 40)
            print(f"  💵 Base Amount: ${utilities_data.get('base_amount', 0):,.2f}")
            print(f"  🏛️  IVA Rate: {utilities_data.get('iva_rate', 0)*100:.1f}% (Stratum {utilities_data.get('stratum', 3)})")
            print(f"  🏛️  IVA Amount: ${utilities_data.get('iva_amount', 0):,.2f}")
            print(f"  📊 ReteFuente Rate: {utilities_data.get('retefuente_rate', 0)*100:.1f}%")
            print(f"  📊 ReteFuente Amount: ${utilities_data.get('retefuente_amount', 0):,.2f}")
            print(f"  🏢 ICA Rate: {utilities_data.get('ica_rate', 0)*100:.1f}%")
            print(f"  🏢 ICA Amount: ${utilities_data.get('ica_amount', 0):,.2f}")
            print(f"  💸 Total Retentions: ${utilities_data.get('total_retenciones', 0):,.2f}")
            print(f"  💰 Net Amount: ${utilities_data.get('net_amount', 0):,.2f}")
            print(f"  📋 Invoice Total: ${utilities_data.get('total_amount', 0):,.2f}")
            print(f"  📜 Tax Rules: {utilities_data.get('tax_rules_applied', 'Unknown')}")
            print()
            
            # Display confidence scores
            print("🎯 CONFIDENCE SCORES:")
            print(f"  OCR Extraction: {result['extraction_confidence']:.2f}")
            print(f"  Utilities Specific: {result['processing_stats']['utilities_specific']}")
            print()
            
            # Display processing stats
            stats = result['processing_stats']
            print("📈 PROCESSING STATISTICS:")
            print(f"  Total Processed: {stats['total_processed']}")
            print(f"  Successful Extractions: {stats['successful_extractions']}")
            print(f"  Utilities Specific: {stats['utilities_specific']}")
            print()
            
            print("🎉 Utilities processing completed successfully!")
            return True
            
        else:
            print(f"❌ Processing failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Enhanced Utilities OCR System Test")
    print("=" * 60)
    
    # Test utilities OCR
    if not test_utilities_enhanced_ocr():
        print("❌ Utilities OCR test failed")
        return False
    
    print("=" * 60)
    print("✅ All tests completed successfully!")
    print("\n🎉 The enhanced utilities OCR system is ready!")
    print("\n📋 Key improvements:")
    print("  ✅ Ollama-powered extraction")
    print("  ✅ Utilities-specific patterns")
    print("  ✅ CREG 2025 tax rules")
    print("  ✅ Stratum-based calculations")
    print("  ✅ Subsidies handling")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)