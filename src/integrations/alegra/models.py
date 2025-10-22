#!/usr/bin/env python3
"""
Modelos Pydantic para validación de datos de Alegra
"""

from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator

class ContactData(BaseModel):
    """Modelo para datos de contacto en Alegra"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del contacto")
    type: str = Field(..., regex="^(client|provider)$", description="Tipo de contacto")
    identification: Optional[str] = Field(None, max_length=20, description="Identificación fiscal")
    email: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", description="Email del contacto")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono del contacto")
    address: Optional[str] = Field(None, max_length=500, description="Dirección del contacto")
    observations: Optional[str] = Field(None, max_length=1000, description="Observaciones")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    @validator('identification')
    def validate_identification(cls, v):
        if v and not v.isdigit():
            raise ValueError('La identificación debe contener solo números')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Cliente Ejemplo",
                "type": "client",
                "identification": "123456789",
                "email": "cliente@ejemplo.com",
                "phone": "3001234567",
                "address": "Calle 123 #45-67",
                "observations": "Cliente preferencial"
            }
        }

class ItemData(BaseModel):
    """Modelo para datos de item en Alegra"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del item")
    price: Decimal = Field(..., gt=0, description="Precio del item")
    unit: str = Field("unidad", max_length=50, description="Unidad de medida")
    initial_quantity: Decimal = Field(1.0, ge=0, description="Cantidad inicial en inventario")
    accounting_account: str = Field("4-01-01-01-01", max_length=20, description="Cuenta contable")
    observations: Optional[str] = Field(None, max_length=1000, description="Observaciones")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('El precio debe ser mayor a 0')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Producto Ejemplo",
                "price": 10000.50,
                "unit": "unidad",
                "initial_quantity": 10.0,
                "accounting_account": "4-01-01-01-01",
                "observations": "Producto de ejemplo"
            }
        }

class TaxData(BaseModel):
    """Modelo para datos de impuestos"""
    iva_rate: Decimal = Field(0.19, ge=0, le=1, description="Tasa de IVA")
    rete_fuente_renta: Decimal = Field(0.0, ge=0, le=1, description="Retención en la fuente - Renta")
    rete_fuente_iva: Decimal = Field(0.0, ge=0, le=1, description="Retención en la fuente - IVA")
    rete_fuente_ica: Decimal = Field(0.0, ge=0, le=1, description="Retención en la fuente - ICA")
    rete_iva: Decimal = Field(0.0, ge=0, le=1, description="Retención de IVA")
    
    @validator('iva_rate', 'rete_fuente_renta', 'rete_fuente_iva', 'rete_fuente_ica', 'rete_iva')
    def validate_tax_rates(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Las tasas de impuestos deben estar entre 0 y 1')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "iva_rate": 0.19,
                "rete_fuente_renta": 0.0,
                "rete_fuente_iva": 0.0,
                "rete_fuente_ica": 0.0,
                "rete_iva": 0.0
            }
        }

class InvoiceItemData(BaseModel):
    """Modelo para items en facturas"""
    id: Optional[str] = Field(None, description="ID del item en Alegra")
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del item")
    price: Decimal = Field(..., gt=0, description="Precio unitario")
    quantity: Decimal = Field(..., gt=0, description="Cantidad")
    discount: Decimal = Field(0.0, ge=0, le=1, description="Descuento (0-1)")
    tax: TaxData = Field(default_factory=TaxData, description="Datos de impuestos")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()
    
    @property
    def subtotal(self) -> Decimal:
        """Calcular subtotal del item"""
        return self.price * self.quantity
    
    @property
    def discount_amount(self) -> Decimal:
        """Calcular monto del descuento"""
        return self.subtotal * self.discount
    
    @property
    def net_amount(self) -> Decimal:
        """Calcular monto neto (subtotal - descuento)"""
        return self.subtotal - self.discount_amount
    
    @property
    def iva_amount(self) -> Decimal:
        """Calcular monto de IVA"""
        return self.net_amount * self.tax.iva_rate
    
    @property
    def total(self) -> Decimal:
        """Calcular total del item"""
        return self.net_amount + self.iva_amount
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Producto Ejemplo",
                "price": 10000.50,
                "quantity": 2.0,
                "discount": 0.1,
                "tax": {
                    "iva_rate": 0.19,
                    "rete_fuente_renta": 0.0,
                    "rete_fuente_iva": 0.0,
                    "rete_fuente_ica": 0.0,
                    "rete_iva": 0.0
                }
            }
        }

