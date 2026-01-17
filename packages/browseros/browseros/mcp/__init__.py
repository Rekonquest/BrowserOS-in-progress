"""
MCP (Model Context Protocol) transport implementations for BrowserOS.

This package provides multiple transport options for MCP servers:
- HTTP transport (existing)
- JSON-RPC 2.0 transport via stdio (new)

Both transports support the same MCP tool interface.
"""

from .json_transport import (
    JsonRpcErrorCode,
    JsonRpcRequest,
    JsonRpcError,
    JsonRpcResponse,
    MCPJsonRpcServer,
    MCPJsonRpcClient,
    create_stdio_server,
)

__all__ = [
    "JsonRpcErrorCode",
    "JsonRpcRequest",
    "JsonRpcError",
    "JsonRpcResponse",
    "MCPJsonRpcServer",
    "MCPJsonRpcClient",
    "create_stdio_server",
]

__version__ = "1.0.0"
