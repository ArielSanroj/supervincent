"""
Constants and configuration for financial analysis.
"""

MONTH_ORDER = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
    'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'
]

MONTH_INDEX = {m: i for i, m in enumerate(MONTH_ORDER)}

DEFAULT_BUDGET = {
    'ingresos_mensual': 100_000_000,
    'gastos_mensual': 125_000_000
}

DEFAULT_EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'arielsanroj@carmanfe.com.co',
    'sender_password': 'jxxu siui wmfp dklj',
    'recipient_email': 'arielsanroj@carmanfe.com.co'
}

# Balance sheet column names
BALANCE_COLUMNS = [
    'Nivel', 'Codigo cuenta contable', 'Nombre cuenta contable',
    'Saldo inicial', 'Movimiento debito', 'Movimiento credito', 'Saldo final'
]
