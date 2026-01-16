# JSON MCP Transport

JSON-RPC 2.0 transport implementation for MCP (Model Context Protocol) servers.

## Overview

BrowserOS now supports **two transport protocols** for MCP:

1. **HTTP Transport** (existing) - RESTful API over HTTP
2. **JSON-RPC 2.0 Transport** (new) - Standard JSON-RPC over stdio

The JSON-RPC transport allows MCP servers to communicate via standard input/output, making them compatible with a wider range of AI tools and frameworks that expect stdio-based communication.

## Why JSON-RPC Transport?

### Benefits

- **Standard Protocol** - JSON-RPC 2.0 is a well-established standard
- **Stdio Communication** - Works with any tool that reads/writes stdio
- **Language Agnostic** - Easy to implement in any programming language
- **Lightweight** - No HTTP overhead, direct process communication
- **Better Integration** - Compatible with more AI frameworks and tools

### Use Cases

- **Claude Desktop** - Native support for stdio MCP servers
- **VS Code Extensions** - Communicate with language servers
- **Command-Line Tools** - Direct CLI integration
- **Embedded Systems** - Lower resource overhead
- **Container Environments** - Simpler deployment without HTTP ports

## JSON-RPC 2.0 Specification

BrowserOS implements the full [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification).

### Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "browser",
    "arguments": {
      "url": "https://example.com"
    }
  },
  "id": "1"
}
```

### Success Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "tool": "browser",
    "result": {
      "title": "Example Domain",
      "content": "..."
    }
  },
  "id": "1"
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Tool not found: invalid_tool",
    "data": {
      "available_tools": ["browser", "filesystem", "terminal"]
    }
  },
  "id": "1"
}
```

## Error Codes

### Standard JSON-RPC Errors

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | Missing required fields |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server internal error |

### MCP-Specific Errors

| Code | Message | Description |
|------|---------|-------------|
| -32000 | Tool not found | Requested tool doesn't exist |
| -32001 | Tool execution error | Tool failed during execution |
| -32002 | Tool timeout | Tool exceeded time limit |
| -32003 | Permission denied | Tool requires elevated permissions |

## MCP Methods

### `tools/list`

List all available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": "1"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {"name": "browser", "available": true},
      {"name": "filesystem", "available": true},
      {"name": "terminal", "available": true}
    ]
  },
  "id": "1"
}
```

### `tools/call`

Execute a tool.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "browser",
    "arguments": {
      "url": "https://example.com",
      "wait_for_load": true
    }
  },
  "id": "2"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tool": "browser",
    "result": {
      "status": "success",
      "title": "Example Domain",
      "url": "https://example.com"
    }
  },
  "id": "2"
}
```

### `ping`

Check if server is alive.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "ping",
  "id": "3"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "ok"
  },
  "id": "3"
}
```

## Server Implementation

### Python Server

```python
from browseros.mcp import MCPJsonRpcServer, create_stdio_server

# Create server
server = create_stdio_server(debug=True)

# Register tool handlers
def browser_tool(params):
    url = params.get("url")
    # Perform browser action
    return {"title": "Page Title", "url": url}

def filesystem_tool(params):
    action = params.get("action")
    path = params.get("path")
    # Perform filesystem action
    return {"success": True, "path": path}

server.add_tool("browser", browser_tool)
server.add_tool("filesystem", filesystem_tool)

# Run server (blocks, reading from stdin)
server.run()
```

### Running the Server

```bash
# Direct execution
python -m browseros.mcp.server

# With Claude Desktop
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "browseros": {
      "command": "python",
      "args": ["-m", "browseros.mcp.server"],
      "transport": "stdio"
    }
  }
}
```

## Client Implementation

### Python Client

```python
import sys
import json
from browseros.mcp import JsonRpcRequest

class StdioClient:
    def __init__(self, server_process):
        self.process = server_process
        self.request_id = 0

    def call_tool(self, tool_name, arguments):
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": str(self.request_id)
        }

        # Send request to server
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response:
            raise Exception(f"Tool error: {response['error']['message']}")

        return response["result"]

# Usage
import subprocess

process = subprocess.Popen(
    ["python", "-m", "browseros.mcp.server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

client = StdioClient(process)
result = client.call_tool("browser", {"url": "https://example.com"})
print(result)
```

### JavaScript/TypeScript Client

```typescript
import { spawn } from 'child_process';
import * as readline from 'readline';

class MCPJsonRpcClient {
  private process: any;
  private rl: readline.Interface;
  private requestId = 0;
  private pendingRequests = new Map();

  constructor(command: string, args: string[]) {
    this.process = spawn(command, args);

    this.rl = readline.createInterface({
      input: this.process.stdout
    });

    this.rl.on('line', (line) => {
      const response = JSON.parse(line);
      const callback = this.pendingRequests.get(response.id);
      if (callback) {
        this.pendingRequests.delete(response.id);
        if (response.error) {
          callback.reject(new Error(response.error.message));
        } else {
          callback.resolve(response.result);
        }
      }
    });
  }

  async callTool(toolName: string, arguments: any): Promise<any> {
    const id = String(++this.requestId);

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });

      const request = {
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: arguments
        },
        id: id
      };

      this.process.stdin.write(JSON.stringify(request) + '\n');
    });
  }

  async listTools(): Promise<any[]> {
    const id = String(++this.requestId);

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });

      const request = {
        jsonrpc: '2.0',
        method: 'tools/list',
        id: id
      };

      this.process.stdin.write(JSON.stringify(request) + '\n');
    });
  }
}

