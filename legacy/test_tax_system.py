#!/usr/bin/env python3
"""
Script de Pruebas para el Sistema de Impuestos Colombianos 2025
Valida cálculos de ReteFuente, IVA e ICA
"""

import json
import sys
from datetime import datetime, timedelta
from tax_calculator import ColombianTaxCalculator, InvoiceData

def test_iva_calculations():
    """Probar cálculos de IVA"""
    print("🧪 PROBANDO CÁLCULOS DE IVA")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    test_cases = [
        {
            "name": "Alimento para mascotas (5% IVA)",
            "description": "ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG",
            "base": 203343.81,
            "expected_rate": 0.05,
            "expected_iva": 10167.19
        },
        {
            "name": "Electrónicos (19% IVA)",
            "description": "iPhone 15 Pro Max 256GB",
            "base": 5000000,
            "expected_rate": 0.19,
            "expected_iva": 950000
        },
        {
            "name": "Alimentos básicos (0% IVA)",
            "description": "Arroz blanco 5kg",
            "base": 15000,
            "expected_rate": 0.00,
            "expected_iva": 0
        },
        {
            "name": "Ropa (19% IVA)",
            "description": "Camisa de algodón",
            "base": 80000,
            "expected_rate": 0.19,
            "expected_iva": 15200
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}")
        
        # Crear datos de prueba
        invoice_data = InvoiceData(
            base_amount=case['base'],
            total_amount=case['base'] + case['expected_iva'],
            iva_amount=case['expected_iva'],
            iva_rate=case['expected_rate'],
            item_type="general",
            description=case['description'],
            vendor_nit="900123456-1",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="123456789-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2025-01-15",
            invoice_number="TEST001"
        )
        
        # Calcular impuestos
        tax_result = calculator.calculate_taxes(invoice_data)
        
        # Validar resultados
        iva_correct = abs(tax_result.iva_amount - case['expected_iva']) < 1
        rate_correct = abs(tax_result.iva_rate - case['expected_rate']) < 0.001
        
        print(f"   Base: ${case['base']:,.2f}")
        print(f"   IVA Calculado: ${tax_result.iva_amount:,.2f} ({tax_result.iva_rate*100:.1f}%)")
        print(f"   IVA Esperado: ${case['expected_iva']:,.2f} ({case['expected_rate']*100:.1f}%)")
        print(f"   ✅ Correcto: {'Sí' if iva_correct and rate_correct else 'No'}")
        
        if not (iva_correct and rate_correct):
            print(f"   ❌ Error en cálculo de IVA")

def test_retefuente_renta():
    """Probar cálculos de ReteFuente Renta"""
    print("\n🧪 PROBANDO RETEFUENTE RENTA")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    test_cases = [
        {
            "name": "Honorarios profesionales (11%)",
            "description": "Honorarios por consultoría contable",
            "base": 2000000,  # > 27 UVT
            "expected_rate": 0.11,
            "expected_rete": 220000
        },
        {
            "name": "Honorarios profesionales (10%)",
            "description": "Honorarios por asesoría legal",
            "base": 1000000,  # < 27 UVT
            "expected_rate": 0.10,
            "expected_rete": 100000
        },
        {
            "name": "Arrendamientos (3.5%)",
            "description": "Arrendamiento de oficina",
            "base": 5000000,
            "expected_rate": 0.035,
            "expected_rete": 175000
        },
        {
            "name": "Compras de bienes (2.5%)",
            "description": "Compra de mercancía",
            "base": 3000000,  # > 27 UVT
            "expected_rate": 0.025,
            "expected_rete": 75000
        },
        {
            "name": "Monto bajo (sin retención)",
            "description": "Servicio menor",
            "base": 50000,  # < 2 UVT
            "expected_rate": 0.0,
            "expected_rete": 0
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}")
        
        # Crear datos de prueba
        invoice_data = InvoiceData(
            base_amount=case['base'],
            total_amount=case['base'] * 1.19,  # Con IVA
            iva_amount=case['base'] * 0.19,
            iva_rate=0.19,
            item_type="general",
            description=case['description'],
            vendor_nit="900123456-1",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="123456789-1",
            buyer_regime="comun",
            buyer_city="bogota",
            invoice_date="2025-01-15",
            invoice_number="TEST002"
        )
        
        # Calcular impuestos
        tax_result = calculator.calculate_taxes(invoice_data)
        
        # Validar resultados
        rete_correct = abs(tax_result.retefuente_renta - case['expected_rete']) < 1
        
        print(f"   Base: ${case['base']:,.2f}")
        print(f"   ReteFuente Calculada: ${tax_result.retefuente_renta:,.2f}")
        print(f"   ReteFuente Esperada: ${case['expected_rete']:,.2f}")
        print(f"   ✅ Correcto: {'Sí' if rete_correct else 'No'}")
        
        if not rete_correct:
            print(f"   ❌ Error en cálculo de ReteFuente")

def test_retefuente_iva():
    """Probar cálculos de ReteFuente IVA"""
    print("\n🧪 PROBANDO RETEFUENTE IVA")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    test_cases = [
        {
            "name": "Monto alto con ReteIVA (15%)",
            "description": "Compra de equipos",
            "base": 6000000,  # > 10 UVT
            "iva_amount": 1140000,  # 19% IVA
            "expected_rete": 171000  # 15% del IVA
        },
        {
            "name": "Monto bajo sin ReteIVA",
            "description": "Compra menor",
            "base": 400000,  # < 10 UVT
            "iva_amount": 76000,
            "expected_rete": 0
        },
        {
            "name": "Régimen simplificado (sin ReteIVA)",
            "description": "Servicio simplificado",
            "base": 2000000,
            "iva_amount": 0,  # Sin IVA
            "expected_rete": 0
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}")
        
        # Crear datos de prueba
        invoice_data = InvoiceData(
            base_amount=case['base'],
            total_amount=case['base'] + case['iva_amount'],
            iva_amount=case['iva_amount'],
            iva_rate=case['iva_amount'] / case['base'] if case['base'] > 0 else 0,
            item_type="general",
            description=case['description'],
            vendor_nit="900123456-1",
            vendor_regime="comun",
            vendor_city="bogota",
            buyer_nit="123456789-1",
            buyer_regime="comun" if case['iva_amount'] > 0 else "simplificado",
            buyer_city="bogota",
            invoice_date="2025-01-15",
            invoice_number="TEST003"
        )
        
        # Calcular impuestos
        tax_result = calculator.calculate_taxes(invoice_data)
        
        # Validar resultados
        rete_correct = abs(tax_result.retefuente_iva - case['expected_rete']) < 1
        
        print(f"   Base: ${case['base']:,.2f}")
        print(f"   IVA: ${case['iva_amount']:,.2f}")
        print(f"   ReteIVA Calculada: ${tax_result.retefuente_iva:,.2f}")
        print(f"   ReteIVA Esperada: ${case['expected_rete']:,.2f}")
        print(f"   ✅ Correcto: {'Sí' if rete_correct else 'No'}")
        
        if not rete_correct:
            print(f"   ❌ Error en cálculo de ReteIVA")

def test_retefuente_ica():
    """Probar cálculos de ReteFuente ICA"""
    print("\n🧪 PROBANDO RETEFUENTE ICA")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    test_cases = [
        {
            "name": "Comercio en Bogotá (0.414%)",
            "description": "Venta de productos comerciales",
            "base": 3000000,  # > 5 UVT
            "vendor_city": "bogota",
            "buyer_city": "medellin",  # Diferente ciudad
            "expected_rete": 12420  # 0.414%
        },
        {
            "name": "Industria en Medellín (0.95%)",
            "description": "Servicios industriales",
            "base": 5000000,
            "vendor_city": "medellin",
            "buyer_city": "bogota",
            "expected_rete": 47500  # 0.95%
        },
        {
            "name": "Misma ciudad (sin ReteICA)",
            "description": "Servicio local",
            "base": 2000000,
            "vendor_city": "bogota",
            "buyer_city": "bogota",
            "expected_rete": 0
        },
        {
            "name": "Monto bajo (sin ReteICA)",
            "description": "Servicio menor",
            "base": 200000,  # < 5 UVT
            "vendor_city": "bogota",
            "buyer_city": "cali",
            "expected_rete": 0
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}")
        
        # Crear datos de prueba
        invoice_data = InvoiceData(
            base_amount=case['base'],
            total_amount=case['base'] * 1.19,
            iva_amount=case['base'] * 0.19,
            iva_rate=0.19,
            item_type="general",
            description=case['description'],
            vendor_nit="900123456-1",
            vendor_regime="comun",
            vendor_city=case['vendor_city'],
            buyer_nit="123456789-1",
            buyer_regime="comun",
            buyer_city=case['buyer_city'],
            invoice_date="2025-01-15",
            invoice_number="TEST004"
        )
        
        # Calcular impuestos
        tax_result = calculator.calculate_taxes(invoice_data)
        
        # Validar resultados
        rete_correct = abs(tax_result.retefuente_ica - case['expected_rete']) < 1
        
        print(f"   Base: ${case['base']:,.2f}")
        print(f"   Vendedor: {case['vendor_city']}, Comprador: {case['buyer_city']}")
        print(f"   ReteICA Calculada: ${tax_result.retefuente_ica:,.2f}")
        print(f"   ReteICA Esperada: ${case['expected_rete']:,.2f}")
        print(f"   ✅ Correcto: {'Sí' if rete_correct else 'No'}")
        
        if not rete_correct:
            print(f"   ❌ Error en cálculo de ReteICA")

def test_complete_invoice():
    """Probar factura completa con todos los impuestos"""
    print("\n🧪 PROBANDO FACTURA COMPLETA")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    # Factura de ejemplo: Royal Canin (como en el PDF real)
    invoice_data = InvoiceData(
        base_amount=203343.81,
        total_amount=213511.00,
        iva_amount=10167.19,
        iva_rate=0.05,
        item_type="pet_food",
        description="ROYAL CANIN GATO GASTROINTESTINAL FIBRE x2KG",
        vendor_nit="52147745-1",
        vendor_regime="comun",
        vendor_city="bogota",
        buyer_nit="1136886917",
        buyer_regime="comun",
        buyer_city="bogota",
        invoice_date="2025-10-10",
        invoice_number="21488"
    )
    
    # Calcular impuestos
    tax_result = calculator.calculate_taxes(invoice_data)
    
    # Mostrar resumen
    print(calculator.get_tax_summary(tax_result))
    
    # Crear payload para Alegra
    alegra_payload = calculator.create_alegra_payload(tax_result)
    print("\n📤 Payload para Alegra:")
    print(json.dumps(alegra_payload, indent=2, ensure_ascii=False))

def test_edge_cases():
    """Probar casos límite y validaciones"""
    print("\n🧪 PROBANDO CASOS LÍMITE")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    # Caso 1: Monto exactamente en el umbral
    print("\n📋 Monto en umbral de ReteFuente (2 UVT)")
    threshold_amount = 2 * calculator.uvt_2025  # 99,598
    
    invoice_data = InvoiceData(
        base_amount=threshold_amount,
        total_amount=threshold_amount * 1.19,
        iva_amount=threshold_amount * 0.19,
        iva_rate=0.19,
        item_type="general",
        description="Servicio en umbral",
        vendor_nit="900123456-1",
        vendor_regime="comun",
        vendor_city="bogota",
        buyer_nit="123456789-1",
        buyer_regime="comun",
        buyer_city="bogota",
        invoice_date="2025-01-15",
        invoice_number="TEST005"
    )
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(f"   Base: ${threshold_amount:,.2f}")
    print(f"   ReteFuente: ${tax_result.retefuente_renta:,.2f}")
    print(f"   ✅ Aplica retención: {'Sí' if tax_result.retefuente_renta > 0 else 'No'}")
    
    # Caso 2: Monto justo debajo del umbral
    print("\n📋 Monto justo debajo del umbral")
    below_threshold = threshold_amount - 1
    
    invoice_data.base_amount = below_threshold
    invoice_data.total_amount = below_threshold * 1.19
    invoice_data.iva_amount = below_threshold * 0.19
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(f"   Base: ${below_threshold:,.2f}")
    print(f"   ReteFuente: ${tax_result.retefuente_renta:,.2f}")
    print(f"   ✅ No aplica retención: {'Sí' if tax_result.retefuente_renta == 0 else 'No'}")

def main():
    """Función principal de pruebas"""
    print("🚀 SISTEMA DE PRUEBAS - IMPUESTOS COLOMBIANOS 2025")
    print("=" * 60)
    
    try:
        # Ejecutar todas las pruebas
        test_iva_calculations()
        test_retefuente_renta()
        test_retefuente_iva()
        test_retefuente_ica()
        test_complete_invoice()
        test_edge_cases()
        
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()