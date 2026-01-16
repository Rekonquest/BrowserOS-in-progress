"""
BrowserOS API Module

Provides enhanced API client with:
- Connection pooling
- Request deduplication
- Exponential backoff retry logic
- Response caching
- Circuit breaker pattern
- Performance statistics
"""

from .enhanced_client import (
    EnhancedAPIClient,
    CircuitBreaker,
    CircuitState,
    RequestStats,
    CacheEntry,
)

__version__ = "1.0.0"

__all__ = [
    'EnhancedAPIClient',
    'CircuitBreaker',
    'CircuitState',
    'RequestStats',
    'CacheEntry',
]
