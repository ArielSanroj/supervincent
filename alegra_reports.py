#!/usr/bin/env python3
"""
Módulo para generar reportes contables y ledgers desde Alegra
"""

import requests
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AlegraReports:
    """Generador de reportes contables desde Alegra"""
    
    def __init__(self):
        self.alegra_email = os.getenv('ALEGRA_USER')
        self.alegra_token = os.getenv('ALEGRA_TOKEN')
        self.base_url = "https://api.alegra.com/api/v1"
        
        if not self.alegra_email or not self.alegra_token:
            raise ValueError("Faltan credenciales de Alegra en .env")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación para Alegra"""
        credentials = f"{self.alegra_email}:{self.alegra_token}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
    
    def generate_ledger_report(self, start_date: str, end_date: str, 
                             report_type: str = 'general-ledger',
                             account_id: Optional[str] = None) -> Optional[Dict]:
        """
        Generar reporte de ledger desde Alegra
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            report_type: Tipo de reporte (general-ledger, trial-balance, journal)
            account_id: ID de cuenta específica (opcional)
        """
        logger = logging.getLogger(__name__)
        logger.info(f"📊 Generando reporte {report_type} desde {start_date} hasta {end_date}")
        
        headers = self.get_auth_headers()
        
        # Mapear tipos de reporte a endpoints de Alegra
        report_endpoints = {
            'general-ledger': 'reports/general-ledger',
            'trial-balance': 'reports/trial-balance',
            'journal': 'reports/journal'
        }
        
        if report_type not in report_endpoints:
            logger.error(f"❌ Tipo de reporte no válido: {report_type}")
            return None
        
        endpoint = report_endpoints[report_type]
        
        # Parámetros de consulta
        params = {
            'startDate': start_date,
            'endDate': end_date
        }
        
        if account_id:
            params['accountId'] = account_id
        
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                report_data = response.json()
                logger.info(f"✅ Reporte {report_type} generado exitosamente")
                
                # Guardar reporte en archivo
                self._save_report_to_file(report_data, report_type, start_date, end_date)
                
                # Mostrar resumen
                self._display_report_summary(report_data, report_type)
                
                return report_data
            else:
                logger.error(f"❌ Error generando reporte: {response.status_code}")
                logger.error(f"📝 Respuesta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en API Alegra: {e}")
            return None
    
    def generate_aging_report(self, start_date: str, end_date: str) -> Optional[Dict]:
        """Generar reporte de aging de cuentas por cobrar y pagar"""
        logger = logging.getLogger(__name__)
        logger.info(f"📊 Generando reporte de aging desde {start_date} hasta {end_date}")
        
        headers = self.get_auth_headers()
        
        try:
            # Obtener facturas pendientes
            invoices_response = requests.get(
                f"{self.base_url}/invoices",
                params={
                    'status': 'open',
                    'startDate': start_date,
                    'endDate': end_date
                },
                headers=headers,
                timeout=30
            )
            
            bills_response = requests.get(
                f"{self.base_url}/bills",
                params={
                    'status': 'open',
                    'startDate': start_date,
                    'endDate': end_date
                },
                headers=headers,
                timeout=30
            )
            
            if invoices_response.status_code == 200 and bills_response.status_code == 200:
                invoices = invoices_response.json()
                bills = bills_response.json()
                
                # Calcular aging
                aging_data = self._calculate_aging(invoices, bills, start_date)
                
                # Guardar reporte
                report_data = {
                    'report_type': 'aging',
                    'period': {'start': start_date, 'end': end_date},
                    'generated_at': datetime.now().isoformat(),
                    'data': aging_data
                }
                
                self._save_report(report_data, 'aging')
                return report_data
            else:
                logger.error(f"❌ Error obteniendo datos: Invoices {invoices_response.status_code}, Bills {bills_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generando aging: {e}")
            return None
    
    def generate_cash_flow_report(self, start_date: str, end_date: str) -> Optional[Dict]:
        """Generar reporte básico de flujo de caja"""
        logger = logging.getLogger(__name__)
        logger.info(f"📊 Generando reporte de flujo de caja desde {start_date} hasta {end_date}")
        
        headers = self.get_auth_headers()
        
        try:
            # Obtener ingresos (invoices pagadas)
            income_response = requests.get(
                f"{self.base_url}/invoices",
                params={
                    'status': 'closed',
                    'startDate': start_date,
                    'endDate': end_date
                },
                headers=headers,
                timeout=30
            )
            
            # Obtener gastos (bills pagadas)
            expenses_response = requests.get(
                f"{self.base_url}/bills",
                params={
                    'status': 'closed',
                    'startDate': start_date,
                    'endDate': end_date
                },
                headers=headers,
                timeout=30
            )
            
            if income_response.status_code == 200 and expenses_response.status_code == 200:
                income_data = income_response.json()
                expense_data = expenses_response.json()
                
                # Calcular flujo de caja
                cash_flow = self._calculate_cash_flow(income_data, expense_data)
                
                # Guardar reporte
                report_data = {
                    'report_type': 'cash_flow',
                    'period': {'start': start_date, 'end': end_date},
                    'generated_at': datetime.now().isoformat(),
                    'data': cash_flow
                }
                
                self._save_report(report_data, 'cash_flow')
                return report_data
            else:
                logger.error(f"❌ Error obteniendo datos: Income {income_response.status_code}, Expenses {expenses_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generando flujo de caja: {e}")
            return None
    
    def _calculate_aging(self, invoices: List[Dict], bills: List[Dict], start_date: str) -> Dict:
        """Calcular aging de cuentas por cobrar y pagar"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        aging_buckets = {
            'current': 0,      # 0-30 días
            '31_60': 0,        # 31-60 días
            '61_90': 0,        # 61-90 días
            'over_90': 0       # Más de 90 días
        }
        
        # Aging de cuentas por cobrar (invoices)
        receivables = {'total': 0, 'aging': aging_buckets.copy()}
        for invoice in invoices:
            if invoice.get('status') == 'open':
                due_date = datetime.strptime(invoice.get('dueDate', invoice.get('date')), '%Y-%m-%d').date()
                days_overdue = (today - due_date).days
                amount = float(invoice.get('total', 0))
                
                receivables['total'] += amount
                
                if days_overdue <= 30:
                    receivables['aging']['current'] += amount
                elif days_overdue <= 60:
                    receivables['aging']['31_60'] += amount
                elif days_overdue <= 90:
                    receivables['aging']['61_90'] += amount
                else:
                    receivables['aging']['over_90'] += amount
        
        # Aging de cuentas por pagar (bills)
        payables = {'total': 0, 'aging': aging_buckets.copy()}
        for bill in bills:
            if bill.get('status') == 'open':
                due_date = datetime.strptime(bill.get('dueDate', bill.get('date')), '%Y-%m-%d').date()
                days_overdue = (today - due_date).days
                amount = float(bill.get('total', 0))
                
                payables['total'] += amount
                
                if days_overdue <= 30:
                    payables['aging']['current'] += amount
                elif days_overdue <= 60:
                    payables['aging']['31_60'] += amount
                elif days_overdue <= 90:
                    payables['aging']['61_90'] += amount
                else:
                    payables['aging']['over_90'] += amount
        
        return {
            'receivables': receivables,
            'payables': payables,
            'net_position': receivables['total'] - payables['total']
        }
    
    def _calculate_cash_flow(self, income_data: List[Dict], expense_data: List[Dict]) -> Dict:
        """Calcular flujo de caja básico"""
        total_income = sum(float(invoice.get('total', 0)) for invoice in income_data)
        total_expenses = sum(float(bill.get('total', 0)) for bill in expense_data)
        
        net_cash_flow = total_income - total_expenses
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_cash_flow': net_cash_flow,
            'income_count': len(income_data),
            'expense_count': len(expense_data)
        }
    
    def _save_report(self, report_data: Dict, report_type: str) -> None:
        """Guardar reporte en archivo JSON"""
        import os
        from datetime import datetime
        logger = logging.getLogger(__name__)
        
        # Crear directorio de reportes si no existe
        reports_dir = 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        
        # Nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{reports_dir}/{report_type}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 Reporte guardado: {filename}")
            
            # También mostrar resumen en consola
            self._print_report_summary(report_data, report_type)
            
        except Exception as e:
            logger.error(f"❌ Error guardando reporte: {e}")
    
    def _print_report_summary(self, report_data: Dict, report_type: str) -> None:
        """Imprimir resumen del reporte en consola"""
        print(f"\n📊 RESUMEN DEL REPORTE {report_type.upper()}")
        print("=" * 50)
        
        if report_type == 'aging':
            data = report_data['data']
            print(f"💰 Cuentas por Cobrar: ${data['receivables']['total']:,.2f}")
            print(f"💸 Cuentas por Pagar: ${data['payables']['total']:,.2f}")
            print(f"📈 Posición Neta: ${data['net_position']:,.2f}")
            
        elif report_type == 'cash_flow':
            data = report_data['data']
            print(f"📈 Ingresos Totales: ${data['total_income']:,.2f}")
            print(f"📉 Gastos Totales: ${data['total_expenses']:,.2f}")
            print(f"💰 Flujo de Caja Neto: ${data['net_cash_flow']:,.2f}")
            
        print("=" * 50)
    
    def _save_report_to_file(self, report_data: Dict, report_type: str, 
                           start_date: str, end_date: str) -> None:
        """Guardar reporte en archivo JSON"""
        logger = logging.getLogger(__name__)
        
        # Crear directorio de reportes si no existe
        os.makedirs('reports', exist_ok=True)
        
        # Nombre del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/{report_type}_{start_date}_{end_date}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"📁 Reporte guardado en: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando reporte: {e}")
    
    def _display_report_summary(self, report_data: Dict, report_type: str) -> None:
        """Mostrar resumen del reporte en consola"""
        logger = logging.getLogger(__name__)
        
        print(f"\n📊 RESUMEN DEL REPORTE {report_type.upper()}")
        print("=" * 50)
        
        if report_type == 'general-ledger':
            if 'data' in report_data:
                entries = report_data['data']
                print(f"📋 Total de entradas: {len(entries)}")
                
                if entries:
                    # Mostrar primeras 5 entradas
                    print("\n🔍 Primeras 5 entradas:")
                    for i, entry in enumerate(entries[:5]):
                        print(f"  {i+1}. {entry.get('date', 'N/A')} - {entry.get('description', 'N/A')} - ${entry.get('debit', 0):,.2f} / ${entry.get('credit', 0):,.2f}")
        
        elif report_type == 'trial-balance':
            if 'data' in report_data:
                accounts = report_data['data']
                print(f"📋 Total de cuentas: {len(accounts)}")
                
                if accounts:
                    # Mostrar primeras 5 cuentas
                    print("\n🔍 Primeras 5 cuentas:")
                    for i, account in enumerate(accounts[:5]):
                        print(f"  {i+1}. {account.get('name', 'N/A')} - Debe: ${account.get('debit', 0):,.2f} - Haber: ${account.get('credit', 0):,.2f}")
        
        elif report_type == 'journal':
            if 'data' in report_data:
                entries = report_data['data']
                print(f"📋 Total de asientos: {len(entries)}")
                
                if entries:
                    # Mostrar primeras 5 asientos
                    print("\n🔍 Primeras 5 asientos:")
                    for i, entry in enumerate(entries[:5]):
                        print(f"  {i+1}. {entry.get('date', 'N/A')} - {entry.get('description', 'N/A')} - ${entry.get('total', 0):,.2f}")
        
        print("=" * 50)

def main():
    """Función principal para ejecutar reportes desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de reportes contables')
    parser.add_argument('--start-date', required=True, help='Fecha de inicio (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='Fecha de fin (YYYY-MM-DD)')
    parser.add_argument('--report-type', choices=['general-ledger', 'trial-balance', 'journal', 'aging', 'cash-flow'], 
                       default='general-ledger', help='Tipo de reporte')
    parser.add_argument('--account-id', help='ID de cuenta específica (opcional)')
    
    args = parser.parse_args()
    
    try:
        reporter = AlegraReports()
        
        if args.report_type in ['aging', 'cash-flow']:
            if args.report_type == 'aging':
                result = reporter.generate_aging_report(args.start_date, args.end_date)
            else:
                result = reporter.generate_cash_flow_report(args.start_date, args.end_date)
        else:
            result = reporter.generate_ledger_report(
                args.start_date, 
                args.end_date, 
                args.report_type,
                args.account_id
            )
        
        if result:
            print("\n✅ Reporte generado exitosamente!")
        else:
            print("\n❌ Error generando reporte")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()