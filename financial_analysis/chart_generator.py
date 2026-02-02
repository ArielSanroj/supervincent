"""
Chart generation module for financial analysis.
"""

import os
import re
import logging
from typing import Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt

from .constants import MONTH_INDEX, DEFAULT_BUDGET

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generates financial charts and visualizations."""

    def __init__(self, reports_dir: str, budget_data: Dict = None):
        self.reports_dir = reports_dir
        self.budget_data = budget_data or DEFAULT_BUDGET
        os.makedirs(reports_dir, exist_ok=True)

    def generate_all_charts(self, metrics: Dict, data: Dict) -> List[str]:
        """Generate all financial charts."""
        month_lower = metrics['current_month'].lower()
        chart_files = []

        try:
            chart_files.append(self._generate_monthly_spending_chart(data, month_lower))
            chart_files.append(self._generate_kpi_dashboard(metrics, month_lower))
            chart_files.append(self._generate_expense_distribution_chart(metrics, month_lower))
            chart_files.append(self._generate_comprehensive_dashboard(metrics, month_lower))
        except Exception as e:
            logger.error(f"Error generating charts: {e}")

        return [f for f in chart_files if f]

    def _generate_monthly_spending_chart(self, data: Dict, month_lower: str) -> Optional[str]:
        """Generate monthly spending chart."""
        try:
            eri = data['eri']
            months = [col for col in eri.columns if re.match(r'^\w+ DE 2025$', str(col))]
            months_sorted = sorted(months, key=lambda x: MONTH_INDEX.get(x.split(' DE')[0], 99))

            total_spending = []
            for month in months_sorted:
                mask = eri['Codigo'].str.match(r'^(51|53|61|72|73)[0-9]{4,}', na=False) & (eri[month] != 0)
                total_spending.append(eri[mask][month].sum())

            plt.figure(figsize=(12, 6))
            plt.bar(months_sorted, total_spending, color='skyblue')
            plt.title(f'Gastos Mensuales - Enero a {data["current_month"]} 2025')
            plt.xlabel('Mes')
            plt.ylabel('Gastos Totales (COP)')
            plt.xticks(rotation=45)
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            file_path = os.path.join(self.reports_dir, f"gastos_mensuales_{month_lower}_2025.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close()
            return file_path
        except Exception as e:
            logger.error(f"Error generating monthly chart: {e}")
        return None

    def _generate_kpi_dashboard(self, metrics: Dict, month_lower: str) -> Optional[str]:
        """Generate KPI dashboard chart."""
        try:
            current_month = metrics['current_month']
            kpis = metrics['kpis']

            kpi_names = [
                'Current Ratio', 'Quick Ratio', 'Margen Bruto %', 'Margen Neto %',
                'ROE %', 'Deuda/Patrimonio', 'Rotacion Inventarios', 'EBITDA'
            ]
            kpi_values = [
                kpis.get('current_ratio', 0),
                kpis.get('quick_ratio', 0),
                kpis.get('margen_bruto', 0),
                kpis.get('margen_neto', 0),
                kpis.get('roe', 0),
                kpis.get('deuda_patrimonio', 0),
                kpis.get('rotacion_inventarios', 0),
                kpis.get('ebitda', 0)
            ]

            plt.figure(figsize=(10, 6))
            plt.bar(kpi_names, kpi_values, color='teal')
            plt.title(f'KPIs Financieros - {current_month} 2025')
            plt.xlabel('KPI')
            plt.ylabel('Valor')
            plt.xticks(rotation=45, ha='right')
            plt.grid(axis='y', linestyle='--', alpha=0.7)

            file_path = os.path.join(self.reports_dir, f"kpi_dashboard_{month_lower}_2025.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close()
            return file_path
        except Exception as e:
            logger.error(f"Error generating KPI dashboard: {e}")
        return None

    def _generate_expense_distribution_chart(self, metrics: Dict, month_lower: str) -> Optional[str]:
        """Generate expense distribution pie chart."""
        try:
            current_month = metrics['current_month']
            gastos_breakdown = metrics['gastos_breakdown']

            categories = []
            values = []
            for cat, val in gastos_breakdown.items():
                if val > 0:
                    categories.append(cat.replace('_', ' ').title())
                    values.append(val)

            if not values:
                return None

            plt.figure(figsize=(10, 8))
            colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
            wedges, texts, autotexts = plt.pie(
                values, labels=categories, autopct='%1.1f%%',
                colors=colors[:len(values)], startangle=90
            )

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            plt.title(f'Distribucion de Gastos - {current_month} 2025', fontsize=14, fontweight='bold')
            plt.axis('equal')

            file_path = os.path.join(self.reports_dir, f"distribucion_gastos_{month_lower}_2025.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close()
            return file_path
        except Exception as e:
            logger.error(f"Error generating expense distribution: {e}")
        return None

    def _generate_comprehensive_dashboard(self, metrics: Dict, month_lower: str) -> Optional[str]:
        """Generate comprehensive dashboard."""
        try:
            current_month = metrics['current_month']

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # Budget vs Actual
            categories = ['Ingresos', 'Gastos']
            budget_values = [self.budget_data['ingresos_mensual'], self.budget_data['gastos_mensual']]
            actual_values = [metrics['ingresos'], metrics['gastos_totales']]

            x = np.arange(len(categories))
            width = 0.35

            ax1.bar(x - width/2, budget_values, width, label='Presupuesto', color='lightgreen', alpha=0.8)
            ax1.bar(x + width/2, actual_values, width, label='Actual', color='lightcoral', alpha=0.8)
            ax1.set_xlabel('Categoria')
            ax1.set_ylabel('Valor (COP)')
            ax1.set_title('Presupuesto vs Actual')
            ax1.set_xticks(x)
            ax1.set_xticklabels(categories)
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # Main KPIs
            kpi_names = ['Current Ratio', 'Quick Ratio', 'Margen Bruto %', 'Margen Neto %']
            kpi_values = [
                metrics['kpis'].get('current_ratio', 0),
                metrics['kpis'].get('quick_ratio', 0),
                metrics['kpis'].get('margen_bruto', 0),
                metrics['kpis'].get('margen_neto', 0)
            ]

            ax2.bar(kpi_names, kpi_values, color='teal', alpha=0.7)
            ax2.set_title('KPIs Principales')
            ax2.set_ylabel('Valor')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)

            # Expense distribution
            gastos_breakdown = metrics['gastos_breakdown']
            categories_gastos = [k.replace('_', ' ').title() for k, v in gastos_breakdown.items() if v > 0]
            values_gastos = [v for v in gastos_breakdown.values() if v > 0]

            if values_gastos:
                ax3.pie(values_gastos, labels=categories_gastos, autopct='%1.1f%%', startangle=90)
                ax3.set_title('Distribucion de Gastos')

            # Executive summary
            ax4.axis('off')
            summary_text = f"""
            RESUMEN EJECUTIVO - {current_month} 2025

            Ingresos: ${metrics['ingresos']:,.0f}
            Gastos: ${metrics['gastos_totales']:,.0f}
            EBITDA: ${metrics['kpis'].get('ebitda', 0):,.0f}
            Current Ratio: {metrics['kpis'].get('current_ratio', 0):.2f}
            Margen Neto: {metrics['kpis'].get('margen_neto', 0):.1f}%
            """
            ax4.text(
                0.1, 0.5, summary_text, fontsize=12, verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.5)
            )

            plt.tight_layout()

            file_path = os.path.join(self.reports_dir, f"dashboard_completo_{month_lower}_2025.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=300)
            plt.close()
            return file_path
        except Exception as e:
            logger.error(f"Error generating comprehensive dashboard: {e}")
        return None
