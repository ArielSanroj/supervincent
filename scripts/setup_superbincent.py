#!/usr/bin/env python3
"""
Script de Configuración para SuperBincent
Configura el sistema integrado de impuestos y análisis financiero
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def create_directories():
    """Crear directorios necesarios"""
    print("📁 Creando directorios del sistema...")
    
    directories = [
        "~/Downloads/superbincent_reports",
        "~/Downloads/superbincent_backups",
        "~/Downloads/superbincent_logs"
    ]
    
    for directory in directories:
        dir_path = os.path.expanduser(directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"   ✅ {directory}")
    
    print("✅ Directorios creados exitosamente")

def create_config_files():
    """Crear archivos de configuración"""
    print("\n⚙️ Creando archivos de configuración...")
    
    # Configuración principal
    main_config = {
        "system": "SuperBincent",
        "version": "1.0.0",
        "created": datetime.now().isoformat(),
        "directories": {
            "downloads": "~/Downloads",
            "reports": "~/Downloads/superbincent_reports",
            "backups": "~/Downloads/superbincent_backups",
            "logs": "~/Downloads/superbincent_logs"
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "your_email@gmail.com",
            "sender_password": "your_app_password",
            "recipient_email": "recipient@example.com"
        },
        "financial": {
            "budget_ingresos_mensual": 100000000,
            "budget_gastos_mensual": 125000000,
            "uvt_2025": 49799
        },
        "taxes": {
            "country": "Colombia",
            "currency": "COP",
            "compliance_threshold": 0.01
        }
    }
    
    config_path = os.path.expanduser("~/Downloads/superbincent_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(main_config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Configuración principal: {config_path}")
    
    # Configuración de email (plantilla)
    email_template = """# Configuración de Email para SuperBincent

## Gmail Setup
1. Habilitar autenticación de 2 factores en Gmail
2. Ir a Configuración de cuenta de Google > Seguridad > Contraseñas de aplicaciones
3. Generar una nueva contraseña para "Correo"
4. Usar esa contraseña (16 caracteres) en la configuración

## Configuración
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'tu_email@gmail.com',  # Tu email de Gmail
    'sender_password': 'tu_contraseña_de_aplicacion',  # Contraseña de aplicación (16 caracteres)
    'recipient_email': 'destinatario@ejemplo.com'  # Email donde enviar reportes
}

## Archivos a actualizar
- financial_analysis.py (línea ~50)
- superbincent_integrated.py (si se usa envío de email)
"""
    
    email_config_path = os.path.expanduser("~/Downloads/email_setup_instructions.txt")
    with open(email_config_path, 'w', encoding='utf-8') as f:
        f.write(email_template)
    
    print(f"   ✅ Instrucciones de email: {email_config_path}")
    
    print("✅ Archivos de configuración creados")

def create_sample_files():
    """Crear archivos de ejemplo"""
    print("\n📄 Creando archivos de ejemplo...")
    
    # Script de prueba
    test_script = """#!/usr/bin/env python3
# Script de prueba para SuperBincent

from superbincent_integrated import SuperBincentIntegrated

def test_system():
    print("🧪 Probando SuperBincent...")
    
    system = SuperBincentIntegrated()
    
    # Mostrar estado
    status = system.get_system_status()
    print(f"Estado: {status}")
    
    # Ejecutar análisis financiero
    result = system.run_financial_analysis_only()
    print(f"Análisis: {result}")

if __name__ == "__main__":
    test_system()
"""
    
    test_path = os.path.expanduser("~/Downloads/test_superbincent.py")
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"   ✅ Script de prueba: {test_path}")
    
    # README del sistema
    readme_content = """# SuperBincent - Sistema Integrado de Impuestos y Análisis Financiero

## 🚀 Descripción
SuperBincent es un sistema integrado que combina:
- Procesamiento automático de facturas (PDF, JPG, Excel)
- Cálculo de impuestos colombianos 2025 (IVA, ReteFuente, ICA)
- Análisis financiero automático con KPIs
- Generación de reportes (Excel, Word, PNG)
- Envío automático por email

## 📁 Estructura de Archivos
```
superbincent/
├── tax_calculator.py              # Motor de cálculos fiscales
├── financial_analysis.py          # Analizador financiero
├── superbincent_integrated.py     # Sistema integrado
├── demo_superbincent_integrated.py # Demostración
├── config/
│   └── tax_rules_CO_2025.json     # Reglas fiscales 2025
└── reports/                       # Reportes generados
```

## 🛠️ Instalación
1. Instalar dependencias:
   ```bash
   pip install pandas openpyxl pdfplumber matplotlib python-docx
   ```

2. Configurar email (opcional):
   - Editar financial_analysis.py
   - Actualizar EMAIL_CONFIG con credenciales Gmail

3. Ejecutar demostración:
   ```bash
   python demo_superbincent_integrated.py
   ```

## 📊 Uso Básico
```python
from superbincent_integrated import SuperBincentIntegrated

# Crear sistema
system = SuperBincentIntegrated()

# Procesar factura
result = system.process_invoice_with_financial_analysis("factura.pdf")

# Análisis financiero
financial = system.run_financial_analysis_only()
```

## 📋 Requisitos
- Python 3.7+
- Archivo financiero: "INFORME DE * APRU- 2025 .xls" en Downloads
- Gmail con autenticación 2FA (para envío de email)

