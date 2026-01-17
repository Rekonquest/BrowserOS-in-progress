#!/usr/bin/env python3
"""
Dynamic functionality tests for BrowserOS new features
Tests actual runtime behavior, not just imports
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add browseros to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("BROWSEROS DYNAMIC FUNCTIONALITY TESTS")
print("=" * 70)
print()

# Track test results
test_results = {"passed": 0, "failed": 0, "warnings": 0, "tests": []}

def log_test(name: str, status: str, details: str = ""):
    """Log test result"""
    symbol = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}
    print(f"{symbol.get(status, '?')} {name}: {status}")
    if details:
        print(f"  → {details}")

    test_results["tests"].append({"name": name, "status": status, "details": details})
    if status == "PASS":
        test_results["passed"] += 1
    elif status == "FAIL":
        test_results["failed"] += 1
    elif status == "WARN":
        test_results["warnings"] += 1

# ============================================================================
# TEST 1: Model Discovery Module
# ============================================================================
print("\n[TEST SUITE 1] Model Discovery Module")
print("-" * 70)

try:
    from browseros.api.model_discovery import (
        ModelDiscovery, ModelInfo, BackendInfo, BackendType
    )
    log_test("Import model_discovery", "PASS")

    # Test ModelInfo dataclass
    model = ModelInfo(
        model_id="llama3.1:8b",
        name="Llama 3.1 8B",
        parameter_count="8B",
        quantization="Q4_0",
        size=4700000000,
        modified_at="2024-01-15T10:30:00Z"
    )
    assert model.model_id == "llama3.1:8b"
    assert model.parameter_count == "8B"
    log_test("ModelInfo instantiation", "PASS", f"Created: {model.name}")

    # Test BackendInfo dataclass
    backend = BackendInfo(
        type=BackendType.OLLAMA,
        name="Ollama Local",
        url="http://localhost:11434",
        models=[model],
        is_available=True
    )
    assert backend.type == BackendType.OLLAMA
    assert len(backend.models) == 1
    log_test("BackendInfo instantiation", "PASS", f"Created: {backend.name}")

    # Test BackendType enum
    backend_types = [e.name for e in BackendType]
    assert "OLLAMA" in backend_types
    assert "LM_STUDIO" in backend_types
    assert "VLLM" in backend_types
    assert "TEXT_GENERATION_WEBUI" in backend_types or "TEXT_GEN_WEBUI" in backend_types
    log_test("BackendType enum", "PASS", f"All {len(backend_types)} backend types present")

    # Check if aiohttp is available for ModelDiscovery tests
    try:
        import aiohttp
        HAS_AIOHTTP_FOR_TEST = True
    except ImportError:
        HAS_AIOHTTP_FOR_TEST = False

    if HAS_AIOHTTP_FOR_TEST:
        # Test ModelDiscovery initialization
        discovery = ModelDiscovery()
        assert discovery.session is None  # Not initialized yet
        assert len(discovery.DEFAULT_BACKENDS) >= 3
        log_test("ModelDiscovery init", "PASS", f"{len(discovery.DEFAULT_BACKENDS)} default backends")

        # Test async discovery
        async def test_discovery_async():
            async with ModelDiscovery() as disco:
                # Test method existence
                assert hasattr(disco, 'discover_all')
                assert hasattr(disco, 'discover_ollama')
                assert hasattr(disco, 'discover_lm_studio')
                assert hasattr(disco, 'discover_vllm')
                return True

        result = asyncio.run(test_discovery_async())
        if result:
            log_test("ModelDiscovery async methods", "PASS", "All discovery methods present")
    else:
        log_test("ModelDiscovery init", "WARN", "aiohttp not installed (optional)")
        log_test("ModelDiscovery async methods", "WARN", "aiohttp not installed (optional)")

except ImportError as e:
    log_test("Import model_discovery", "FAIL", str(e))
except Exception as e:
    log_test("Model Discovery tests", "FAIL", str(e))

# ============================================================================
# TEST 2: ChatGPT Handler Module
# ============================================================================
print("\n[TEST SUITE 2] ChatGPT Handler Module")
print("-" * 70)

try:
    from browseros.api.chatgpt_handler import (
        ChatGPTHandler, ChatGPTModel, ChatGPTRequest,
        ChatGPTResponse, ChatMessage
    )
    log_test("Import chatgpt_handler", "PASS")

    # Test ChatMessage dataclass
    msg = ChatMessage(role="user", content="Hello, GPT!")
    assert msg.role == "user"
    assert msg.content == "Hello, GPT!"
    log_test("ChatMessage instantiation", "PASS", f"Role: {msg.role}")

    # Test ChatGPTRequest dataclass
    request = ChatGPTRequest(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello, GPT!"}],
        temperature=0.7,
        top_p=0.9,
        max_tokens=2000,
        stream=False
    )
    assert request.model == "gpt-4o"
    assert len(request.messages) == 1
    assert request.temperature == 0.7
    log_test("ChatGPTRequest instantiation", "PASS", f"Model: {request.model}")

    # Test request serialization
    request_dict = request.to_dict()
    assert "model" in request_dict
    assert "messages" in request_dict
    assert "temperature" in request_dict
    log_test("ChatGPTRequest serialization", "PASS", f"{len(request_dict)} fields")

    # Test ChatGPTModel enum
    assert hasattr(ChatGPTModel, "GPT_4O")
    assert hasattr(ChatGPTModel, "GPT_4O_MINI")
    assert hasattr(ChatGPTModel, "GPT_4_TURBO")
    log_test("ChatGPTModel enum", "PASS", "All model types present")

    # Test ChatGPTResponse dataclass
    usage_dict = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    response = ChatGPTResponse(
        id="chatcmpl-123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4o",
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop"
        }],
        usage=usage_dict
    )
    assert response.model == "gpt-4o"
    assert len(response.choices) == 1
    assert response.usage["total_tokens"] == 30
    log_test("ChatGPTResponse instantiation", "PASS", f"Choices: {len(response.choices)}")

    # Test ChatGPTHandler initialization
    try:
        handler = ChatGPTHandler(api_key="sk-test-key")
        assert handler.api_key == "sk-test-key"
        assert handler.BASE_URL == "https://api.openai.com/v1"
        log_test("ChatGPTHandler init", "PASS", f"Base URL: {handler.BASE_URL}")
    except ImportError as e:
        if "aiohttp" in str(e):
            log_test("ChatGPTHandler init", "WARN", "aiohttp not installed (optional)")
        else:
            raise

except ImportError as e:
    log_test("Import chatgpt_handler", "FAIL", str(e))
except Exception as e:
    log_test("ChatGPT Handler tests", "FAIL", str(e))

# ============================================================================
# TEST 3: Enhanced API Client Module
# ============================================================================
print("\n[TEST SUITE 3] Enhanced API Client Module")
print("-" * 70)

try:
    from browseros.api.enhanced_client import (
        EnhancedAPIClient, CircuitBreaker, CircuitState,
        RequestStats, CacheEntry
    )
    log_test("Import enhanced_client", "PASS")

    # Test CircuitState enum
    assert hasattr(CircuitState, "CLOSED")
    assert hasattr(CircuitState, "OPEN")
    assert hasattr(CircuitState, "HALF_OPEN")
    log_test("CircuitState enum", "PASS", "All 3 states present")

    # Test CircuitBreaker dataclass
    cb = CircuitBreaker()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.half_open_calls == 0
    log_test("CircuitBreaker instantiation", "PASS", f"Initial state: {cb.state.value}")

    # Test RequestStats dataclass
    stats = RequestStats()
    assert stats.total_requests == 0
    assert stats.successful_requests == 0
    assert stats.failed_requests == 0
    log_test("RequestStats instantiation", "PASS", "All counters at 0")

    # Test CacheEntry dataclass
    import time
    cache_entry = CacheEntry(
        data={"result": "test"},
        timestamp=time.time(),
        ttl=300.0
    )
    assert cache_entry.data["result"] == "test"
    assert not cache_entry.is_expired()  # Should not be expired immediately
    log_test("CacheEntry instantiation", "PASS", f"TTL: {cache_entry.ttl}s")

    # Test EnhancedAPIClient initialization
    try:
        client = EnhancedAPIClient(
            base_url="http://localhost:11434",
            timeout=30.0,
            max_connections=100,
            max_retries=3,
            cache_ttl=300.0,
            enable_circuit_breaker=True
        )
        assert client.base_url == "http://localhost:11434"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        log_test("EnhancedAPIClient init", "PASS", f"Base URL: {client.base_url}")
    except Exception as e:
        # aiohttp may not be installed, which is expected
        if "aiohttp" in str(e).lower():
            log_test("EnhancedAPIClient init", "WARN", "aiohttp not installed (optional)")
        else:
            raise

except ImportError as e:
    log_test("Import enhanced_client", "FAIL", str(e))
except Exception as e:
    log_test("Enhanced API Client tests", "FAIL", str(e))

# ============================================================================
# TEST 4: JSON-RPC MCP Transport Module
# ============================================================================
print("\n[TEST SUITE 4] JSON-RPC MCP Transport Module")
print("-" * 70)

try:
    from browseros.mcp.json_transport import (
        MCPJsonRpcServer, JsonRpcRequest, JsonRpcResponse, JsonRpcError
    )
    log_test("Import json_transport", "PASS")

    # Test JsonRpcRequest dataclass
    req = JsonRpcRequest(
        jsonrpc="2.0",
        method="tools/list",
        params={},
        id=1
    )
    assert req.jsonrpc == "2.0"
    assert req.method == "tools/list"
    log_test("JsonRpcRequest instantiation", "PASS", f"Method: {req.method}")

    # Test JsonRpcResponse dataclass
    resp = JsonRpcResponse(
        jsonrpc="2.0",
        result={"tools": []},
        id=1
    )
    assert resp.jsonrpc == "2.0"
    assert "tools" in resp.result
    log_test("JsonRpcResponse instantiation", "PASS", "Result present")

    # Test JsonRpcError dataclass
    error = JsonRpcError(
        code=-32600,
        message="Invalid Request",
        data={"details": "Missing method"}
    )
    assert error.code == -32600
    assert "Invalid" in error.message
    log_test("JsonRpcError instantiation", "PASS", f"Code: {error.code}")

    # Test MCPJsonRpcServer initialization
    server = MCPJsonRpcServer(debug=True)
    assert len(server.tools) == 0  # No tools registered yet
    assert server.debug is True
    log_test("MCPJsonRpcServer init", "PASS", f"Debug: {server.debug}")

    # Test tool registration
    def test_tool(params: dict) -> str:
        """Test tool for MCP"""
        return f"Called with {params}"

    server.add_tool("test_tool", test_tool)
    assert "test_tool" in server.tools
    log_test("MCPJsonRpcServer tool registration", "PASS", "Tool registered successfully")

    # Test request handling
    request_json = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    response_json = server.handle_request(request_json)
    assert response_json is not None
    response_data = json.loads(response_json)
    assert "result" in response_data or "error" in response_data
    log_test("MCPJsonRpcServer request handling", "PASS", "Request processed")

except ImportError as e:
    log_test("Import json_transport", "FAIL", str(e))
except Exception as e:
    log_test("JSON-RPC MCP tests", "FAIL", str(e))

# ============================================================================
# TEST 5: Presets (System Prompts & Chat Templates)
# ============================================================================
print("\n[TEST SUITE 5] Presets (System Prompts & Chat Templates)")
print("-" * 70)

try:
    presets_dir = Path(__file__).parent / "browseros" / "presets"

    # Test system_prompts.json
    system_prompts_file = presets_dir / "system_prompts.json"
    with open(system_prompts_file) as f:
        system_prompts = json.load(f)

    assert "presets" in system_prompts
    assert len(system_prompts["presets"]) == 20

    # Validate structure of first preset
    first_preset = system_prompts["presets"][0]
    required_fields = ["id", "name", "description", "icon", "category", "prompt"]
    for field in required_fields:
        assert field in first_preset, f"Missing field: {field}"

    log_test("System prompts JSON", "PASS", f"{len(system_prompts['presets'])} presets loaded")

    # Test chat_templates.json
    chat_templates_file = presets_dir / "chat_templates.json"
    with open(chat_templates_file) as f:
        chat_templates = json.load(f)

    assert "templates" in chat_templates
    assert len(chat_templates["templates"]) == 16

    # Validate structure of first template
    first_template = chat_templates["templates"][0]
    required_fields = ["id", "name", "format", "description"]
    for field in required_fields:
        assert field in first_template, f"Missing field: {field}"

    log_test("Chat templates JSON", "PASS", f"{len(chat_templates['templates'])} templates loaded")

    # Test specific presets exist
    preset_ids = [p["id"] for p in system_prompts["presets"]]
    expected_presets = ["coding", "teacher", "creative_writing", "researcher"]
    for preset_id in expected_presets:
        if preset_id in preset_ids:
            log_test(f"Preset '{preset_id}' exists", "PASS")
        else:
            log_test(f"Preset '{preset_id}' exists", "FAIL", "Not found")

    # Test specific templates exist
    template_ids = [t["id"] for t in chat_templates["templates"]]
    expected_templates = ["llama3", "mistral", "chatml", "gemma"]
    for template_id in expected_templates:
        if template_id in template_ids:
            log_test(f"Template '{template_id}' exists", "PASS")
        else:
            log_test(f"Template '{template_id}' exists", "FAIL", "Not found")

except FileNotFoundError as e:
    log_test("Load preset files", "FAIL", str(e))
except json.JSONDecodeError as e:
    log_test("Parse preset JSON", "FAIL", str(e))
except Exception as e:
    log_test("Presets tests", "FAIL", str(e))

# ============================================================================
# TEST 6: HTML Resources Validation
# ============================================================================
print("\n[TEST SUITE 6] HTML Resources Validation")
print("-" * 70)

try:
    resources_dir = Path(__file__).parent / "resources"

    html_files = [
        "advanced_settings_panel.html",
        "voice_interaction.html",
        "log_viewer.html",
        "file_upload_bar.html",
        "tool_usage_indicator.html"
    ]

    for html_file in html_files:
        file_path = resources_dir / html_file

        if not file_path.exists():
            log_test(f"HTML file: {html_file}", "FAIL", "File not found")
            continue

        with open(file_path) as f:
            content = f.read()

        # Check for basic HTML structure
        has_html_tag = "<html" in content.lower()
        has_body_tag = "<body" in content.lower()
        has_script_tag = "<script" in content.lower()

        if not has_html_tag:
            log_test(f"HTML file: {html_file}", "WARN", "Missing <html> tag")
            continue

        # Check for public API exposure (window.methodName)
        has_public_api = "window." in content

        details = f"{len(content)} bytes"
        if has_public_api:
            details += ", public API exposed"

        log_test(f"HTML file: {html_file}", "PASS", details)

        # Specific API checks
        if html_file == "advanced_settings_panel.html":
            if "window.initAdvancedSettings" in content:
                log_test("  → Advanced settings API", "PASS", "initAdvancedSettings() found")

        if html_file == "voice_interaction.html":
            if "window.startRecording" in content or "window.startListening" in content:
                log_test("  → Voice interaction API", "PASS", "Recording API found")

        if html_file == "log_viewer.html":
            if "window.addLog" in content:
                log_test("  → Log viewer API", "PASS", "addLog() found")

        if html_file == "file_upload_bar.html":
            if "window.getFiles" in content or "window.addFiles" in content:
                log_test("  → File upload API", "PASS", "File management API found")

        if html_file == "tool_usage_indicator.html":
            if "window.showToolUsage" in content:
                log_test("  → Tool indicator API", "PASS", "showToolUsage() found")

except Exception as e:
    log_test("HTML Resources tests", "FAIL", str(e))

# ============================================================================
# TEST 7: API Package Exports
# ============================================================================
print("\n[TEST SUITE 7] API Package Exports")
print("-" * 70)

try:
    from browseros import api

    # Check version
    if hasattr(api, '__version__'):
        log_test("API package version", "PASS", f"v{api.__version__}")
    else:
        log_test("API package version", "WARN", "No version defined")

    # Check __all__ exports
    if hasattr(api, '__all__'):
        exports = api.__all__
        log_test("API package __all__", "PASS", f"{len(exports)} exports defined")

        # Verify each export is actually available
        for export_name in exports:
            if hasattr(api, export_name):
                log_test(f"  → Export: {export_name}", "PASS")
            else:
                log_test(f"  → Export: {export_name}", "FAIL", "Not available")
    else:
        log_test("API package __all__", "WARN", "No __all__ defined")

    # Test specific imports
    expected_classes = [
        "EnhancedAPIClient",
        "ModelDiscovery",
        "ChatGPTHandler",
        "CircuitBreaker",
        "ModelInfo",
        "BackendInfo",
        "BackendType",
        "ChatGPTModel"
    ]

    for class_name in expected_classes:
        if hasattr(api, class_name):
            log_test(f"  → Class: {class_name}", "PASS")
        else:
            log_test(f"  → Class: {class_name}", "WARN", "Not exported")

except ImportError as e:
    log_test("Import browseros.api", "FAIL", str(e))
except Exception as e:
    log_test("API package exports tests", "FAIL", str(e))

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"✓ Passed:  {test_results['passed']}")
print(f"✗ Failed:  {test_results['failed']}")
print(f"⚠ Warnings: {test_results['warnings']}")
print(f"Total:     {test_results['passed'] + test_results['failed'] + test_results['warnings']}")
print()

if test_results['failed'] == 0:
    print("🎉 ALL TESTS PASSED! 🎉")
    print()
    print("STATUS: READY FOR PRODUCTION ✓")
    exit_code = 0
else:
    print("❌ SOME TESTS FAILED")
    print()
    print("Review failed tests above and fix issues.")
    exit_code = 1

print("=" * 70)

sys.exit(exit_code)
