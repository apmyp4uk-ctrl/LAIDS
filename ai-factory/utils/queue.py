"""Task queue for agent communication."""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from queue import Queue as SyncQueue
import logging


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Task:
    """Task for agent execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    payload: Any = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    assigned_agent: Optional[str] = None
    
    def update(self, **kwargs):
        """Update task fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()


class TaskQueue:
    """Asynchronous task queue."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.tasks: dict[str, Task] = {}
        self.pending_queue: list[Task] = []
        self._lock = asyncio.Lock()
        self._event = asyncio.Event()
    
    async def add(self, task: Task) -> str:
        """Add task to queue."""
        async with self._lock:
            if len(self.tasks) >= self.max_size:
                raise RuntimeError("Queue is full")
            
            self.tasks[task.id] = task
            self.pending_queue.append(task)
            self.pending_queue.sort(key=lambda t: t.priority.value, reverse=True)
            
            self._event.set()
            return task.id
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Task]:
        """Get next task from queue."""
        await self._event.wait()
        
        async with self._lock:
            if self.pending_queue:
                task = self.pending_queue.pop(0)
                task.update(status=TaskStatus.RUNNING)
                self._event.clear()
                return task
            
            self._event.clear()
            return None
    
    async def get_nowait(self) -> Optional[Task]:
        """Get task without waiting."""
        async with self._lock:
            if self.pending_queue:
                task = self.pending_queue.pop(0)
                task.update(status=TaskStatus.RUNNING)
                return task
            return None
    
    async def complete(self, task_id: str, result: Any = None):
        """Mark task as completed."""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.update(status=TaskStatus.COMPLETED, result=result)
    
    async def fail(self, task_id: str, error: str):
        """Mark task as failed."""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.update(status=TaskStatus.FAILED, error=error)
    
    async def cancel(self, task_id: str):
        """Cancel task."""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.update(status=TaskStatus.CANCELLED)
                
                # Remove from pending queue
                self.pending_queue = [
                    t for t in self.pending_queue if t.id != task_id
                ]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks by status."""
        return [t for t in self.tasks.values() if t.status == status]
    
    def get_pending_count(self) -> int:
        """Get pending task count."""
        return len(self.pending_queue)
    
    async def retry_failed(self, max_retries: int = 3):
        """Retry failed tasks."""
        async with self._lock:
            for task in self.tasks.values():
                if (task.status == TaskStatus.FAILED and 
                    task.retry_count < max_retries):
                    task.retry_count += 1
                    task.update(status=TaskStatus.PENDING)
                    self.pending_queue.append(task)
                    self.pending_queue.sort(
                        key=lambda t: t.priority.value, reverse=True
                    )