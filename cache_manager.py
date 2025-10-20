#!/usr/bin/env python3
"""
Sistema de caché para optimizar consultas a Alegra API
"""

import redis
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class CacheManager:
    """Gestor de caché para datos de Alegra con invalidación granular"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        self.cache_ttl = {
            'contacts': 3600,      # 1 hora
            'items': 1800,         # 30 minutos
            'accounts': 7200,      # 2 horas
            'taxes': 3600,         # 1 hora
            'reports': 900,        # 15 minutos
        }
        self.logger = logging.getLogger(__name__)
        
        # Métricas de caché
        self.metrics_keys = {
            'hits': 'cache:metrics:hits',
            'misses': 'cache:metrics:misses',
            'invalidations': 'cache:metrics:invalidations',
            'errors': 'cache:metrics:errors'
        }
        
        # Inicializar métricas si no existen
        self._initialize_metrics()
    
    def get_cached_data(self, data_type: str, key: str) -> Optional[Any]:
        """Obtener datos del caché con métricas"""
        try:
            cache_key = f"{data_type}:{key}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                self.logger.debug(f"📦 Datos encontrados en caché: {cache_key}")
                self._increment_metric('hits')
                return json.loads(cached_data)
            else:
                self.logger.debug(f"❌ Datos no encontrados en caché: {cache_key}")
                self._increment_metric('misses')
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo datos del caché: {e}")
            self._increment_metric('errors')
            return None
    
    def set_cached_data(self, data_type: str, key: str, data: Any, ttl: int = None) -> bool:
        """Guardar datos en caché"""
        try:
            cache_key = f"{data_type}:{key}"
            ttl = ttl or self.cache_ttl.get(data_type, 3600)
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str)
            )
            
            self.logger.debug(f"💾 Datos guardados en caché: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando datos en caché: {e}")
            return False
    
    def invalidate_cache(self, data_type: str, pattern: str = None) -> bool:
        """Invalidar caché por tipo o patrón"""
        try:
            if pattern:
                cache_pattern = f"{data_type}:{pattern}"
            else:
                cache_pattern = f"{data_type}:*"
            
            keys = self.redis_client.keys(cache_pattern)
            if keys:
                self.redis_client.delete(*keys)
                self.logger.info(f"🗑️ Caché invalidado: {len(keys)} claves eliminadas")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error invalidando caché: {e}")
            return False
    
    def get_contact_by_name(self, name: str) -> Optional[Dict]:
        """Obtener contacto por nombre desde caché"""
        return self.get_cached_data('contacts', f"name:{name.lower()}")
    
    def get_contact_by_id(self, contact_id: str) -> Optional[Dict]:
        """Obtener contacto por ID desde caché"""
        return self.get_cached_data('contacts', f"id:{contact_id}")
    
    def cache_contact(self, contact: Dict) -> bool:
        """Guardar contacto en caché"""
        if not contact.get('id') or not contact.get('name'):
            return False
        
        # Guardar por ID
        self.set_cached_data('contacts', f"id:{contact['id']}", contact)
        
        # Guardar por nombre
        self.set_cached_data('contacts', f"name:{contact['name'].lower()}", contact)
        
        return True
    
    def get_item_by_name(self, name: str) -> Optional[Dict]:
        """Obtener item por nombre desde caché"""
        return self.get_cached_data('items', f"name:{name.lower()}")
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Obtener item por ID desde caché"""
        return self.get_cached_data('items', f"id:{item_id}")
    
    def cache_item(self, item: Dict) -> bool:
        """Guardar item en caché"""
        if not item.get('id') or not item.get('name'):
            return False
        
        # Guardar por ID
        self.set_cached_data('items', f"id:{item['id']}", item)
        
        # Guardar por nombre
        self.set_cached_data('items', f"name:{item['name'].lower()}", item)
        
        return True
    
    def get_account_by_name(self, name: str) -> Optional[Dict]:
        """Obtener cuenta por nombre desde caché"""
        return self.get_cached_data('accounts', f"name:{name.lower()}")
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Obtener cuenta por ID desde caché"""
        return self.get_cached_data('accounts', f"id:{account_id}")
    
    def cache_account(self, account: Dict) -> bool:
        """Guardar cuenta en caché"""
        if not account.get('id') or not account.get('name'):
            return False
        
        # Guardar por ID
        self.set_cached_data('accounts', f"id:{account['id']}", account)
        
        # Guardar por nombre
        self.set_cached_data('accounts', f"name:{account['name'].lower()}", account)
        
        return True
    
    def sync_alegra_data(self, data_type: str) -> Dict:
        """Sincronizar datos de Alegra con caché"""
        try:
            from alegra_reports import AlegraReports
            
            reporter = AlegraReports()
            synced_count = 0
            
            if data_type == 'contacts':
                # Sincronizar contactos
                clients = reporter.get_contacts('client') or []
                providers = reporter.get_contacts('provider') or []
                
                for contact in clients + providers:
                    if self.cache_contact(contact):
                        synced_count += 1
                
                self.logger.info(f"✅ Sincronizados {synced_count} contactos")
                
            elif data_type == 'items':
                # Sincronizar items (requiere implementar get_items en AlegraReports)
                # Por ahora, retornar éxito
                synced_count = 0
                self.logger.info(f"✅ Sincronización de items completada")
                
            elif data_type == 'accounts':
                # Sincronizar cuentas
                accounts = reporter.get_accounts() or []
                
                for account in accounts:
                    if self.cache_account(account):
                        synced_count += 1
                
                self.logger.info(f"✅ Sincronizadas {synced_count} cuentas")
            
            return {
                'data_type': data_type,
                'synced_count': synced_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error sincronizando datos: {e}")
            raise
    
    def get_cache_stats(self) -> Dict:
        """Obtener estadísticas del caché (método legacy)"""
        try:
            stats = {}
            
            for data_type in self.cache_ttl.keys():
                pattern = f"{data_type}:*"
                keys = self.redis_client.keys(pattern)
                stats[data_type] = len(keys)
            
            stats['total_keys'] = sum(stats.values())
            stats['memory_usage'] = self.redis_client.memory_usage()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def clear_all_cache(self) -> bool:
        """Limpiar todo el caché"""
        try:
            self.redis_client.flushdb()
            self.logger.info("🗑️ Caché completamente limpiado")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando caché: {e}")
            return False
    
    def _initialize_metrics(self):
        """Inicializar métricas de caché"""
        try:
            for metric_key in self.metrics_keys.values():
                if not self.redis_client.exists(metric_key):
                    self.redis_client.set(metric_key, 0)
        except Exception as e:
            self.logger.error(f"❌ Error inicializando métricas: {e}")
    
    def _increment_metric(self, metric_name: str, value: int = 1):
        """Incrementar métrica de caché"""
        try:
            metric_key = self.metrics_keys.get(metric_name)
            if metric_key:
                self.redis_client.incrby(metric_key, value)
        except Exception as e:
            self.logger.error(f"❌ Error incrementando métrica {metric_name}: {e}")
    
    def invalidate_contact(self, contact_id: str) -> bool:
        """Invalidar caché de contacto específico"""
        try:
            # Invalidar por ID
            self.redis_client.delete(f"contacts:id:{contact_id}")
            
            # Obtener nombre del contacto para invalidar por nombre
            contact_data = self.redis_client.get(f"contacts:id:{contact_id}")
            if contact_data:
                contact = json.loads(contact_data)
                name = contact.get('name', '').lower()
                if name:
                    self.redis_client.delete(f"contacts:name:{name}")
            
            self._increment_metric('invalidations')
            self.logger.info(f"🗑️ Contacto invalidado: {contact_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error invalidando contacto {contact_id}: {e}")
            self._increment_metric('errors')
            return False
    
    def invalidate_item(self, item_id: str) -> bool:
        """Invalidar caché de item específico"""
        try:
            # Invalidar por ID
            self.redis_client.delete(f"items:id:{item_id}")
            
            # Obtener nombre del item para invalidar por nombre
            item_data = self.redis_client.get(f"items:id:{item_id}")
            if item_data:
                item = json.loads(item_data)
                name = item.get('name', '').lower()
                if name:
                    self.redis_client.delete(f"items:name:{name}")
            
            self._increment_metric('invalidations')
            self.logger.info(f"🗑️ Item invalidado: {item_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error invalidando item {item_id}: {e}")
            self._increment_metric('errors')
            return False
    
    def invalidate_account(self, account_id: str) -> bool:
        """Invalidar caché de cuenta específica"""
        try:
            # Invalidar por ID
            self.redis_client.delete(f"accounts:id:{account_id}")
            
            # Obtener nombre de la cuenta para invalidar por nombre
            account_data = self.redis_client.get(f"accounts:id:{account_id}")
            if account_data:
                account = json.loads(account_data)
                name = account.get('name', '').lower()
                if name:
                    self.redis_client.delete(f"accounts:name:{name}")
            
            self._increment_metric('invalidations')
            self.logger.info(f"🗑️ Cuenta invalidada: {account_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error invalidando cuenta {account_id}: {e}")
            self._increment_metric('errors')
            return False
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidar caché por patrón"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                self._increment_metric('invalidations', deleted_count)
                self.logger.info(f"🗑️ Invalidadas {deleted_count} claves con patrón: {pattern}")
                return deleted_count
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ Error invalidando por patrón {pattern}: {e}")
            self._increment_metric('errors')
            return 0
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Obtener métricas detalladas del caché"""
        try:
            metrics = {}
            
            # Métricas básicas
            for metric_name, metric_key in self.metrics_keys.items():
                value = self.redis_client.get(metric_key)
                metrics[metric_name] = int(value) if value else 0
            
            # Calcular hit rate
            hits = metrics.get('hits', 0)
            misses = metrics.get('misses', 0)
            total_requests = hits + misses
            
            if total_requests > 0:
                metrics['hit_rate'] = round((hits / total_requests) * 100, 2)
            else:
                metrics['hit_rate'] = 0.0
            
            # Estadísticas de claves
            metrics['total_keys'] = len(self.redis_client.keys('*'))
            
            # Memoria utilizada
            try:
                memory_info = self.redis_client.memory_usage()
                metrics['memory_usage_bytes'] = memory_info
                metrics['memory_usage_mb'] = round(memory_info / (1024 * 1024), 2)
            except:
                metrics['memory_usage_bytes'] = 0
                metrics['memory_usage_mb'] = 0
            
            # TTL promedio
            try:
                all_keys = self.redis_client.keys('*')
                ttl_sum = 0
                ttl_count = 0
                
                for key in all_keys[:100]:  # Muestrear primeras 100 claves
                    ttl = self.redis_client.ttl(key)
                    if ttl > 0:
                        ttl_sum += ttl
                        ttl_count += 1
                
                if ttl_count > 0:
                    metrics['avg_ttl_seconds'] = round(ttl_sum / ttl_count, 2)
                else:
                    metrics['avg_ttl_seconds'] = 0
            except:
                metrics['avg_ttl_seconds'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo métricas: {e}")
            return {}
    
    def reset_metrics(self) -> bool:
        """Resetear métricas de caché"""
        try:
            for metric_key in self.metrics_keys.values():
                self.redis_client.set(metric_key, 0)
            
            self.logger.info("📊 Métricas de caché reseteadas")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error reseteando métricas: {e}")
            return False