class InvoiceData(BaseModel):
    """Modelo para datos de factura"""
    client_id: str = Field(..., description="ID del cliente en Alegra")
    date: datetime = Field(default_factory=datetime.now, description="Fecha de la factura")
    due_date: Optional[datetime] = Field(None, description="Fecha de vencimiento")
    items: List[InvoiceItemData] = Field(..., min_items=1, description="Items de la factura")
    observations: Optional[str] = Field(None, max_length=1000, description="Observaciones")
    payment_method: str = Field("cash", max_length=50, description="Método de pago")
    payment_form: str = Field("immediate", max_length=50, description="Forma de pago")
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('La factura debe tener al menos un item')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        if v and 'date' in values and v < values['date']:
            raise ValueError('La fecha de vencimiento no puede ser anterior a la fecha de la factura')
        return v
    
    @property
    def subtotal(self) -> Decimal:
        """Calcular subtotal de la factura"""
        return sum(item.net_amount for item in self.items)
    
    @property
    def total_iva(self) -> Decimal:
        """Calcular total de IVA"""
        return sum(item.iva_amount for item in self.items)
    
    @property
    def total(self) -> Decimal:
        """Calcular total de la factura"""
        return self.subtotal + self.total_iva
    
    class Config:
        schema_extra = {
            "example": {
                "client_id": "123",
                "date": "2025-01-10T10:00:00Z",
                "due_date": "2025-01-17T10:00:00Z",
                "items": [
                    {
                        "name": "Producto 1",
                        "price": 10000.0,
                        "quantity": 2.0,
                        "discount": 0.0,
                        "tax": {
                            "iva_rate": 0.19,
                            "rete_fuente_renta": 0.0,
                            "rete_fuente_iva": 0.0,
                            "rete_fuente_ica": 0.0,
                            "rete_iva": 0.0
                        }
                    }
                ],
                "observations": "Factura de ejemplo",
                "payment_method": "cash",
                "payment_form": "immediate"
            }
        }

class BillData(BaseModel):
    """Modelo para datos de bill (factura de compra)"""
    provider_id: str = Field(..., description="ID del proveedor en Alegra")
    date: datetime = Field(default_factory=datetime.now, description="Fecha de la bill")
    due_date: Optional[datetime] = Field(None, description="Fecha de vencimiento")
    items: List[InvoiceItemData] = Field(..., min_items=1, description="Items de la bill")
    observations: Optional[str] = Field(None, max_length=1000, description="Observaciones")
    payment_method: str = Field("cash", max_length=50, description="Método de pago")
    payment_form: str = Field("immediate", max_length=50, description="Forma de pago")
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('La bill debe tener al menos un item')
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        if v and 'date' in values and v < values['date']:
            raise ValueError('La fecha de vencimiento no puede ser anterior a la fecha de la bill')
        return v
    
    @property
    def subtotal(self) -> Decimal:
        """Calcular subtotal de la bill"""
        return sum(item.net_amount for item in self.items)
    
    @property
    def total_iva(self) -> Decimal:
        """Calcular total de IVA"""
        return sum(item.iva_amount for item in self.items)
    
    @property
    def total(self) -> Decimal:
        """Calcular total de la bill"""
        return self.subtotal + self.total_iva
    
    class Config:
        schema_extra = {
            "example": {
                "provider_id": "456",
                "date": "2025-01-10T10:00:00Z",
                "due_date": "2025-01-17T10:00:00Z",
                "items": [
                    {
                        "name": "Producto Compra",
                        "price": 5000.0,
                        "quantity": 1.0,
                        "discount": 0.0,
                        "tax": {
                            "iva_rate": 0.19,
                            "rete_fuente_renta": 0.0,
                            "rete_fuente_iva": 0.0,
                            "rete_fuente_ica": 0.0,
                            "rete_iva": 0.0
                        }
                    }
                ],
                "observations": "Bill de ejemplo",
                "payment_method": "cash",
                "payment_form": "immediate"
            }
        }

class AlegraResponse(BaseModel):
    """Modelo para respuestas de Alegra API"""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos de respuesta")
    message: Optional[str] = Field(None, description="Mensaje de respuesta")
    errors: Optional[List[str]] = Field(None, description="Lista de errores")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Cliente Ejemplo"},
                "message": "Operación exitosa",
                "errors": None
            }
        }

class CompanyInfo(BaseModel):
    """Modelo para información de la empresa en Alegra"""
    id: str = Field(..., description="ID de la empresa")
    name: str = Field(..., description="Nombre de la empresa")
    identification: str = Field(..., description="Identificación fiscal")
    email: Optional[str] = Field(None, description="Email de la empresa")
    phone: Optional[str] = Field(None, description="Teléfono de la empresa")
    address: Optional[str] = Field(None, description="Dirección de la empresa")
    currency: str = Field("COP", description="Moneda de la empresa")
    timezone: str = Field("America/Bogota", description="Zona horaria")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "1",
                "name": "Mi Empresa S.A.S",
                "identification": "900123456-1",
                "email": "info@miempresa.com",
                "phone": "3001234567",
                "address": "Calle 123 #45-67, Bogotá",
                "currency": "COP",
                "timezone": "America/Bogota"
            }
        }