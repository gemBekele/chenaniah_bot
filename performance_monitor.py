#!/usr/bin/env python3
"""
Performance Monitoring Tool for Chenaniah Bot System
Monitors system resources, database performance, and API response times
"""

import asyncio
import aiohttp
import psutil
import sqlite3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, api_base_url: str = "http://localhost:5000", db_path: str = "./vocalist_screening.db"):
        self.api_base_url = api_base_url
        self.db_path = db_path
        self.metrics = []
        self.session = None
        
    async def create_session(self):
        """Create aiohttp session"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            memory_used = memory.used / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            disk_used = disk.used / (1024**3)  # GB
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower() or 'node' in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'available_gb': memory_available,
                    'used_gb': memory_used
                },
                'disk': {
                    'percent': disk_percent,
                    'free_gb': disk_free,
                    'used_gb': disk_used
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': processes
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table sizes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                table_info = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    # Get table size (approximate)
                    cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    table_info[table_name] = {
                        'row_count': count
                    }
                
                # Get database file size
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                
                # Get recent activity (last hour)
                cursor.execute("""
                    SELECT COUNT(*) FROM submissions 
                    WHERE submitted_at > datetime('now', '-1 hour')
                """)
                recent_submissions = cursor.fetchone()[0]
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'database_size_bytes': db_size,
                    'database_size_mb': db_size / (1024**2),
                    'table_info': table_info,
                    'recent_submissions_1h': recent_submissions
                }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {}
    
    async def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoint response times"""
        endpoints = [
            '/api/health',
            '/api/stats',
            '/api/submissions'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                url = f"{self.api_base_url}{endpoint}"
                
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    status_code = response.status
                    
                    results[endpoint] = {
                        'response_time': response_time,
                        'status_code': status_code,
                        'success': status_code == 200
                    }
                    
            except Exception as e:
                results[endpoint] = {
                    'response_time': None,
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'endpoints': results
        }
    
    async def monitor_audio_files(self) -> Dict[str, Any]:
        """Monitor audio file storage"""
        try:
            audio_dir = Path("audio_files")
            if not audio_dir.exists():
                return {'timestamp': datetime.now().isoformat(), 'error': 'Audio directory not found'}
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            for file_path in audio_dir.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    ext = file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024**2),
                'file_types': file_types
            }
        except Exception as e:
            logger.error(f"Error monitoring audio files: {e}")
            return {'timestamp': datetime.now().isoformat(), 'error': str(e)}
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        await self.create_session()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_metrics(),
            'database': self.get_database_metrics(),
            'api': await self.test_api_endpoints(),
            'audio_files': await self.monitor_audio_files()
        }
        
        await self.close_session()
        return metrics
    
    async def monitor_continuously(self, interval_seconds: int = 30, duration_minutes: int = 10):
        """Monitor system continuously for specified duration"""
        logger.info(f"Starting continuous monitoring for {duration_minutes} minutes (interval: {interval_seconds}s)")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                metrics = await self.collect_metrics()
                self.metrics.append(metrics)
                
                # Log key metrics
                system = metrics.get('system', {})
                cpu = system.get('cpu', {}).get('percent', 0)
                memory = system.get('memory', {}).get('percent', 0)
                
                logger.info(f"CPU: {cpu:.1f}%, Memory: {memory:.1f}%")
                
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(interval_seconds)
        
        logger.info("Continuous monitoring completed")
    
    def analyze_metrics(self) -> Dict[str, Any]:
        """Analyze collected metrics and provide insights"""
        if not self.metrics:
            return {'error': 'No metrics collected'}
        
        # System metrics analysis
        cpu_values = [m.get('system', {}).get('cpu', {}).get('percent', 0) for m in self.metrics]
        memory_values = [m.get('system', {}).get('memory', {}).get('percent', 0) for m in self.metrics]
        
        # API response times
        api_times = []
        for m in self.metrics:
            api = m.get('api', {}).get('endpoints', {})
            for endpoint, data in api.items():
                if data.get('response_time'):
                    api_times.append(data['response_time'])
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_samples': len(self.metrics),
            'system_analysis': {
                'cpu': {
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0
                },
                'memory': {
                    'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0
                }
            },
            'api_analysis': {
                'avg_response_time': sum(api_times) / len(api_times) if api_times else 0,
                'max_response_time': max(api_times) if api_times else 0,
                'min_response_time': min(api_times) if api_times else 0
            },
            'recommendations': self.generate_recommendations(cpu_values, memory_values, api_times)
        }
        
        return analysis
    
    def generate_recommendations(self, cpu_values: List[float], memory_values: List[float], api_times: List[float]) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []
        
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            
            if avg_cpu > 80:
                recommendations.append("High CPU usage detected. Consider optimizing code or scaling up.")
            if max_cpu > 95:
                recommendations.append("CPU usage spikes detected. Monitor for bottlenecks.")
        
        if memory_values:
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            
            if avg_memory > 80:
                recommendations.append("High memory usage detected. Consider memory optimization.")
            if max_memory > 95:
                recommendations.append("Memory usage spikes detected. Check for memory leaks.")
        
        if api_times:
            avg_api_time = sum(api_times) / len(api_times)
            max_api_time = max(api_times)
            
            if avg_api_time > 2.0:
                recommendations.append("Slow API response times detected. Consider database optimization.")
            if max_api_time > 5.0:
                recommendations.append("API response time spikes detected. Check for blocking operations.")
        
        if not recommendations:
            recommendations.append("System performance appears to be within normal ranges.")
        
        return recommendations
    
    def save_metrics(self, filename: str = None):
        """Save collected metrics to JSON file"""
        if not filename:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Performance metrics saved to {filename}")
    
    def save_analysis(self, filename: str = None):
        """Save analysis results to JSON file"""
        if not filename:
            filename = f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        analysis = self.analyze_metrics()
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Performance analysis saved to {filename}")
        
        # Print recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            logger.info("Performance Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec}")

async def main():
    parser = argparse.ArgumentParser(description='Performance Monitoring Tool')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--db-path', default='./vocalist_screening.db', help='Database path')
    parser.add_argument('--interval', type=int, default=30, help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=10, help='Monitoring duration in minutes')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze existing metrics')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.api_url, args.db_path)
    
    try:
        if args.analyze_only:
            # Load existing metrics and analyze
            monitor.metrics = json.load(open('performance_metrics_latest.json', 'r'))
            monitor.save_analysis()
        else:
            # Run continuous monitoring
            await monitor.monitor_continuously(args.interval, args.duration)
            monitor.save_metrics()
            monitor.save_analysis()
        
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())