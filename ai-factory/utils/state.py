"""State persistence for AI Factory."""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class SystemState:
    """System state for persistence."""
    started_at: str = ""
    last_task_id: str = ""
    tasks_completed: int = 0
    tokens_used: int = 0
    agents_state: dict = field(default_factory=dict)
    conversation_history: list = field(default_factory=list)
    config_hash: str = ""


@dataclass  
class TaskState:
    """Task state for persistence."""
    task_id: str = ""
    name: str = ""
    description: str = ""
    status: str = ""
    result: Any = None
    created_at: str = ""
    completed_at: str = ""


class StateManager:
    """Manages persistent state."""
    
    STATE_FILE = "state/ai-factory-state.json"
    HISTORY_FILE = "state/conversation-history.json"
    
    def __init__(self):
        self.state_dir = Path("state")
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "ai-factory-state.json"
        self.history_file = self.state_dir / "conversation-history.json"
    
    def save_state(self, system_state: SystemState):
        """Save system state."""
        data = {
            'saved_at': datetime.now().isoformat(),
            'state': asdict(system_state)
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_state(self) -> Optional[SystemState]:
        """Load system state."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file) as f:
                data = json.load(f)
            
            state_data = data.get('state', {})
            return SystemState(
                started_at=state_data.get('started_at', ''),
                last_task_id=state_data.get('last_task_id', ''),
                tasks_completed=state_data.get('tasks_completed', 0),
                tokens_used=state_data.get('tokens_used', 0),
                agents_state=state_data.get('agents_state', {}),
                conversation_history=state_data.get('conversation_history', []),
                config_hash=state_data.get('config_hash', '')
            )
        except Exception:
            return None
    
    def save_conversation(self, role: str, content: str):
        """Save conversation message."""
        history = []
        
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 100 messages
        history = history[-100:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_conversation(self) -> list:
        """Load conversation history."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file) as f:
                return json.load(f)
        except:
            return []
    
    def save_task(self, task: TaskState):
        """Save individual task state."""
        tasks_file = self.state_dir / "tasks.json"
        tasks = []
        
        if tasks_file.exists():
            try:
                with open(tasks_file) as f:
                    tasks = json.load(f)
            except:
                tasks = []
        
        # Add or update task
        found = False
        for i, t in enumerate(tasks):
            if t.get('task_id') == task.task_id:
                tasks[i] = asdict(task)
                found = True
                break
        
        if not found:
            tasks.append(asdict(task))
        
        # Keep last 50 tasks
        tasks = tasks[-50:]
        
        with open(tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2, default=str)
    
    def load_tasks(self) -> list:
        """Load all saved tasks."""
        tasks_file = self.state_dir / "tasks.json"
        
        if not tasks_file.exists():
            return []
        
        try:
            with open(tasks_file) as f:
                return json.load(f)
        except:
            return []


# Global state manager
state_manager = StateManager()