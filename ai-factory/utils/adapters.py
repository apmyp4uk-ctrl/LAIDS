"""Cloud API adapters for multiple LLM providers."""
import os
import asyncio
from typing import Optional, Any
from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai
from groq import AsyncGroq

from tenacity import retry, stop_after_attempt, wait_exponential


class BaseAdapter(ABC):
    """Base adapter for LLM APIs."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt."""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass


class OpenAIAdapter(BaseAdapter):
    """OpenAI API adapter."""
    
    def __init__(self, config: dict):
        self.config = config
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_key_here':
            self.client = AsyncOpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.enabled = False
            self.client = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.enabled or not self.client:
            return ""
        
        model = self.config.get('cloud_apis', {}).get('openai', {}).get('model', 'gpt-4o-mini')
        max_tokens = self.config.get('cloud_apis', {}).get('openai', {}).get('max_tokens', 16000)
        timeout = self.config.get('cloud_apis', {}).get('openai', {}).get('timeout', 60)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def count_tokens(self, text: str) -> int:
        # Approximate token count (roughly 1 token per 4 chars)
        return len(text) // 4


class AnthropicAdapter(BaseAdapter):
    """Anthropic API adapter."""
    
    def __init__(self, config: dict):
        self.config = config
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key and api_key != 'your_anthropic_key_here':
            self.client = AsyncAnthropic(api_key=api_key)
            self.enabled = True
        else:
            self.enabled = False
            self.client = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.enabled or not self.client:
            return ""
        
        model = self.config.get('cloud_apis', {}).get('anthropic', {}).get('model', 'claude-3-haiku-20240307')
        max_tokens = self.config.get('cloud_apis', {}).get('anthropic', {}).get('max_tokens', 200000)
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return response.content[0].text
    
    async def count_tokens(self, text: str) -> int:
        return len(text) // 4


class GoogleAdapter(BaseAdapter):
    """Google Gemini API adapter."""
    
    def __init__(self, config: dict):
        self.config = config
        api_key = os.environ.get('GOOGLE_API_KEY')
        if api_key and api_key != 'your_google_key_here':
            genai.configure(api_key=api_key)
            self.enabled = True
        else:
            self.enabled = False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.enabled:
            return ""
        
        model = self.config.get('cloud_apis', {}).get('google', {}).get('model', 'gemini-2.0-flash')
        
        response = genai.generate_text(
            model=model,
            prompt=prompt,
            **kwargs
        )
        
        return response.text if response else ""
    
    async def count_tokens(self, text: str) -> int:
        return len(text) // 4


class GroqAdapter(BaseAdapter):
    """Groq API adapter."""
    
    def __init__(self, config: dict):
        self.config = config
        api_key = os.environ.get('GROQ_API_KEY')
        if api_key and api_key != 'your_groq_key_here':
            self.client = AsyncGroq(api_key=api_key)
            self.enabled = True
        else:
            self.enabled = False
            self.client = None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.enabled or not self.client:
            return ""
        
        model = self.config.get('cloud_apis', {}).get('groq', {}).get('model', 'llama-3.3-70b-versatile')
        max_tokens = self.config.get('cloud_apis', {}).get('groq', {}).get('max_tokens', 8192)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def count_tokens(self, text: str) -> int:
        return len(text) // 4


class OllamaAdapter(BaseAdapter):
    """Local Ollama adapter."""
    
    def __init__(self, config: dict):
        self.config = config
        import ollama
        
        self.host = config.get('ollama', {}).get('host', 'http://localhost:11434')
        self.model = config.get('ollama', {}).get('model', 'mistral')
        self.timeout = config.get('ollama', {}).get('timeout', 120)
        self.max_tokens = config.get('ollama', {}).get('max_tokens', 4096)
        self.client = ollama.AsyncClient(host=self.host)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': kwargs.get('temperature', 0.7),
                    'num_predict': self.max_tokens,
                }
            )
            return response.get('response', '')
        except Exception as e:
            # Try fallback model
            fallback = self.config.get('ollama', {}).get('fallback_model')
            if fallback and fallback != self.model:
                try:
                    response = await self.client.generate(
                        model=fallback,
                        prompt=prompt,
                        options={
                            'temperature': kwargs.get('temperature', 0.7),
                            'num_predict': self.max_tokens,
                        }
                    )
                    return response.get('response', '')
                except:
                    pass
            raise
    
    async def count_tokens(self, text: str) -> int:
        return len(text) // 4


class AdapterManager:
    """Manage multiple API adapters."""
    
    def __init__(self, config: dict):
        self.config = config
        self.adapters = {}
        self._init_adapters()
    
    def _init_adapters(self):
        """Initialize all adapters."""
        self.adapters['ollama'] = OllamaAdapter(self.config)
        self.adapters['openai'] = OpenAIAdapter(self.config)
        self.adapters['anthropic'] = AnthropicAdapter(self.config)
        self.adapters['google'] = GoogleAdapter(self.config)
        self.adapters['groq'] = GroqAdapter(self.config)
    
    def get(self, name: str) -> Optional[BaseAdapter]:
        """Get adapter by name."""
        return self.adapters.get(name)
    
    def get_enabled(self) -> list:
        """Get list of enabled adapters."""
        return [name for name, adapter in self.adapters.items() 
                if getattr(adapter, 'enabled', True)]
    
    def select_adapter(self, task_type: str = 'general') -> str:
        """Select best adapter for task."""
        enabled = self.get_enabled()
        
        if not enabled:
            return 'ollama'
        
        # Route based on task type
        routing = {
            'coding': ['groq', 'anthropic', 'openai'],
            'reasoning': ['anthropic', 'openai', 'google'],
            'fast': ['groq', 'openai', 'google'],
            'general': enabled
        }
        
        candidates = routing.get(task_type, enabled)
        for adapter in candidates:
            if adapter in enabled:
                return adapter
        
        return enabled[0] if enabled else 'ollama'