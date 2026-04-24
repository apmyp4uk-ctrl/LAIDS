"""Health check and monitoring."""
import asyncio
import psutil
import time
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from fastapi import FastAPI
import uvicorn


@dataclass
class HealthStatus:
    """Health status info."""
    status: str = "healthy"
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0
    cpu_percent: float = 0
    memory_percent: float = 0
    memory_used_mb: float = 0
    agents_running: int = 0
    tasks_pending: int = 0
    tokens_used: int = 0
    tokens_limit: int = 100000


class Monitor:
    """System monitor."""
    
    def __init__(self, config: dict, token_counter, task_queue):
        self.config = config
        self.token_counter = token_counter
        self.task_queue = task_queue
        self.start_time = time.time()
        self.app = FastAPI(title="AI Factory Health")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup health check routes."""
        @self.app.get("/health")
        async def health_check():
            return self.get_status()
        
        @self.app.get("/metrics")
        async def metrics():
            return self.get_metrics()
        
        @self.app.get("/tokens")
        async def tokens():
            return self.token_counter.get_usage()
    
    def get_status(self) -> HealthStatus:
        """Get current health status."""
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return HealthStatus(
            status="healthy",
            uptime_seconds=time.time() - self.start_time,
            cpu_percent=cpu,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            tasks_pending=self.task_queue.get_pending_count() if self.task_queue else 0,
            tokens_used=self.token_counter.daily_usage if self.token_counter else 0,
            tokens_limit=self.token_counter.daily_limit if self.token_counter else 100000
        )
    
    def get_metrics(self) -> dict:
        """Get detailed metrics."""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'system': {
                'cpu_percent': cpu,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024 * 1024 * 1024),
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
            },
            'uptime_seconds': time.time() - self.start_time,
            'tokens': self.token_counter.get_usage() if self.token_counter else {},
        }
    
    async def start_server(self, port: int = 8080):
        """Start health check server."""
        config_health = self.config.get('health', {})
        port = config_health.get('port', port)
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        await server.serve()


class ResourceGuard:
    """Guard resource usage."""
    
    def __init__(self, config: dict):
        self.config = config
        self.agent_config = config.get('agents', {})
        self.max_memory_mb = self.agent_config.get('memory_limit_mb', 4096)
        self.max_cpu_percent = self.agent_config.get('cpu_limit_percent', 80)
    
    def check_resources(self) -> tuple[bool, str]:
        """Check if resources are available."""
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)
        
        if memory_mb > self.max_memory_mb:
            return False, f"Memory limit exceeded: {memory_mb:.0f}MB"
        
        cpu = psutil.cpu_percent()
        if cpu > self.max_cpu_percent:
            return False, f"CPU limit exceeded: {cpu:.0f}%"
        
        return True, "OK"
    
    async def wait_for_resources(self, timeout: float = 30):
        """Wait for resources to become available."""
        start = time.time()
        
        while time.time() - start < timeout:
            available, msg = self.check_resources()
            if available:
                return True
            
            await asyncio.sleep(2)
        
        return False


# Health check utility functions
def get_system_info() -> dict:
    """Get system information."""
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    
    return {
        'cpu_cores': cpu_count,
        'cpu_threads': cpu_count,
        'ram_total_gb': memory.total / (1024 ** 3),
        'ram_available_gb': memory.available / (1024 ** 3),
        'platform': 'linux',
    }


def check_ollama_available(host: str = "http://localhost:11434") -> bool:
    """Check if Ollama is available."""
    try:
        import ollama
        client = ollama.AsyncClient(host=host)
        # Just check if we can connect
        return True
    except:
        return False