#!/usr/bin/env python3
"""
Cliente para Nanobot (experimental) con manejo robusto de errores
"""

import logging
from typing import Any, Dict, Optional
import requests

from ...exceptions import NanobotAPIError, IntegrationError

class NanobotClient:
    """Cliente para integración con Nanobot (feature experimental)"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Configurar sesión
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def classify_invoice(self, agent: str, text: str) -> Dict[str, Any]:
        """
        Clasificar factura usando agente de Nanobot
        
        Args:
            agent: Nombre del agente clasificador
            text: Texto de la factura
            
        Returns:
            Resultado de la clasificación
            
        Raises:
            NanobotAPIError: Si la clasificación falla
        """
        try:
            payload = {
                "mode": "agent",
                "name": agent,
                "input": text,
                "chat": False,
            }
            
            response = self._call("/api/call", payload)
            
            self.logger.debug("Clasificación Nanobot exitosa", extra={
                "agent": agent,
                "text_length": len(text)
            })
            
            return response
            
        except Exception as e:
            self.logger.error("Error en clasificación Nanobot", extra={
                "agent": agent,
                "error": str(e)
            })
            raise NanobotAPIError(f"Error clasificando con Nanobot: {e}")
    
    def triage_invoice(self, agent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triage de factura usando agente de Nanobot
        
        Args:
            agent: Nombre del agente de triage
            payload: Datos para triage
            
        Returns:
            Resultado del triage
            
        Raises:
            NanobotAPIError: Si el triage falla
        """
        try:
            body = {
                "mode": "agent",
                "name": agent,
                "input": payload,
                "chat": False,
            }
            
            response = self._call("/api/call", body)
            
            self.logger.debug("Triage Nanobot exitoso", extra={
                "agent": agent,
                "payload_keys": list(payload.keys())
            })
            
            return response
            
        except Exception as e:
            self.logger.error("Error en triage Nanobot", extra={
                "agent": agent,
                "error": str(e)
            })
            raise NanobotAPIError(f"Error en triage con Nanobot: {e}")
    
    def _call(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realizar llamada a API de Nanobot
        
        Args:
            path: Endpoint de la API
            payload: Datos a enviar
            
        Returns:
            Respuesta de la API
            
        Raises:
            NanobotAPIError: Si la llamada falla
        """
        url = f"{self.base_url}{path}"
        
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                raise NanobotAPIError(
                    f"Nanobot returned status {response.status_code}: {response.text.strip()}"
                )
            
            try:
                data = response.json().get("response")
            except ValueError as e:
                raise NanobotAPIError("Failed to decode Nanobot response as JSON") from e
            
            if not data or "output" not in data:
                raise NanobotAPIError("Nanobot response missing output field")
            
            return data["output"]
            
        except requests.RequestException as e:
            raise NanobotAPIError(f"Request failed: {str(e)}") from e

