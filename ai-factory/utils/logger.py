"""Logging utilities for AI Factory."""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


class AIFactoryLogger:
    """Custom logger with file and console output."""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logging with file rotation."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(log_level)
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_dir = Path(log_config.get('file', 'logs/ai-factory.log')).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_config.get('file', 'logs/ai-factory.log'),
            when='D',
            interval=1,
            backupCount=log_config.get('retention_days', 30)
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)


class TokenCounter:
    """Track token usage across all APIs."""
    
    def __init__(self, config: dict):
        self.config = config
        self.tokens_config = config.get('tokens', {})
        self.daily_limit = self.tokens_config.get('daily_limit', 100000)
        self.warning_threshold = self.tokens_config.get('warning_threshold', 0.8)
        
        self.incoming_tokens = 0
        self.outgoing_tokens = 0
        self.daily_usage = 0
        self.last_reset = datetime.now()
        self._check_daily_reset()
    
    def _check_daily_reset(self):
        """Reset counters if new day."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.incoming_tokens = 0
            self.outgoing_tokens = 0
            self.daily_usage = 0
            self.last_reset = now
    
    def add_tokens(self, incoming: int = 0, outgoing: int = 0):
        """Add token counts."""
        if self.tokens_config.get('track_incoming', True):
            self.incoming_tokens += incoming
        if self.tokens_config.get('track_outgoing', True):
            self.outgoing_tokens += outgoing
        self.daily_usage += incoming + outgoing
    
    def get_usage(self) -> dict:
        """Get current usage stats."""
        return {
            'incoming': self.incoming_tokens,
            'outgoing': self.outgoing_tokens,
            'total': self.daily_usage,
            'daily_limit': self.daily_limit,
            'percent_used': self.daily_usage / self.daily_limit if self.daily_limit > 0 else 0
        }
    
    def is_warning_threshold(self) -> bool:
        """Check if warning threshold reached."""
        return self.daily_usage >= self.daily_limit * self.warning_threshold
    
    def is_limit_reached(self) -> bool:
        """Check if daily limit reached."""
        return self.daily_usage >= self.daily_limit