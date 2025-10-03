import psutil
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_available_gb: float
    active_connections: int
    process_count: int
    bot_memory_mb: float
    bot_cpu_percent: float
    
class PerformanceMonitor:
    """
    Real-time performance monitoring for bot and system resources.
    Provides alerts when thresholds are exceeded.
    """
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.is_running = False
        self.monitor_task = None
        
        # Thresholds for alerts
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'queue_percent': 80.0
        }
        
        # Metrics history (last 100 readings)
        self.metrics_history = []
        self.max_history = 100
        
        # Alert cooldown to prevent spam
        self.last_alert_time = {}
        self.alert_cooldown_seconds = 300  # 5 minutes
        
        logger.info(f"Performance monitor initialized with {check_interval}s interval")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_available_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Process count
            process_count = len(psutil.pids())
            
            # Bot-specific metrics
            bot_memory_mb = 0
            bot_cpu_percent = 0
            
            try:
                current_process = psutil.Process()
                bot_memory_mb = current_process.memory_info().rss / (1024 * 1024)
                bot_cpu_percent = current_process.cpu_percent()
            except Exception as e:
                logger.debug(f"Could not get bot process metrics: {e}")
            
            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_available_gb=disk_available_gb,
                active_connections=connections,
                process_count=process_count,
                bot_memory_mb=bot_memory_mb,
                bot_cpu_percent=bot_cpu_percent
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def check_thresholds(self, metrics: SystemMetrics, queue_stats: Optional[Dict] = None) -> list:
        """
        Check if any metrics exceed thresholds
        
        Returns:
            List of alert messages
        """
        alerts = []
        current_time = datetime.now()
        
        def should_send_alert(alert_type: str) -> bool:
            """Check if enough time has passed since last alert"""
            if alert_type not in self.last_alert_time:
                return True
            
            time_since_last = (current_time - self.last_alert_time[alert_type]).total_seconds()
            return time_since_last >= self.alert_cooldown_seconds
        
        # Check CPU
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            if should_send_alert('cpu'):
                alerts.append(f"⚠️ HIGH CPU USAGE: {metrics.cpu_percent:.1f}% (threshold: {self.thresholds['cpu_percent']}%)")
                self.last_alert_time['cpu'] = current_time
        
        # Check Memory
        if metrics.memory_percent > self.thresholds['memory_percent']:
            if should_send_alert('memory'):
                alerts.append(
                    f"⚠️ HIGH MEMORY USAGE: {metrics.memory_percent:.1f}% "
                    f"(available: {metrics.memory_available_mb:.0f} MB)"
                )
                self.last_alert_time['memory'] = current_time
        
        # Check Disk
        if metrics.disk_usage_percent > self.thresholds['disk_percent']:
            if should_send_alert('disk'):
                alerts.append(
                    f"⚠️ LOW DISK SPACE: {metrics.disk_usage_percent:.1f}% used "
                    f"(available: {metrics.disk_available_gb:.1f} GB)"
                )
                self.last_alert_time['disk'] = current_time
        
        # Check Queue if provided
        if queue_stats:
            queue_capacity = (queue_stats.get('current_queue_size', 0) / 1000) * 100
            if queue_capacity > self.thresholds['queue_percent']:
                if should_send_alert('queue'):
                    alerts.append(
                        f"⚠️ QUEUE FILLING UP: {queue_stats.get('current_queue_size', 0)} items "
                        f"({queue_capacity:.1f}% capacity)"
                    )
                    self.last_alert_time['queue'] = current_time
        
        return alerts
    
    async def monitor_loop(self, queue=None):
        """Main monitoring loop"""
        logger.info("Performance monitoring started")
        
        while self.is_running:
            try:
                # Collect metrics
                metrics = self.get_system_metrics()
                
                if metrics:
                    # Store in history
                    self.metrics_history.append(metrics)
                    if len(self.metrics_history) > self.max_history:
                        self.metrics_history.pop(0)
                    
                    # Get queue stats if available
                    queue_stats = queue.get_stats() if queue else None
                    
                    # Check thresholds
                    alerts = self.check_thresholds(metrics, queue_stats)
                    
                    # Log alerts
                    for alert in alerts:
                        logger.warning(alert)
                    
                    # Log current status
                    logger.info(
                        f"System Status - CPU: {metrics.cpu_percent:.1f}%, "
                        f"Memory: {metrics.memory_percent:.1f}% "
                        f"({metrics.memory_available_mb:.0f} MB available), "
                        f"Bot: {metrics.bot_memory_mb:.1f} MB, "
                        f"Connections: {metrics.active_connections}"
                    )
                    
                    if queue_stats:
                        logger.info(
                            f"Queue Status - Size: {queue_stats['current_queue_size']}, "
                            f"Processed: {queue_stats['total_processed']}, "
                            f"Failed: {queue_stats['total_failed']}, "
                            f"Avg Processing Time: {queue_stats['average_processing_time']:.2f}s"
                        )
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def start(self, queue=None):
        """Start performance monitoring"""
        if self.is_running:
            logger.warning("Performance monitor is already running")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self.monitor_loop(queue))
        logger.info("Performance monitor started")
    
    async def stop(self):
        """Stop performance monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitor stopped")
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent metrics"""
        if not self.metrics_history:
            return None
        
        metrics = self.metrics_history[-1]
        return {
            'timestamp': metrics.timestamp,
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'memory_available_mb': metrics.memory_available_mb,
            'disk_usage_percent': metrics.disk_usage_percent,
            'disk_available_gb': metrics.disk_available_gb,
            'active_connections': metrics.active_connections,
            'bot_memory_mb': metrics.bot_memory_mb,
            'bot_cpu_percent': metrics.bot_cpu_percent
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics from metrics history"""
        if not self.metrics_history:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        
        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'memory_min': min(memory_values),
            'samples': len(self.metrics_history)
        }
    
    def export_metrics(self, filepath: str):
        """Export metrics history to JSON file"""
        try:
            data = [
                {
                    'timestamp': m.timestamp,
                    'cpu_percent': m.cpu_percent,
                    'memory_percent': m.memory_percent,
                    'memory_available_mb': m.memory_available_mb,
                    'disk_usage_percent': m.disk_usage_percent,
                    'disk_available_gb': m.disk_available_gb,
                    'active_connections': m.active_connections,
                    'bot_memory_mb': m.bot_memory_mb,
                    'bot_cpu_percent': m.bot_cpu_percent
                }
                for m in self.metrics_history
            ]
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(data)} metrics to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")

