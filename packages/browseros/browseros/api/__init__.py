"""
BrowserOS API Module

Provides enhanced API client with:
- Connection pooling
- Request deduplication
- Exponential backoff retry logic
- Response caching
- Circuit breaker pattern
- Performance statistics
- Model discovery for local backends
- ChatGPT custom API handler
"""

from .enhanced_client import (
    EnhancedAPIClient,
    CircuitBreaker,
    CircuitState,
    RequestStats,
    CacheEntry,
)

from .model_discovery import (
    ModelDiscovery,
    ModelInfo,
    BackendInfo,
    BackendType,
)

from .chatgpt_handler import (
    ChatGPTHandler,
    ChatGPTModel,
    ChatGPTRequest,
    ChatGPTResponse,
    ChatMessage,
)

__version__ = "1.1.0"

__all__ = [
    # Enhanced client
    'EnhancedAPIClient',
    'CircuitBreaker',
    'CircuitState',
    'RequestStats',
    'CacheEntry',
    # Model discovery
    'ModelDiscovery',
    'ModelInfo',
    'BackendInfo',
    'BackendType',
    # ChatGPT handler
    'ChatGPTHandler',
    'ChatGPTModel',
    'ChatGPTRequest',
    'ChatGPTResponse',
    'ChatMessage',
]
