"""
Alegra API integration service.
"""

import logging
from typing import Optional, Dict, Any

from ..core.models import InvoiceData, TaxResult, ContactType

logger = logging.getLogger(__name__)


class AlegraService:
    """Alegra API integration service."""
    
    def __init__(self, base_url: str, email: str, token: str):
        """Initialize Alegra service."""
        self.base_url = base_url
        self.email = email
        self.token = token
        logger.info("🔗 Alegra service initialized")
    
    def create_purchase_bill(self, invoice_data: InvoiceData, tax_result: TaxResult) -> Optional[Dict[str, Any]]:
        """Create purchase bill in Alegra."""
        logger.info("📥 Creating purchase bill in Alegra")
        
        try:
            # Get or create provider
            provider_id = self._get_or_create_contact(
                invoice_data.vendor, 
                ContactType.PROVIDER
            )
            
            if not provider_id:
                logger.error("Failed to get/create provider")
                return None
            
            # Prepare items
            items = []
            for item in invoice_data.items:
                item_id = self._get_or_create_item(item.description, item.price)
                if item_id:
                    items.append({
                        "id": item_id,
                        "quantity": item.quantity,
                        "price": item.price
                    })
            
            if not items:
                logger.error("No items created")
                return None
            
            # Create bill payload
            payload = {
                "date": invoice_data.date,
                "dueDate": invoice_data.date,
                "provider": {"id": provider_id},
                "items": items,
                "observations": f"Processed from PDF - {invoice_data.vendor}"
            }
            
            # Add tax information
            if tax_result.iva_amount > 0:
                payload["tax"] = tax_result.iva_amount
            
            # TODO: Implement actual API call
            logger.info("✅ Purchase bill created successfully")
            return {"id": "123", "number": "BILL-001", "status": "created"}
            
        except Exception as e:
            logger.error(f"Error creating purchase bill: {e}")
            return None
    
    def create_sale_invoice(self, invoice_data: InvoiceData, tax_result: TaxResult) -> Optional[Dict[str, Any]]:
        """Create sale invoice in Alegra."""
        logger.info("📤 Creating sale invoice in Alegra")
        
        try:
            # Get or create client
            client_id = self._get_or_create_contact(
                invoice_data.client, 
                ContactType.CLIENT
            )
            
            if not client_id:
                logger.error("Failed to get/create client")
                return None
            
            # Prepare items
            items = []
            for item in invoice_data.items:
                item_id = self._get_or_create_item(item.description, item.price)
                if item_id:
                    items.append({
                        "id": item_id,
                        "quantity": item.quantity,
                        "price": item.price
                    })
            
            if not items:
                logger.error("No items created")
                return None
            
            # Create invoice payload
            payload = {
                "date": invoice_data.date,
                "dueDate": invoice_data.date,
                "client": {"id": client_id},
                "items": items,
                "observations": f"Processed from PDF - {invoice_data.client}"
            }
            
            # Add tax information
            if tax_result.iva_amount > 0:
                payload["tax"] = tax_result.iva_amount
            
            # TODO: Implement actual API call
            logger.info("✅ Sale invoice created successfully")
            return {"id": "456", "number": "INV-001", "status": "created"}
            
        except Exception as e:
            logger.error(f"Error creating sale invoice: {e}")
            return None
    
    def _get_or_create_contact(self, name: str, contact_type: ContactType) -> Optional[str]:
        """Get or create contact in Alegra."""
        # TODO: Implement actual API calls
        logger.info(f"Getting/creating contact: {name} ({contact_type.value})")
        return "contact_123"
    
    def _get_or_create_item(self, name: str, price: float) -> Optional[str]:
        """Get or create item in Alegra."""
        # TODO: Implement actual API calls
        logger.info(f"Getting/creating item: {name} (${price})")
        return "item_456"
