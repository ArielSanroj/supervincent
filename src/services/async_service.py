"""
Async processing service for scalable invoice processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import aiohttp
import aiofiles
from celery import Celery

from ..core.models import InvoiceData, ProcessingResult
from ..core.parsers import InvoiceParserFactory
from .invoice_service import InvoiceService
from .tax_service import TaxService
from .alegra_service import AlegraService

logger = logging.getLogger(__name__)


class AsyncInvoiceProcessor:
    """Async invoice processor for high-volume processing."""
    
    def __init__(self, 
                 tax_service: TaxService,
                 alegra_service: AlegraService,
                 max_concurrent: int = 10):
        """Initialize async processor."""
        self.tax_service = tax_service
        self.alegra_service = alegra_service
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Initialize Celery for background tasks
        self.celery_app = Celery('invoicebot')
        self.celery_app.config_from_object('celery_config')
    
    async def process_invoice_async(self, file_path: str) -> ProcessingResult:
        """Process single invoice asynchronously."""
        async with self.semaphore:
            try:
                logger.info(f"🔄 Processing invoice async: {file_path}")
                
                # Parse invoice
                invoice_data = await self._parse_invoice_async(file_path)
                if not invoice_data:
                    return ProcessingResult(
                        success=False,
                        invoice_data=None,
                        tax_result=None,
                        alegra_result=None,
                        error_message="Failed to parse invoice"
                    )
                
                # Calculate taxes
                tax_result = self.tax_service.calculate_taxes(invoice_data)
                
                # Create in Alegra
                alegra_result = await self._create_in_alegra_async(invoice_data, tax_result)
                
                return ProcessingResult(
                    success=True,
                    invoice_data=invoice_data,
                    tax_result=tax_result,
                    alegra_result=alegra_result
                )
                
            except Exception as e:
                logger.error(f"Error processing invoice {file_path}: {e}")
                return ProcessingResult(
                    success=False,
                    invoice_data=None,
                    tax_result=None,
                    alegra_result=None,
                    error_message=str(e)
                )
    
    async def process_batch_async(self, file_paths: List[str]) -> List[ProcessingResult]:
        """Process multiple invoices concurrently."""
        logger.info(f"🚀 Processing batch of {len(file_paths)} invoices")
        
        tasks = [
            self.process_invoice_async(file_path) 
            for file_path in file_paths
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProcessingResult(
                    success=False,
                    invoice_data=None,
                    tax_result=None,
                    alegra_result=None,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.success)
        logger.info(f"✅ Batch processing complete: {successful}/{len(file_paths)} successful")
        
        return processed_results
    
    async def _parse_invoice_async(self, file_path: str) -> Optional[InvoiceData]:
        """Parse invoice asynchronously."""
        try:
            # Run CPU-intensive parsing in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                InvoiceParserFactory.parse_invoice, 
                file_path
            )
        except Exception as e:
            logger.error(f"Error parsing invoice {file_path}: {e}")
            return None
    
    async def _create_in_alegra_async(self, 
                                    invoice_data: InvoiceData, 
                                    tax_result) -> Optional[Dict[str, Any]]:
        """Create invoice in Alegra asynchronously."""
        try:
            # Run API calls in thread pool
            loop = asyncio.get_event_loop()
            
            if invoice_data.invoice_type.value == "compra":
                return await loop.run_in_executor(
                    None,
                    self.alegra_service.create_purchase_bill,
                    invoice_data,
                    tax_result
                )
            else:
                return await loop.run_in_executor(
                    None,
                    self.alegra_service.create_sale_invoice,
                    invoice_data,
                    tax_result
                )
        except Exception as e:
            logger.error(f"Error creating in Alegra: {e}")
            return None
    
    async def process_directory_async(self, directory_path: str) -> Dict[str, Any]:
        """Process all invoices in a directory asynchronously."""
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Find all supported files
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_paths = [
            str(f) for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        if not file_paths:
            logger.warning(f"No supported files found in {directory_path}")
            return {
                "total_files": 0,
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "results": []
            }
        
        # Process all files
        results = await self.process_batch_async(file_paths)
        
        # Move processed files
        await self._move_processed_files(file_paths, results)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return {
            "total_files": len(file_paths),
            "processed": len(results),
            "successful": successful,
            "failed": failed,
            "results": [
                {
                    "file_path": file_paths[i],
                    "success": results[i].success,
                    "error": results[i].error_message if not results[i].success else None
                }
                for i in range(len(file_paths))
            ]
        }
    
    async def _move_processed_files(self, 
                                  file_paths: List[str], 
                                  results: List[ProcessingResult]) -> None:
        """Move processed files to appropriate directories."""
        processed_dir = Path("facturas/processed")
        error_dir = Path("facturas/error")
        
        processed_dir.mkdir(parents=True, exist_ok=True)
        error_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path, result in zip(file_paths, results):
            source = Path(file_path)
            
            if result.success:
                destination = processed_dir / source.name
            else:
                destination = error_dir / source.name
            
            try:
                # Move file
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    source.rename,
                    destination
                )
                logger.info(f"Moved {source.name} to {destination.parent.name}")
            except Exception as e:
                logger.error(f"Error moving file {source.name}: {e}")


class CeleryTaskProcessor:
    """Celery-based background task processor."""
    
    def __init__(self, celery_app: Celery):
        """Initialize Celery processor."""
        self.celery_app = celery_app
    
    def process_invoice_task(self, file_path: str) -> Dict[str, Any]:
        """Celery task for processing single invoice."""
        try:
            # This would be called by Celery worker
            # For now, we'll just return a mock result
            return {
                "status": "success",
                "file_path": file_path,
                "processed_at": datetime.now().isoformat(),
                "message": "Invoice processed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "file_path": file_path,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def process_batch_task(self, file_paths: List[str]) -> Dict[str, Any]:
        """Celery task for processing batch of invoices."""
        try:
            # This would process multiple files
            return {
                "status": "success",
                "total_files": len(file_paths),
                "processed_at": datetime.now().isoformat(),
                "message": f"Batch of {len(file_paths)} invoices processed"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    def schedule_processing(self, file_paths: List[str]) -> str:
        """Schedule invoice processing for later execution."""
        task = self.celery_app.send_task(
            'process_invoices',
            args=[file_paths],
            countdown=60  # Process in 1 minute
        )
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of scheduled task."""
        task = self.celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
            "error": str(task.info) if task.failed() else None
        }


# Celery task definitions
def process_invoice_celery(file_path: str):
    """Celery task for processing single invoice."""
    try:
        # This would integrate with the actual processing logic
        logger.info(f"Processing invoice: {file_path}")
        
        # Simulate processing time
        import time
        time.sleep(2)
        
        return {
            "status": "success",
            "file_path": file_path,
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return {
            "status": "error",
            "file_path": file_path,
            "error": str(e)
        }


def process_batch_celery(file_paths: List[str]):
    """Celery task for processing batch of invoices."""
    try:
        logger.info(f"Processing batch of {len(file_paths)} invoices")
        
        results = []
        for file_path in file_paths:
            result = process_invoice_celery.delay(file_path)
            results.append(result.id)
        
        return {
            "status": "success",
            "task_ids": results,
            "total_files": len(file_paths),
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

