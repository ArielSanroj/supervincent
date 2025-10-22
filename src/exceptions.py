#!/usr/bin/env python3
"""
Jerarquía de excepciones custom para InvoiceBot
"""

class InvoiceBotError(Exception):
    """Excepción base para todos los errores de InvoiceBot"""
    pass

class ValidationError(InvoiceBotError):
    """Error de validación de datos"""
    pass

class ParsingError(InvoiceBotError):
    """Error en parsing de documentos"""
    pass

class IntegrationError(InvoiceBotError):
    """Error en integración con servicios externos"""
    pass

class AlegraAPIError(IntegrationError):
    """Error específico de API Alegra"""
    pass

class DIANAPIError(IntegrationError):
    """Error específico de API DIAN"""
    pass

class NanobotAPIError(IntegrationError):
    """Error específico de API Nanobot"""
    pass

class ConfigurationError(InvoiceBotError):
    """Error de configuración"""
    pass

class SecurityError(InvoiceBotError):
    """Error de seguridad"""
    pass

class CacheError(InvoiceBotError):
    """Error de caché"""
    pass

