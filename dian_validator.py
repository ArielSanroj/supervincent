#!/usr/bin/env python3
"""
Validador DIAN para facturas electrónicas en Colombia
"""

import requests
import json
import logging
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

@dataclass
class DIANValidationResult:
    """Resultado de validación DIAN"""
    is_valid: bool
    cufe: Optional[str]
    qr_code: Optional[str]
    errors: List[str]
    warnings: List[str]
    dian_response: Dict[str, Any]

class DIANValidator:
    """Validador de facturas electrónicas DIAN"""
    
    def __init__(self, test_mode: bool = True):
        self.test_mode = test_mode
        self.logger = logging.getLogger(__name__)
        
        # URLs de DIAN (modo test y producción)
        if test_mode:
            self.base_url = "https://catalogo-vpfe.dian.gov.co"
            self.api_key = "test_api_key"  # En producción, usar API key real
        else:
            self.base_url = "https://catalogo-vpfe.dian.gov.co"
            self.api_key = None  # Configurar API key real
        
        # Configuración de headers
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def validate_electronic_invoice(self, invoice_data: Dict) -> DIANValidationResult:
        """Validar factura electrónica contra DIAN"""
        try:
            self.logger.info("🔍 Iniciando validación DIAN...")
            
            # Generar CUFE
            cufe = self._generate_cufe(invoice_data)
            
            # Validar estructura XML
            xml_validation = self._validate_xml_structure(invoice_data)
            
            # Validar campos obligatorios
            field_validation = self._validate_required_fields(invoice_data)
            
            # Validar formato de NIT
            nit_validation = self._validate_nit_format(invoice_data)
            
            # Validar cálculos fiscales
            tax_validation = self._validate_tax_calculations(invoice_data)
            
            # Combinar resultados
            all_errors = []
            all_warnings = []
            
            all_errors.extend(xml_validation['errors'])
            all_warnings.extend(xml_validation['warnings'])
            
            all_errors.extend(field_validation['errors'])
            all_warnings.extend(field_validation['warnings'])
            
            all_errors.extend(nit_validation['errors'])
            all_warnings.extend(nit_validation['warnings'])
            
            all_errors.extend(tax_validation['errors'])
            all_warnings.extend(tax_validation['warnings'])
            
            # Generar QR Code
            qr_code = self._generate_qr_code(invoice_data, cufe)
            
            # Simular respuesta DIAN (en modo test)
            dian_response = self._simulate_dian_response(invoice_data, cufe)
            
            is_valid = len(all_errors) == 0
            
            return DIANValidationResult(
                is_valid=is_valid,
                cufe=cufe,
                qr_code=qr_code,
                errors=all_errors,
                warnings=all_warnings,
                dian_response=dian_response
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación DIAN: {e}")
            return DIANValidationResult(
                is_valid=False,
                cufe=None,
                qr_code=None,
                errors=[f"Error interno: {str(e)}"],
                warnings=[],
                dian_response={}
            )
    
    def _generate_cufe(self, invoice_data: Dict) -> str:
        """Generar CUFE (Código Único de Facturación Electrónica)"""
        try:
            # Datos para generar CUFE
            nit_emisor = invoice_data.get('nit_emisor', '')
            nit_receptor = invoice_data.get('nit_receptor', '')
            fecha_emision = invoice_data.get('fecha', '')
            numero_factura = invoice_data.get('numero_factura', '')
            total = str(invoice_data.get('total', 0))
            iva = str(invoice_data.get('iva', 0))
            
            # Crear string para hash
            cufe_string = f"{nit_emisor}|{nit_receptor}|{fecha_emision}|{numero_factura}|{total}|{iva}"
            
            # Generar hash SHA-384
            cufe_hash = hashlib.sha384(cufe_string.encode('utf-8')).hexdigest()
            
            return cufe_hash.upper()
            
        except Exception as e:
            self.logger.error(f"❌ Error generando CUFE: {e}")
            return ""
    
    def _validate_xml_structure(self, invoice_data: Dict) -> Dict[str, List[str]]:
        """Validar estructura XML de la factura"""
        errors = []
        warnings = []
        
        try:
            # En una implementación real, aquí se validaría el XML contra el XSD de DIAN
            # Por ahora, validar campos básicos
            
            required_fields = [
                'nit_emisor', 'nit_receptor', 'fecha', 'numero_factura', 'total'
            ]
            
            for field in required_fields:
                if not invoice_data.get(field):
                    errors.append(f"Campo obligatorio faltante: {field}")
            
            # Validar formato de fecha
            fecha = invoice_data.get('fecha', '')
            if fecha:
                try:
                    datetime.strptime(fecha, '%Y-%m-%d')
                except ValueError:
                    errors.append("Formato de fecha inválido. Debe ser YYYY-MM-DD")
            
            # Validar total
            total = invoice_data.get('total', 0)
            if total <= 0:
                errors.append("El total debe ser mayor a cero")
            
        except Exception as e:
            errors.append(f"Error validando estructura XML: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_required_fields(self, invoice_data: Dict) -> Dict[str, List[str]]:
        """Validar campos obligatorios DIAN"""
        errors = []
        warnings = []
        
        # Campos obligatorios según DIAN
        required_fields = {
            'nit_emisor': 'NIT del emisor',
            'nit_receptor': 'NIT del receptor',
            'fecha': 'Fecha de emisión',
            'numero_factura': 'Número de factura',
            'total': 'Total de la factura',
            'iva': 'IVA',
            'razon_social_emisor': 'Razón social del emisor',
            'razon_social_receptor': 'Razón social del receptor'
        }
        
        for field, description in required_fields.items():
            if not invoice_data.get(field):
                errors.append(f"Campo obligatorio DIAN faltante: {description}")
        
        # Validar longitud de campos
        if invoice_data.get('numero_factura'):
            if len(str(invoice_data['numero_factura'])) > 20:
                warnings.append("Número de factura muy largo (máximo 20 caracteres)")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_nit_format(self, invoice_data: Dict) -> Dict[str, List[str]]:
        """Validar formato de NIT"""
        errors = []
        warnings = []
        
        try:
            from tax_validator import TaxValidator
            
            validator = TaxValidator('CO')
            
            # Validar NIT del emisor
            nit_emisor = invoice_data.get('nit_emisor', '')
            if nit_emisor and not validator.validate_nit_format(nit_emisor):
                errors.append("Formato de NIT del emisor inválido")
            
            # Validar NIT del receptor
            nit_receptor = invoice_data.get('nit_receptor', '')
            if nit_receptor and not validator.validate_nit_format(nit_receptor):
                errors.append("Formato de NIT del receptor inválido")
            
        except Exception as e:
            errors.append(f"Error validando formato de NIT: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_tax_calculations(self, invoice_data: Dict) -> Dict[str, List[str]]:
        """Validar cálculos fiscales DIAN"""
        errors = []
        warnings = []
        
        try:
            from tax_validator import TaxValidator
            
            validator = TaxValidator('CO')
            validation_result = validator.validate_invoice_taxes(invoice_data)
            
            errors.extend(validation_result.errors)
            warnings.extend(validation_result.warnings)
            
        except Exception as e:
            errors.append(f"Error validando cálculos fiscales: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _generate_qr_code(self, invoice_data: Dict, cufe: str) -> str:
        """Generar código QR para la factura"""
        try:
            # Datos para QR (simplificado)
            qr_data = {
                'cufe': cufe,
                'nit_emisor': invoice_data.get('nit_emisor', ''),
                'nit_receptor': invoice_data.get('nit_receptor', ''),
                'fecha': invoice_data.get('fecha', ''),
                'total': invoice_data.get('total', 0),
                'iva': invoice_data.get('iva', 0)
            }
            
            # En una implementación real, aquí se generaría el QR usando una librería
            # Por ahora, retornar datos en formato string
            qr_string = f"CUFE:{cufe}|NIT:{qr_data['nit_emisor']}|TOTAL:{qr_data['total']}"
            
            return qr_string
            
        except Exception as e:
            self.logger.error(f"❌ Error generando QR: {e}")
            return ""
    
    def _simulate_dian_response(self, invoice_data: Dict, cufe: str) -> Dict[str, Any]:
        """Simular respuesta de DIAN (modo test)"""
        return {
            'status': 'ACCEPTED' if self.test_mode else 'PENDING',
            'cufe': cufe,
            'timestamp': datetime.now().isoformat(),
            'dian_response_code': '200' if self.test_mode else '202',
            'message': 'Factura válida' if self.test_mode else 'Enviada a DIAN para validación',
            'test_mode': self.test_mode
        }
    
    def validate_cufe(self, cufe: str) -> bool:
        """Validar CUFE contra DIAN"""
        try:
            if self.test_mode:
                # En modo test, validar formato básico
                return len(cufe) == 96 and cufe.isalnum()
            else:
                # En producción, consultar DIAN
                response = requests.get(
                    f"{self.base_url}/api/v1/cufe/{cufe}",
                    headers=self.headers,
                    timeout=30
                )
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"❌ Error validando CUFE: {e}")
            return False
    
    def get_dian_status(self, cufe: str) -> Dict[str, Any]:
        """Obtener estado de factura en DIAN"""
        try:
            if self.test_mode:
                return {
                    'cufe': cufe,
                    'status': 'ACCEPTED',
                    'timestamp': datetime.now().isoformat(),
                    'test_mode': True
                }
            else:
                response = requests.get(
                    f"{self.base_url}/api/v1/status/{cufe}",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        'cufe': cufe,
                        'status': 'ERROR',
                        'error': f"HTTP {response.status_code}",
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estado DIAN: {e}")
            return {
                'cufe': cufe,
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }