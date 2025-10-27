#!/usr/bin/env python3
"""
Prueba simple del sistema de impuestos
"""

from tax_calculator import ColombianTaxCalculator, InvoiceData

def test_royal_canin_invoice():
    """Probar la factura de Royal Canin del PDF real"""
    print("🧪 PROBANDO FACTURA ROYAL CANIN")
    print("=" * 50)
    
    calculator = ColombianTaxCalculator()
    
    # Datos reales de la factura
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
    
    # Mostrar resultados
    print(calculator.get_tax_summary(tax_result))
    
    # Crear payload para Alegra (sin métodos)
    alegra_payload = {
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
    
    print("\n📤 Payload para Alegra:")
    import json
    print(json.dumps(alegra_payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_royal_canin_invoice()