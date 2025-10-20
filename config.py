"""
Configuración para el procesador de facturas
"""

import json
import os
from typing import Any, Dict


def _load_settings() -> Dict[str, Any]:
    settings_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
    if not os.path.exists(settings_path):
        return {}

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


SETTINGS = _load_settings()


# Patrones de regex para extracción de datos de PDF
PDF_PATTERNS = {
    'fecha': [
        r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Fecha de emisión[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    ],
    'cliente': [
        r'Cliente[:\s]+(.+)',
        r'Customer[:\s]+(.+)',
        r'Facturar a[:\s]+(.+)',
        r'Bill to[:\s]+(.+)',
        r'Razón Social[:\s]+(.+)',
        r'Nombre[:\s]+(.+)'
    ],
    'total': [
        r'Total[:\s]+\$?([\d,]+\.?\d*)',
        r'Amount[:\s]+\$?([\d,]+\.?\d*)',
        r'Subtotal[:\s]+\$?([\d,]+\.?\d*)',
        r'Importe Total[:\s]+\$?([\d,]+\.?\d*)',
        r'Total a Pagar[:\s]+\$?([\d,]+\.?\d*)'
    ],
    'iva': [
        r'IVA[:\s]+\$?([\d,]+\.?\d*)',
        r'Impuesto[:\s]+\$?([\d,]+\.?\d*)',
        r'Tax[:\s]+\$?([\d,]+\.?\d*)',
        r'19%[:\s]+\$?([\d,]+\.?\d*)'
    ],
    'retenciones': [
        r'Retención[:\s]+\$?([\d,]+\.?\d*)',
        r'Retenido[:\s]+\$?([\d,]+\.?\d*)',
        r'Retention[:\s]+\$?([\d,]+\.?\d*)',
        r'Rete[:\s]+\$?([\d,]+\.?\d*)'
    ],
    'nit_proveedor': [
        r'NIT[:\s]+(\d+[-]?\d*)',
        r'Nit[:\s]+(\d+[-]?\d*)',
        r'Tax ID[:\s]+(\d+[-]?\d*)',
        r'Identificación[:\s]+(\d+[-]?\d*)'
    ],
    'numero_factura': [
        r'Factura[:\s]+#?(\d+)',
        r'Invoice[:\s]+#?(\d+)',
        r'Número[:\s]+(\d+)',
        r'No[.\s]+(\d+)'
    ],
    'items': {
        'start_markers': [
            'descripción', 'descripcion', 'item', 'concepto', 'producto',
            'servicio', 'cantidad', 'precio', 'importe'
        ],
        'end_markers': [
            'subtotal', 'total', 'impuestos', 'iva', 'descuento'
        ]
    }
}

# Configuración de XML namespaces
XML_NAMESPACES = {
    'cfdi': 'http://www.sat.gob.mx/cfd/3',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'dian': 'http://www.dian.gov.co/servicios/facturaelectronica/v1',
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}

# Configuración de Alegra
ALEGRA_CONFIG = SETTINGS.get('alegra', {
    'base_url': 'https://api.alegra.com/api/v1',
    'timeout': 30,
    'max_retries': 3,
    'default_due_days': 30
})

# Configuración de logging
LOGGING_CONFIG = SETTINGS.get('logging', {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'file': 'invoice_processor.log',
    'max_size': 10485760,  # 10MB
    'backup_count': 5
})

# Configuración de monitoreo de carpetas
FOLDER_MONITOR_CONFIG = SETTINGS.get('folder_monitor', {
    'recursive': False,
    'ignore_patterns': ['.tmp', '~', '.DS_Store', 'Thumbs.db'],
    'process_delay': 1  # segundos
})


NANOBOT_CONFIG = SETTINGS.get('nanobot', {
    'enabled': False,
    'host': 'http://localhost:8080',
    'classifier_agent': 'invoice_classifier',
    'triage_agent': 'invoice_triage',
    'confidence_threshold': 0.75,
    'triage_on_api_error': True
})


def _load_accounting_config() -> Dict[str, Any]:
    accounting_path = os.path.join(os.path.dirname(__file__), 'config', 'accounting_accounts.json')
    if not os.path.exists(accounting_path):
        return {}

    try:
        with open(accounting_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


ACCOUNTING_CONFIG = _load_accounting_config()


def _load_tax_rules() -> Dict[str, Any]:
    """Cargar reglas fiscales desde archivo JSON"""
    tax_rules_path = os.path.join(os.path.dirname(__file__), 'config', 'tax_rules.json')
    if not os.path.exists(tax_rules_path):
        return {}
    
    try:
        with open(tax_rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


TAX_RULES = _load_tax_rules()