// Usage
const client = new MCPJsonRpcClient('python', ['-m', 'browseros.mcp.server']);

const tools = await client.listTools();
console.log('Available tools:', tools);

const result = await client.callTool('browser', {
  url: 'https://example.com'
});
console.log('Result:', result);
```

## Configuration

### BrowserOS Settings

Configure JSON-RPC transport in BrowserOS settings:

1. Navigate to `chrome://browseros/mcp`
2. Enable **JSON-RPC Transport**
3. Configure:
   - Transport type: `stdio` or `http`
   - Debug logging: Enable/disable
   - Timeout: Request timeout in seconds

### Environment Variables

```bash
# Enable JSON-RPC transport
export BROWSEROS_MCP_TRANSPORT=stdio

# Enable debug logging
export BROWSEROS_MCP_DEBUG=true

# Set request timeout (seconds)
export BROWSEROS_MCP_TIMEOUT=30
```

### Configuration File

`~/.config/browseros/mcp_config.json`:

```json
{
  "transport": "stdio",
  "debug": false,
  "timeout": 30,
  "tools": {
    "browser": {
      "enabled": true,
      "timeout": 60
    },
    "filesystem": {
      "enabled": true,
      "max_file_size": "10MB"
    }
  }
}
```

## Comparison: HTTP vs JSON-RPC

| Feature | HTTP Transport | JSON-RPC Transport |
|---------|----------------|-------------------|
| Protocol | RESTful HTTP/1.1 | JSON-RPC 2.0 |
| Communication | HTTP requests | Stdio (stdin/stdout) |
| Port Required | Yes (default 9100) | No |
| Latency | ~10-50ms | ~1-5ms |
| Overhead | HTTP headers | Minimal JSON |
| Streaming | SSE (Server-Sent Events) | Line-by-line |
| Error Handling | HTTP status codes | JSON-RPC error codes |
| Authentication | HTTP headers/cookies | Process isolation |
| Remote Access | Yes | No (local only) |
| Best For | Web services, APIs | CLI tools, desktop apps |

## Integration Examples

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "browseros": {
      "command": "python",
      "args": ["-m", "browseros.mcp.server"],
      "transport": "stdio",
      "env": {
        "BROWSEROS_MCP_DEBUG": "false"
      }
    }
  }
}
```

### VS Code Extension

```typescript
// In your VS Code extension
import { spawn } from 'child_process';

const mcpServer = spawn('python', ['-m', 'browseros.mcp.server']);

// Send request
const request = {
  jsonrpc: '2.0',
  method: 'tools/call',
  params: {
    name: 'browser',
    arguments: { url: 'https://example.com' }
  },
  id: '1'
};

mcpServer.stdin.write(JSON.dumps(request) + '\n');
```

### Command Line

```bash
# Start server
python -m browseros.mcp.server

# In another terminal, send JSON-RPC request
echo '{"jsonrpc":"2.0","method":"tools/list","id":"1"}' | python -m browseros.mcp.server

# With jq for pretty output
echo '{"jsonrpc":"2.0","method":"tools/list","id":"1"}' | \
  python -m browseros.mcp.server | jq .
```

## Testing

### Unit Tests

```python
import pytest
from browseros.mcp import MCPJsonRpcServer, JsonRpcRequest

def test_list_tools():
    server = MCPJsonRpcServer()
    server.add_tool("test", lambda p: p)

    request = '{"jsonrpc":"2.0","method":"tools/list","id":"1"}'
    response = server.handle_request(request)

    assert "test" in response

def test_call_tool():
    server = MCPJsonRpcServer()
    server.add_tool("echo", lambda p: {"echo": p})

    request = '''{
      "jsonrpc": "2.0",
      "method": "tools/call",
      "params": {"name": "echo", "arguments": {"msg": "hello"}},
      "id": "1"
    }'''

    response = server.handle_request(request)
    assert "hello" in response
```

### Integration Tests

```bash
# Test with real server
python -m browseros.mcp.server &
SERVER_PID=$!

# Send test request
echo '{"jsonrpc":"2.0","method":"ping","id":"1"}' | \
  nc localhost 9100

# Cleanup
kill $SERVER_PID
```

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
ps aux | grep browseros.mcp.server

# Test with simple ping
echo '{"jsonrpc":"2.0","method":"ping","id":"1"}' | \
  python -m browseros.mcp.server
```

### Parse Errors

```python
# Enable debug logging
server = create_stdio_server(debug=True)

# Check stderr for error details
python -m browseros.mcp.server 2>error.log
```

### Tool Not Found

```bash
# List available tools
echo '{"jsonrpc":"2.0","method":"tools/list","id":"1"}' | \
  python -m browseros.mcp.server
```

## See Also

- [Tool Usage Indicator](tool-usage-indicator.md)
- [MCP HTTP Transport](mcp-http-transport.md)
- [BrowserOS MCP Server](../server/mcp-server.md)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
