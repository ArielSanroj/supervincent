#!/usr/bin/env python3
"""
Script de prueba para el sistema conversacional
Simula entrada del usuario para testing automatizado
"""

import subprocess
import sys
import os

def test_conversational_system():
    """Probar el sistema conversacional con entrada simulada"""
    
    # Archivo a procesar
    test_file = "/Users/arielsanroj/Downloads/testfactura2.jpg"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo de prueba no encontrado: {test_file}")
        return False
    
    print("🧪 Probando sistema conversacional...")
    print(f"📁 Archivo: {test_file}")
    
    # Simular entrada del usuario (opción 2 = VENTA)
    input_data = "2\n"
    
    try:
        # Ejecutar el procesador conversacional con entrada simulada
        result = subprocess.run([
            sys.executable, 
            "invoice_processor_conversational.py", 
            "process", 
            test_file
        ], 
        input=input_data, 
        text=True, 
        capture_output=True,
        cwd="/Users/arielsanroj/PycharmProjects/betibot"
        )
        
        print("📤 Salida del comando:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Errores:")
            print(result.stderr)
        
        # Verificar si fue exitoso
        if "¡Factura procesada exitosamente!" in result.stdout:
            print("✅ ¡Prueba exitosa!")
            return True
        else:
            print("❌ Prueba falló")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando prueba: {e}")
        return False

if __name__ == "__main__":
    success = test_conversational_system()
    sys.exit(0 if success else 1)