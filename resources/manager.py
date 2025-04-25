from typing import Any, Dict, Optional, Iterator
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.cache import LRUCache
from monitoring.token_monitor import TokenMonitor

@dataclass
class ResourceMetadata:
    """Metadata for a managed resource"""
    type: str
    size: int
    chunk_size: int
    compression: bool
    timestamp: float
    custom_metadata: Dict[str, Any]

class Resource(ABC):
    """Abstract base class for token-efficient resources"""
    
    @abstractmethod
    def get_chunk(self, start: int, size: int) -> bytes:
        """Get resource data in chunks"""
        pass
        
    @abstractmethod
    def get_metadata(self) -> ResourceMetadata:
        """Get resource metadata"""
        pass
        
    @abstractmethod
    def estimate_chunk_tokens(self, chunk_size: int) -> int:
        """Estimate tokens for chunk size"""
        pass

class StreamingResource(Resource):
    """Base implementation for streaming resources"""
    
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
        self._data_stream = None
        
    def get_chunk(self, start: int, size: int) -> bytes:
        if not self._data_stream:
            self._data_stream = self._init_stream()
        return self._data_stream.read(start, size)
        
    def _init_stream(self):
        """Initialize data stream - override in subclasses"""
        raise NotImplementedError
        
    def estimate_chunk_tokens(self, chunk_size: int) -> int:
        """Basic token estimation"""
        return chunk_size // 4  # Basic estimation

class ResourceManager:
    """Manages token-efficient resource access and caching"""
    
    def __init__(self, cache_size: int, compression: bool,
                 token_monitor: TokenMonitor):
        """
        Initialize resource manager
        
        Args:
            cache_size: Maximum cache size
            compression: Whether to use compression
            token_monitor: Token monitoring instance
        """
        self.compression = compression
        self.token_monitor = token_monitor
        
        # Resource registry
        self.resources: Dict[str, Resource] = {}
        
        # Cache for resource chunks
        self.chunk_cache = LRUCache(
            max_size=cache_size,
            ttl=3600  # 1 hour TTL for chunks
        )
        
        # Cache for resource metadata
        self.metadata_cache = LRUCache(
            max_size=cache_size // 10,  # Smaller cache for metadata
            ttl=300  # 5 minute TTL for metadata
        )
        
        self.logger = logging.getLogger('ResourceManager')
        
    def register(self, resource: Resource, uri: str) -> None:
        """
        Register a new resource
        
        Args:
            resource: Resource implementation
            uri: Resource URI
        """
        if not isinstance(resource, Resource):
            raise TypeError("Resource must implement Resource interface")
            
        self.resources[uri] = resource
        
        # Cache initial metadata
        try:
            metadata = resource.get_metadata()
            self.metadata_cache.set(uri, metadata)
        except Exception as e:
            self.logger.warning(f"Failed to cache metadata for {uri}: {e}")
            
    async def handle_request(self, request: Dict[str, Any], 
                           request_id: str) -> Dict[str, Any]:
        """
        Handle resource request with token optimization
        
        Args:
            request: Request data
            request_id: Request tracking ID
            
        Returns:
            dict: Response data
        """
        uri = request.get('uri')
        if not uri or uri not in self.resources:
            raise ValueError(f"Invalid resource URI: {uri}")
            
        operation = request.get('operation', 'get_chunk')
        
        if operation == 'get_chunk':
            return await self._handle_chunk_request(request, request_id, uri)
        elif operation == 'get_metadata':
            return await self._handle_metadata_request(request_id, uri)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    async def _handle_chunk_request(self, request: Dict[str, Any], 
                                  request_id: str, uri: str) -> Dict[str, Any]:
        """Handle chunk data request"""
        start = request.get('start', 0)
        size = request.get('size', self.resources[uri].chunk_size)
        
        # Check cache first
        cache_key = f"{uri}:{start}:{size}"
        if cached := self.chunk_cache.get(cache_key):
            self.token_monitor.record_cache_hit(request_id)
            return {"data": cached}
            
        # Get resource
        resource = self.resources[uri]
        
        # Estimate tokens
        estimated_tokens = resource.estimate_chunk_tokens(size)
        
        # Record operation before executing
        self.token_monitor.record_operation(
            request_id,
            "resource_chunk",
            estimated_tokens,
            {"uri": uri, "start": start, "size": size}
        )
        
        # Get data
        try:
            data = resource.get_chunk(start, size)
            
            # Cache result
            self.chunk_cache.set(cache_key, data)
            
            return {"data": data}
            
        except Exception as e:
            self.logger.error(f"Error getting chunk from {uri}: {e}")
            raise
            
    async def _handle_metadata_request(self, request_id: str, uri: str) -> Dict[str, Any]:
        """Handle metadata request"""
        # Check cache first
        if cached := self.metadata_cache.get(uri):
            self.token_monitor.record_cache_hit(request_id)
            return {"metadata": cached}
            
        # Get resource
        resource = self.resources[uri]
        
        # Record operation
        self.token_monitor.record_operation(
            request_id,
            "resource_metadata",
            10,  # Minimal token cost for metadata
            {"uri": uri}
        )
        
        # Get metadata
        try:
            metadata = resource.get_metadata()
            
            # Cache result
            self.metadata_cache.set(uri, metadata)
            
            return {"metadata": metadata}
            
        except Exception as e:
            self.logger.error(f"Error getting metadata from {uri}: {e}")
            raise
            
    def get_stats(self) -> Dict[str, Any]:
        """Get resource manager statistics"""
        return {
            "registered_resources": len(self.resources),
            "chunk_cache": self.chunk_cache.get_stats(),
            "metadata_cache": self.metadata_cache.get_stats(),
            "compression_enabled": self.compression
        }
        
    def clear_caches(self) -> None:
        """Clear all resource caches"""
        self.chunk_cache.clear()
        self.metadata_cache.clear()
        
    def remove_resource(self, uri: str) -> None:
        """Remove a registered resource and its cached data"""
        if uri in self.resources:
            del self.resources[uri]
            
            # Clear cached data
            self.chunk_cache.remove(uri)
            self.metadata_cache.remove(uri)
            
            self.logger.info(f"Removed resource: {uri}")