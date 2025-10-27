"""
Data models and types for SuperVincent InvoiceBot.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class InvoiceType(Enum):
    """Invoice type enumeration."""
    PURCHASE = "compra"
    SALE = "venta"


class ContactType(Enum):
    """Contact type enumeration."""
    CLIENT = "client"
    PROVIDER = "provider"


@dataclass
class InvoiceItem:
    """Invoice item data model."""
    code: str
    description: str
    quantity: float
    price: float
    
    @property
    def total(self) -> float:
        """Calculate item total."""
        return self.quantity * self.price


@dataclass
class InvoiceData:
    """Invoice data model."""
    invoice_type: InvoiceType
    date: str
    vendor: str
    client: str
    items: List[InvoiceItem]
    subtotal: float
    taxes: float
    total: float
    vendor_nit: Optional[str] = None
    vendor_regime: str = "comun"
    vendor_city: str = "bogota"
    buyer_nit: Optional[str] = None
    buyer_regime: str = "comun"
    buyer_city: str = "bogota"
    invoice_number: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class TaxResult:
    """Tax calculation result."""
    iva_amount: float
    iva_rate: float
    retefuente_renta: float
    retefuente_iva: float
    retefuente_ica: float
    total_withholdings: float
    net_amount: float
    compliance_status: str
    tax_breakdown: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Invoice processing result."""
    success: bool
    invoice_data: Optional[InvoiceData]
    tax_result: Optional[TaxResult]
    alegra_result: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class ContactInfo:
    """Contact information model."""
    id: str
    name: str
    contact_type: ContactType
    nit: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


@dataclass
class ItemInfo:
    """Item information model."""
    id: str
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
