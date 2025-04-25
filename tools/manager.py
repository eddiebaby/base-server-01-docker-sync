from typing import Any, Dict, Optional, Iterator, List
import logging
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.cache import TokenCache
from monitoring.token_monitor import TokenMonitor, TokenBudgetExceeded

@dataclass
class ToolMetadata:
    """Metadata for a registered tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    token_budget: int
    batch_size: int
    custom_metadata: Dict[str, Any]

class Tool(ABC):
    """Abstract base class for token-efficient tools"""
    
    @abstractmethod
    def estimate_tokens(self, input_data: Dict[str, Any]) -> int:
        """Estimate tokens needed for input"""
        pass
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Execute tool with streaming results"""
        pass
        
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata"""
        pass

class BatchProcessingTool(Tool):
    """Base implementation for batch processing tools"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        
    def estimate_tokens(self, input_data: Dict[str, Any]) -> int:
        """Basic token estimation"""
        return len(str(input_data)) // 4  # Basic estimation
        
    async def execute(self, input_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Process in batches"""
        for batch in self._get_batches(input_data):
            result = await self._process_batch(batch)
            yield result
            
    @abstractmethod
    async def _process_batch(self, batch: Any) -> Dict[str, Any]:
        """Process a single batch - override in subclasses"""
        pass
        
    def _get_batches(self, data: Any) -> Iterator[Any]:
        """Split data into batches"""
        if isinstance(data, (list, tuple)):
            for i in range(0, len(data), self.batch_size):
                yield data[i:i + self.batch_size]
        else:
            yield data

class ToolManager:
    """Manages tool registration, execution and token budgeting"""
    
    def __init__(self, token_budget: int, batch_size: int,
                 token_monitor: TokenMonitor):
        """
        Initialize tool manager
        
        Args:
            token_budget: Global token budget
            batch_size: Default batch size
            token_monitor: Token monitoring instance
        """
        self.token_budget = token_budget
        self.default_batch_size = batch_size
        self.token_monitor = token_monitor
        
        # Tool registry
        self.tools: Dict[str, Tool] = {}
        
        # Result cache
        self.result_cache = TokenCache(
            max_size=1000,
            ttl=300,  # 5 minute TTL
            token_limit=token_budget // 10  # 10% of budget
        )
        
        # Metadata cache
        self.metadata_cache = TokenCache(
            max_size=100,  # Small cache for metadata
            ttl=3600  # 1 hour TTL
        )
        
        self.logger = logging.getLogger('ToolManager')
        
    def register(self, tool: Tool, name: str) -> None:
        """
        Register a new tool
        
        Args:
            tool: Tool implementation
            name: Tool name
        """
        if not isinstance(tool, Tool):
            raise TypeError("Tool must implement Tool interface")
            
        self.tools[name] = tool
        
        # Cache metadata
        try:
            metadata = tool.get_metadata()
            self.metadata_cache.set(name, metadata)
        except Exception as e:
            self.logger.warning(f"Failed to cache metadata for {name}: {e}")
            
    async def handle_request(self, request: Dict[str, Any], 
                           request_id: str) -> Dict[str, Any]:
        """
        Handle tool execution request with token optimization
        
        Args:
            request: Request data
            request_id: Request tracking ID
            
        Returns:
            dict: Response data
        """
        tool_name = request.get('tool')
        if not tool_name or tool_name not in self.tools:
            raise ValueError(f"Invalid tool name: {tool_name}")
            
        operation = request.get('operation', 'execute')
        
        if operation == 'execute':
            return await self._handle_execution(request, request_id, tool_name)
        elif operation == 'get_metadata':
            return await self._handle_metadata_request(request_id, tool_name)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    async def _handle_execution(self, request: Dict[str, Any],
                              request_id: str, tool_name: str) -> Dict[str, Any]:
        """Handle tool execution request"""
        input_data = request.get('input', {})
        
        # Check cache first
        cache_key = f"{tool_name}:{hash(str(input_data))}"
        if cached := self.result_cache.get(cache_key):
            self.token_monitor.record_cache_hit(request_id)
            return {"result": cached}
            
        # Get tool
        tool = self.tools[tool_name]
        
        # Estimate tokens
        estimated_tokens = tool.estimate_tokens(input_data)
        
        # Check budget before executing
        if estimated_tokens > self.token_budget:
            raise TokenBudgetExceeded(
                f"Estimated tokens {estimated_tokens} exceeds budget {self.token_budget}"
            )
            
        # Record operation
        self.token_monitor.record_operation(
            request_id,
            "tool_execution",
            estimated_tokens,
            {"tool": tool_name, "input_size": len(str(input_data))}
        )
        
        # Execute tool with streaming results
        try:
            results = []
            async for result in tool.execute(input_data):
                results.append(result)
                
                # Check accumulated tokens
                result_tokens = len(str(results)) // 4  # Basic estimation
                if result_tokens > self.token_budget:
                    raise TokenBudgetExceeded(
                        f"Accumulated tokens {result_tokens} exceeds budget"
                    )
                    
            # Cache final results if not too large
            final_result = {"results": results}
            if len(str(final_result)) // 4 <= self.token_budget // 10:
                self.result_cache.set(cache_key, final_result)
                
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {e}")
            raise
            
    async def _handle_metadata_request(self, request_id: str, 
                                     tool_name: str) -> Dict[str, Any]:
        """Handle metadata request"""
        # Check cache first
        if cached := self.metadata_cache.get(tool_name):
            self.token_monitor.record_cache_hit(request_id)
            return {"metadata": cached}
            
        # Get tool
        tool = self.tools[tool_name]
        
        # Record operation
        self.token_monitor.record_operation(
            request_id,
            "tool_metadata",
            10,  # Minimal token cost
            {"tool": tool_name}
        )
        
        # Get metadata
        try:
            metadata = tool.get_metadata()
            
            # Cache result
            self.metadata_cache.set(tool_name, metadata)
            
            return {"metadata": metadata}
            
        except Exception as e:
            self.logger.error(f"Error getting metadata for {tool_name}: {e}")
            raise
            
    def get_stats(self) -> Dict[str, Any]:
        """Get tool manager statistics"""
        return {
            "registered_tools": len(self.tools),
            "result_cache": self.result_cache.get_stats(),
            "metadata_cache": self.metadata_cache.get_stats(),
            "token_budget": self.token_budget,
            "default_batch_size": self.default_batch_size
        }
        
    def clear_caches(self) -> None:
        """Clear all tool caches"""
        self.result_cache.clear()
        self.metadata_cache.clear()
        
    def remove_tool(self, name: str) -> None:
        """Remove a registered tool and its cached data"""
        if name in self.tools:
            del self.tools[name]
            
            # Clear cached data
            self.result_cache.remove(name)
            self.metadata_cache.remove(name)
            
            self.logger.info(f"Removed tool: {name}")