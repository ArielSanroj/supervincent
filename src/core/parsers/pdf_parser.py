#!/usr/bin/env python3
"""
Parser especializado para documentos PDF con múltiples estrategias de parsing
y caché de resultados
"""

import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Pattern
import pdfplumber
import logging

from ...utils.config import ConfigManager
from ...exceptions import ParsingError

class PDFParser:
    """
    Parser robusto para PDFs con múltiples estrategias de parsing,
    caché de resultados y manejo de errores mejorado
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Caché de resultados por hash de archivo
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Patrones de regex compilados para mejor performance
        self.patterns = self._compile_patterns()
        
        # Estrategias de parsing ordenadas por prioridad
        self.parsing_strategies = [
            self._parse_with_standard_patterns,
            self._parse_with_advanced_patterns,
            self._parse_with_fallback_patterns
        ]
    
    def _compile_patterns(self) -> Dict[str, List[Pattern]]:
        """Compilar patrones de regex una sola vez para mejor performance"""
        return {
            'fecha': [
                re.compile(r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE),
                re.compile(r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE),
                re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE),
                re.compile(r'Fecha de emisión[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', re.IGNORECASE)
            ],
            'cliente': [
                re.compile(r'Cliente[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Customer[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Facturar a[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Bill to[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Razón Social[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Nombre[:\s]+(.+)', re.IGNORECASE)
            ],
            'proveedor': [
                re.compile(r'Proveedor[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Supplier[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'Vendor[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'De[:\s]+(.+)', re.IGNORECASE),
                re.compile(r'From[:\s]+(.+)', re.IGNORECASE)
            ],
            'total': [
                re.compile(r'Total[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Amount[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Subtotal[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Importe Total[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Total a Pagar[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE)
            ],
            'iva': [
                re.compile(r'IVA[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Impuesto[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'Tax[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE),
                re.compile(r'19%[:\s]+\$?([\d,]+\.?\d*)', re.IGNORECASE)
            ],
            'nit': [
                re.compile(r'NIT[:\s]+(\d+[-]?\d*)', re.IGNORECASE),
                re.compile(r'Nit[:\s]+(\d+[-]?\d*)', re.IGNORECASE),
                re.compile(r'Tax ID[:\s]+(\d+[-]?\d*)', re.IGNORECASE),
                re.compile(r'Identificación[:\s]+(\d+[-]?\d*)', re.IGNORECASE)
            ],
            'numero_factura': [
                re.compile(r'Factura[:\s]+#?(\d+)', re.IGNORECASE),
                re.compile(r'Invoice[:\s]+#?(\d+)', re.IGNORECASE),
                re.compile(r'Número[:\s]+(\d+)', re.IGNORECASE),
                re.compile(r'No[.\s]+(\d+)', re.IGNORECASE)
            ]
        }
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calcular hash del archivo para caché"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def extract_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extraer datos del PDF usando múltiples estrategias de parsing
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con datos extraídos o None si falla
        """
        try:
            # Verificar caché
            file_hash = self._get_file_hash(file_path)
            if file_hash in self._cache:
                self.logger.debug("Datos obtenidos de caché", extra={"file_hash": file_hash})
                return self._cache[file_hash]
            
            # Extraer texto del PDF
            texto = self._extract_text_from_pdf(file_path)
            if not texto:
                return None
            
            # Aplicar estrategias de parsing
            datos = self._parse_with_strategies(texto)
            
            # Agregar metadatos
            datos['text'] = texto
            datos['archivo'] = file_path
            datos['timestamp_procesamiento'] = datetime.now().isoformat()
            
            # Guardar en caché
            self._cache[file_hash] = datos
            
            self.logger.info("PDF procesado exitosamente", extra={
                "file_path": file_path,
                "text_length": len(texto),
                "data_fields": list(datos.keys())
            })
            
            return datos
            
        except Exception as e:
            self.logger.error("Error procesando PDF", extra={
                "file_path": file_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise ParsingError(f"Error procesando PDF {file_path}: {e}")
    
    def _extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extraer texto del PDF usando pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                texto = ''
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        texto += f"\n--- Página {page_num + 1} ---\n{page_text}"
                
                if not texto.strip():
                    self.logger.warning("No se pudo extraer texto del PDF", extra={"file_path": file_path})
                    return None
                
                return texto.strip()
                
        except Exception as e:
            self.logger.error("Error extrayendo texto del PDF", extra={
                "file_path": file_path,
                "error": str(e)
            })
            return None
    
    def _parse_with_strategies(self, texto: str) -> Dict[str, Any]:
        """Aplicar múltiples estrategias de parsing hasta encontrar datos válidos"""
        for strategy in self.parsing_strategies:
            try:
                datos = strategy(texto)
                if self._validate_parsed_data(datos):
                    self.logger.debug("Datos parseados con estrategia", extra={
                        "strategy": strategy.__name__,
                        "fields_found": len([k for k, v in datos.items() if v])
                    })
                    return datos
            except Exception as e:
                self.logger.debug("Estrategia falló", extra={
                    "strategy": strategy.__name__,
                    "error": str(e)
                })
                continue
        
        # Si todas las estrategias fallan, devolver datos mínimos
        self.logger.warning("Todas las estrategias de parsing fallaron, usando datos mínimos")
        return self._create_minimal_data(texto)
    
    def _parse_with_standard_patterns(self, texto: str) -> Dict[str, Any]:
        """Parsing con patrones estándar más comunes"""
        datos = {}
        
        # Extraer fecha
        for pattern in self.patterns['fecha']:
            match = pattern.search(texto)
            if match:
                fecha_str = match.group(1)
                fecha_formateada = self._parse_date(fecha_str)
                if fecha_formateada:
                    datos['fecha'] = fecha_formateada
                    break
        
        # Extraer cliente/proveedor
        for pattern in self.patterns['cliente']:
            match = pattern.search(texto)
            if match:
                datos['cliente'] = match.group(1).strip()
                break
        
        for pattern in self.patterns['proveedor']:
            match = pattern.search(texto)
            if match:
                datos['proveedor'] = match.group(1).strip()
                break
        
        # Extraer total
        for pattern in self.patterns['total']:
            match = pattern.search(texto)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    datos['total'] = float(total_str)
                    break
                except ValueError:
                    continue
        
        # Extraer items
        datos['items'] = self._extract_items_from_text(texto)
        
        return datos
    
    def _parse_with_advanced_patterns(self, texto: str) -> Dict[str, Any]:
        """Parsing con patrones avanzados y análisis de estructura"""
        datos = {}
        
        # Análisis de líneas para encontrar patrones estructurales
        lines = texto.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Buscar fecha en formato más flexible
            if any(keyword in line_lower for keyword in ['fecha', 'date']):
                fecha = self._extract_date_from_line(line)
                if fecha:
                    datos['fecha'] = fecha
            
            # Buscar totales con contexto
            if any(keyword in line_lower for keyword in ['total', 'amount', 'importe']):
                total = self._extract_amount_from_line(line)
                if total:
                    datos['total'] = total
            
            # Buscar información de contacto
            if any(keyword in line_lower for keyword in ['cliente', 'customer', 'proveedor', 'supplier']):
                contacto = self._extract_contact_from_line(line)
                if contacto:
                    if 'cliente' in line_lower or 'customer' in line_lower:
                        datos['cliente'] = contacto
                    else:
                        datos['proveedor'] = contacto
        
        # Extraer items con análisis de tabla
        datos['items'] = self._extract_items_advanced(texto)
        
        return datos
    
    def _parse_with_fallback_patterns(self, texto: str) -> Dict[str, Any]:
        """Parsing de fallback con patrones más permisivos"""
        datos = {}
        
        # Buscar cualquier fecha en el texto
        fecha_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', texto)
        if fecha_matches:
            fecha = self._parse_date(fecha_matches[0])
            if fecha:
                datos['fecha'] = fecha
        
        # Buscar cualquier número que parezca un total
        amount_matches = re.findall(r'\$?([\d,]+\.?\d*)', texto)
        amounts = []
        for match in amount_matches:
            try:
                amount = float(match.replace(',', ''))
                if 10 <= amount <= 1_000_000:  # Rango razonable
                    amounts.append(amount)
            except ValueError:
                continue
        
        if amounts:
            # Usar el número más grande como total
            datos['total'] = max(amounts)
        
        # Crear items genéricos
        datos['items'] = [{
            'descripcion': 'Producto/Servicio procesado desde PDF',
            'cantidad': 1.0,
            'precio': datos.get('total', 100.0)
        }]
        
        return datos
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parsear fecha en diferentes formatos"""
        formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d',
            '%d-%m-%y', '%d/%m/%y'
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _extract_date_from_line(self, line: str) -> Optional[str]:
        """Extraer fecha de una línea específica"""
        date_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', line)
        for match in date_matches:
            fecha = self._parse_date(match)
            if fecha:
                return fecha
        return None
    
    def _extract_amount_from_line(self, line: str) -> Optional[float]:
        """Extraer monto de una línea específica"""
        amount_matches = re.findall(r'\$?([\d,]+\.?\d*)', line)
        for match in amount_matches:
            try:
                amount = float(match.replace(',', ''))
                if 10 <= amount <= 1_000_000:
                    return amount
            except ValueError:
                continue
        return None
    
    def _extract_contact_from_line(self, line: str) -> Optional[str]:
        """Extraer información de contacto de una línea"""
        # Remover números y caracteres especiales, mantener texto
        contact = re.sub(r'[\d$:]+', '', line).strip()
        if len(contact) > 3 and len(contact) < 100:
            return contact
        return None
    
    def _extract_items_from_text(self, texto: str) -> List[Dict[str, Any]]:
        """Extraer items de factura desde texto con análisis básico"""
        items = []
        lines = texto.split('\n')
        in_items_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detectar inicio de sección de items
            if any(keyword in line.lower() for keyword in ['descripción', 'item', 'producto', 'servicio', 'cantidad', 'precio']):
                in_items_section = True
                continue
            
            # Detectar fin de sección de items
            if any(keyword in line.lower() for keyword in ['subtotal', 'total', 'impuestos', 'iva']):
                in_items_section = False
                continue
            
            # Extraer item si estamos en la sección correcta
            if in_items_section:
                item = self._parse_item_line(line)
                if item:
                    items.append(item)
        
        # Si no se encontraron items, crear uno genérico
        if not items:
            items.append({
                'descripcion': 'Producto/Servicio procesado desde PDF',
                'cantidad': 1.0,
                'precio': 100.0
            })
        
        return items
    
    def _extract_items_advanced(self, texto: str) -> List[Dict[str, Any]]:
        """Extraer items con análisis avanzado de estructura"""
        items = []
        
        # Buscar patrones de tabla
        lines = texto.split('\n')
        for i, line in enumerate(lines):
            # Buscar líneas que contengan números (posibles items)
            numbers = re.findall(r'[\d,]+\.?\d*', line)
            if len(numbers) >= 2:  # Al menos cantidad y precio
                try:
                    cantidad = float(numbers[0].replace(',', ''))
                    precio = float(numbers[1].replace(',', ''))
                    
                    # Extraer descripción (texto sin números)
                    descripcion = re.sub(r'[\d,]+\.?\d*', '', line).strip()
                    
                    if descripcion and cantidad > 0 and precio > 0:
                        items.append({
                            'descripcion': descripcion,
                            'cantidad': cantidad,
                            'precio': precio
                        })
                except ValueError:
                    continue
        
        return items if items else self._extract_items_from_text(texto)
    
    def _parse_item_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parsear una línea individual como item"""
        numbers = re.findall(r'[\d,]+\.?\d*', line)
        if len(numbers) >= 2:
            try:
                cantidad = float(numbers[0].replace(',', ''))
                precio = float(numbers[1].replace(',', ''))
                descripcion = re.sub(r'[\d,]+\.?\d*', '', line).strip()
                
                if descripcion and cantidad > 0 and precio > 0:
                    return {
                        'descripcion': descripcion,
                        'cantidad': cantidad,
                        'precio': precio
                    }
            except ValueError:
                pass
        return None
    
    def _validate_parsed_data(self, datos: Dict[str, Any]) -> bool:
        """Validar que los datos parseados sean mínimamente útiles"""
        # Debe tener al menos fecha o total
        has_date = 'fecha' in datos and datos['fecha']
        has_total = 'total' in datos and isinstance(datos['total'], (int, float)) and datos['total'] > 0
        has_contact = 'cliente' in datos or 'proveedor' in datos
        
        return has_date or has_total or has_contact
    
    def _create_minimal_data(self, texto: str) -> Dict[str, Any]:
        """Crear datos mínimos cuando el parsing falla"""
        return {
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'total': 100.0,
            'items': [{
                'descripcion': 'Producto/Servicio procesado desde PDF',
                'cantidad': 1.0,
                'precio': 100.0
            }]
        }
    
    def clear_cache(self) -> None:
        """Limpiar caché de resultados"""
        self._cache.clear()
        self.logger.info("Caché de PDF parser limpiado")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return {
            'cache_size': len(self._cache),
            'cache_keys': list(self._cache.keys())
        }

