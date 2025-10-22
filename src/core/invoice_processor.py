#!/usr/bin/env python3
"""
Procesador principal consolidado de facturas - Versión enterprise
Incluye: type hints completos, validación robusta, manejo de errores consistente,
logging estructurado, context managers y todas las funcionalidades unificadas
"""

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import pdfplumber
import requests
from dotenv import load_dotenv

# Local imports
from ..utils.config import ConfigManager
from ..utils.security import InputValidator, SecurityManager
from ..utils.logging import StructuredLogger
from ..core.parsers import PDFParser, ImageParser
from ..core.validators import TaxValidator
from ..integrations.alegra.client import AlegraClient
from ..integrations.nanobot.client import NanobotClient
from ..exceptions import (
    InvoiceBotError, ValidationError, ParsingError, 
    IntegrationError, ConfigurationError
)

# Load environment variables
load_dotenv()

class InvoiceType(Enum):
    """Tipos de factura soportados"""
    PURCHASE = "compra"
    SALE = "venta"
    UNKNOWN = "unknown"

@dataclass
class ProcessingResult:
    """Resultado del procesamiento de factura"""
    success: bool
    invoice_type: InvoiceType
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class InvoiceProcessor:
    """
    Procesador principal consolidado de facturas con todas las funcionalidades
    unificadas de las versiones anteriores
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        use_nanobot: Optional[bool] = None,
        nanobot_host: Optional[str] = None,
        nanobot_confidence_threshold: Optional[float] = None,
    ) -> None:
        """
        Inicializar procesador con configuración unificada
        
        Args:
            config_path: Ruta al archivo de configuración
            use_nanobot: Habilitar integración Nanobot
            nanobot_host: Host de Nanobot
            nanobot_confidence_threshold: Umbral de confianza para Nanobot
        """
        # Configuración unificada
        self.config = ConfigManager(config_path)
        self.logger = StructuredLogger(self.__class__.__name__)
        self.security = SecurityManager()
        self.input_validator = InputValidator()
        
        # Configuración de Alegra
        self.alegra_client = AlegraClient(
            email=self.config.get('alegra.email'),
            token=self.config.get('alegra.token'),
            base_url=self.config.get('alegra.base_url'),
            timeout=self.config.get('alegra.timeout', 30),
            max_retries=self.config.get('alegra.max_retries', 3)
        )
        
        # Configuración de Nanobot (experimental)
        self.nanobot_enabled = use_nanobot if use_nanobot is not None else self.config.get('nanobot.enabled', False)
        self.nanobot_client: Optional[NanobotClient] = None
        
        if self.nanobot_enabled:
            try:
                host = nanobot_host or self.config.get('nanobot.host', 'http://localhost:8080')
                self.nanobot_client = NanobotClient(host)
                self.nanobot_confidence_threshold = (
                    nanobot_confidence_threshold or 
                    self.config.get('nanobot.confidence_threshold', 0.75)
                )
                self.logger.info("Nanobot habilitado", extra={"nanobot_host": host})
            except Exception as e:
                self.logger.warning("No se pudo inicializar Nanobot", extra={"error": str(e)})
                self.nanobot_enabled = False
        
        # Parsers especializados
        self.pdf_parser = PDFParser(self.config)
        self.image_parser = ImageParser(self.config)
        self.tax_validator = TaxValidator(self.config)
        
        # Cache de resultados
        self._processing_cache: Dict[str, ProcessingResult] = {}
        
        # Asegurar directorios necesarios
        self._ensure_directories()
        
        self.logger.info("Procesador inicializado", extra={
            "nanobot_enabled": self.nanobot_enabled,
            "alegra_configured": bool(self.alegra_client.email and self.alegra_client.token)
        })
    
    def _ensure_directories(self) -> None:
        """Asegurar que los directorios necesarios existan"""
        directories = [
            'logs',
            'facturas/processed',
            'facturas/error',
            'backup',
            'reports',
            'cache'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.debug("Directorio asegurado", extra={"directory": directory})
    
    @contextmanager
    def _processing_context(self, file_path: str):
        """Context manager para procesamiento de archivos con cleanup automático"""
        start_time = datetime.now()
        file_hash = self._get_file_hash(file_path)
        
        try:
            self.logger.info("Iniciando procesamiento", extra={
                "file_path": file_path,
                "file_hash": file_hash
            })
            yield file_hash
        except Exception as e:
            self.logger.error("Error en procesamiento", extra={
                "file_path": file_path,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
        finally:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info("Procesamiento completado", extra={
                "file_path": file_path,
                "processing_time": processing_time
            })
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calcular hash del archivo para caché"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def detect_invoice_type(self, texto: str) -> InvoiceType:
        """
        Detectar automáticamente el tipo de factura (compra/venta)
        con fallback a clasificación legacy si Nanobot falla
        """
        texto_lower = texto.lower()
        
        # Intentar clasificación con Nanobot si está habilitado
        if self.nanobot_enabled and self.nanobot_client:
            try:
                response = self.nanobot_client.classify_invoice(
                    self.config.get('nanobot.classifier_agent', 'invoice_classifier'),
                    texto
                )
                
                if isinstance(response, dict):
                    tipo = str(response.get('tipo', '')).lower()
                    confianza = self._safe_float(response.get('confianza'))
                    
                    self.logger.info("Clasificación Nanobot", extra={
                        "tipo": tipo,
                        "confianza": confianza,
                        "razon": response.get('razon', '')
                    })
                    
                    if tipo in ['compra', 'venta'] and confianza and confianza >= self.nanobot_confidence_threshold:
                        return InvoiceType.PURCHASE if tipo == 'compra' else InvoiceType.SALE
                    
                    # Si confianza es baja, usar triage
                    if confianza and confianza < self.nanobot_confidence_threshold:
                        triage_result = self._invoke_triage_agent(texto, response)
                        if triage_result:
                            tipo_corregido = triage_result.get('tipo')
                            if tipo_corregido in ['compra', 'venta']:
                                return InvoiceType.PURCHASE if tipo_corregido == 'compra' else InvoiceType.SALE
                        
            except Exception as e:
                self.logger.warning("Error en clasificación Nanobot", extra={"error": str(e)})
        
        # Fallback a clasificación legacy
        return self._legacy_detect_invoice_type(texto_lower)
    
    def _legacy_detect_invoice_type(self, texto_lower: str) -> InvoiceType:
        """Detección legacy de tipo de factura basada en keywords"""
        compra_keywords = [
            'proveedor', 'proveedores', 'compra', 'compras', 'factura de compra',
            'bill', 'purchase', 'supplier', 'vendor', 'factura de proveedor',
            'orden de compra', 'oc', 'pedido', 'receipt'
        ]
        
        venta_keywords = [
            'cliente', 'clientes', 'venta', 'ventas', 'factura de venta',
            'invoice', 'sale', 'customer', 'factura de cliente',
            'orden de venta', 'ov', 'cotización', 'quote'
        ]
        
        compra_score = sum(1 for keyword in compra_keywords if keyword in texto_lower)
        venta_score = sum(1 for keyword in venta_keywords if keyword in texto_lower)
        
        self.logger.debug("Clasificación legacy", extra={
            "compra_score": compra_score,
            "venta_score": venta_score
        })
        
        if compra_score > venta_score:
            return InvoiceType.PURCHASE
        elif venta_score > compra_score:
            return InvoiceType.SALE
        else:
            # Patrones adicionales para desempate
            if any(pattern in texto_lower for pattern in ['factura electrónica de venta', 'invoice']):
                return InvoiceType.SALE
            elif any(pattern in texto_lower for pattern in ['bill', 'receipt', 'proveedor']):
                return InvoiceType.PURCHASE
            else:
                self.logger.warning("No se pudo determinar tipo de factura, asumiendo VENTA")
                return InvoiceType.SALE
    
    def _invoke_triage_agent(self, texto: str, classification: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invocar agente de triage de Nanobot para corrección de clasificaciones"""
        if not self.nanobot_enabled or not self.nanobot_client:
            return None
        
        try:
            triage_payload = {
                'texto': texto,
                'clasificacion': classification,
            }
            return self.nanobot_client.triage_invoice(
                self.config.get('nanobot.triage_agent', 'invoice_triage'),
                triage_payload
            )
        except Exception as e:
            self.logger.error("Error en triage de Nanobot", extra={"error": str(e)})
            return None
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Convertir valor a float de forma segura"""
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    def process_invoice(self, file_path: str) -> ProcessingResult:
        """
        Procesar factura con detección automática de tipo y parsing robusto
        
        Args:
            file_path: Ruta al archivo de factura (PDF, JPG, PNG)
            
        Returns:
            ProcessingResult con datos extraídos y metadatos
        """
        # Validar entrada
        if not self.input_validator.validate_file_path(file_path):
            return ProcessingResult(
                success=False,
                invoice_type=InvoiceType.UNKNOWN,
                errors=[f"Archivo no válido: {file_path}"]
            )
        
        # Verificar caché
        file_hash = self._get_file_hash(file_path)
        if file_hash in self._processing_cache:
            cached_result = self._processing_cache[file_hash]
            self.logger.info("Resultado obtenido de caché", extra={"file_hash": file_hash})
            return cached_result
        
        with self._processing_context(file_path) as processing_id:
            try:
                # Extraer datos según tipo de archivo
                if file_path.lower().endswith('.pdf'):
                    raw_data = self.pdf_parser.extract_data(file_path)
                elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    raw_data = self.image_parser.extract_data(file_path)
                else:
                    return ProcessingResult(
                        success=False,
                        invoice_type=InvoiceType.UNKNOWN,
                        errors=[f"Formato no soportado: {Path(file_path).suffix}"]
                    )
                
                if not raw_data:
                    return ProcessingResult(
                        success=False,
                        invoice_type=InvoiceType.UNKNOWN,
                        errors=["No se pudieron extraer datos del archivo"]
                    )
                
                # Detectar tipo de factura
                invoice_type = self.detect_invoice_type(raw_data.get('text', ''))
                
                # Validar y enriquecer datos
                validated_data = self.tax_validator.validate_and_enrich(raw_data, invoice_type)
                
                # Crear resultado
                result = ProcessingResult(
                    success=True,
                    invoice_type=invoice_type,
                    data=validated_data
                )
                
                # Guardar en caché
                self._processing_cache[file_hash] = result
                
                self.logger.info("Factura procesada exitosamente", extra={
                    "file_path": file_path,
                    "invoice_type": invoice_type.value,
                    "total": validated_data.get('total', 0)
                })
                
                return result
                
            except Exception as e:
                self.logger.error("Error procesando factura", extra={
                    "file_path": file_path,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                return ProcessingResult(
                    success=False,
                    invoice_type=InvoiceType.UNKNOWN,
                    errors=[f"Error interno: {str(e)}"]
                )
    
    def create_purchase_bill(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear factura de compra (bill) en Alegra con manejo robusto de errores
        
        Args:
            invoice_data: Datos de la factura procesada
            
        Returns:
            Datos de la bill creada o None si falla
        """
        try:
            self.logger.info("Creando bill de compra", extra={
                "proveedor": invoice_data.get('proveedor', 'N/A'),
                "total": invoice_data.get('total', 0)
            })
            
            # Validar datos requeridos
            required_fields = ['proveedor', 'total', 'fecha']
            missing_fields = [field for field in required_fields if not invoice_data.get(field)]
            if missing_fields:
                raise ValidationError(f"Campos requeridos faltantes: {missing_fields}")
            
            # Crear o obtener contacto
            contact_id = self.alegra_client.get_or_create_contact(
                name=invoice_data['proveedor'],
                contact_type='provider'
            )
            
            if not contact_id:
                self.logger.warning("Usando contacto fallback", extra={"proveedor": invoice_data['proveedor']})
                contact_id = self.alegra_client.get_or_create_contact(
                    name="Consumidor Final",
                    contact_type='provider'
                )
            
            # Crear items
            items = []
            for item in invoice_data.get('items', []):
                item_id = self.alegra_client.get_or_create_item(
                    name=item['descripcion'],
                    price=item['precio'],
                    quantity=item['cantidad']
                )
                if item_id:
                    items.append({
                        'id': item_id,
                        'quantity': item['cantidad'],
                        'price': item['precio']
                    })
            
            # Crear bill
            bill_data = {
                'date': invoice_data['fecha'],
                'dueDate': invoice_data.get('fecha_vencimiento', invoice_data['fecha']),
                'client': {'id': contact_id},
                'items': items,
                'observations': f"Procesado automáticamente desde {invoice_data.get('archivo', 'N/A')}"
            }
            
            result = self.alegra_client.create_bill(bill_data)
            
            if result:
                self.logger.info("Bill creada exitosamente", extra={
                    "bill_id": result.get('id'),
                    "proveedor": invoice_data['proveedor']
                })
                
                # Registrar backup local
                self._register_local_purchase(invoice_data, result)
                
                return result
            else:
                self.logger.error("Error creando bill en Alegra")
                return None
                
        except Exception as e:
            self.logger.error("Error creando bill de compra", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None
    
    def create_sale_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear factura de venta (invoice) en Alegra con manejo robusto de errores
        
        Args:
            invoice_data: Datos de la factura procesada
            
        Returns:
            Datos de la invoice creada o None si falla
        """
        try:
            self.logger.info("Creando invoice de venta", extra={
                "cliente": invoice_data.get('cliente', 'N/A'),
                "total": invoice_data.get('total', 0)
            })
            
            # Validar datos requeridos
            required_fields = ['cliente', 'total', 'fecha']
            missing_fields = [field for field in required_fields if not invoice_data.get(field)]
            if missing_fields:
                raise ValidationError(f"Campos requeridos faltantes: {missing_fields}")
            
            # Crear o obtener contacto
            contact_id = self.alegra_client.get_or_create_contact(
                name=invoice_data['cliente'],
                contact_type='client'
            )
            
            if not contact_id:
                self.logger.warning("Usando contacto fallback", extra={"cliente": invoice_data['cliente']})
                contact_id = self.alegra_client.get_or_create_contact(
                    name="Consumidor Final",
                    contact_type='client'
                )
            
            # Crear items
            items = []
            for item in invoice_data.get('items', []):
                item_id = self.alegra_client.get_or_create_item(
                    name=item['descripcion'],
                    price=item['precio'],
                    quantity=item['cantidad']
                )
                if item_id:
                    items.append({
                        'id': item_id,
                        'quantity': item['cantidad'],
                        'price': item['precio']
                    })
            
            # Crear invoice
            invoice_payload = {
                'date': invoice_data['fecha'],
                'dueDate': invoice_data.get('fecha_vencimiento', invoice_data['fecha']),
                'client': {'id': contact_id},
                'items': items,
                'observations': f"Procesado automáticamente desde {invoice_data.get('archivo', 'N/A')}"
            }
            
            result = self.alegra_client.create_invoice(invoice_payload)
            
            if result:
                self.logger.info("Invoice creada exitosamente", extra={
                    "invoice_id": result.get('id'),
                    "cliente": invoice_data['cliente']
                })
                
                return result
            else:
                self.logger.error("Error creando invoice en Alegra")
                return None
                
        except Exception as e:
            self.logger.error("Error creando invoice de venta", extra={
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None
    
    def _register_local_purchase(self, invoice_data: Dict[str, Any], alegra_result: Dict[str, Any]) -> None:
        """Registrar compra localmente como backup"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'alegra_id': alegra_result.get('id'),
                'invoice_data': invoice_data,
                'alegra_response': alegra_result
            }
            
            backup_file = f"backup/facturas_compra_{datetime.now().strftime('%Y%m%d')}.json"
            Path(backup_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Append to backup file
            if Path(backup_file).exists():
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_records = json.load(f)
            else:
                backup_records = []
            
            backup_records.append(backup_data)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_records, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Backup registrado", extra={"backup_file": backup_file})
            
        except Exception as e:
            self.logger.warning("Error registrando backup", extra={"error": str(e)})
    
    def process_invoice_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Método de compatibilidad con versiones anteriores
        Procesa archivo y crea bill/invoice automáticamente según tipo detectado
        """
        result = self.process_invoice(file_path)
        
        if not result.success:
            return None
        
        # Agregar ruta del archivo a los datos
        result.data['archivo'] = file_path
        
        # Crear bill o invoice según tipo detectado
        if result.invoice_type == InvoiceType.PURCHASE:
            alegra_result = self.create_purchase_bill(result.data)
        elif result.invoice_type == InvoiceType.SALE:
            alegra_result = self.create_sale_invoice(result.data)
        else:
            self.logger.warning("Tipo de factura desconocido, no se creará en Alegra")
            return result.data
        
        if alegra_result:
            result.data['alegra_id'] = alegra_result.get('id')
            result.data['alegra_url'] = alegra_result.get('url')
        
        return result.data


def main():
    """Función principal para CLI"""
    parser = argparse.ArgumentParser(description='Procesador de facturas InvoiceBot')
    parser.add_argument('command', choices=['process', 'report'], help='Comando a ejecutar')
    parser.add_argument('file_path', nargs='?', help='Ruta al archivo de factura')
    parser.add_argument('--use-nanobot', action='store_true', help='Usar Nanobot para clasificación')
    parser.add_argument('--nanobot-host', help='Host de Nanobot')
    parser.add_argument('--nanobot-confidence', type=float, help='Umbral de confianza de Nanobot')
    parser.add_argument('--start-date', help='Fecha de inicio para reportes (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Fecha de fin para reportes (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        # Inicializar procesador
        processor = InvoiceProcessor(
            use_nanobot=args.use_nanobot,
            nanobot_host=args.nanobot_host,
            nanobot_confidence_threshold=args.nanobot_confidence
        )
        
        if args.command == 'process':
            if not args.file_path:
                print("❌ Error: Se requiere ruta al archivo para procesar")
                sys.exit(1)
            
            result = processor.process_invoice_file(args.file_path)
            if result:
                print("✅ Factura procesada exitosamente")
                print(f"📄 Tipo: {result.get('tipo', 'N/A')}")
                print(f"💰 Total: ${result.get('total', 0):,.2f}")
                if result.get('alegra_id'):
                    print(f"🔗 Alegra ID: {result['alegra_id']}")
            else:
                print("❌ Error procesando factura")
                sys.exit(1)
        
        elif args.command == 'report':
            # Generar reportes (implementar según necesidad)
            print("📊 Generando reportes...")
            # TODO: Implementar generación de reportes
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

