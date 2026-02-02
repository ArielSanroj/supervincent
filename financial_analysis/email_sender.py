"""
Email sending module for financial reports.
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from typing import Dict

from .constants import DEFAULT_EMAIL_CONFIG

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles sending financial reports via email."""

    def __init__(self, config: Dict = None):
        self.config = config or DEFAULT_EMAIL_CONFIG

    def send_report(self, reports: Dict[str, str], metrics: Dict) -> bool:
        """Send financial report via email."""
        try:
            current_month = metrics['current_month']

            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['recipient_email']
            msg['Subject'] = f'Reporte CFO SuperBincent - {current_month} 2025'

            html_body = self._build_email_body(metrics)
            msg.attach(MIMEText(html_body, 'html'))

            self._attach_files(msg, reports)
            self._send_email(msg)

            logger.info(f"Email sent successfully to {self.config['recipient_email']}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def _build_email_body(self, metrics: Dict) -> str:
        """Build HTML email body."""
        current_month = metrics['current_month']

        return f"""
        <html>
        <body>
            <h2>Reporte Financiero SuperBincent - {current_month} 2025</h2>

            <h3>Resumen Ejecutivo:</h3>
            <ul>
                <li><strong>Ingresos:</strong> ${metrics['ingresos']:,.0f} COP</li>
                <li><strong>Gastos Totales:</strong> ${metrics['gastos_totales']:,.0f} COP</li>
                <li><strong>% Ejecutado Gastos:</strong> {metrics['presupuesto_ejecutado']['gastos_pct']:.1f}%</li>
                <li><strong>Current Ratio:</strong> {metrics['kpis'].get('current_ratio', 0):.2f}</li>
                <li><strong>EBITDA:</strong> ${metrics['kpis'].get('ebitda', 0):,.0f} COP</li>
            </ul>

            <h3>Archivos Adjuntos:</h3>
            <ul>
                <li>Balance Consolidado (Excel)</li>
                <li>Presupuesto Ejecutado (Excel)</li>
                <li>KPIs Financieros (Excel)</li>
                <li>Informe para Junta Directiva (Word)</li>
                <li>Graficos y Visualizaciones (PNG)</li>
            </ul>

            <p><em>Reporte generado automaticamente por SuperBincent CFO Bot</em></p>
        </body>
        </html>
        """

    def _attach_files(self, msg: MIMEMultipart, reports: Dict[str, str]) -> None:
        """Attach report files to email."""
        for report_type, file_path in reports.items():
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(file_path)}'
                    )
                    msg.attach(part)

    def _send_email(self, msg: MIMEMultipart) -> None:
        """Send the email via SMTP."""
        server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
        server.starttls()
        server.login(self.config['sender_email'], self.config['sender_password'])
        server.send_message(msg)
        server.quit()
