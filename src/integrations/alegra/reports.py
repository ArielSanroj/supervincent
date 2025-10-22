#!/usr/bin/env python3
"""
Módulo para generación de reportes de Alegra
Consolida funcionalidad de alegra_reports.py y alegra_reports_backup.py
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from pathlib import Path

from .client import AlegraClient
from .models import AlegraResponse

class AlegraReports:
    """
    Generador de reportes de Alegra con funcionalidades consolidadas
    """
    
    def __init__(self, client: AlegraClient):
        """
        Inicializar generador de reportes
        
        Args:
            client: Cliente de Alegra configurado
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        
        # Configuración de reportes
        self.reports_config = {
            'general_ledger': {
                'endpoint': 'reports/general-ledger',
                'default_params': {
                    'startDate': None,
                    'endDate': None,
                    'account': None
                }
            },
            'trial_balance': {
                'endpoint': 'reports/trial-balance',
                'default_params': {
                    'startDate': None,
                    'endDate': None,
                    'level': 1
                }
            },
            'journal': {
                'endpoint': 'reports/journal',
                'default_params': {
                    'startDate': None,
                    'endDate': None,
                    'account': None
                }
            },
            'auxiliary_ledgers': {
                'endpoint': 'reports/auxiliary-ledgers',
                'default_params': {
                    'startDate': None,
                    'endDate': None,
                    'account': None
                }
            }
        }
    
    def generate_general_ledger(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        account: Optional[str] = None,
        save_to_file: bool = True,
        output_dir: str = "reports"
    ) -> Dict[str, Any]:
        """
        Generar reporte de mayor general
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            account: Cuenta específica (opcional)
            save_to_file: Guardar en archivo
            output_dir: Directorio de salida
            
        Returns:
            Datos del reporte
        """
        try:
            params = {
                'startDate': self._format_date(start_date),
                'endDate': self._format_date(end_date)
            }
            
            if account:
                params['account'] = account
            
            self.logger.info("Generando reporte de mayor general", extra={
                "start_date": params['startDate'],
                "end_date": params['endDate'],
                "account": account
            })
            
            result = self.client._make_request('GET', 'reports/general-ledger', params=params)
            
            if save_to_file:
                filename = f"mayor_general_{params['startDate']}_{params['endDate']}.json"
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info("Reporte guardado en archivo", extra={"filepath": str(filepath)})
            
            return {
                'success': True,
                'data': result,
                'summary': self._summarize_general_ledger(result),
                'filepath': str(filepath) if save_to_file else None
            }
            
        except Exception as e:
            self.logger.error("Error generando mayor general", extra={"error": str(e)})
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def generate_trial_balance(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        level: int = 1,
        save_to_file: bool = True,
        output_dir: str = "reports"
    ) -> Dict[str, Any]:
        """
        Generar reporte de balance de prueba
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            level: Nivel de detalle (1-5)
            save_to_file: Guardar en archivo
            output_dir: Directorio de salida
            
        Returns:
            Datos del reporte
        """
        try:
            params = {
                'startDate': self._format_date(start_date),
                'endDate': self._format_date(end_date),
                'level': level
            }
            
            self.logger.info("Generando balance de prueba", extra={
                "start_date": params['startDate'],
                "end_date": params['endDate'],
                "level": level
            })
            
            result = self.client._make_request('GET', 'reports/trial-balance', params=params)
            
            if save_to_file:
                filename = f"balance_prueba_{params['startDate']}_{params['endDate']}_nivel{level}.json"
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info("Reporte guardado en archivo", extra={"filepath": str(filepath)})
            
            return {
                'success': True,
                'data': result,
                'summary': self._summarize_trial_balance(result),
                'filepath': str(filepath) if save_to_file else None
            }
            
        except Exception as e:
            self.logger.error("Error generando balance de prueba", extra={"error": str(e)})
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def generate_journal(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        account: Optional[str] = None,
        save_to_file: bool = True,
        output_dir: str = "reports"
    ) -> Dict[str, Any]:
        """
        Generar reporte de diario
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            account: Cuenta específica (opcional)
            save_to_file: Guardar en archivo
            output_dir: Directorio de salida
            
        Returns:
            Datos del reporte
        """
        try:
            params = {
                'startDate': self._format_date(start_date),
                'endDate': self._format_date(end_date)
            }
            
            if account:
                params['account'] = account
            
            self.logger.info("Generando reporte de diario", extra={
                "start_date": params['startDate'],
                "end_date": params['endDate'],
                "account": account
            })
            
            result = self.client._make_request('GET', 'reports/journal', params=params)
            
            if save_to_file:
                filename = f"diario_{params['startDate']}_{params['endDate']}.json"
                if account:
                    filename = f"diario_{params['startDate']}_{params['endDate']}_cuenta{account}.json"
                
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info("Reporte guardado en archivo", extra={"filepath": str(filepath)})
            
            return {
                'success': True,
                'data': result,
                'summary': self._summarize_journal(result),
                'filepath': str(filepath) if save_to_file else None
            }
            
        except Exception as e:
            self.logger.error("Error generando diario", extra={"error": str(e)})
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def generate_auxiliary_ledgers(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        account: Optional[str] = None,
        save_to_file: bool = True,
        output_dir: str = "reports"
    ) -> Dict[str, Any]:
        """
        Generar reporte de auxiliares
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            account: Cuenta específica (opcional)
            save_to_file: Guardar en archivo
            output_dir: Directorio de salida
            
        Returns:
            Datos del reporte
        """
        try:
            params = {
                'startDate': self._format_date(start_date),
                'endDate': self._format_date(end_date)
            }
            
            if account:
                params['account'] = account
            
            self.logger.info("Generando auxiliares", extra={
                "start_date": params['startDate'],
                "end_date": params['endDate'],
                "account": account
            })
            
            result = self.client._make_request('GET', 'reports/auxiliary-ledgers', params=params)
            
            if save_to_file:
                filename = f"auxiliares_{params['startDate']}_{params['endDate']}.json"
                if account:
                    filename = f"auxiliares_{params['startDate']}_{params['endDate']}_cuenta{account}.json"
                
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info("Reporte guardado en archivo", extra={"filepath": str(filepath)})
            
            return {
                'success': True,
                'data': result,
                'summary': self._summarize_auxiliary_ledgers(result),
                'filepath': str(filepath) if save_to_file else None
            }
            
        except Exception as e:
            self.logger.error("Error generando auxiliares", extra={"error": str(e)})
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def generate_all_reports(
        self,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        output_dir: str = "reports"
    ) -> Dict[str, Any]:
        """
        Generar todos los reportes disponibles
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            output_dir: Directorio de salida
            
        Returns:
            Resumen de todos los reportes generados
        """
        try:
            self.logger.info("Generando todos los reportes", extra={
                "start_date": self._format_date(start_date),
                "end_date": self._format_date(end_date)
            })
            
            results = {}
            
            # Mayor general
            results['general_ledger'] = self.generate_general_ledger(
                start_date, end_date, save_to_file=True, output_dir=output_dir
            )
            
            # Balance de prueba
            results['trial_balance'] = self.generate_trial_balance(
                start_date, end_date, save_to_file=True, output_dir=output_dir
            )
            
            # Diario
            results['journal'] = self.generate_journal(
                start_date, end_date, save_to_file=True, output_dir=output_dir
            )
            
            # Auxiliares
            results['auxiliary_ledgers'] = self.generate_auxiliary_ledgers(
                start_date, end_date, save_to_file=True, output_dir=output_dir
            )
            
            # Resumen
            summary = {
                'total_reports': len(results),
                'successful_reports': sum(1 for r in results.values() if r.get('success', False)),
                'failed_reports': sum(1 for r in results.values() if not r.get('success', False)),
                'generated_files': [
                    r.get('filepath') for r in results.values() 
                    if r.get('success', False) and r.get('filepath')
                ]
            }
            
            self.logger.info("Todos los reportes generados", extra=summary)
            
            return {
                'success': True,
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            self.logger.error("Error generando todos los reportes", extra={"error": str(e)})
            return {
                'success': False,
                'error': str(e),
                'results': {}
            }
    
    def _format_date(self, date_input: Union[str, date, datetime]) -> str:
        """Formatear fecha para Alegra API"""
        if isinstance(date_input, str):
            return date_input
        
        if isinstance(date_input, datetime):
            return date_input.strftime('%Y-%m-%d')
        
        if isinstance(date_input, date):
            return date_input.strftime('%Y-%m-%d')
        
        raise ValueError(f"Formato de fecha no soportado: {type(date_input)}")
    
    def _summarize_general_ledger(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear resumen del mayor general"""
        if not data or 'data' not in data:
            return {'error': 'No hay datos para resumir'}
        
        accounts = data.get('data', [])
        
        return {
            'total_accounts': len(accounts),
            'total_debits': sum(account.get('debit', 0) for account in accounts),
            'total_credits': sum(account.get('credit', 0) for account in accounts),
            'balance': sum(account.get('balance', 0) for account in accounts)
        }
    
    def _summarize_trial_balance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear resumen del balance de prueba"""
        if not data or 'data' not in data:
            return {'error': 'No hay datos para resumir'}
        
        accounts = data.get('data', [])
        
        return {
            'total_accounts': len(accounts),
            'total_debits': sum(account.get('debit', 0) for account in accounts),
            'total_credits': sum(account.get('credit', 0) for account in accounts),
            'is_balanced': abs(sum(account.get('debit', 0) for account in accounts) - 
                              sum(account.get('credit', 0) for account in accounts)) < 0.01
        }
    
    def _summarize_journal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear resumen del diario"""
        if not data or 'data' not in data:
            return {'error': 'No hay datos para resumir'}
        
        entries = data.get('data', [])
        
        return {
            'total_entries': len(entries),
            'total_debits': sum(entry.get('debit', 0) for entry in entries),
            'total_credits': sum(entry.get('credit', 0) for entry in entries),
            'date_range': {
                'start': min(entry.get('date', '') for entry in entries) if entries else None,
                'end': max(entry.get('date', '') for entry in entries) if entries else None
            }
        }
    
    def _summarize_auxiliary_ledgers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear resumen de auxiliares"""
        if not data or 'data' not in data:
            return {'error': 'No hay datos para resumir'}
        
        ledgers = data.get('data', [])
        
        return {
            'total_ledgers': len(ledgers),
            'total_entries': sum(len(ledger.get('entries', [])) for ledger in ledgers),
            'accounts_with_activity': len([l for l in ledgers if l.get('entries')])
        }