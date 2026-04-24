"""Prompt cache for optimizing token usage."""
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class PromptCache:
    """Cache for prompts to reduce token usage."""
    
    CACHE_FILE = "state/prompt-cache.json"
    
    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_file = Path(self.CACHE_FILE)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _hash(self, prompt: str) -> str:
        """Hash prompt for cache key."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    def get(self, prompt: str, model: str = "default") -> Optional[str]:
        """Get cached response."""
        key = f"{model}:{self._hash(prompt)}"
        
        entry = self.cache.get(key)
        if not entry:
            return None
        
        # Check TTL
        cached_at = datetime.fromisoformat(entry['cached_at'])
        if datetime.now() - cached_at > self.ttl:
            del self.cache[key]
            self._save_cache()
            return None
        
        return entry['response']
    
    def set(self, prompt: str, response: str, model: str = "default"):
        """Cache response."""
        key = f"{model}:{self._hash(prompt)}"
        
        self.cache[key] = {
            'prompt': prompt[:100],  # Store truncated prompt
            'response': response,
            'cached_at': datetime.now().isoformat()
        }
        
        # Clean old entries
        self._clean_expired()
        self._save_cache()
    
    def _clean_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired = []
        
        for key, entry in self.cache.items():
            cached_at = datetime.fromisoformat(entry['cached_at'])
            if now - cached_at > self.ttl:
                expired.append(key)
        
        for key in expired:
            del self.cache[key]
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'entries': len(self.cache),
            'file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
    
    def clear(self):
        """Clear cache."""
        self.cache = {}
        self._save_cache()


# Global prompt cache
prompt_cache = PromptCache()