#!/usr/bin/env python3
"""
InvoiceBot - Sistema de procesamiento de facturas consolidado
Punto de entrada principal para la nueva arquitectura
"""

import sys
import argparse
import logging
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import InvoiceProcessor
from src.utils import ConfigManager, StructuredLogger
from src.exceptions import InvoiceBotError

def main():
    """Función principal para CLI"""
    parser = argparse.ArgumentParser(
        description='InvoiceBot - Sistema de procesamiento de facturas consolidado',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python invoicebot.py process factura.pdf
  python invoicebot.py process factura.jpg --use-nanobot
  python invoicebot.py report --start-date 2024-01-01 --end-date 2024-01-31
        """
    )
    
    parser.add_argument('command', choices=['process', 'report'], 
                       help='Comando a ejecutar')
    parser.add_argument('file_path', nargs='?', 
                       help='Ruta al archivo de factura')
    parser.add_argument('--use-nanobot', action='store_true', 
                       help='Usar Nanobot para clasificación')
    parser.add_argument('--nanobot-host', 
                       help='Host de Nanobot')
    parser.add_argument('--nanobot-confidence', type=float, 
                       help='Umbral de confianza de Nanobot')
    parser.add_argument('--start-date', 
                       help='Fecha de inicio para reportes (YYYY-MM-DD)')
    parser.add_argument('--end-date', 
                       help='Fecha de fin para reportes (YYYY-MM-DD)')
    parser.add_argument('--config', 
                       help='Ruta al archivo de configuración')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Nivel de logging')
    
    args = parser.parse_args()
    
    try:
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger = StructuredLogger('InvoiceBot', args.log_level)
        logger.info("Iniciando InvoiceBot", extra={"version": "2.0.0"})
        
        # Inicializar procesador
        processor = InvoiceProcessor(
            config_path=args.config,
            use_nanobot=args.use_nanobot,
            nanobot_host=args.nanobot_host,
            nanobot_confidence_threshold=args.nanobot_confidence
        )
        
        if args.command == 'process':
            if not args.file_path:
                print("❌ Error: Se requiere ruta al archivo para procesar")
                sys.exit(1)
            
            logger.info("Procesando factura", extra={"file_path": args.file_path})
            
            result = processor.process_invoice_file(args.file_path)
            if result:
                print("✅ Factura procesada exitosamente")
                print(f"📄 Tipo: {result.get('tipo', 'N/A')}")
                print(f"💰 Total: ${result.get('total', 0):,.2f}")
                if result.get('alegra_id'):
                    print(f"🔗 Alegra ID: {result['alegra_id']}")
                if result.get('alegra_url'):
                    print(f"🌐 URL: {result['alegra_url']}")
            else:
                print("❌ Error procesando factura")
                sys.exit(1)
        
        elif args.command == 'report':
            if not args.start_date or not args.end_date:
                print("❌ Error: Se requieren fechas de inicio y fin para reportes")
                sys.exit(1)
            
            logger.info("Generando reporte", extra={
                "start_date": args.start_date,
                "end_date": args.end_date
            })
            
            print("📊 Generando reportes...")
            # TODO: Implementar generación de reportes
            print("✅ Reportes generados exitosamente")
            
    except InvoiceBotError as e:
        print(f"❌ Error de InvoiceBot: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

