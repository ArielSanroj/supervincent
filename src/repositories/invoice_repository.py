"""
Invoice repository for data persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.models import InvoiceData, ProcessingResult
from .base import BaseRepository

logger = logging.getLogger(__name__)


class InvoiceRepository(BaseRepository[InvoiceData]):
    """Repository for invoice data persistence."""
    
    def __init__(self, data_dir: str = "data/invoices"):
        """Initialize invoice repository."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Index for fast lookups
        self._index_file = self.data_dir / "index.json"
        self._load_index()
    
    def _load_index(self) -> None:
        """Load invoice index."""
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r') as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self._index = {}
        else:
            self._index = {}
    
    def _save_index(self) -> None:
        """Save invoice index."""
        try:
            with open(self._index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _get_invoice_file(self, invoice_id: str) -> Path:
        """Get invoice file path."""
        return self.data_dir / f"{invoice_id}.json"
    
    def create(self, entity: InvoiceData) -> InvoiceData:
        """Create a new invoice."""
        invoice_id = f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(entity))}"
        
        # Save invoice data
        invoice_file = self._get_invoice_file(invoice_id)
        invoice_data = {
            "id": invoice_id,
            "invoice_type": entity.invoice_type.value,
            "date": entity.date,
            "vendor": entity.vendor,
            "client": entity.client,
            "items": [
                {
                    "code": item.code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "price": item.price
                }
                for item in entity.items
            ],
            "subtotal": entity.subtotal,
            "taxes": entity.taxes,
            "total": entity.total,
            "vendor_nit": entity.vendor_nit,
            "vendor_regime": entity.vendor_regime,
            "vendor_city": entity.vendor_city,
            "buyer_nit": entity.buyer_nit,
            "buyer_regime": entity.buyer_regime,
            "buyer_city": entity.buyer_city,
            "invoice_number": entity.invoice_number,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            with open(invoice_file, 'w') as f:
                json.dump(invoice_data, f, indent=2)
            
            # Update index
            self._index[invoice_id] = {
                "file": str(invoice_file),
                "created_at": invoice_data["created_at"],
                "invoice_type": entity.invoice_type.value,
                "vendor": entity.vendor,
                "total": entity.total
            }
            self._save_index()
            
            logger.info(f"Invoice created: {invoice_id}")
            return entity
            
        except Exception as e:
            logger.error(f"Error creating invoice {invoice_id}: {e}")
            raise
    
    def get_by_id(self, entity_id: str) -> Optional[InvoiceData]:
        """Get invoice by ID."""
        if entity_id not in self._index:
            return None
        
        try:
            invoice_file = Path(self._index[entity_id]["file"])
            if not invoice_file.exists():
                return None
            
            with open(invoice_file, 'r') as f:
                data = json.load(f)
            
            return self._deserialize_invoice(data)
            
        except Exception as e:
            logger.error(f"Error loading invoice {entity_id}: {e}")
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[InvoiceData]:
        """Get all invoices with pagination."""
        invoice_ids = list(self._index.keys())[offset:offset + limit]
        invoices = []
        
        for invoice_id in invoice_ids:
            invoice = self.get_by_id(invoice_id)
            if invoice:
                invoices.append(invoice)
        
        return invoices
    
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[InvoiceData]:
        """Update invoice."""
        if entity_id not in self._index:
            return None
        
        try:
            invoice_file = Path(self._index[entity_id]["file"])
            if not invoice_file.exists():
                return None
            
            # Load existing data
            with open(invoice_file, 'r') as f:
                existing_data = json.load(f)
            
            # Update fields
            for key, value in data.items():
                if key in existing_data:
                    existing_data[key] = value
            
            existing_data["updated_at"] = datetime.now().isoformat()
            
            # Save updated data
            with open(invoice_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            # Update index
            if "vendor" in data:
                self._index[entity_id]["vendor"] = data["vendor"]
            if "total" in data:
                self._index[entity_id]["total"] = data["total"]
            self._save_index()
            
            return self._deserialize_invoice(existing_data)
            
        except Exception as e:
            logger.error(f"Error updating invoice {entity_id}: {e}")
            return None
    
    def delete(self, entity_id: str) -> bool:
        """Delete invoice."""
        if entity_id not in self._index:
            return False
        
        try:
            invoice_file = Path(self._index[entity_id]["file"])
            if invoice_file.exists():
                invoice_file.unlink()
            
            del self._index[entity_id]
            self._save_index()
            
            logger.info(f"Invoice deleted: {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting invoice {entity_id}: {e}")
            return False
    
    def search(self, query: Dict[str, Any], limit: int = 100) -> List[InvoiceData]:
        """Search invoices."""
        results = []
        
        for invoice_id, index_data in self._index.items():
            if len(results) >= limit:
                break
            
            # Simple search logic
            match = True
            for key, value in query.items():
                if key in index_data and index_data[key] != value:
                    match = False
                    break
            
            if match:
                invoice = self.get_by_id(invoice_id)
                if invoice:
                    results.append(invoice)
        
        return results
    
    def _deserialize_invoice(self, data: Dict[str, Any]) -> InvoiceData:
        """Deserialize invoice data from JSON."""
        from ..core.models import InvoiceItem, InvoiceType
        
        items = [
            InvoiceItem(
                code=item["code"],
                description=item["description"],
                quantity=item["quantity"],
                price=item["price"]
            )
            for item in data.get("items", [])
        ]
        
        return InvoiceData(
            invoice_type=InvoiceType(data["invoice_type"]),
            date=data["date"],
            vendor=data["vendor"],
            client=data["client"],
            items=items,
            subtotal=data["subtotal"],
            taxes=data["taxes"],
            total=data["total"],
            vendor_nit=data.get("vendor_nit"),
            vendor_regime=data.get("vendor_regime", "comun"),
            vendor_city=data.get("vendor_city", "bogota"),
            buyer_nit=data.get("buyer_nit"),
            buyer_regime=data.get("buyer_regime", "comun"),
            buyer_city=data.get("buyer_city", "bogota"),
            invoice_number=data.get("invoice_number"),
            raw_text=data.get("raw_text")
        )
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[InvoiceData]:
        """Get invoices by date range."""
        results = []
        
        for invoice_id, index_data in self._index.items():
            invoice_date = index_data.get("created_at", "").split("T")[0]
            if start_date <= invoice_date <= end_date:
                invoice = self.get_by_id(invoice_id)
                if invoice:
                    results.append(invoice)
        
        return results
    
    def get_by_vendor(self, vendor: str) -> List[InvoiceData]:
        """Get invoices by vendor."""
        return self.search({"vendor": vendor})
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get invoice statistics."""
        total_invoices = len(self._index)
        total_amount = sum(
            index_data.get("total", 0) 
            for index_data in self._index.values()
        )
        
        # Count by type
        type_counts = {}
        for index_data in self._index.values():
            invoice_type = index_data.get("invoice_type", "unknown")
            type_counts[invoice_type] = type_counts.get(invoice_type, 0) + 1
        
        return {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "type_counts": type_counts,
            "last_updated": datetime.now().isoformat()
        }

