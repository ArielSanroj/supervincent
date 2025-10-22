#!/usr/bin/env python3
"""
Cliente robusto para Alegra API con connection pooling, retry automático,
circuit breaker y manejo de errores mejorado
"""

import base64
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...exceptions import AlegraAPIError, IntegrationError

class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class AlegraConfig:
    """Configuración del cliente Alegra"""
    email: str
    token: str
    base_url: str = "https://api.alegra.com/api/v1"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

class AlegraClient:
    """
    Cliente robusto para Alegra API con todas las funcionalidades
    de las versiones anteriores consolidadas
    """
    
    def __init__(
        self,
        email: str,
        token: str,
        base_url: str = "https://api.alegra.com/api/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Inicializar cliente Alegra
        
        Args:
            email: Email de Alegra
            token: Token de API
            base_url: URL base de la API
            timeout: Timeout en segundos
            max_retries: Número máximo de reintentos
        """
        self.config = AlegraConfig(
            email=email,
            token=token,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Circuit breaker
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        
        # Rate limiting
        self.last_request_time = 0
        
        # Cache de contactos e items
        self._contacts_cache: Dict[str, str] = {}  # name -> id
        self._items_cache: Dict[str, str] = {}  # name -> id
        
        # Configurar sesión HTTP
        self._setup_session()
        
        self.logger.info("Cliente Alegra inicializado", extra={
            "base_url": base_url,
            "timeout": timeout,
            "max_retries": max_retries
        })
    
    def _setup_session(self) -> None:
        """Configurar sesión HTTP con retry y connection pooling"""
        self.session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configurar headers por defecto
        self.session.headers.update(self._get_auth_headers())
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Obtener headers de autenticación"""
        credentials = f"{self.config.email}:{self.config.token}"
        auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"
        
        return {
            'Authorization': auth_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _check_circuit_breaker(self) -> bool:
        """Verificar estado del circuit breaker"""
        if self.circuit_state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.config.circuit_breaker_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                self.logger.info("Circuit breaker: cambiando a HALF_OPEN")
                return True
            return False
        return True
    
    def _record_success(self) -> None:
        """Registrar éxito y resetear circuit breaker"""
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            self.logger.info("Circuit breaker: cambiando a CLOSED")
    
    def _record_failure(self) -> None:
        """Registrar fallo y actualizar circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.circuit_breaker_threshold:
            self.circuit_state = CircuitState.OPEN
            self.logger.warning("Circuit breaker: cambiando a OPEN", extra={
                "failure_count": self.failure_count
            })
    
    def _rate_limit_delay(self) -> None:
        """Aplicar rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            delay = self.config.rate_limit_delay - time_since_last
            time.sleep(delay)
        
        self.last_request_time = time.time()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realizar request a Alegra API con manejo robusto de errores
        
        Args:
            method: Método HTTP
            endpoint: Endpoint de la API
            data: Datos a enviar
            params: Parámetros de query
            
        Returns:
            Respuesta de la API
            
        Raises:
            AlegraAPIError: Si la request falla
        """
        # Verificar circuit breaker
        if not self._check_circuit_breaker():
            raise AlegraAPIError("Circuit breaker abierto - servicio no disponible")
        
        # Aplicar rate limiting
        self._rate_limit_delay()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            self.logger.debug("Realizando request a Alegra", extra={
                "method": method,
                "url": url,
                "endpoint": endpoint
            })
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            
            # Log de respuesta
            self.logger.debug("Respuesta de Alegra", extra={
                "status_code": response.status_code,
                "response_size": len(response.content)
            })
            
            # Manejar diferentes códigos de estado
            if response.status_code == 200:
                self._record_success()
                return response.json()
            
            elif response.status_code == 201:
                self._record_success()
                return response.json()
            
            elif response.status_code == 429:  # Rate limit
                self.logger.warning("Rate limit alcanzado, esperando...")
                time.sleep(2)
                return self._make_request(method, endpoint, data, params)
            
            elif response.status_code == 400:
                error_msg = f"Bad Request: {response.text}"
                self.logger.error("Error 400 en Alegra", extra={"response": response.text})
                raise AlegraAPIError(error_msg)
            
            elif response.status_code == 401:
                error_msg = "Unauthorized: credenciales inválidas"
                self.logger.error("Error 401 en Alegra - credenciales inválidas")
                raise AlegraAPIError(error_msg)
            
            elif response.status_code == 404:
                error_msg = f"Not Found: {endpoint}"
                self.logger.warning("Error 404 en Alegra", extra={"endpoint": endpoint})
                raise AlegraAPIError(error_msg)
            
            elif response.status_code >= 500:
                self._record_failure()
                error_msg = f"Server Error: {response.status_code}"
                self.logger.error("Error del servidor Alegra", extra={
                    "status_code": response.status_code,
                    "response": response.text
                })
                raise AlegraAPIError(error_msg)
            
            else:
                error_msg = f"Unexpected status code: {response.status_code}"
                self.logger.error("Código de estado inesperado", extra={
                    "status_code": response.status_code,
                    "response": response.text
                })
                raise AlegraAPIError(error_msg)
                
        except requests.exceptions.Timeout:
            self._record_failure()
            raise AlegraAPIError(f"Timeout en request a {endpoint}")
        
        except requests.exceptions.ConnectionError:
            self._record_failure()
            raise AlegraAPIError(f"Error de conexión a {endpoint}")
        
        except requests.exceptions.RequestException as e:
            self._record_failure()
            raise AlegraAPIError(f"Error en request: {str(e)}")
    
    def get_or_create_contact(
        self,
        name: str,
        contact_type: str = 'client',
        **kwargs
    ) -> Optional[str]:
        """
        Obtener o crear contacto en Alegra con fallback robusto
        
        Args:
            name: Nombre del contacto
            contact_type: Tipo de contacto ('client', 'provider')
            **kwargs: Datos adicionales del contacto
            
        Returns:
            ID del contacto o None si falla
        """
        try:
            # Verificar caché
            cache_key = f"{name}_{contact_type}"
            if cache_key in self._contacts_cache:
                self.logger.debug("Contacto encontrado en caché", extra={"name": name})
                return self._contacts_cache[cache_key]
            
            # Buscar contacto existente
            contact_id = self._search_contact(name, contact_type)
            if contact_id:
                self._contacts_cache[cache_key] = contact_id
                return contact_id
            
            # Crear nuevo contacto
            contact_data = {
                'name': name,
                'type': contact_type,
                'identification': kwargs.get('identification', ''),
                'email': kwargs.get('email', ''),
                'phone': kwargs.get('phone', ''),
                'address': kwargs.get('address', ''),
                'observations': kwargs.get('observations', '')
            }
            
            result = self._make_request('POST', 'contacts', contact_data)
            
            if result and 'id' in result:
                contact_id = str(result['id'])
                self._contacts_cache[cache_key] = contact_id
                
                self.logger.info("Contacto creado exitosamente", extra={
                    "contact_id": contact_id,
                    "name": name,
                    "type": contact_type
                })
                
                return contact_id
            
            return None
            
        except Exception as e:
            self.logger.error("Error creando/obteniendo contacto", extra={
                "name": name,
                "type": contact_type,
                "error": str(e)
            })
            
            # Fallback a contacto genérico
            if contact_type == 'client':
                return self._get_fallback_client()
            else:
                return self._get_fallback_provider()
    
    def _search_contact(self, name: str, contact_type: str) -> Optional[str]:
        """Buscar contacto existente por nombre"""
        try:
            params = {
                'query': name,
                'type': contact_type,
                'limit': 10
            }
            
            result = self._make_request('GET', 'contacts', params=params)
            
            if result and 'data' in result:
                for contact in result['data']:
                    if contact.get('name', '').lower() == name.lower():
                        return str(contact['id'])
            
            return None
            
        except Exception as e:
            self.logger.debug("Error buscando contacto", extra={"error": str(e)})
            return None
    
    def _get_fallback_client(self) -> Optional[str]:
        """Obtener ID de cliente fallback (Consumidor Final)"""
        try:
            return self.get_or_create_contact(
                name="Consumidor Final",
                contact_type='client',
                identification="00000000",
                email="consumidor@final.com"
            )
        except Exception:
            return None
    
    def _get_fallback_provider(self) -> Optional[str]:
        """Obtener ID de proveedor fallback"""
        try:
            return self.get_or_create_contact(
                name="Proveedor Genérico",
                contact_type='provider',
                identification="00000000",
                email="proveedor@generico.com"
            )
        except Exception:
            return None
    
    def get_or_create_item(
        self,
        name: str,
        price: float,
        quantity: float = 1.0,
        **kwargs
    ) -> Optional[str]:
        """
        Obtener o crear item en Alegra
        
        Args:
            name: Nombre del item
            price: Precio del item
            quantity: Cantidad
            **kwargs: Datos adicionales del item
            
        Returns:
            ID del item o None si falla
        """
        try:
            # Verificar caché
            cache_key = f"{name}_{price}"
            if cache_key in self._items_cache:
                self.logger.debug("Item encontrado en caché", extra={"name": name})
                return self._items_cache[cache_key]
            
            # Buscar item existente
            item_id = self._search_item(name)
            if item_id:
                self._items_cache[cache_key] = item_id
                return item_id
            
            # Crear nuevo item
            item_data = {
                'name': name,
                'price': price,
                'inventory': {
                    'unit': kwargs.get('unit', 'unidad'),
                    'initialQuantity': quantity
                },
                'accountingAccount': kwargs.get('accounting_account', '4-01-01-01-01'),
                'observations': kwargs.get('observations', '')
            }
            
            result = self._make_request('POST', 'items', item_data)
            
            if result and 'id' in result:
                item_id = str(result['id'])
                self._items_cache[cache_key] = item_id
                
                self.logger.info("Item creado exitosamente", extra={
                    "item_id": item_id,
                    "name": name,
                    "price": price
                })
                
                return item_id
            
            return None
            
        except Exception as e:
            self.logger.error("Error creando/obteniendo item", extra={
                "name": name,
                "price": price,
                "error": str(e)
            })
            return None
    
    def _search_item(self, name: str) -> Optional[str]:
        """Buscar item existente por nombre"""
        try:
            params = {
                'query': name,
                'limit': 10
            }
            
            result = self._make_request('GET', 'items', params=params)
            
            if result and 'data' in result:
                for item in result['data']:
                    if item.get('name', '').lower() == name.lower():
                        return str(item['id'])
            
            return None
            
        except Exception as e:
            self.logger.debug("Error buscando item", extra={"error": str(e)})
            return None
    
    def create_bill(self, bill_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear bill (factura de compra) en Alegra
        
        Args:
            bill_data: Datos de la bill
            
        Returns:
            Datos de la bill creada o None si falla
        """
        try:
            result = self._make_request('POST', 'bills', bill_data)
            
            if result:
                self.logger.info("Bill creada exitosamente", extra={
                    "bill_id": result.get('id'),
                    "client_id": bill_data.get('client', {}).get('id')
                })
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error("Error creando bill", extra={
                "error": str(e),
                "bill_data": bill_data
            })
            return None
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear invoice (factura de venta) en Alegra
        
        Args:
            invoice_data: Datos de la invoice
            
        Returns:
            Datos de la invoice creada o None si falla
        """
        try:
            result = self._make_request('POST', 'invoices', invoice_data)
            
            if result:
                self.logger.info("Invoice creada exitosamente", extra={
                    "invoice_id": result.get('id'),
                    "client_id": invoice_data.get('client', {}).get('id')
                })
                
                return result
            
            return None
            
        except Exception as e:
            self.logger.error("Error creando invoice", extra={
                "error": str(e),
                "invoice_data": invoice_data
            })
            return None
    
    def get_company_info(self) -> Optional[Dict[str, Any]]:
        """Obtener información de la empresa"""
        try:
            result = self._make_request('GET', 'company')
            return result
        except Exception as e:
            self.logger.error("Error obteniendo información de empresa", extra={"error": str(e)})
            return None
    
    def clear_cache(self) -> None:
        """Limpiar caché de contactos e items"""
        self._contacts_cache.clear()
        self._items_cache.clear()
        self.logger.info("Caché de Alegra limpiado")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del caché"""
        return {
            'contacts_cache_size': len(self._contacts_cache),
            'items_cache_size': len(self._items_cache),
            'circuit_breaker_state': self.circuit_state.value,
            'failure_count': self.failure_count
        }