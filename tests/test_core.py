import pytest
import asyncio
from typing import Dict, Any
import json
from pathlib import Path
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

from core.server import MCPServer
from core.cache import TokenCache, LRUCache
from resources.manager import Resource, ResourceMetadata
from tools.manager import Tool, ToolMetadata
from monitoring.token_monitor import TokenMonitor, TokenBudgetExceeded

class MockResource(Resource):
    """Mock resource for testing"""
    
    def __init__(self, data: str = "test data"):
        self.data = data
        
    def get_chunk(self, start: int, size: int) -> bytes:
        end = min(start + size, len(self.data))
        return self.data[start:end].encode('utf-8')
        
    def get_metadata(self) -> ResourceMetadata:
        return ResourceMetadata(
            type="test",
            size=len(self.data),
            chunk_size=10,
            compression=False,
            timestamp=0,
            custom_metadata={}
        )
        
    def estimate_chunk_tokens(self, chunk_size: int) -> int:
        return chunk_size // 4

class MockTool(Tool):
    """Mock tool for testing"""
    
    def estimate_tokens(self, input_data: Dict[str, Any]) -> int:
        return len(str(input_data)) // 4
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": f"processed: {input_data}"}
        
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mock_tool",
            description="Test tool",
            input_schema={},
            output_schema={},
            token_budget=1000,
            batch_size=100,
            custom_metadata={}
        )

@pytest.fixture
def config_path(tmp_path):
    """Create temporary config file"""
    config = {
        "server": {
            "cache_size": 100,
            "batch_size": 10,
            "compression": False,
            "token_budget": 1000
        },
        "monitoring": {
            "thresholds": {
                "warning": 800,
                "critical": 900
            },
            "alert_handlers": ["log"]
        }
    }
    
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file)

@pytest.fixture
async def server(config_path):
    """Create test server instance"""
    server = MCPServer(config_path)
    yield server

def test_lru_cache():
    """Test basic LRU cache functionality"""
    cache = LRUCache(max_size=2)
    
    # Test basic set/get
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    
    # Test LRU eviction
    cache.set("key3", "value3")
    assert cache.get("key1") is None  # Should be evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

def test_token_cache():
    """Test token-aware cache"""
    cache = TokenCache(max_size=2, token_limit=10)
    
    # Test token limit enforcement
    assert cache.set("key1", "small", token_count=5)  # Should succeed
    assert not cache.set("key2", "too_large", token_count=15)  # Should fail
    
    # Test stats
    stats = cache.get_stats()
    assert stats["total_tokens"] == 5
    assert stats["token_limit"] == 10

@pytest.mark.asyncio
async def test_server_resource_handling(server):
    """Test server resource handling"""
    resource = MockResource()
    server.register_resource(resource, "test/resource")
    
    # Test chunk request
    request = {
        "type": "resource",
        "uri": "test/resource",
        "operation": "get_chunk",
        "start": 0,
        "size": 5
    }
    
    result = await server.handle_request(request)
    assert result["data"].decode('utf-8') == "test "
    
    # Test metadata request
    request["operation"] = "get_metadata"
    result = await server.handle_request(request)
    assert result["metadata"].type == "test"

@pytest.mark.asyncio
async def test_server_tool_handling(server):
    """Test server tool handling"""
    tool = MockTool()
    server.register_tool(tool, "test_tool")
    
    # Test tool execution
    request = {
        "type": "tool",
        "tool": "test_tool",
        "operation": "execute",
        "input": {"test": "data"}
    }
    
    result = await server.handle_request(request)
    assert "result" in result
    
    # Test metadata request
    request["operation"] = "get_metadata"
    result = await server.handle_request(request)
    assert result["metadata"].name == "mock_tool"

@pytest.mark.asyncio
async def test_token_budget_enforcement(server):
    """Test token budget enforcement"""
    tool = MockTool()
    server.register_tool(tool, "test_tool")
    
    # Create large input that exceeds token budget
    large_input = "x" * 5000
    
    request = {
        "type": "tool",
        "tool": "test_tool",
        "operation": "execute",
        "input": {"data": large_input}
    }
    
    # The error is being caught in the handle_request method and returned as an error response
    result = await server.handle_request(request)
    assert "error" in result
    assert "exceeds budget" in result["error"]

@pytest.mark.asyncio
async def test_caching_behavior(server):
    """Test request caching"""
    tool = MockTool()
    server.register_tool(tool, "test_tool")
    
    request = {
        "type": "tool",
        "tool": "test_tool",
        "operation": "execute",
        "input": {"test": "data"}
    }
    
    # First request should process
    result1 = await server.handle_request(request)
    
    # Second request should hit cache
    result2 = await server.handle_request(request)
    
    assert result1 == result2
    
    # Verify cache hit in metrics
    stats = server.get_stats()
    assert stats["cache"]["size"] > 0

def test_token_monitor():
    """Test token monitoring"""
    monitor = TokenMonitor(
        budget_thresholds={"warning": 80, "critical": 90},
        alert_handlers={"warning": lambda *args: None}
    )
    
    # Start tracking
    request_id = monitor.start_tracking()
    
    # Record operations
    monitor.record_operation(request_id, "test", 50)
    assert monitor.is_within_budget(request_id)
    
    # Record cache hit
    monitor.record_cache_hit(request_id)
    
    # Finish tracking
    stats = monitor.finish_tracking(request_id)
    assert stats["total_tokens"] == 50
    assert stats["cache_hits"] == 1

if __name__ == '__main__':
    pytest.main([__file__])