#!/usr/bin/env python3
"""
Monitor de colas Celery para el sistema de facturas
"""

import time
import json
from datetime import datetime
from celery import Celery
from celery_config import app
from cache_manager import CacheManager

class QueueMonitor:
    """Monitor de colas y tareas Celery"""
    
    def __init__(self):
        self.app = app
        self.cache_manager = CacheManager()
        self.logger = None
    
    def get_queue_stats(self) -> dict:
        """Obtener estadísticas de las colas"""
        try:
            inspect = self.app.control.inspect()
            
            # Estadísticas de workers
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            # Estadísticas de colas
            queue_stats = {}
            
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in queue_stats:
                            queue_stats[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                        queue_stats[queue]['active'] += 1
            
            if scheduled_tasks:
                for worker, tasks in scheduled_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in queue_stats:
                            queue_stats[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                        queue_stats[queue]['scheduled'] += 1
            
            if reserved_tasks:
                for worker, tasks in reserved_tasks.items():
                    for task in tasks:
                        queue = task.get('delivery_info', {}).get('routing_key', 'unknown')
                        if queue not in queue_stats:
                            queue_stats[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
                        queue_stats[queue]['reserved'] += 1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'queues': queue_stats,
                'total_active': sum(stats['active'] for stats in queue_stats.values()),
                'total_scheduled': sum(stats['scheduled'] for stats in queue_stats.values()),
                'total_reserved': sum(stats['reserved'] for stats in queue_stats.values())
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_worker_stats(self) -> dict:
        """Obtener estadísticas de workers"""
        try:
            inspect = self.app.control.inspect()
            
            # Información de workers
            stats = inspect.stats()
            active = inspect.active()
            scheduled = inspect.scheduled()
            reserved = inspect.reserved()
            
            worker_info = {}
            
            if stats:
                for worker, worker_stats in stats.items():
                    worker_info[worker] = {
                        'status': 'online',
                        'total_tasks': worker_stats.get('total', {}).get('invoicebot.tasks.process_invoice', 0),
                        'active_tasks': len(active.get(worker, [])),
                        'scheduled_tasks': len(scheduled.get(worker, [])),
                        'reserved_tasks': len(reserved.get(worker, [])),
                        'pool': worker_stats.get('pool', {}),
                        'rusage': worker_stats.get('rusage', {})
                    }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'workers': worker_info,
                'total_workers': len(worker_info)
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_task_history(self, limit: int = 100) -> dict:
        """Obtener historial de tareas"""
        try:
            # Esto requeriría una base de datos para persistir el historial
            # Por ahora, retornar estructura básica
            return {
                'timestamp': datetime.now().isoformat(),
                'message': 'Historial de tareas no implementado',
                'limit': limit
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_cache_stats(self) -> dict:
        """Obtener estadísticas del caché"""
        try:
            return self.cache_manager.get_cache_metrics()
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_compliance_stats(self) -> dict:
        """Obtener estadísticas de cumplimiento fiscal"""
        try:
            from dian_resilience import DIANResilienceManager
            
            resilience_manager = DIANResilienceManager()
            return resilience_manager.get_compliance_stats()
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_system_health(self) -> dict:
        """Obtener salud general del sistema"""
        try:
            # Verificar conectividad con Redis
            redis_healthy = self.cache_manager.redis_client.ping()
            
            # Verificar workers activos
            inspect = self.app.control.inspect()
            active_workers = inspect.active()
            workers_healthy = len(active_workers) > 0
            
            # Verificar colas
            queue_stats = self.get_queue_stats()
            queues_healthy = 'error' not in queue_stats
            
            # Calcular score de salud
            health_score = 0
            if redis_healthy:
                health_score += 0.4
            if workers_healthy:
                health_score += 0.4
            if queues_healthy:
                health_score += 0.2
            
            return {
                'timestamp': datetime.now().isoformat(),
                'health_score': round(health_score, 2),
                'status': 'healthy' if health_score >= 0.8 else 'degraded' if health_score >= 0.5 else 'unhealthy',
                'components': {
                    'redis': 'healthy' if redis_healthy else 'unhealthy',
                    'workers': 'healthy' if workers_healthy else 'unhealthy',
                    'queues': 'healthy' if queues_healthy else 'unhealthy'
                },
                'recommendations': self._get_health_recommendations(health_score, redis_healthy, workers_healthy, queues_healthy)
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'health_score': 0.0,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _get_health_recommendations(self, health_score: float, redis_healthy: bool, 
                                  workers_healthy: bool, queues_healthy: bool) -> list:
        """Obtener recomendaciones de salud"""
        recommendations = []
        
        if not redis_healthy:
            recommendations.append("Verificar conexión con Redis")
        
        if not workers_healthy:
            recommendations.append("Iniciar workers de Celery")
        
        if not queues_healthy:
            recommendations.append("Verificar configuración de colas")
        
        if health_score < 0.5:
            recommendations.append("Revisar logs de errores")
            recommendations.append("Considerar reiniciar el sistema")
        
        return recommendations
    
    def print_dashboard(self):
        """Imprimir dashboard en consola"""
        print("\n" + "="*80)
        print("📊 DASHBOARD DE MONITOREO - SISTEMA DE FACTURAS")
        print("="*80)
        
        # Salud del sistema
        health = self.get_system_health()
        print(f"\n🏥 SALUD DEL SISTEMA: {health['status'].upper()}")
        print(f"   Score: {health['health_score']}/1.0")
        
        for component, status in health.get('components', {}).items():
            emoji = "✅" if status == 'healthy' else "❌"
            print(f"   {emoji} {component.title()}: {status}")
        
        # Estadísticas de colas
        queue_stats = self.get_queue_stats()
        if 'error' not in queue_stats:
            print(f"\n📋 ESTADÍSTICAS DE COLAS:")
            print(f"   Total Activas: {queue_stats['total_active']}")
            print(f"   Total Programadas: {queue_stats['total_scheduled']}")
            print(f"   Total Reservadas: {queue_stats['total_reserved']}")
            
            for queue, stats in queue_stats['queues'].items():
                print(f"   📦 {queue}: A:{stats['active']} S:{stats['scheduled']} R:{stats['reserved']}")
        
        # Estadísticas de workers
        worker_stats = self.get_worker_stats()
        if 'error' not in worker_stats:
            print(f"\n👷 WORKERS ACTIVOS: {worker_stats['total_workers']}")
            for worker, stats in worker_stats['workers'].items():
                print(f"   🔧 {worker}: {stats['active_tasks']} tareas activas")
        
        # Estadísticas de caché
        cache_stats = self.get_cache_stats()
        if 'error' not in cache_stats:
            print(f"\n💾 CACHÉ:")
            print(f"   Total de claves: {cache_stats.get('total_keys', 0)}")
            print(f"   Hit Rate: {cache_stats.get('hit_rate', 0)}%")
            print(f"   Hits: {cache_stats.get('hits', 0)}")
            print(f"   Misses: {cache_stats.get('misses', 0)}")
            print(f"   Memoria: {cache_stats.get('memory_usage_mb', 0)} MB")
            print(f"   TTL Promedio: {cache_stats.get('avg_ttl_seconds', 0)}s")
        
        # Estadísticas de cumplimiento fiscal
        compliance_stats = self.get_compliance_stats()
        if 'error' not in compliance_stats:
            print(f"\n📋 CUMPLIMIENTO FISCAL:")
            print(f"   Total facturas: {compliance_stats.get('total_invoices', 0)}")
            print(f"   ✅ Validadas: {compliance_stats.get('validated', 0)} ({compliance_stats.get('validated_percentage', 0)}%)")
            print(f"   ⏳ Pendientes: {compliance_stats.get('pending', 0)} ({compliance_stats.get('pending_percentage', 0)}%)")
            print(f"   🔄 Reintentos: {compliance_stats.get('retry', 0)} ({compliance_stats.get('retry_percentage', 0)}%)")
            print(f"   ❌ Fallidas: {compliance_stats.get('failed', 0)} ({compliance_stats.get('failed_percentage', 0)}%)")
        
        print("\n" + "="*80)
        print(f"🕐 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de colas Celery')
    parser.add_argument('--dashboard', action='store_true', 
                       help='Mostrar dashboard en consola')
    parser.add_argument('--json', action='store_true',
                       help='Mostrar estadísticas en formato JSON')
    parser.add_argument('--watch', action='store_true',
                       help='Monitoreo continuo (actualizar cada 30 segundos)')
    
    args = parser.parse_args()
    
    monitor = QueueMonitor()
    
    if args.json:
        stats = {
            'health': monitor.get_system_health(),
            'queues': monitor.get_queue_stats(),
            'workers': monitor.get_worker_stats(),
            'cache': monitor.get_cache_stats()
        }
        print(json.dumps(stats, indent=2))
    
    elif args.watch:
        try:
            while True:
                monitor.print_dashboard()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Monitoreo detenido")
    
    else:
        monitor.print_dashboard()

if __name__ == "__main__":
    main()