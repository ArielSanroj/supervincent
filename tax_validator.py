#!/usr/bin/env python3
"""
Validador de impuestos por país con reglas fiscales específicas
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TaxValidationResult:
    """Resultado de validación de impuestos"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    calculated_taxes: Dict[str, float]
    compliance_score: float

class TaxValidator:
    """Validador de impuestos con reglas específicas por país"""
    
    def __init__(self, country_code: str = 'CO'):
        self.country_code = country_code.upper()
        self.tax_rules = self._load_tax_rules()
        self.logger = logging.getLogger(__name__)
    
    def _load_tax_rules(self) -> Dict[str, Any]:
        """Cargar reglas fiscales por país"""
        try:
            rules_path = f"config/tax_rules_{self.country_code}.json"
            
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Reglas por defecto si no existe archivo específico
                return self._get_default_rules()
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando reglas fiscales: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Reglas fiscales por defecto"""
        return {
            "iva_rates": {
                "standard": 0.19,
                "reduced": 0.05,
                "exempt": 0.0
            },
            "retenciones": {
                "rete_iva": {
                    "natural": 0.035,
                    "juridico": 0.035,
                    "threshold": 1000000
                },
                "rete_fuente": {
                    "natural": 0.11,
                    "juridico": 0.035,
                    "threshold": 1000000
                },
                "rete_ica": {
                    "natural": 0.01,
                    "juridico": 0.01,
                    "threshold": 1000000
                }
            },
            "validation_rules": {
                "tolerance_percentage": 0.01,
                "require_nit_providers": True,
                "require_cc_clients": True,
                "max_amount_without_approval": 1000000
            }
        }
    
    def validate_invoice_taxes(self, invoice_data: Dict) -> TaxValidationResult:
        """Validar impuestos de una factura"""
        errors = []
        warnings = []
        calculated_taxes = {}
        
        try:
            # Obtener datos básicos
            total = invoice_data.get('total', 0)
            items = invoice_data.get('items', [])
            invoice_type = invoice_data.get('tipo', 'venta')
            
            # Calcular total de items
            items_total = sum(item.get('precio', 0) for item in items)
            
            # Validar IVA
            iva_validation = self._validate_iva(invoice_data, items_total)
            errors.extend(iva_validation['errors'])
            warnings.extend(iva_validation['warnings'])
            calculated_taxes.update(iva_validation['calculated'])
            
            # Validar retenciones
            retention_validation = self._validate_retenciones(invoice_data, items_total, invoice_type)
            errors.extend(retention_validation['errors'])
            warnings.extend(retention_validation['warnings'])
            calculated_taxes.update(retention_validation['calculated'])
            
            # Validar total general
            total_validation = self._validate_total(invoice_data, calculated_taxes)
            errors.extend(total_validation['errors'])
            warnings.extend(total_validation['warnings'])
            
            # Calcular score de cumplimiento
            compliance_score = self._calculate_compliance_score(errors, warnings)
            
            return TaxValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                calculated_taxes=calculated_taxes,
                compliance_score=compliance_score
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error validando impuestos: {e}")
            return TaxValidationResult(
                is_valid=False,
                errors=[f"Error interno: {str(e)}"],
                warnings=[],
                calculated_taxes={},
                compliance_score=0.0
            )
    
    def _validate_iva(self, invoice_data: Dict, items_total: float) -> Dict[str, Any]:
        """Validar IVA"""
        errors = []
        warnings = []
        calculated = {}
        
        try:
            # Obtener IVA reportado
            reported_iva = invoice_data.get('iva', 0)
            
            # Calcular IVA esperado
            iva_rate = self.tax_rules['iva_rates']['standard']
            expected_iva = items_total * iva_rate
            
            # Verificar tolerancia
            tolerance = items_total * self.tax_rules['validation_rules']['tolerance_percentage']
            
            if abs(reported_iva - expected_iva) > tolerance:
                if abs(reported_iva - expected_iva) > tolerance * 2:
                    errors.append(f"IVA no coincide: Reportado ${reported_iva:,.2f}, Esperado ${expected_iva:,.2f}")
                else:
                    warnings.append(f"IVA ligeramente diferente: Reportado ${reported_iva:,.2f}, Esperado ${expected_iva:,.2f}")
            
            calculated['iva_calculated'] = expected_iva
            calculated['iva_rate'] = iva_rate
            
        except Exception as e:
            errors.append(f"Error validando IVA: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'calculated': calculated
        }
    
    def _validate_retenciones(self, invoice_data: Dict, items_total: float, invoice_type: str) -> Dict[str, Any]:
        """Validar retenciones"""
        errors = []
        warnings = []
        calculated = {}
        
        try:
            # Solo validar retenciones para compras
            if invoice_type != 'compra':
                return {'errors': [], 'warnings': [], 'calculated': {}}
            
            # Obtener tipo de proveedor (simplificado)
            provider_type = self._determine_provider_type(invoice_data)
            
            # Validar cada tipo de retención
            for retention_type, rules in self.tax_rules['retenciones'].items():
                if items_total >= rules['threshold']:
                    expected_rate = rules[provider_type]
                    expected_amount = items_total * expected_rate
                    
                    reported_amount = invoice_data.get(retention_type, 0)
                    tolerance = items_total * self.tax_rules['validation_rules']['tolerance_percentage']
                    
                    if abs(reported_amount - expected_amount) > tolerance:
                        if abs(reported_amount - expected_amount) > tolerance * 2:
                            errors.append(f"{retention_type.upper()} no coincide: Reportado ${reported_amount:,.2f}, Esperado ${expected_amount:,.2f}")
                        else:
                            warnings.append(f"{retention_type.upper()} ligeramente diferente: Reportado ${reported_amount:,.2f}, Esperado ${expected_amount:,.2f}")
                    
                    calculated[f"{retention_type}_calculated"] = expected_amount
                    calculated[f"{retention_type}_rate"] = expected_rate
        
        except Exception as e:
            errors.append(f"Error validando retenciones: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'calculated': calculated
        }
    
    def _validate_total(self, invoice_data: Dict, calculated_taxes: Dict) -> Dict[str, Any]:
        """Validar total de la factura"""
        errors = []
        warnings = []
        
        try:
            reported_total = invoice_data.get('total', 0)
            items_total = sum(item.get('precio', 0) for item in invoice_data.get('items', []))
            
            # Calcular total esperado
            expected_total = items_total
            expected_total += calculated_taxes.get('iva_calculated', 0)
            expected_total -= calculated_taxes.get('rete_iva_calculated', 0)
            expected_total -= calculated_taxes.get('rete_fuente_calculated', 0)
            expected_total -= calculated_taxes.get('rete_ica_calculated', 0)
            
            # Verificar tolerancia
            tolerance = reported_total * self.tax_rules['validation_rules']['tolerance_percentage']
            
            if abs(reported_total - expected_total) > tolerance:
                errors.append(f"Total no coincide: Reportado ${reported_total:,.2f}, Esperado ${expected_total:,.2f}")
        
        except Exception as e:
            errors.append(f"Error validando total: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'calculated': {}
        }
    
    def _determine_provider_type(self, invoice_data: Dict) -> str:
        """Determinar tipo de proveedor basado en NIT"""
        try:
            nit = invoice_data.get('nit_proveedor', '')
            if not nit:
                return 'juridico'  # Por defecto
            
            # Limpiar NIT
            clean_nit = nit.replace('-', '').replace('.', '')
            
            # Validar longitud
            if len(clean_nit) < 8:
                return 'juridico'
            
            # En Colombia, los NITs de personas naturales suelen tener ciertos patrones
            # Esta es una lógica simplificada
            if clean_nit.startswith('1') and len(clean_nit) == 10:
                return 'natural'
            elif clean_nit.startswith('9') and len(clean_nit) == 10:
                return 'natural'
            else:
                return 'juridico'
                
        except Exception:
            return 'juridico'
    
    def calculate_dynamic_retenciones(self, invoice_data: Dict) -> Dict[str, float]:
        """Calcular retenciones dinámicas basadas en tipo de proveedor"""
        try:
            provider_type = self._determine_provider_type(invoice_data)
            items_total = sum(item.get('precio', 0) for item in invoice_data.get('items', []))
            
            calculated_retenciones = {}
            
            for retention_type, rules in self.tax_rules['retenciones'].items():
                if items_total >= rules['threshold']:
                    rate = rules[provider_type]
                    amount = items_total * rate
                    calculated_retenciones[retention_type] = amount
                else:
                    calculated_retenciones[retention_type] = 0.0
            
            return calculated_retenciones
            
        except Exception as e:
            self.logger.error(f"❌ Error calculando retenciones dinámicas: {e}")
            return {}
    
    def get_provider_retention_rates(self, provider_type: str) -> Dict[str, float]:
        """Obtener tasas de retención para un tipo de proveedor"""
        try:
            rates = {}
            
            for retention_type, rules in self.tax_rules['retenciones'].items():
                rates[retention_type] = rules.get(provider_type, 0.0)
            
            return rates
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo tasas de retención: {e}")
            return {}
    
    def _calculate_compliance_score(self, errors: List[str], warnings: List[str]) -> float:
        """Calcular score de cumplimiento (0.0 a 1.0)"""
        if not errors and not warnings:
            return 1.0
        
        # Penalizar errores más que warnings
        error_penalty = len(errors) * 0.3
        warning_penalty = len(warnings) * 0.1
        
        score = max(0.0, 1.0 - error_penalty - warning_penalty)
        return round(score, 2)
    
    def get_tax_rules_for_country(self) -> Dict[str, Any]:
        """Obtener reglas fiscales para el país"""
        return self.tax_rules
    
    def validate_nit_format(self, nit: str) -> bool:
        """Validar formato de NIT (Colombia)"""
        if self.country_code != 'CO':
            return True  # No validar para otros países
        
        try:
            # Validar formato básico de NIT colombiano
            if not nit or len(nit) < 8:
                return False
            
            # Remover guiones y puntos
            clean_nit = nit.replace('-', '').replace('.', '')
            
            # Debe ser numérico
            if not clean_nit.isdigit():
                return False
            
            # Validar dígito de verificación (algoritmo simplificado)
            return self._validate_nit_check_digit(clean_nit)
            
        except Exception:
            return False
    
    def _validate_nit_check_digit(self, nit: str) -> bool:
        """Validar dígito de verificación del NIT (simplificado)"""
        try:
            # Algoritmo simplificado de validación de NIT
            if len(nit) < 8:
                return False
            
            # Tomar los primeros 8 dígitos
            base = nit[:8]
            check_digit = int(nit[8]) if len(nit) > 8 else 0
            
            # Calcular dígito de verificación
            weights = [71, 67, 59, 53, 47, 43, 41, 37]
            total = sum(int(digit) * weight for digit, weight in zip(base, weights))
            calculated_check = total % 11
            
            return calculated_check == check_digit
            
        except Exception:
            return False