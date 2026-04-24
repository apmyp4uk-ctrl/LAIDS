"""Configuration loader with hot-reload support."""
import os
import yaml
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigHandler(FileSystemEventHandler):
    """Handle config file changes."""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = None
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.json')):
            if self.last_modified is None or \
               datetime.now() - self.last_modified > 2:
                self.callback()
                self.last_modified = datetime.now()


class Config:
    """Configuration manager with hot-reload."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.config = {}
        self.config_file = None
        self.observer = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        config_paths = [
            Path('configs/config.yaml'),
            Path('configs/config.json'),
            Path('/workspace/project/ai-factory/configs/config.yaml'),
        ]
        
        for path in config_paths:
            if path.exists():
                self.config_file = path
                if path.suffix == '.yaml':
                    with open(path) as f:
                        self.config = yaml.safe_load(f)
                elif path.suffix == '.json':
                    with open(path) as f:
                        self.config = json.load(f)
                break
        
        # Load from .env if exists
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by key path (e.g., 'ollama.host')."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
    
    def watch(self, callback):
        """Watch for config changes."""
        if self.config_file and not self.observer:
            handler = ConfigHandler(callback)
            self.observer = Observer()
            self.observer.schedule(
                handler,
                str(self.config_file.parent),
                recursive=False
            )
            self.observer.start()
    
    def stop_watch(self):
        """Stop watching for config changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()


# Global config instance
config = Config()