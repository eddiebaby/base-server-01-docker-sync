# Token-Efficient MCP Server Implementation

A high-performance Model Context Protocol (MCP) server implementation with built-in token optimization and monitoring.

## Features

- **Token-Efficient Resource Management**
  - Streaming data access
  - Chunked processing
  - Efficient caching
  - Compression support

- **Token-Aware Tool Management**
  - Token budget enforcement
  - Result streaming
  - Batch processing
  - Cache optimization

- **Comprehensive Token Monitoring**
  - Real-time usage tracking
  - Budget thresholds
  - Alert system
  - Usage analytics

## Architecture

The server is built around four core components:

1. **Core Server (core/server.py)**
   - Central coordination
   - Request handling
   - Configuration management
   - Component integration

2. **Resource Manager (resources/manager.py)**
   - Resource registration
   - Streaming access
   - Chunk management
   - Resource caching

3. **Tool Manager (tools/manager.py)**
   - Tool registration
   - Token budgeting
   - Result streaming
   - Tool caching

4. **Token Monitor (monitoring/token_monitor.py)**
   - Usage tracking
   - Budget enforcement
   - Alert handling
   - Metrics collection

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Configure the server through `config/server_config.json`:

```json
{
  "server": {
    "cache_size": 1000,
    "batch_size": 100,
    "compression": true,
    "token_budget": 10000
  },
  "monitoring": {
    "thresholds": {
      "warning": 8000,
      "critical": 9500
    }
  }
}
```

## Usage

### Basic Server Setup

```python
from core.server import MCPServer

# Initialize server
server = MCPServer()

# Register resources and tools
server.register_resource(my_resource, "example/resource")
server.register_tool(my_tool, "example_tool")

# Handle requests
result = await server.handle_request({
    "type": "tool",
    "tool": "example_tool",
    "operation": "execute",
    "input": {...}
})
```

### Creating Resources

Implement the `Resource` interface for token-efficient data access:

```python
from resources.manager import Resource, ResourceMetadata

class MyResource(Resource):
    def get_chunk(self, start: int, size: int) -> bytes:
        # Implement chunked data access
        pass
        
    def get_metadata(self) -> ResourceMetadata:
        # Return resource metadata
        pass
        
    def estimate_chunk_tokens(self, chunk_size: int) -> int:
        # Estimate token usage
        pass
```

### Creating Tools

Implement the `Tool` interface for token-aware processing:

```python
from tools.manager import Tool, ToolMetadata

class MyTool(Tool):
    def estimate_tokens(self, input_data: dict) -> int:
        # Estimate token usage
        pass
        
    async def execute(self, input_data: dict) -> Iterator[dict]:
        # Implement token-efficient processing
        pass
        
    def get_metadata(self) -> ToolMetadata:
        # Return tool metadata
        pass
```

### Token Monitoring

Monitor token usage and get statistics:

```python
# Get server statistics
stats = server.get_stats()
print(f"Token Usage: {stats['token_usage']}")
print(f"Cache Stats: {stats['cache']}")

# Configure alerts
def token_alert(request_id: str, usage: int, threshold: int):
    print(f"Token alert: Request {request_id} used {usage} tokens")

server.token_monitor.alert_handlers['warning'] = token_alert
```

## Example Implementation

See `examples/text_processing.py` for a complete example showing:
- Text resource with streaming
- Text analysis tool with batching
- Token monitoring and caching
- Request handling

Run the example:
```bash
python -m examples.text_processing
```

## Best Practices

1. **Resource Implementation**
   - Use streaming for large data
   - Implement efficient chunking
   - Optimize metadata
   - Cache appropriately

2. **Tool Implementation**
   - Estimate tokens accurately
   - Stream results when possible
   - Use batch processing
   - Handle budget limits

3. **Token Optimization**
   - Monitor usage patterns
   - Set appropriate thresholds
   - Use caching strategically
   - Compress when beneficial

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## License

MIT License - See LICENSE file for details