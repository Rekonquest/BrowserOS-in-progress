#!/usr/bin/env python3
"""
JSON-RPC 2.0 Transport for MCP (Model Context Protocol).

This module implements JSON-RPC 2.0 transport for MCP servers, allowing
communication via stdio (standard input/output) in addition to HTTP.

JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification

Usage:
    # Server-side
    server = MCPJsonRpcServer()
    server.add_tool("browser", browser_tool_handler)
    server.run()  # Reads from stdin, writes to stdout

    # Client-side
    client = MCPJsonRpcClient()
    response = client.call_tool("browser", {"url": "https://example.com"})
"""

import json
import sys
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class JsonRpcErrorCode(Enum):
    """Standard JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific error codes (-32000 to -32099)
    TOOL_NOT_FOUND = -32000
    TOOL_EXECUTION_ERROR = -32001
    TOOL_TIMEOUT = -32002
    PERMISSION_DENIED = -32003


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request object."""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.params is not None:
            data["params"] = self.params
        if self.id is not None:
            data["id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcRequest":
        """Create from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data["method"],
            params=data.get("params"),
            id=data.get("id")
        )


@dataclass
class JsonRpcError:
    """JSON-RPC 2.0 error object."""
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 response object."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            data["error"] = self.error.to_dict()
        else:
            data["result"] = self.result
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcResponse":
        """Create from dictionary."""
        error_data = data.get("error")
        error = None
        if error_data:
            error = JsonRpcError(
                code=error_data["code"],
                message=error_data["message"],
                data=error_data.get("data")
            )

        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            result=data.get("result"),
            error=error,
            id=data.get("id")
        )


class MCPJsonRpcServer:
    """
    MCP Server with JSON-RPC 2.0 transport over stdio.

    Handles tool registration and execution via JSON-RPC protocol.
    Reads requests from stdin and writes responses to stdout.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the JSON-RPC server.

        Args:
            debug: Enable debug logging to stderr
        """
        self.tools: Dict[str, Callable] = {}
        self.debug = debug

    def _log(self, message: str) -> None:
        """Log debug message to stderr."""
        if self.debug:
            print(f"[MCP JSON-RPC] {message}", file=sys.stderr)

    def add_tool(self, name: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Register a tool with the server.

        Args:
            name: Tool name (e.g., "browser", "filesystem")
            handler: Function that handles tool execution
                     Takes params dict, returns result or raises exception
        """
        self.tools[name] = handler
        self._log(f"Registered tool: {name}")

    def handle_request(self, request_line: str) -> Optional[str]:
        """
        Handle a single JSON-RPC request.

        Args:
            request_line: JSON-encoded request string

        Returns:
            JSON-encoded response string, or None for notifications
        """
        try:
            # Parse request
            request_data = json.loads(request_line)
            request = JsonRpcRequest.from_dict(request_data)

            self._log(f"Received request: {request.method} (id={request.id})")

            # Handle MCP methods
            if request.method == "tools/list":
                result = self._handle_list_tools()
            elif request.method == "tools/call":
                result = self._handle_call_tool(request.params or {})
            elif request.method == "ping":
                result = {"status": "ok"}
            else:
                # Unknown method
                return self._error_response(
                    request.id,
                    JsonRpcErrorCode.METHOD_NOT_FOUND.value,
                    f"Method not found: {request.method}"
                )

            # Create success response
            response = JsonRpcResponse(result=result, id=request.id)
            return json.dumps(response.to_dict())

        except json.JSONDecodeError as e:
            # Parse error
            return self._error_response(
                None,
                JsonRpcErrorCode.PARSE_ERROR.value,
                f"Parse error: {str(e)}"
            )
        except KeyError as e:
            # Invalid request (missing required field)
            return self._error_response(
                None,
                JsonRpcErrorCode.INVALID_REQUEST.value,
                f"Invalid request: missing {str(e)}"
            )
        except Exception as e:
            # Internal error
            return self._error_response(
                None,
                JsonRpcErrorCode.INTERNAL_ERROR.value,
                f"Internal error: {str(e)}"
            )

    def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle tools/list method."""
        return {
            "tools": [
                {"name": name, "available": True}
                for name in self.tools.keys()
            ]
        }

    def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call method."""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing 'name' parameter")

        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        try:
            self._log(f"Executing tool: {tool_name}")
            result = self.tools[tool_name](tool_params)
            return {"result": result, "tool": tool_name}
        except Exception as e:
            self._log(f"Tool execution error: {str(e)}")
            raise

    def _error_response(self, request_id: Optional[str], code: int, message: str) -> str:
        """Create a JSON-RPC error response."""
        error = JsonRpcError(code=code, message=message)
        response = JsonRpcResponse(error=error, id=request_id)
        return json.dumps(response.to_dict())

    def run(self) -> None:
        """
        Run the server, reading from stdin and writing to stdout.

        This method blocks and processes requests until stdin is closed.
        """
        self._log("MCP JSON-RPC server started")
        self._log(f"Available tools: {', '.join(self.tools.keys())}")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                response = self.handle_request(line)
                if response:
                    print(response, flush=True)

        except KeyboardInterrupt:
            self._log("Server stopped by user")
        except Exception as e:
            self._log(f"Server error: {str(e)}")
            raise


class MCPJsonRpcClient:
    """
    MCP Client with JSON-RPC 2.0 transport.

    Sends requests to an MCP server and receives responses.
    Can communicate via stdio or any other stream.
    """

    def __init__(self):
        """Initialize the JSON-RPC client."""
        self.request_id = 0

    def _next_id(self) -> str:
        """Generate next request ID."""
        self.request_id += 1
        return str(self.request_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the server.

        Returns:
            List of tool information dictionaries
        """
        request = JsonRpcRequest(
            method="tools/list",
            id=self._next_id()
        )
        return self._send_request(request)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool-specific arguments

        Returns:
            Tool execution result

        Raises:
            Exception: If tool execution fails
        """
        request = JsonRpcRequest(
            method="tools/call",
            params={"name": tool_name, "arguments": arguments},
            id=self._next_id()
        )
        return self._send_request(request)

    def ping(self) -> bool:
        """
        Ping the server to check if it's alive.

        Returns:
            True if server responds successfully
        """
        request = JsonRpcRequest(
            method="ping",
            id=self._next_id()
        )
        response = self._send_request(request)
        return response.get("status") == "ok"

    def _send_request(self, request: JsonRpcRequest) -> Any:
        """
        Send a request and return the result.

        This is a template method to be overridden by subclasses
        with specific transport implementations.

        Args:
            request: The request to send

        Returns:
            The result from the response

        Raises:
            Exception: If the response contains an error
        """
        raise NotImplementedError("Subclasses must implement _send_request")


def create_stdio_server(debug: bool = False) -> MCPJsonRpcServer:
    """
    Create an MCP JSON-RPC server that communicates via stdio.

    Args:
        debug: Enable debug logging

    Returns:
        Configured server instance

    Example:
        server = create_stdio_server(debug=True)
        server.add_tool("echo", lambda params: params)
        server.run()
    """
    return MCPJsonRpcServer(debug=debug)


__all__ = [
    "JsonRpcErrorCode",
    "JsonRpcRequest",
    "JsonRpcError",
    "JsonRpcResponse",
    "MCPJsonRpcServer",
    "MCPJsonRpcClient",
    "create_stdio_server",
]
