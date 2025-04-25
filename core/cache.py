from collections import OrderedDict
from typing import Any, Optional
import time

class LRUCache:
    """Token-efficient LRU cache implementation with size limits and TTL support"""
    
    def __init__(self, max_size: int, ttl: Optional[int] = None):
        """
        Initialize LRU cache with size and optional time-to-live
        
        Args:
            max_size: Maximum number of items to store
            ttl: Optional time-to-live in seconds for cache entries
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()  # {key: (value, timestamp)}
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with token-efficient access
        
        Args:
            key: Cache key to lookup
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None
            
        value, timestamp = self._cache[key]
        
        # Check TTL if enabled
        if self.ttl and time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
            
        # Move to end for LRU tracking
        self._cache.move_to_end(key)
        return value
        
    def set(self, key: str, value: Any) -> None:
        """
        Set cache value with token-efficient storage
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove oldest if at max size
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            
        # Store with timestamp
        self._cache[key] = (value, time.time())
        
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        
    def remove(self, key: str) -> None:
        """Remove specific cache entry"""
        if key in self._cache:
            del self._cache[key]
            
    @property
    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)
        
    def get_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "ttl": self.ttl,
            "oldest_entry_age": self._get_oldest_age()
        }
        
    def _get_oldest_age(self) -> Optional[float]:
        """Get age of oldest cache entry in seconds"""
        if not self._cache:
            return None
        _, timestamp = next(iter(self._cache.values()))
        return time.time() - timestamp

class TokenCache(LRUCache):
    """Specialized cache for token-aware storage and retrieval"""
    
    def __init__(self, max_size: int, ttl: Optional[int] = None, 
                 token_limit: Optional[int] = None):
        """
        Initialize token-aware cache
        
        Args:
            max_size: Maximum number of items
            ttl: Optional time-to-live in seconds
            token_limit: Optional maximum tokens per entry
        """
        super().__init__(max_size, ttl)
        self.token_limit = token_limit
        self.token_counts = {}  # {key: token_count}
        
    def set(self, key: str, value: Any, token_count: Optional[int] = None) -> bool:
        """
        Set cache value with token tracking
        
        Args:
            key: Cache key
            value: Value to cache
            token_count: Optional count of tokens in value
            
        Returns:
            bool: True if cached, False if rejected due to token limit
        """
        # Estimate tokens if not provided
        if token_count is None:
            token_count = self._estimate_tokens(value)
            
        # Check token limit if set
        if self.token_limit and token_count > self.token_limit:
            return False
            
        super().set(key, value)
        self.token_counts[key] = token_count
        return True
        
    def remove(self, key: str) -> None:
        """Remove cache entry and token count"""
        super().remove(key)
        self.token_counts.pop(key, None)
        
    def clear(self) -> None:
        """Clear cache and token counts"""
        super().clear()
        self.token_counts.clear()
        
    def get_stats(self) -> dict:
        """Get extended cache statistics with token info"""
        stats = super().get_stats()
        stats.update({
            "total_tokens": sum(self.token_counts.values()),
            "avg_tokens_per_entry": (
                sum(self.token_counts.values()) / len(self.token_counts)
                if self.token_counts else 0
            ),
            "token_limit": self.token_limit
        })
        return stats
        
    def _estimate_tokens(self, value: Any) -> int:
        """Estimate token count for a value"""
        # Basic estimation - override for better accuracy
        return len(str(value)) // 4