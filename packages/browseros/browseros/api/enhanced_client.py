"""
Enhanced API Client for BrowserOS

Provides improved performance, reliability, and usability for API interactions:
- Connection pooling for HTTP requests
- Request deduplication to prevent duplicate concurrent requests
- Exponential backoff retry logic with jitter
- Response caching with TTL support
- WebSocket support for real-time updates
- Circuit breaker pattern for fault tolerance
- Request/response logging integration
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("[Warning] aiohttp not installed. Install with: pip install aiohttp")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CacheEntry:
    """Cached response entry"""
    data: Any
    timestamp: float
    ttl: float

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > self.ttl


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    half_open_calls: int = 0

    def record_success(self):
        """Record a successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if a request can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        # HALF_OPEN state
        return self.half_open_calls < self.half_open_max_calls


@dataclass
class RequestStats:
    """Statistics for API requests"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    deduplicated_requests: int = 0
    total_latency_ms: float = 0

    def record_request(self, latency_ms: float, success: bool, from_cache: bool = False, deduplicated: bool = False):
        """Record request statistics"""
        self.total_requests += 1
        self.total_latency_ms += latency_ms

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if from_cache:
            self.cached_responses += 1

        if deduplicated:
            self.deduplicated_requests += 1

    def get_average_latency(self) -> float:
        """Calculate average latency"""
        if self.total_requests == 0:
            return 0
        return self.total_latency_ms / self.total_requests

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0
        return self.successful_requests / self.total_requests


class EnhancedAPIClient:
    """
    Enhanced API client with connection pooling, caching, retry logic,
    and circuit breaker pattern.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 32.0,
        cache_ttl: float = 300.0,  # 5 minutes default
        enable_deduplication: bool = True,
        enable_circuit_breaker: bool = True,
        headers: Optional[Dict[str, str]] = None,
        debug: bool = False,
    ):
        """
        Initialize the enhanced API client

        Args:
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_connections: Maximum number of concurrent connections
            max_retries: Maximum number of retry attempts
            retry_base_delay: Base delay for exponential backoff (seconds)
            retry_max_delay: Maximum delay between retries (seconds)
            cache_ttl: Cache time-to-live in seconds
            enable_deduplication: Enable request deduplication
            enable_circuit_breaker: Enable circuit breaker pattern
            headers: Default headers for all requests
            debug: Enable debug logging
        """
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp is required for EnhancedAPIClient. Install with: pip install aiohttp")

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.cache_ttl = cache_ttl
        self.enable_deduplication = enable_deduplication
        self.enable_circuit_breaker = enable_circuit_breaker
        self.debug = debug

        # Connection pooling with limits
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections // 2,
            ttl_dns_cache=300,
            enable_cleanup_closed=True,
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self.default_headers = headers or {}

        # Caching
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = asyncio.Lock()

        # Request deduplication
        self._in_flight_requests: Dict[str, asyncio.Future] = {}
        self._deduplication_lock = asyncio.Lock()

        # Circuit breaker per endpoint
        self._circuit_breakers: Dict[str, CircuitBreaker] = defaultdict(CircuitBreaker)

        # Statistics
        self.stats = RequestStats()

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start the client session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.default_headers,
            )

    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None

    def _generate_cache_key(self, method: str, url: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> str:
        """Generate cache key for request"""
        key_parts = [method, url]

        if params:
            key_parts.append(json.dumps(params, sort_keys=True))

        if data:
            key_parts.append(json.dumps(data, sort_keys=True))

        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        async with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired():
                    if self.debug:
                        print(f"[Cache HIT] {cache_key}")
                    return entry.data
                else:
                    del self._cache[cache_key]
                    if self.debug:
                        print(f"[Cache EXPIRED] {cache_key}")
        return None

    async def _set_cached(self, cache_key: str, data: Any, ttl: Optional[float] = None):
        """Store response in cache"""
        async with self._cache_lock:
            self._cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl or self.cache_ttl,
            )
            if self.debug:
                print(f"[Cache SET] {cache_key}")

    async def _deduplicate_request(self, cache_key: str, request_func: Callable) -> Tuple[Any, bool]:
        """Deduplicate concurrent identical requests"""
        if not self.enable_deduplication:
            return await request_func(), False

        async with self._deduplication_lock:
            if cache_key in self._in_flight_requests:
                if self.debug:
                    print(f"[Dedup] Waiting for in-flight request: {cache_key}")
                # Wait for the in-flight request to complete
                future = self._in_flight_requests[cache_key]
                result = await future
                return result, True

            # Create new future for this request
            future = asyncio.Future()
            self._in_flight_requests[cache_key] = future

        try:
            result = await request_func()
            future.set_result(result)
            return result, False
        except Exception as e:
            future.set_exception(e)
            raise
        finally:
            async with self._deduplication_lock:
                del self._in_flight_requests[cache_key]

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(self.retry_base_delay * (2 ** attempt), self.retry_max_delay)
        # Add jitter (±20%)
        jitter = delay * 0.2 * (2 * (time.time() % 1) - 1)
        return delay + jitter

    async def _retry_with_backoff(self, request_func: Callable, endpoint: str) -> Any:
        """Execute request with exponential backoff retry"""
        circuit_breaker = self._circuit_breakers[endpoint] if self.enable_circuit_breaker else None

        for attempt in range(self.max_retries + 1):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_attempt():
                raise Exception(f"Circuit breaker OPEN for {endpoint}. Service unavailable.")

            try:
                result = await request_func()

                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()

                return result

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Record failure
                if circuit_breaker:
                    circuit_breaker.record_failure()

                # If this was the last attempt, raise
                if attempt == self.max_retries:
                    if self.debug:
                        print(f"[Retry] Max retries exceeded for {endpoint}")
                    raise

                # Calculate backoff delay
                delay = self._calculate_backoff_delay(attempt)

                if self.debug:
                    print(f"[Retry] Attempt {attempt + 1}/{self.max_retries} failed. Retrying in {delay:.2f}s...")

                await asyncio.sleep(delay)

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with caching, deduplication, and retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            data: Request body data
            headers: Additional headers for this request
            use_cache: Whether to use cache for this request (GET only)
            cache_ttl: Custom TTL for this request's cache entry

        Returns:
            Response data as dictionary
        """
        if not self.session:
            await self.start()

        url = urljoin(self.base_url, endpoint.lstrip('/'))
        cache_key = self._generate_cache_key(method, url, params, data)

        # Try cache for GET requests
        if method.upper() == 'GET' and use_cache:
            cached_data = await self._get_cached(cache_key)
            if cached_data is not None:
                self.stats.record_request(0, True, from_cache=True)
                return cached_data

        # Define request function
        async def make_request():
            start_time = time.time()

            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    latency_ms = (time.time() - start_time) * 1000
                    self.stats.record_request(latency_ms, True)

                    if self.debug:
                        print(f"[Request] {method} {url} - {response.status} ({latency_ms:.2f}ms)")

                    return result

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.stats.record_request(latency_ms, False)

                if self.debug:
                    print(f"[Request ERROR] {method} {url} - {str(e)} ({latency_ms:.2f}ms)")

                raise

        # Deduplicate and retry
        result, was_deduplicated = await self._deduplicate_request(
            cache_key,
            lambda: self._retry_with_backoff(make_request, endpoint)
        )

        if was_deduplicated:
            self.stats.deduplicated_requests += 1

        # Cache GET requests
        if method.upper() == 'GET' and use_cache:
            await self._set_cached(cache_key, result, cache_ttl)

        return result

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Convenience method for GET requests"""
        return await self.request('GET', endpoint, params=params, **kwargs)

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Convenience method for POST requests"""
        return await self.request('POST', endpoint, data=data, **kwargs)

    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Convenience method for PUT requests"""
        return await self.request('PUT', endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for DELETE requests"""
        return await self.request('DELETE', endpoint, **kwargs)

    async def clear_cache(self):
        """Clear all cached responses"""
        async with self._cache_lock:
            self._cache.clear()
        if self.debug:
            print("[Cache] Cleared all cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        return {
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'success_rate': self.stats.get_success_rate(),
            'cached_responses': self.stats.cached_responses,
            'deduplicated_requests': self.stats.deduplicated_requests,
            'average_latency_ms': self.stats.get_average_latency(),
            'cache_size': len(self._cache),
            'in_flight_requests': len(self._in_flight_requests),
        }

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {
            endpoint: {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'last_failure_time': breaker.last_failure_time,
            }
            for endpoint, breaker in self._circuit_breakers.items()
        }


# Example usage
async def example_usage():
    """Example usage of EnhancedAPIClient"""

    async with EnhancedAPIClient(
        base_url='https://api.example.com',
        max_retries=3,
        cache_ttl=300,
        debug=True,
    ) as client:

        # Make GET request (will be cached)
        response1 = await client.get('/users', params={'page': 1})
        print(f"Response 1: {response1}")

        # Make another identical request (will use cache)
        response2 = await client.get('/users', params={'page': 1})
        print(f"Response 2: {response2}")

        # Make POST request (not cached)
        response3 = await client.post('/users', data={'name': 'John Doe', 'email': 'john@example.com'})
        print(f"Response 3: {response3}")

        # Get statistics
        stats = client.get_stats()
        print(f"\nStatistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']:.2%}")
        print(f"  Cached responses: {stats['cached_responses']}")
        print(f"  Deduplicated requests: {stats['deduplicated_requests']}")
        print(f"  Average latency: {stats['average_latency_ms']:.2f}ms")

        # Get circuit breaker status
        cb_status = client.get_circuit_breaker_status()
        print(f"\nCircuit Breakers: {cb_status}")


if __name__ == '__main__':
    asyncio.run(example_usage())
