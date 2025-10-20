#!/usr/bin/env python3
"""
Sistema de resiliencia para validaciones DIAN/SAT con fallback local
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ComplianceStatus(Enum):
    """Estados de cumplimiento fiscal"""
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"
    RETRY = "retry"
    FALLBACK = "fallback"

@dataclass
class ComplianceRecord:
    """Registro de cumplimiento fiscal"""
    invoice_id: str
    file_path: str
    status: ComplianceStatus
    dian_response: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    updated_at: datetime = None
    next_retry_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class DIANResilienceManager:
    """Gestor de resiliencia para validaciones DIAN"""
    
    def __init__(self, fallback_folder: str = "compliance_fallback"):
        self.fallback_folder = fallback_folder
        self.logger = logging.getLogger(__name__)
        
        # Crear carpeta de fallback
        os.makedirs(fallback_folder, exist_ok=True)
        
        # Archivo de registros de cumplimiento
        self.compliance_file = os.path.join(fallback_folder, "compliance_records.json")
        self.compliance_records = self._load_compliance_records()
    
    def _load_compliance_records(self) -> Dict[str, ComplianceRecord]:
        """Cargar registros de cumplimiento desde archivo"""
        try:
            if os.path.exists(self.compliance_file):
                with open(self.compliance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                records = {}
                for invoice_id, record_data in data.items():
                    # Convertir string de datetime a objeto datetime
                    if record_data.get('created_at'):
                        record_data['created_at'] = datetime.fromisoformat(record_data['created_at'])
                    if record_data.get('updated_at'):
                        record_data['updated_at'] = datetime.fromisoformat(record_data['updated_at'])
                    if record_data.get('next_retry_at'):
                        record_data['next_retry_at'] = datetime.fromisoformat(record_data['next_retry_at'])
                    
                    # Convertir string de status a enum
                    if record_data.get('status'):
                        record_data['status'] = ComplianceStatus(record_data['status'])
                    
                    records[invoice_id] = ComplianceRecord(**record_data)
                
                return records
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando registros de cumplimiento: {e}")
            return {}
    
    def _save_compliance_records(self):
        """Guardar registros de cumplimiento en archivo"""
        try:
            # Convertir objetos a diccionarios serializables
            data = {}
            for invoice_id, record in self.compliance_records.items():
                record_dict = {
                    'invoice_id': record.invoice_id,
                    'file_path': record.file_path,
                    'status': record.status.value,
                    'dian_response': record.dian_response,
                    'error_message': record.error_message,
                    'retry_count': record.retry_count,
                    'max_retries': record.max_retries,
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat(),
                    'next_retry_at': record.next_retry_at.isoformat() if record.next_retry_at else None
                }
                data[invoice_id] = record_dict
            
            with open(self.compliance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error guardando registros de cumplimiento: {e}")
    
    def register_invoice(self, invoice_id: str, file_path: str, invoice_data: Dict) -> ComplianceRecord:
        """Registrar factura para validación de cumplimiento"""
        try:
            record = ComplianceRecord(
                invoice_id=invoice_id,
                file_path=file_path,
                status=ComplianceStatus.PENDING
            )
            
            self.compliance_records[invoice_id] = record
            self._save_compliance_records()
            
            # Guardar backup de la factura
            self._save_invoice_backup(invoice_id, invoice_data)
            
            self.logger.info(f"📋 Factura registrada para validación: {invoice_id}")
            return record
            
        except Exception as e:
            self.logger.error(f"❌ Error registrando factura {invoice_id}: {e}")
            raise
    
    def _save_invoice_backup(self, invoice_id: str, invoice_data: Dict):
        """Guardar backup de la factura"""
        try:
            backup_file = os.path.join(self.fallback_folder, f"{invoice_id}_backup.json")
            
            backup_data = {
                'invoice_id': invoice_id,
                'invoice_data': invoice_data,
                'backup_created': datetime.now().isoformat(),
                'compliance_status': ComplianceStatus.PENDING.value
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error guardando backup de factura {invoice_id}: {e}")
    
    def update_compliance_status(self, invoice_id: str, status: ComplianceStatus, 
                               dian_response: Dict = None, error_message: str = None):
        """Actualizar estado de cumplimiento"""
        try:
            if invoice_id in self.compliance_records:
                record = self.compliance_records[invoice_id]
                record.status = status
                record.updated_at = datetime.now()
                
                if dian_response:
                    record.dian_response = dian_response
                
                if error_message:
                    record.error_message = error_message
                
                # Calcular próximo reintento si es necesario
                if status == ComplianceStatus.RETRY:
                    record.retry_count += 1
                    if record.retry_count < record.max_retries:
                        # Reintentar en 1, 5, 15 minutos (exponential backoff)
                        delay_minutes = 1 * (3 ** (record.retry_count - 1))
                        record.next_retry_at = datetime.now() + timedelta(minutes=delay_minutes)
                    else:
                        record.status = ComplianceStatus.FAILED
                        record.next_retry_at = None
                
                self._save_compliance_records()
                self.logger.info(f"📊 Estado actualizado: {invoice_id} -> {status.value}")
                
        except Exception as e:
            self.logger.error(f"❌ Error actualizando estado {invoice_id}: {e}")
    
    def get_pending_retries(self) -> List[ComplianceRecord]:
        """Obtener facturas pendientes de reintento"""
        try:
            now = datetime.now()
            pending = []
            
            for record in self.compliance_records.values():
                if (record.status == ComplianceStatus.RETRY and 
                    record.next_retry_at and 
                    record.next_retry_at <= now):
                    pending.append(record)
            
            return pending
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo reintentos pendientes: {e}")
            return []
    
    def get_failed_invoices(self) -> List[ComplianceRecord]:
        """Obtener facturas con validación fallida"""
        try:
            return [record for record in self.compliance_records.values() 
                   if record.status == ComplianceStatus.FAILED]
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo facturas fallidas: {e}")
            return []
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de cumplimiento"""
        try:
            stats = {
                'total_invoices': len(self.compliance_records),
                'pending': 0,
                'validated': 0,
                'failed': 0,
                'retry': 0,
                'fallback': 0
            }
            
            for record in self.compliance_records.values():
                stats[record.status.value] += 1
            
            # Calcular porcentajes
            total = stats['total_invoices']
            if total > 0:
                for status in ['pending', 'validated', 'failed', 'retry', 'fallback']:
                    stats[f'{status}_percentage'] = round((stats[status] / total) * 100, 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def cleanup_old_records(self, days_old: int = 30):
        """Limpiar registros antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            # Filtrar registros antiguos
            old_records = []
            for invoice_id, record in self.compliance_records.items():
                if record.created_at < cutoff_date:
                    old_records.append(invoice_id)
            
            # Eliminar registros antiguos
            for invoice_id in old_records:
                del self.compliance_records[invoice_id]
                cleaned_count += 1
                
                # Eliminar archivo de backup
                backup_file = os.path.join(self.fallback_folder, f"{invoice_id}_backup.json")
                if os.path.exists(backup_file):
                    os.remove(backup_file)
            
            if cleaned_count > 0:
                self._save_compliance_records()
                self.logger.info(f"🧹 Limpieza completada: {cleaned_count} registros eliminados")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"❌ Error en limpieza: {e}")
            return 0