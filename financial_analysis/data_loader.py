"""
Financial data loading module.
"""

import os
import re
import glob
import logging
from typing import Dict, Optional

import pandas as pd

from .constants import MONTH_ORDER, MONTH_INDEX, BALANCE_COLUMNS

logger = logging.getLogger(__name__)


class FinancialDataLoader:
    """Handles loading and parsing of financial Excel files."""

    def __init__(self, downloads_dir: str = None):
        self.downloads_dir = downloads_dir or os.path.expanduser("~/Downloads")

    def detect_latest_file(self) -> Optional[str]:
        """Detect the most recent financial file."""
        pattern = os.path.join(self.downloads_dir, "INFORME DE * APRU- 2025 .xls")
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"No financial file found with pattern: {pattern}")
            return None

        latest_file = max(files, key=os.path.getmtime)
        logger.info(f"Financial file detected: {latest_file}")
        return latest_file

    def extract_month_from_filename(self, filename: str) -> str:
        """Extract month from filename."""
        match = re.search(r'DE (\w+) APRU', filename)
        if not match:
            raise ValueError("Could not extract month from filename")
        return match.group(1).upper()

    def load_data(self, file_path: str) -> Dict:
        """Load financial data from Excel file."""
        try:
            xls = pd.ExcelFile(file_path)
            current_month = self.extract_month_from_filename(os.path.basename(file_path))

            logger.info(f"Loading financial data for {current_month}")
            logger.info(f"Available sheets: {xls.sheet_names}")

            data = {
                'balance_sheet_name': f'BALANCE {current_month}',
                'sheets': xls.sheet_names,
                'current_month': current_month,
                'file_path': file_path
            }

            if data['balance_sheet_name'] not in xls.sheet_names:
                raise ValueError(f"Sheet '{data['balance_sheet_name']}' not found")

            data['balance'] = self._read_balance_sheet(xls, data['balance_sheet_name'])
            data['eri'] = self._read_eri_sheet(xls)
            data['resultado'] = self._read_resultado_sheet(xls)
            data['extracto'] = self._read_extracto_sheet(xls)

            logger.info("Financial data loaded successfully")
            return data

        except Exception as e:
            logger.error(f"Error loading financial data: {e}")
            raise

    def _read_balance_sheet(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """Read balance sheet."""
        df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=4)

        expected_cols = BALANCE_COLUMNS
        if len(df.columns) >= len(expected_cols):
            df.columns = expected_cols + [f'Extra_{i}' for i in range(len(df.columns) - len(expected_cols))]
        else:
            df.columns = [f'Col_{i}' for i in range(len(df.columns))]

        df['Saldo final'] = pd.to_numeric(df['Saldo final'], errors='coerce').fillna(0)
        df['Nivel'] = df['Nivel'].astype(str).fillna('')

        return df

    def _read_eri_sheet(self, xls: pd.ExcelFile) -> pd.DataFrame:
        """Read ERI sheet."""
        df = pd.read_excel(xls, sheet_name='INFORME-ERI', skiprows=1)

        eri_month_cols = [col for col in df.columns if re.match(r'^\w+ DE 2025$', str(col))]
        eri_month_cols_sorted = sorted(
            eri_month_cols,
            key=lambda x: MONTH_INDEX.get(x.split(' DE')[0], 99)
        )

        if not eri_month_cols_sorted:
            eri_month_cols = [
                col for col in df.columns[2:-1]
                if col in [f"{m} DE 2025" for m in MONTH_ORDER]
            ]
            eri_month_cols_sorted = sorted(
                eri_month_cols,
                key=lambda x: MONTH_INDEX.get(x.split(' DE')[0], 99)
            )

        df.columns = ['COMPARATIVO MES', 'Nombre'] + list(df.columns[2:-1]) + ['OBSERVACIONES']
        df['Codigo'] = df['COMPARATIVO MES'].astype(str).fillna('')
        df['Nombre'] = df['Nombre'].astype(str).fillna('')
        df['Display Name'] = df.apply(
            lambda row: row['Nombre'] if row['Nombre'].strip() and row['Nombre'] != 'nan' else row['Codigo'],
            axis=1
        )

        for col in eri_month_cols_sorted:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    def _read_resultado_sheet(self, xls: pd.ExcelFile) -> pd.DataFrame:
        """Read income statement sheet."""
        df = pd.read_excel(xls, sheet_name='ESTADO RESULTADO', skiprows=3)

        num_columns = len(df.columns)
        df.columns = ['Descripcion'] + [f'Col_{i}' for i in range(num_columns - 1)]

        return df

    def _read_extracto_sheet(self, xls: pd.ExcelFile) -> pd.DataFrame:
        """Read cover/summary sheet."""
        try:
            df = pd.read_excel(xls, sheet_name='CARATULA', skiprows=5)
            num_columns = len(df.columns)
            df.columns = [f'Column_{i}' for i in range(num_columns)]
            return df
        except Exception as e:
            logger.warning(f"Could not read CARATULA: {e}")
            return pd.DataFrame()