## 🎯 Características
- ✅ Normativa DIAN 2025 actualizada
- ✅ UVT 2025: $49,799
- ✅ Cálculo automático de impuestos
- ✅ KPIs financieros automáticos
- ✅ Reportes en múltiples formatos
- ✅ Compliance fiscal automático
- ✅ Integración con Alegra API
"""
    
    readme_path = os.path.expanduser("~/Downloads/README_SUPERBINCENT.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"   ✅ README: {readme_path}")
    
    print("✅ Archivos de ejemplo creados")

def check_dependencies():
    """Verificar dependencias"""
    print("\n🔍 Verificando dependencias...")
    
    required_packages = [
        'pandas',
        'openpyxl', 
        'pdfplumber',
        'matplotlib',
        'docx',
        'numpy',
        'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'docx':
                from docx import Document
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - FALTANTE")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Paquetes faltantes: {', '.join(missing_packages)}")
        print("Instalar con: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ Todas las dependencias están instaladas")
        return True

def create_launcher_script():
    """Crear script de lanzamiento"""
    print("\n🚀 Creando script de lanzamiento...")
    
    launcher_content = """#!/usr/bin/env python3
# SuperBincent Launcher
# Script para ejecutar SuperBincent fácilmente

import sys
import os
from pathlib import Path

def main():
    print("🚀 SuperBincent - Sistema Integrado")
    print("=" * 50)
    
    # Agregar directorio actual al path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        from superbincent_integrated import SuperBincentIntegrated
        
        # Crear sistema
        system = SuperBincentIntegrated()
        
        # Mostrar menú
        while True:
            print("\\n📋 MENÚ PRINCIPAL:")
            print("1. 📊 Análisis financiero completo")
            print("2. 📄 Procesar factura específica")
            print("3. 📈 Estado del sistema")
            print("4. 🧪 Ejecutar demostración")
            print("5. ❌ Salir")
            
            choice = input("\\nSelecciona una opción (1-5): ").strip()
            
            if choice == "1":
                print("\\n📊 Ejecutando análisis financiero...")
                result = system.run_financial_analysis_only()
                if result.get('status') == 'success':
                    print("✅ Análisis completado exitosamente")
                else:
                    print(f"❌ Error: {result.get('error', 'Desconocido')}")
            
            elif choice == "2":
                file_path = input("\\n📄 Ingresa la ruta del archivo: ").strip()
                if os.path.exists(file_path):
                    print(f"\\nProcesando: {file_path}")
                    result = system.process_invoice_with_financial_analysis(file_path)
                    if result.get('status') == 'success':
                        print("✅ Factura procesada exitosamente")
                    else:
                        print(f"❌ Error: {result.get('message', 'Desconocido')}")
                else:
                    print("❌ Archivo no encontrado")
            
            elif choice == "3":
                print("\\n📈 Estado del sistema:")
                status = system.get_system_status()
                print(f"Sistema: {status.get('system', 'N/A')}")
                print(f"Versión: {status.get('version', 'N/A')}")
                print(f"Archivo financiero: {'✅' if status.get('financial_files', {}).get('latest_detected') else '❌'}")
                print(f"Reportes: {status.get('reports', {}).get('files_count', 0)} archivos")
            
            elif choice == "4":
                print("\\n🧪 Ejecutando demostración...")
                from demo_superbincent_integrated import demo_integrated_system
                demo_integrated_system()
            
            elif choice == "5":
                print("\\n👋 ¡Hasta luego!")
                break
            
            else:
                print("\\n❌ Opción inválida")
    
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("Asegúrate de que todos los archivos estén en el mismo directorio")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
"""
    
    launcher_path = os.path.expanduser("~/Downloads/superbincent_launcher.py")
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    # Hacer ejecutable
    os.chmod(launcher_path, 0o755)
    
    print(f"   ✅ Launcher: {launcher_path}")
    print("✅ Script de lanzamiento creado")

def main():
    """Función principal de configuración"""
    print("🚀 CONFIGURACIÓN DE SUPERBINCENT")
    print("=" * 50)
    print("Sistema Integrado de Impuestos y Análisis Financiero")
    print("Versión: 1.0.0")
    print("Fecha:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n⚠️ Instala las dependencias faltantes antes de continuar")
        return
    
    # Crear directorios
    create_directories()
    
    # Crear archivos de configuración
    create_config_files()
    
    # Crear archivos de ejemplo
    create_sample_files()
    
    # Crear script de lanzamiento
    create_launcher_script()
    
    # Resumen final
    print("\n" + "="*50)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("="*50)
    
    print("\n📁 ARCHIVOS CREADOS:")
    print("   📄 superbincent_config.json - Configuración principal")
    print("   📄 email_setup_instructions.txt - Instrucciones de email")
    print("   📄 test_superbincent.py - Script de prueba")
    print("   📄 README_SUPERBINCENT.md - Documentación")
    print("   🚀 superbincent_launcher.py - Lanzador del sistema")
    
    print("\n📁 DIRECTORIOS CREADOS:")
    print("   📊 ~/Downloads/superbincent_reports - Reportes generados")
    print("   💾 ~/Downloads/superbincent_backups - Respaldos")
    print("   📝 ~/Downloads/superbincent_logs - Logs del sistema")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("   1. Configurar email en financial_analysis.py")
    print("   2. Ejecutar: python superbincent_launcher.py")
    print("   3. O ejecutar: python demo_superbincent_integrated.py")
    
    print("\n💡 ARCHIVOS IMPORTANTES:")
    print("   📊 Archivo financiero: 'INFORME DE * APRU- 2025 .xls' en Downloads")
    print("   📄 Facturas de prueba: testfactura.pdf, testfactura2.jpg")
    
    print("\n🏆 ¡SuperBincent configurado exitosamente! 🏆")

if __name__ == "__main__":
    main()