from collections import Counter, defaultdict
from typing import Dict, Optional, Any, List
import time
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TokenOperation:
    """Represents a single token-consuming operation"""
    type: str
    tokens: int
    timestamp: float
    metadata: Dict[str, Any]

class TokenBudgetExceeded(Exception):
    """Raised when token budget is exceeded"""
    pass

class TokenMonitor:
    """Monitors and manages token usage across the MCP server"""
    
    def __init__(self, budget_thresholds: Dict[str, int], 
                 alert_handlers: Optional[Dict[str, callable]] = None):
        """
        Initialize token monitor
        
        Args:
            budget_thresholds: Dict of threshold names to token counts
            alert_handlers: Optional dict of threshold names to handler functions
        """
        self.budget_thresholds = budget_thresholds
        self.alert_handlers = alert_handlers or {}
        
        # Metrics tracking
        self.metrics = {
            "token_usage": Counter(),
            "request_counts": Counter(),
            "cache_hits": Counter(),
            "budget_exceeded": Counter()
        }
        
        # Time series data for analysis
        self.time_series = defaultdict(list)
        
        # Active request tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        
        # Configure logging
        self.logger = logging.getLogger('TokenMonitor')
        
    def start_tracking(self) -> str:
        """
        Start tracking token usage for a new request
        
        Returns:
            str: Request tracking ID
        """
        request_id = str(uuid.uuid4())
        self.active_requests[request_id] = {
            "start_time": time.time(),
            "token_count": 0,
            "operations": [],
            "cache_hits": 0
        }
        return request_id
        
    def record_operation(self, request_id: str, op_type: str, 
                        token_count: int, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a token-consuming operation
        
        Args:
            request_id: Request tracking ID
            op_type: Type of operation
            token_count: Number of tokens used
            metadata: Optional operation metadata
        
        Raises:
            TokenBudgetExceeded: If operation would exceed token budget
        """
        if request_id not in self.active_requests:
            self.logger.warning(f"Attempt to record operation for unknown request {request_id}")
            return
            
        request_data = self.active_requests[request_id]
        new_total = request_data["token_count"] + token_count
        
        # Check budget thresholds
        self._check_thresholds(request_id, new_total)
        
        # Record operation
        operation = TokenOperation(
            type=op_type,
            tokens=token_count,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        request_data["operations"].append(operation)
        request_data["token_count"] = new_total
        
        # Update metrics
        self.metrics["token_usage"][op_type] += token_count
        
    def record_cache_hit(self, request_id: str) -> None:
        """Record cache hit for request"""
        if request_id in self.active_requests:
            self.active_requests[request_id]["cache_hits"] += 1
            self.metrics["cache_hits"]["total"] += 1
            
    def is_within_budget(self, request_id: str) -> bool:
        """Check if request is within token budget"""
        if request_id not in self.active_requests:
            return False
            
        return self.active_requests[request_id]["token_count"] < \
               self.budget_thresholds["critical"]
               
    def finish_tracking(self, request_id: str) -> Dict[str, Any]:
        """
        Complete token tracking for request
        
        Args:
            request_id: Request tracking ID
            
        Returns:
            dict: Request statistics
        """
        if request_id not in self.active_requests:
            return {}
            
        request_data = self.active_requests.pop(request_id)
        duration = time.time() - request_data["start_time"]
        total_tokens = request_data["token_count"]
        
        # Update metrics
        self.metrics["request_counts"]["total"] += 1
        if total_tokens >= self.budget_thresholds["critical"]:
            self.metrics["budget_exceeded"]["total"] += 1
            
        # Record time series data
        self._record_to_time_series(total_tokens, duration)
        
        return {
            "duration": duration,
            "total_tokens": total_tokens,
            "operation_count": len(request_data["operations"]),
            "cache_hits": request_data["cache_hits"]
        }
        
    def get_metrics(self, window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get monitoring metrics
        
        Args:
            window: Optional time window to restrict metrics
            
        Returns:
            dict: Current metrics
        """
        if not window:
            return dict(self.metrics)
            
        # Filter time series data by window
        cutoff = time.time() - window.total_seconds()
        windowed_data = {
            ts: data for ts, data in self.time_series.items()
            if ts >= cutoff
        }
        
        return {
            "token_usage": self._aggregate_window(windowed_data, "tokens"),
            "request_counts": len(windowed_data),
            "avg_tokens_per_request": (
                sum(d["tokens"] for d in windowed_data.values()) / len(windowed_data)
                if windowed_data else 0
            ),
            "peak_token_usage": max(
                (d["tokens"] for d in windowed_data.values()),
                default=0
            )
        }
        
    def _check_thresholds(self, request_id: str, token_count: int) -> None:
        """Check if token usage crosses any thresholds"""
        for threshold_name, threshold_value in self.budget_thresholds.items():
            if token_count > threshold_value:
                # Call threshold handler if configured
                if handler := self.alert_handlers.get(threshold_name):
                    handler(request_id, token_count, threshold_value)
                    
                # Raise exception for critical threshold
                if threshold_name == "critical":
                    raise TokenBudgetExceeded(
                        f"Token budget exceeded: {token_count} > {threshold_value}"
                    )
                    
    def _record_to_time_series(self, tokens: int, duration: float) -> None:
        """Record metrics to time series data"""
        timestamp = int(time.time())  # Round to nearest second
        self.time_series[timestamp].append({
            "tokens": tokens,
            "duration": duration
        })
        
        # Cleanup old data (keep last 24 hours)
        cutoff = timestamp - 86400
        self.time_series = {
            ts: data for ts, data in self.time_series.items()
            if ts >= cutoff
        }
        
    def _aggregate_window(self, data: Dict[int, List[Dict]], 
                         field: str) -> Dict[str, int]:
        """Aggregate time series data by field"""
        totals = Counter()
        for entries in data.values():
            for entry in entries:
                totals["total"] += entry[field]
                
        return dict(totals)