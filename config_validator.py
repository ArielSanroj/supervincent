#!/usr/bin/env python3
"""
Validador de configuración y seguridad para InvoiceBot
"""

import os
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Tuple

class ConfigValidator:
    """Validador de configuración y seguridad"""
    
    def __init__(self):
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Validar toda la configuración"""
        self.logger.info("🔍 Iniciando validación de configuración...")
        
        # Validar credenciales de Alegra
        self._validate_alegra_credentials()
        
        # Validar estructura de directorios
        self._validate_directory_structure()
        
        # Validar archivos de configuración
        self._validate_config_files()
        
        # Validar permisos de archivos
        self._validate_file_permissions()
        
        # Validar configuración de logging
        self._validate_logging_config()
        
        # Validar cumplimiento NIIF
        self._validate_niif_compliance()
        
        success = len(self.errors) == 0
        
        if success:
            self.logger.info("✅ Validación completada exitosamente")
        else:
            self.logger.error(f"❌ Validación falló con {len(self.errors)} errores")
        
        return success, self.errors, self.warnings
    
    def _validate_alegra_credentials(self):
        """Validar credenciales de Alegra"""
        self.logger.info("🔐 Validando credenciales de Alegra...")
        
        email = os.getenv('ALEGRA_USER')
        token = os.getenv('ALEGRA_TOKEN')
        
        if not email:
            self.errors.append("ALEGRA_USER no está definido en .env")
        elif not self._is_valid_email(email):
            self.errors.append("ALEGRA_USER no es un email válido")
        
        if not token:
            self.errors.append("ALEGRA_TOKEN no está definido en .env")
        elif len(token) < 10:
            self.warnings.append("ALEGRA_TOKEN parece ser muy corto")
        
        # Verificar que las credenciales no estén en el código
        if self._check_credentials_in_code():
            self.errors.append("Credenciales encontradas en el código fuente")
    
    def _validate_directory_structure(self):
        """Validar estructura de directorios"""
        self.logger.info("📁 Validando estructura de directorios...")
        
        required_dirs = [
            'logs',
            'reports',
            'facturas',
            'backup'
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"📁 Directorio creado: {directory}")
                except Exception as e:
                    self.errors.append(f"No se pudo crear directorio {directory}: {e}")
    
    def _validate_config_files(self):
        """Validar archivos de configuración"""
        self.logger.info("📄 Validando archivos de configuración...")
        
        required_files = [
            '.env',
            'requirements.txt',
            'invoice_processor_enhanced.py',
            'alegra_reports.py'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                self.errors.append(f"Archivo requerido no encontrado: {file_path}")
    
    def _validate_file_permissions(self):
        """Validar permisos de archivos"""
        self.logger.info("🔒 Validando permisos de archivos...")
        
        sensitive_files = ['.env', 'logs/', 'reports/']
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                # Verificar que .env no sea legible por otros
                if file_path == '.env':
                    stat = os.stat(file_path)
                    if stat.st_mode & 0o077:
                        self.warnings.append(f"Archivo {file_path} tiene permisos demasiado abiertos")
    
    def _validate_logging_config(self):
        """Validar configuración de logging"""
        self.logger.info("📝 Validando configuración de logging...")
        
        # Verificar que el directorio de logs existe
        if not os.path.exists('logs'):
            self.errors.append("Directorio de logs no existe")
        
        # Verificar que se puede escribir en logs
        try:
            test_file = 'logs/test_write.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            self.errors.append(f"No se puede escribir en directorio de logs: {e}")
    
    def _validate_niif_compliance(self):
        """Validar cumplimiento NIIF"""
        self.logger.info("📊 Validando cumplimiento NIIF...")
        
        # Verificar que se incluyen campos requeridos para NIIF
        required_fields = [
            'accountingAccount',  # Cuenta contable
            'costCenter',         # Centro de costo
            'project'             # Proyecto
        ]
        
        # Esto es más una advertencia ya que se implementaría en el código
        self.warnings.append("Verificar que los payloads incluyan campos NIIF requeridos")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _check_credentials_in_code(self) -> bool:
        """Verificar si las credenciales están hardcodeadas en el código"""
        code_files = [
            'invoice_processor_enhanced.py',
            'alegra_reports.py',
            'invoice_watcher.py'
        ]
        
        for file_path in code_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Buscar patrones de credenciales hardcodeadas
                    if 'asanroj10@gmail.com' in content or '***REMOVED***' in content:
                        return True
                except Exception:
                    continue
        
        return False
    
    def generate_security_report(self) -> str:
        """Generar reporte de seguridad"""
        report = f"""
REPORTE DE SEGURIDAD - InvoiceBot
================================
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ERRORES ({len(self.errors)}):
"""
        
        for i, error in enumerate(self.errors, 1):
            report += f"{i}. {error}\n"
        
        report += f"\nADVERTENCIAS ({len(self.warnings)}):\n"
        for i, warning in enumerate(self.warnings, 1):
            report += f"{i}. {warning}\n"
        
        report += f"""
RECOMENDACIONES DE SEGURIDAD:
1. Mantener .env fuera del control de versiones
2. Usar permisos restrictivos en archivos sensibles
3. Rotar tokens de API regularmente
4. Monitorear logs de acceso
5. Implementar backup automático de datos
6. Validar entrada de datos antes de procesar
7. Usar HTTPS para todas las comunicaciones

ESTADO: {'✅ SEGURO' if len(self.errors) == 0 else '❌ REQUIERE ATENCIÓN'}
"""
        
        return report

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validador de configuración InvoiceBot')
    parser.add_argument('--report', action='store_true', help='Generar reporte de seguridad')
    parser.add_argument('--fix', action='store_true', help='Intentar corregir errores automáticamente')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/config_validator.log'),
            logging.StreamHandler()
        ]
    )
    
    validator = ConfigValidator()
    success, errors, warnings = validator.validate_all()
    
    if args.report:
        report = validator.generate_security_report()
        print(report)
        
        # Guardar reporte
        with open('reports/security_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        print("\n📁 Reporte guardado en: reports/security_report.txt")
    
    if not success:
        print(f"\n❌ Se encontraron {len(errors)} errores que requieren atención")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️ Se encontraron {len(warnings)} advertencias")
        for warning in warnings:
            print(f"  - {warning}")

if __name__ == "__main__":
    main()