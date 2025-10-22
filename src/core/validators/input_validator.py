#!/usr/bin/env python3
"""
Validador de entrada con sanitización y validación robusta
"""

import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging

from ...exceptions import ValidationError

class InputValidator:
    """
    Validador de entrada con sanitización y validación robusta
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Patrones de regex seguros
        self.safe_patterns = {
            'filename': re.compile(r'^[a-zA-Z0-9._-]+$'),
            'contact_name': re.compile(r'^[a-zA-Z0-9\s\.\-_]+$'),
            'amount': re.compile(r'^\d+(\.\d{1,2})?$'),
            'date': re.compile(r'^\d{4}-\d{2}-\d{2}$')
        }
        
        # Caracteres peligrosos
        self.dangerous_chars = {'<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$'}
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validar ruta de archivo con whitelist de extensiones y sanitización
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            True si es válido, False en caso contrario
        """
        try:
            path = Path(file_path)
            
            # Verificar que el archivo existe
            if not path.exists():
                self.logger.warning("Archivo no encontrado", extra={"file_path": file_path})
                return False
            
            # Verificar extensión
            allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
            if path.suffix.lower() not in allowed_extensions:
                self.logger.warning("Extensión no permitida", extra={
                    "file_path": file_path,
                    "extension": path.suffix,
                    "allowed": list(allowed_extensions)
                })
                return False
            
            # Verificar tamaño (50MB máximo)
            max_size_mb = 50
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                self.logger.warning("Archivo demasiado grande", extra={
                    "file_path": file_path,
                    "size_mb": file_size_mb,
                    "max_size_mb": max_size_mb
                })
                return False
            
            # Verificar nombre de archivo seguro
            if not self.safe_patterns['filename'].match(path.name):
                self.logger.warning("Nombre de archivo contiene caracteres peligrosos", extra={
                    "file_path": file_path,
                    "filename": path.name
                })
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Error validando archivo", extra={
                "file_path": file_path,
                "error": str(e)
            })
            return False
    
    def sanitize_contact_name(self, name: str) -> str:
        """
        Sanitizar nombre de contacto eliminando caracteres peligrosos
        
        Args:
            name: Nombre original
            
        Returns:
            Nombre sanitizado
        """
        if not name:
            return "Consumidor Final"
        
        # Eliminar caracteres peligrosos
        sanitized = ''.join(c for c in name if c not in self.dangerous_chars)
        
        # Limitar longitud
        sanitized = sanitized[:100]
        
        # Validar con regex
        if not self.safe_patterns['contact_name'].match(sanitized):
            self.logger.warning("Nombre de contacto no válido, usando fallback", extra={
                "original": name,
                "sanitized": sanitized
            })
            return "Consumidor Final"
        
        return sanitized.strip()
    
    def validate_amount(self, amount: Any) -> Optional[float]:
        """
        Validar y convertir monto a float de forma segura
        
        Args:
            amount: Monto a validar
            
        Returns:
            Monto como float o None si no es válido
        """
        try:
            if isinstance(amount, (int, float)):
                amount_str = str(amount)
            else:
                amount_str = str(amount).strip()
            
            # Validar formato
            if not self.safe_patterns['amount'].match(amount_str):
                return None
            
            amount_float = float(amount_str)
            
            # Validar rango razonable
            if amount_float < 0 or amount_float > 1_000_000_000:  # 1 billón
                return None
            
            return amount_float
            
        except (ValueError, TypeError):
            return None
    
    def validate_date(self, date_str: str) -> bool:
        """
        Validar formato de fecha YYYY-MM-DD
        
        Args:
            date_str: Fecha como string
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not isinstance(date_str, str):
            return False
        
        return bool(self.safe_patterns['date'].match(date_str.strip()))
    
    def validate_invoice_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validar datos de factura completos
        
        Args:
            data: Datos de la factura
            
        Returns:
            Lista de errores encontrados
        """
        errors = []
        
        # Validar campos requeridos
        required_fields = ['fecha', 'total']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar fecha
        if 'fecha' in data and not self.validate_date(data['fecha']):
            errors.append("Formato de fecha inválido (debe ser YYYY-MM-DD)")
        
        # Validar total
        if 'total' in data:
            validated_total = self.validate_amount(data['total'])
            if validated_total is None:
                errors.append("Monto total inválido")
            else:
                data['total'] = validated_total  # Actualizar con valor validado
        
        # Validar items
        if 'items' in data and isinstance(data['items'], list):
            for i, item in enumerate(data['items']):
                if not isinstance(item, dict):
                    errors.append(f"Item {i} no es un diccionario válido")
                    continue
                
                # Validar campos del item
                item_errors = self._validate_item(item, i)
                errors.extend(item_errors)
        
        return errors
    
    def _validate_item(self, item: Dict[str, Any], index: int) -> List[str]:
        """Validar item individual"""
        errors = []
        
        required_item_fields = ['descripcion', 'cantidad', 'precio']
        for field in required_item_fields:
            if field not in item:
                errors.append(f"Item {index}: campo requerido faltante: {field}")
        
        # Validar cantidad
        if 'cantidad' in item:
            try:
                cantidad = float(item['cantidad'])
                if cantidad <= 0:
                    errors.append(f"Item {index}: cantidad debe ser mayor a 0")
            except (ValueError, TypeError):
                errors.append(f"Item {index}: cantidad inválida")
        
        # Validar precio
        if 'precio' in item:
            precio_validado = self.validate_amount(item['precio'])
            if precio_validado is None:
                errors.append(f"Item {index}: precio inválido")
            else:
                item['precio'] = precio_validado  # Actualizar con valor validado
        
        return errors

