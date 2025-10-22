#!/usr/bin/env python3
"""
Validador de impuestos y enriquecimiento de datos fiscales
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from ...utils.config import ConfigManager
from ...exceptions import ValidationError

class InvoiceType(Enum):
    """Tipos de factura"""
    PURCHASE = "compra"
    SALE = "venta"
    UNKNOWN = "unknown"

class TaxValidator:
    """
    Validador de impuestos y enriquecimiento de datos fiscales
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuración de impuestos por defecto
        self.tax_config = {
            'iva_rate': 0.19,  # 19% IVA Colombia
            'retefuente_rate': 0.035,  # 3.5% ReteFuente
            'ica_rate': 0.00414,  # ICA Bogotá
            'currency': 'COP'
        }
    
    def validate_and_enrich(self, raw_data: Dict[str, Any], invoice_type: InvoiceType) -> Dict[str, Any]:
        """
        Validar y enriquecer datos de factura con información fiscal
        
        Args:
            raw_data: Datos extraídos del documento
            invoice_type: Tipo de factura detectado
            
        Returns:
            Datos enriquecidos y validados
        """
        try:
            # Crear copia de los datos
            enriched_data = raw_data.copy()
            
            # Validar datos básicos
            validation_errors = self._validate_basic_data(enriched_data)
            if validation_errors:
                self.logger.warning("Errores de validación encontrados", extra={
                    "errors": validation_errors
                })
            
            # Enriquecer con información fiscal
            self._enrich_tax_data(enriched_data, invoice_type)
            
            # Calcular impuestos
            self._calculate_taxes(enriched_data, invoice_type)
            
            # Agregar metadatos
            enriched_data['tipo'] = invoice_type.value
            enriched_data['timestamp_validacion'] = datetime.now().isoformat()
            enriched_data['moneda'] = self.tax_config['currency']
            
            self.logger.info("Datos enriquecidos exitosamente", extra={
                "invoice_type": invoice_type.value,
                "total": enriched_data.get('total', 0),
                "iva_amount": enriched_data.get('iva_amount', 0)
            })
            
            return enriched_data
            
        except Exception as e:
            self.logger.error("Error enriqueciendo datos", extra={
                "error": str(e),
                "invoice_type": invoice_type.value
            })
            raise ValidationError(f"Error enriqueciendo datos fiscales: {e}")
    
    def _validate_basic_data(self, data: Dict[str, Any]) -> List[str]:
        """Validar datos básicos de la factura"""
        errors = []
        
        # Validar fecha
        if 'fecha' not in data or not data['fecha']:
            errors.append("Fecha de factura requerida")
        else:
            try:
                datetime.strptime(data['fecha'], '%Y-%m-%d')
            except ValueError:
                errors.append("Formato de fecha inválido")
        
        # Validar total
        if 'total' not in data or not isinstance(data['total'], (int, float)):
            errors.append("Total de factura requerido")
        elif data['total'] <= 0:
            errors.append("Total debe ser mayor a 0")
        
        # Validar contacto
        if not data.get('cliente') and not data.get('proveedor'):
            errors.append("Cliente o proveedor requerido")
        
        return errors
    
    def _enrich_tax_data(self, data: Dict[str, Any], invoice_type: InvoiceType) -> None:
        """Enriquecer datos con información fiscal"""
        
        # Agregar información de contacto fiscal
        if invoice_type == InvoiceType.PURCHASE and data.get('proveedor'):
            data['proveedor_nit'] = self._extract_nit_from_text(data.get('text', ''))
            data['proveedor_regime'] = self._determine_tax_regime(data.get('proveedor_nit'))
        
        elif invoice_type == InvoiceType.SALE and data.get('cliente'):
            data['cliente_nit'] = self._extract_nit_from_text(data.get('text', ''))
            data['cliente_regime'] = self._determine_tax_regime(data.get('cliente_nit'))
        
        # Agregar información de ubicación
        data['ubicacion'] = self._extract_location_from_text(data.get('text', ''))
        
        # Agregar número de factura si no existe
        if 'numero_factura' not in data:
            data['numero_factura'] = self._extract_invoice_number(data.get('text', ''))
    
    def _extract_nit_from_text(self, text: str) -> Optional[str]:
        """Extraer NIT del texto"""
        import re
        
        # Patrones para NIT colombiano
        nit_patterns = [
            r'NIT[:\s]+(\d+[-]?\d*)',
            r'Nit[:\s]+(\d+[-]?\d*)',
            r'Identificación[:\s]+(\d+[-]?\d*)',
            r'Tax ID[:\s]+(\d+[-]?\d*)'
        ]
        
        for pattern in nit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_tax_regime(self, nit: Optional[str]) -> str:
        """Determinar régimen fiscal basado en NIT"""
        if not nit:
            return "simplificado"
        
        # Lógica simplificada para determinar régimen
        # En implementación real, esto consultaría base de datos DIAN
        if len(nit.replace('-', '')) >= 8:
            return "comun"
        else:
            return "simplificado"
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extraer ubicación del texto"""
        # Patrones para ciudades colombianas
        cities = [
            'Bogotá', 'Bogota', 'Medellín', 'Medellin', 'Cali', 'Barranquilla',
            'Cartagena', 'Bucaramanga', 'Pereira', 'Santa Marta'
        ]
        
        for city in cities:
            if city.lower() in text.lower():
                return city
        
        return "Bogotá"  # Default
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extraer número de factura del texto"""
        import re
        
        patterns = [
            r'Factura[:\s]+#?(\d+)',
            r'Invoice[:\s]+#?(\d+)',
            r'Número[:\s]+(\d+)',
            r'No[.\s]+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "AUTO-" + datetime.now().strftime('%Y%m%d%H%M%S')
    
    def _calculate_taxes(self, data: Dict[str, Any], invoice_type: InvoiceType) -> None:
        """Calcular impuestos según el tipo de factura"""
        
        total = data.get('total', 0)
        if total <= 0:
            return
        
        # Calcular IVA
        iva_rate = self.tax_config['iva_rate']
        iva_amount = total * iva_rate
        
        data['iva_rate'] = iva_rate
        data['iva_amount'] = iva_amount
        data['base_amount'] = total - iva_amount
        
        # Calcular retenciones según tipo de factura
        if invoice_type == InvoiceType.PURCHASE:
            # ReteFuente para compras
            retefuente_rate = self.tax_config['retefuente_rate']
            data['retefuente_amount'] = total * retefuente_rate
            
            # ICA para compras
            ica_rate = self.tax_config['ica_rate']
            data['ica_amount'] = total * ica_rate
            
            # Total retenciones
            data['total_retenciones'] = data['retefuente_amount'] + data['ica_amount']
            data['net_amount'] = total - data['total_retenciones']
        
        else:  # SALE
            # Para ventas, no hay retenciones normalmente
            data['retefuente_amount'] = 0
            data['ica_amount'] = 0
            data['total_retenciones'] = 0
            data['net_amount'] = total
    
    def validate_tax_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar cumplimiento fiscal
        
        Args:
            data: Datos de la factura
            
        Returns:
            Resultado de validación de cumplimiento
        """
        compliance_result = {
            'compliant': True,
            'warnings': [],
            'errors': []
        }
        
        # Validar montos
        total = data.get('total', 0)
        iva_amount = data.get('iva_amount', 0)
        expected_iva = total * self.tax_config['iva_rate']
        
        if abs(iva_amount - expected_iva) > 0.01:  # Tolerancia de 1 centavo
            compliance_result['warnings'].append(
                f"IVA calculado ({iva_amount:.2f}) no coincide con esperado ({expected_iva:.2f})"
            )
        
        # Validar NIT si existe
        nit = data.get('proveedor_nit') or data.get('cliente_nit')
        if nit and not self._validate_nit_format(nit):
            compliance_result['errors'].append("Formato de NIT inválido")
            compliance_result['compliant'] = False
        
        # Validar rangos de montos
        if total > 1_000_000:  # 1 millón COP
            compliance_result['warnings'].append("Monto alto detectado - verificar documentación")
        
        return compliance_result
    
    def _validate_nit_format(self, nit: str) -> bool:
        """Validar formato de NIT colombiano"""
        import re
        
        # NIT puede tener formato: 12345678-9 o 123456789
        nit_clean = nit.replace('-', '')
        
        if not re.match(r'^\d{8,10}$', nit_clean):
            return False
        
        # Validar dígito de verificación (algoritmo simplificado)
        if len(nit_clean) == 9:
            return self._validate_nit_check_digit(nit_clean)
        
        return True
    
    def _validate_nit_check_digit(self, nit: str) -> bool:
        """Validar dígito de verificación del NIT"""
        try:
            # Algoritmo de validación de NIT colombiano
            weights = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
            
            # Tomar los primeros 8 dígitos
            base_nit = nit[:8]
            check_digit = int(nit[8])
            
            # Calcular suma ponderada
            total = sum(int(digit) * weight for digit, weight in zip(base_nit, weights))
            
            # Calcular dígito de verificación
            remainder = total % 11
            calculated_check = 11 - remainder if remainder > 1 else remainder
            
            return calculated_check == check_digit
            
        except (ValueError, IndexError):
            return False

