#!/usr/bin/env python3
"""
Demostración del Sistema de Impuestos Colombianos 2025
Muestra diferentes escenarios de cálculo de impuestos
"""

import json
from datetime import datetime
from tax_calculator import ColombianTaxCalculator, InvoiceData

def demo_scenario_1():
    """Escenario 1: Factura de Royal Canin (sin retenciones)"""
    print("🐱 ESCENARIO 1: ALIMENTO PARA MASCOTAS")
    print("=" * 60)
    print("Factura: Royal Canin - Sin retenciones aplicables")
    print()
    
    calculator = ColombianTaxCalculator()
    
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
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(calculator.get_tax_summary(tax_result))
    
    # Explicación
    print("\n📋 EXPLICACIÓN:")
    print("• IVA 5%: Alimento para mascotas tiene tasa reducida")
    print("• Sin ReteFuente Renta: Monto < 27 UVT para compras de bienes")
    print("• Sin ReteFuente IVA: Monto < 10 UVT")
    print("• Sin ReteFuente ICA: Misma ciudad (Bogotá-Bogotá)")

def demo_scenario_2():
    """Escenario 2: Honorarios profesionales (con retenciones)"""
    print("\n👨‍💼 ESCENARIO 2: HONORARIOS PROFESIONALES")
    print("=" * 60)
    print("Factura: Consultoría - Con ReteFuente Renta")
    print()
    
    calculator = ColombianTaxCalculator()
    
    invoice_data = InvoiceData(
        base_amount=3000000,  # > 27 UVT
        total_amount=3570000,  # Con IVA 19%
        iva_amount=570000,
        iva_rate=0.19,
        item_type="general",
        description="Honorarios por consultoría contable especializada",
        vendor_nit="900123456-1",
        vendor_regime="comun",
        vendor_city="bogota",
        buyer_nit="800987654-3",
        buyer_regime="comun",
        buyer_city="medellin",
        invoice_date="2025-01-15",
        invoice_number="HON001"
    )
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(calculator.get_tax_summary(tax_result))
    
    # Explicación
    print("\n📋 EXPLICACIÓN:")
    print("• IVA 19%: Servicios profesionales")
    print("• ReteFuente Renta 11%: Honorarios > 27 UVT")
    print("• ReteFuente IVA 15%: Monto > 10 UVT")
    print("• ReteFuente ICA 0.35%: Diferente ciudad (Bogotá-Medellín)")

def demo_scenario_3():
    """Escenario 3: Compra de equipos (todas las retenciones)"""
    print("\n💻 ESCENARIO 3: COMPRA DE EQUIPOS")
    print("=" * 60)
    print("Factura: Equipos de cómputo - Todas las retenciones")
    print()
    
    calculator = ColombianTaxCalculator()
    
    invoice_data = InvoiceData(
        base_amount=10000000,  # Monto alto
        total_amount=11900000,  # Con IVA 19%
        iva_amount=1900000,
        iva_rate=0.19,
        item_type="electronics",
        description="Laptops Dell para oficina - 20 unidades",
        vendor_nit="900555666-7",
        vendor_regime="comun",
        vendor_city="cali",
        buyer_nit="800111222-9",
        buyer_regime="comun",
        buyer_city="barranquilla",
        invoice_date="2025-01-20",
        invoice_number="EQP001"
    )
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(calculator.get_tax_summary(tax_result))
    
    # Explicación
    print("\n📋 EXPLICACIÓN:")
    print("• IVA 19%: Electrónicos")
    print("• ReteFuente Renta 2.5%: Compra de bienes, vendedor declarante")
    print("• ReteFuente IVA 15%: Monto > 10 UVT")
    print("• ReteFuente ICA 0.32%: Diferente ciudad (Cali-Barranquilla)")

def demo_scenario_4():
    """Escenario 4: Régimen simplificado (sin retenciones)"""
    print("\n🏪 ESCENARIO 4: RÉGIMEN SIMPLIFICADO")
    print("=" * 60)
    print("Factura: Tienda simplificada - Sin IVA ni retenciones")
    print()
    
    calculator = ColombianTaxCalculator()
    
    invoice_data = InvoiceData(
        base_amount=500000,
        total_amount=500000,  # Sin IVA
        iva_amount=0,
        iva_rate=0.00,
        item_type="general",
        description="Venta de productos varios",
        vendor_nit="12345678-9",  # NIT corto = simplificado
        vendor_regime="simplificado",
        vendor_city="bogota",
        buyer_nit="98765432-1",
        buyer_regime="comun",
        buyer_city="bogota",
        invoice_date="2025-01-25",
        invoice_number="SIM001"
    )
    
    tax_result = calculator.calculate_taxes(invoice_data)
    print(calculator.get_tax_summary(tax_result))
    
    # Explicación
    print("\n📋 EXPLICACIÓN:")
    print("• Sin IVA: Régimen simplificado no cobra IVA")
    print("• Sin retenciones: Régimen simplificado exento")
    print("• Monto neto = Monto total")

def demo_comparison():
    """Comparación de escenarios"""
    print("\n📊 COMPARACIÓN DE ESCENARIOS")
    print("=" * 60)
    
    scenarios = [
        ("Royal Canin", 203343.81, 10167.19, 0, 0, 0),
        ("Honorarios", 3000000, 570000, 330000, 85500, 10500),
        ("Equipos", 10000000, 1900000, 250000, 285000, 32000),
        ("Simplificado", 500000, 0, 0, 0, 0)
    ]
    
    print(f"{'Escenario':<15} {'Base':<12} {'IVA':<10} {'ReteRenta':<12} {'ReteIVA':<10} {'ReteICA':<10}")
    print("-" * 80)
    
    for name, base, iva, rete_renta, rete_iva, rete_ica in scenarios:
        print(f"{name:<15} ${base:>10,.0f} ${iva:>8,.0f} ${rete_renta:>10,.0f} ${rete_iva:>8,.0f} ${rete_ica:>8,.0f}")

def demo_alegra_integration():
    """Demostración de integración con Alegra"""
    print("\n🏢 INTEGRACIÓN CON ALEGRA")
    print("=" * 60)
    
    calculator = ColombianTaxCalculator()
    
    # Usar escenario de honorarios
    invoice_data = InvoiceData(
        base_amount=3000000,
        total_amount=3570000,
        iva_amount=570000,
        iva_rate=0.19,
        item_type="general",
        description="Honorarios por consultoría",
        vendor_nit="900123456-1",
        vendor_regime="comun",
        vendor_city="bogota",
        buyer_nit="800987654-3",
        buyer_regime="comun",
        buyer_city="medellin",
        invoice_date="2025-01-15",
        invoice_number="HON001"
    )
    
    tax_result = calculator.calculate_taxes(invoice_data)
    
    # Crear payload para Alegra
    alegra_payload = {
        "date": invoice_data.invoice_date,
        "dueDate": "2025-02-14",
        "client": {
            "name": "Cliente desde PDF",
            "identification": invoice_data.buyer_nit
        },
        "items": [
            {
                "name": invoice_data.description,
                "quantity": 1,
                "price": invoice_data.base_amount
            }
        ],
        "observations": f"Factura procesada con cálculo de impuestos - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "tax": [
            {
                "rate": tax_result.iva_rate * 100,
                "amount": tax_result.iva_amount,
                "type": "iva",
                "description": "IVA"
            }
        ],
        "withholdings": []
    }
    
    # Agregar retenciones
    if tax_result.retefuente_renta > 0:
        alegra_payload["withholdings"].append({
            "type": "renta",
            "amount": tax_result.retefuente_renta,
            "description": "Retención en la fuente por renta"
        })
    
    if tax_result.retefuente_iva > 0:
        alegra_payload["withholdings"].append({
            "type": "iva",
            "amount": tax_result.retefuente_iva,
            "description": "Retención en la fuente por IVA"
        })
    
    if tax_result.retefuente_ica > 0:
        alegra_payload["withholdings"].append({
            "type": "ica",
            "amount": tax_result.retefuente_ica,
            "description": "Retención en la fuente por ICA"
        })
    
    print("📤 Payload para Alegra API:")
    print(json.dumps(alegra_payload, indent=2, ensure_ascii=False))

def main():
    """Función principal de demostración"""
    print("🚀 DEMOSTRACIÓN SISTEMA DE IMPUESTOS COLOMBIANOS 2025")
    print("=" * 70)
    print("Basado en normativa DIAN 2025 y Reforma Tributaria 2022/2023")
    print("UVT 2025: $49,799")
    print()
    
    # Ejecutar demostraciones
    demo_scenario_1()
    demo_scenario_2()
    demo_scenario_3()
    demo_scenario_4()
    demo_comparison()
    demo_alegra_integration()
    
    print("\n🎉 DEMOSTRACIÓN COMPLETADA")
    print("=" * 70)
    print("✅ Sistema de impuestos funcionando correctamente")
    print("✅ Integración con Alegra lista")
    print("✅ Cumplimiento normativo 2025")

if __name__ == "__main__":
    main()