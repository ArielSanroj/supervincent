"""
Financial metrics calculation module.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

from .constants import DEFAULT_BUDGET

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates financial metrics and KPIs."""

    def __init__(self, budget_data: Dict = None):
        self.budget_data = budget_data or DEFAULT_BUDGET

    def calculate_metrics(self, data: Dict) -> Dict:
        """Calculate main financial metrics."""
        if not data:
            raise ValueError("No financial data provided")

        current_month = data['current_month']
        current_month_col = f"{current_month} DE 2025"

        if current_month_col not in data['eri'].columns:
            current_month_col = data['eri'].columns[-1]

        actual_ingresos = self._extract_income(data)
        gastos_breakdown, actual_total_gastos = self._calculate_expenses(data, current_month_col)

        kpis = self._calculate_kpis(data, actual_ingresos, actual_total_gastos)

        ejecutado_ingresos_pct = (
            (actual_ingresos / self.budget_data['ingresos_mensual']) * 100
            if actual_ingresos > 0 else 0
        )
        ejecutado_gastos_pct = (
            (actual_total_gastos / self.budget_data['gastos_mensual']) * 100
            if actual_total_gastos > 0 else 0
        )

        metrics = {
            'current_month': current_month,
            'ingresos': actual_ingresos,
            'gastos_totales': actual_total_gastos,
            'gastos_breakdown': gastos_breakdown,
            'presupuesto_ejecutado': {
                'ingresos_pct': ejecutado_ingresos_pct,
                'gastos_pct': ejecutado_gastos_pct
            },
            'kpis': kpis
        }

        logger.info(f"Metrics calculated for {current_month}")
        return metrics

    def _extract_income(self, data: Dict) -> float:
        """Extract income from data."""
        try:
            ingresos_row = data['resultado'].loc[
                data['resultado']['Descripcion'].str.contains(
                    'INGRESOS ORDINARIOS', case=False, na=False
                )
            ]
            return ingresos_row.iloc[0, 1] if not ingresos_row.empty else 0
        except Exception:
            return 0

    def _calculate_expenses(self, data: Dict, month_col: str) -> tuple:
        """Calculate expenses by category."""
        try:
            eri = data['eri']
            mask_admin = eri['Codigo'].str.match(r'^51[0-9]{4,}', na=False) & (eri[month_col] != 0)
            mask_otros = eri['Codigo'].str.match(r'^53[0-9]{4,}', na=False) & (eri[month_col] != 0)
            mask_venta = eri['Codigo'].str.match(r'^61[0-9]{4,}', na=False) & (eri[month_col] != 0)
            mask_prod = eri['Codigo'].str.match(r'^(72|73)[0-9]{4,}', na=False) & (eri[month_col] != 0)

            gastos_admin = eri[mask_admin][month_col].sum()
            gastos_otros = eri[mask_otros][month_col].sum()
            costos_venta = eri[mask_venta][month_col].sum()
            costos_prod = eri[mask_prod][month_col].sum()
            total = gastos_admin + gastos_otros + costos_venta + costos_prod

            breakdown = {
                'administrativos': gastos_admin,
                'otros': gastos_otros,
                'costos_venta': costos_venta,
                'costos_produccion': costos_prod
            }

            return breakdown, total
        except Exception as e:
            logger.error(f"Error calculating expenses: {e}")
            return {'administrativos': 0, 'otros': 0, 'costos_venta': 0, 'costos_produccion': 0}, 0

    def _calculate_kpis(self, data: Dict, ingresos: float, gastos: float) -> Dict:
        """Calculate financial KPIs."""
        try:
            balance = data['balance']
            resultado = data['resultado']
            eri = data['eri']
            current_month_col = f"{data['current_month']} DE 2025"

            total_assets = self._get_class_value(balance, '1')
            activos_corrientes = self._get_current_assets(balance)
            inventarios = self._get_group_value(balance, '14')
            pasivos_corrientes = abs(self._get_class_value(balance, '2'))
            patrimonio = abs(self._get_class_value(balance, '3')) or (total_assets - pasivos_corrientes)

            utilidad = self._get_result_value(resultado, 'RESULTADO DEL EJERCICIO')
            costos = self._get_result_value(resultado, 'COSTO DE VENTA')

            depreciacion = eri[eri['Codigo'].str.match(r'^51[0-9]{4}', na=False)][current_month_col].sum()
            intereses = eri[eri['Codigo'].str.match(r'^530520.*', na=False)][current_month_col].sum()

            current_ratio = activos_corrientes / pasivos_corrientes if pasivos_corrientes else 0
            quick_ratio = (activos_corrientes - inventarios) / pasivos_corrientes if pasivos_corrientes else 0
            margen_bruto = ((ingresos - costos) / ingresos) * 100 if ingresos else 0
            margen_neto = (utilidad / ingresos) * 100 if ingresos else 0
            roe = (utilidad / patrimonio) * 100 if patrimonio else 0
            deuda_patrimonio = pasivos_corrientes / patrimonio if patrimonio else 0
            rotacion_inventarios = costos / inventarios if inventarios else 0
            ebitda = utilidad + depreciacion + intereses

            return {
                'current_ratio': current_ratio,
                'quick_ratio': quick_ratio,
                'margen_bruto': margen_bruto,
                'margen_neto': margen_neto,
                'roe': roe,
                'deuda_patrimonio': deuda_patrimonio,
                'rotacion_inventarios': rotacion_inventarios,
                'ebitda': ebitda,
                'total_assets': total_assets,
                'activos_corrientes': activos_corrientes,
                'pasivos_corrientes': pasivos_corrientes,
                'patrimonio': patrimonio,
                'utilidad_neta': utilidad
            }
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}

    def _get_class_value(self, balance: pd.DataFrame, class_code: str) -> float:
        """Get value for a balance class."""
        row = balance[(balance['Nivel'] == 'Clase') & (balance['Codigo cuenta contable'] == class_code)]
        return row['Saldo final'].iloc[0] if not row.empty else 0

    def _get_group_value(self, balance: pd.DataFrame, group_code: str) -> float:
        """Get value for a balance group."""
        row = balance[(balance['Nivel'] == 'Grupo') & (balance['Codigo cuenta contable'] == group_code)]
        return row['Saldo final'].iloc[0] if not row.empty else 0

    def _get_current_assets(self, balance: pd.DataFrame) -> float:
        """Get total current assets."""
        current_groups = ['11', '12', '13', '14']
        return balance[
            (balance['Nivel'] == 'Grupo') &
            balance['Codigo cuenta contable'].isin(current_groups)
        ]['Saldo final'].sum()

    def _get_result_value(self, resultado: pd.DataFrame, keyword: str) -> float:
        """Get value from income statement by keyword."""
        row = resultado[resultado['Descripcion'].str.contains(keyword, case=False, na=False)]
        return row.iloc[0, 1] if not row.empty else 0
