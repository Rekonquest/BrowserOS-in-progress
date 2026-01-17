"""
Model Discovery System for BrowserOS

Automatically discovers available models from local backends:
- Ollama (http://localhost:11434)
- LM Studio / OpenAI-compatible (http://localhost:1234)
- Other OpenAI-compatible backends

This eliminates manual model ID entry and keeps the model list up-to-date.
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("[Warning] aiohttp not installed. Install with: pip install aiohttp")


class BackendType(Enum):
    """Types of supported backends"""
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"
    LM_STUDIO = "lm_studio"
    VLLM = "vllm"
    TEXT_GENERATION_WEBUI = "text_generation_webui"


@dataclass
class ModelInfo:
    """Information about a discovered model"""
    model_id: str
    name: str
    size: Optional[int] = None  # Size in bytes
    quantization: Optional[str] = None
    family: Optional[str] = None  # e.g., "llama", "mistral"
    parameter_count: Optional[str] = None  # e.g., "7B", "13B"
    context_length: Optional[int] = None
    modified_at: Optional[str] = None


@dataclass
class BackendInfo:
    """Information about a discovered backend"""
    type: BackendType
    url: str
    name: str
    is_available: bool = False
    models: List[ModelInfo] = field(default_factory=list)
    version: Optional[str] = None
    error: Optional[str] = None


class ModelDiscovery:
    """
    Discovers models from local backends automatically
    """

    # Default backend endpoints to check
    DEFAULT_BACKENDS = [
        {"type": BackendType.OLLAMA, "url": "http://localhost:11434", "name": "Ollama"},
        {"type": BackendType.LM_STUDIO, "url": "http://localhost:1234/v1", "name": "LM Studio"},
        {"type": BackendType.OPENAI_COMPATIBLE, "url": "http://localhost:8000/v1", "name": "vLLM"},
        {"type": BackendType.TEXT_GENERATION_WEBUI, "url": "http://localhost:5000/v1", "name": "Text Generation WebUI"},
    ]

    def __init__(self, timeout: float = 2.0):
        """
        Initialize model discovery

        Args:
            timeout: Connection timeout in seconds
        """
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")

        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start the HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(ssl=False)  # Allow local HTTP
            )

    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def discover_ollama(self, url: str) -> List[ModelInfo]:
        """
        Discover models from Ollama backend

        Args:
            url: Ollama base URL (e.g., "http://localhost:11434")

        Returns:
            List of discovered models
        """
        models = []

        try:
            # Try to list Ollama models
            async with self.session.get(f"{url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()

                    for model in data.get("models", []):
                        models.append(ModelInfo(
                            model_id=model.get("name", ""),
                            name=model.get("name", ""),
                            size=model.get("size"),
                            quantization=model.get("details", {}).get("quantization_level"),
                            family=model.get("details", {}).get("family"),
                            parameter_count=model.get("details", {}).get("parameter_size"),
                            context_length=model.get("details", {}).get("context_length"),
                            modified_at=model.get("modified_at"),
                        ))

        except Exception as e:
            print(f"[Model Discovery] Ollama error: {e}")

        return models

    async def discover_openai_compatible(self, url: str) -> List[ModelInfo]:
        """
        Discover models from OpenAI-compatible backend (LM Studio, vLLM, etc.)

        Args:
            url: Base URL (e.g., "http://localhost:1234/v1")

        Returns:
            List of discovered models
        """
        models = []

        try:
            # Try OpenAI-compatible /models endpoint
            async with self.session.get(f"{url}/models") as response:
                if response.status == 200:
                    data = await response.json()

                    for model in data.get("data", []):
                        model_id = model.get("id", "")

                        # Try to extract metadata
                        # LM Studio sometimes includes context length
                        context_length = None
                        if "context_length" in model:
                            context_length = model["context_length"]
                        elif "max_model_len" in model:  # vLLM format
                            context_length = model["max_model_len"]

                        models.append(ModelInfo(
                            model_id=model_id,
                            name=model_id,
                            context_length=context_length,
                        ))

        except Exception as e:
            print(f"[Model Discovery] OpenAI-compatible error: {e}")

        return models

    async def check_backend(self, backend_config: Dict) -> BackendInfo:
        """
        Check if a backend is available and discover its models

        Args:
            backend_config: Backend configuration dict with type, url, name

        Returns:
            BackendInfo with discovery results
        """
        backend_type = backend_config["type"]
        url = backend_config["url"]
        name = backend_config["name"]

        backend = BackendInfo(
            type=backend_type,
            url=url,
            name=name,
        )

        try:
            # Discover models based on backend type
            if backend_type == BackendType.OLLAMA:
                backend.models = await self.discover_ollama(url)
                backend.is_available = len(backend.models) > 0
                print(f"[Model Discovery] {name}: {'✓' if backend.is_available else '✗'} ({len(backend.models)} models)")

            elif backend_type in [BackendType.LM_STUDIO, BackendType.OPENAI_COMPATIBLE,
                                   BackendType.VLLM, BackendType.TEXT_GENERATION_WEBUI]:
                backend.models = await self.discover_openai_compatible(url)
                backend.is_available = len(backend.models) > 0
                print(f"[Model Discovery] {name}: {'✓' if backend.is_available else '✗'} ({len(backend.models)} models)")

        except Exception as e:
            backend.error = str(e)
            backend.is_available = False
            print(f"[Model Discovery] {name}: ✗ Error: {e}")

        return backend

    async def discover_all(self, custom_backends: Optional[List[Dict]] = None) -> List[BackendInfo]:
        """
        Discover models from all backends

        Args:
            custom_backends: Optional list of custom backend configs to check

        Returns:
            List of BackendInfo for all checked backends
        """
        if not self.session:
            await self.start()

        # Combine default and custom backends
        backends_to_check = self.DEFAULT_BACKENDS.copy()
        if custom_backends:
            backends_to_check.extend(custom_backends)

        # Check all backends concurrently
        tasks = [self.check_backend(backend) for backend in backends_to_check]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return results
        backends = []
        for result in results:
            if isinstance(result, BackendInfo):
                backends.append(result)

        return backends

    def to_json(self, backends: List[BackendInfo]) -> str:
        """
        Convert discovery results to JSON

        Args:
            backends: List of BackendInfo

        Returns:
            JSON string
        """
        data = {
            "backends": [
                {
                    "type": backend.type.value,
                    "url": backend.url,
                    "name": backend.name,
                    "is_available": backend.is_available,
                    "version": backend.version,
                    "error": backend.error,
                    "models": [
                        {
                            "model_id": model.model_id,
                            "name": model.name,
                            "size": model.size,
                            "quantization": model.quantization,
                            "family": model.family,
                            "parameter_count": model.parameter_count,
                            "context_length": model.context_length,
                            "modified_at": model.modified_at,
                        }
                        for model in backend.models
                    ]
                }
                for backend in backends
            ]
        }

        return json.dumps(data, indent=2)


async def main():
    """Example usage of model discovery"""
    async with ModelDiscovery(timeout=3.0) as discovery:
        print("Discovering models from local backends...")
        print()

        backends = await discovery.discover_all()

        for backend in backends:
            if backend.is_available:
                print(f"✓ {backend.name} ({backend.url})")
                print(f"  Found {len(backend.models)} models:")
                for model in backend.models:
                    size_info = f" ({model.parameter_count})" if model.parameter_count else ""
                    quant_info = f" [{model.quantization}]" if model.quantization else ""
                    print(f"    - {model.model_id}{size_info}{quant_info}")
                print()
            else:
                error_msg = f" - {backend.error}" if backend.error else ""
                print(f"✗ {backend.name} ({backend.url}) - Not available{error_msg}")
                print()

        # Output JSON format
        print("\nJSON Output:")
        print(discovery.to_json(backends))


if __name__ == "__main__":
    asyncio.run(main())
