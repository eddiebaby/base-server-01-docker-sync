import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from core.cache import TokenCache
from monitoring.token_monitor import TokenMonitor
from resources.manager import ResourceManager
from tools.manager import ToolManager

class MCPServer:
    """Token-efficient MCP server implementation"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MCP server with configuration
        
        Args:
            config_path: Optional path to config file, uses default if not provided
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MCPServer')
        
        # Initialize components
        self._init_components()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load server configuration from file
        
        Args:
            config_path: Path to config file or None for default
            
        Returns:
            dict: Server configuration
        """
        if not config_path:
            config_path = Path(__file__).parent.parent / 'config' / 'server_config.json'
            
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            raise RuntimeError(f"Configuration load failed: {e}")
            
    def _init_components(self) -> None:
        """Initialize server components with token optimization"""
        # Token cache for server-wide use
        self.token_cache = TokenCache(
            max_size=self.config['server']['cache_size'],
            token_limit=self.config['server']['token_budget'] // 10  # 10% of total budget
        )
        
        # Token monitoring
        self.token_monitor = TokenMonitor(
            budget_thresholds=self.config['monitoring']['thresholds'],
            alert_handlers=self._setup_alert_handlers()
        )
        
        # Resource management
        self.resource_mgr = ResourceManager(
            cache_size=self.config['server']['cache_size'],
            compression=self.config['server']['compression'],
            token_monitor=self.token_monitor
        )
        
        # Tool management
        self.tool_mgr = ToolManager(
            token_budget=self.config['server']['token_budget'],
            batch_size=self.config['server']['batch_size'],
            token_monitor=self.token_monitor
        )
        
    def _setup_alert_handlers(self) -> Dict[str, callable]:
        """Set up handlers for token budget alerts"""
        handlers = {}
        
        def log_handler(request_id: str, usage: int, threshold: int):
            self.logger.warning(
                f"Token budget alert: Request {request_id} used {usage} tokens "
                f"(threshold: {threshold})"
            )
            
        def notify_handler(request_id: str, usage: int, threshold: int):
            # Implement notification logic (email, Slack, etc.)
            pass
            
        # Register configured handlers
        if 'log' in self.config['monitoring']['alert_handlers']:
            handlers['log'] = log_handler
        if 'notify' in self.config['monitoring']['alert_handlers']:
            handlers['notify'] = notify_handler
            
        return handlers
        
    def register_resource(self, resource: Any, uri: str) -> None:
        """
        Register a new resource with token monitoring
        
        Args:
            resource: Resource implementation
            uri: Resource URI for access
        """
        try:
            self.resource_mgr.register(resource, uri)
            self.logger.info(f"Registered resource at URI: {uri}")
        except Exception as e:
            self.logger.error(f"Failed to register resource {uri}: {e}")
            raise
            
    def register_tool(self, tool: Any, name: str) -> None:
        """
        Register a new tool with token budget constraints
        
        Args:
            tool: Tool implementation
            name: Tool name for access
        """
        try:
            self.tool_mgr.register(tool, name)
            self.logger.info(f"Registered tool: {name}")
        except Exception as e:
            self.logger.error(f"Failed to register tool {name}: {e}")
            raise
            
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP request with token optimization
        
        Args:
            request: Request data
            
        Returns:
            dict: Response data
        """
        # Start token tracking
        request_id = self.token_monitor.start_tracking()
        
        try:
            # Check token cache
            cache_key = self._get_cache_key(request)
            if cached := self.token_cache.get(cache_key):
                self.token_monitor.record_cache_hit(request_id)
                return cached
                
            # Process request
            result = await self._process_request(request, request_id)
            
            # Cache if within budget
            if self.token_monitor.is_within_budget(request_id):
                self.token_cache.set(cache_key, result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing request {request_id}: {e}")
            return {"error": str(e)}
            
        finally:
            # Complete token tracking
            self.token_monitor.finish_tracking(request_id)
            
    async def _process_request(self, request: Dict[str, Any], 
                             request_id: str) -> Dict[str, Any]:
        """
        Process request based on type
        
        Args:
            request: Request data
            request_id: Request tracking ID
            
        Returns:
            dict: Response data
        """
        req_type = request.get('type')
        
        if req_type == 'resource':
            return await self.resource_mgr.handle_request(request, request_id)
        elif req_type == 'tool':
            return await self.tool_mgr.handle_request(request, request_id)
        else:
            raise ValueError(f"Unknown request type: {req_type}")
            
    def _get_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        # Basic implementation - override for more sophisticated caching
        return f"{request.get('type')}:{request.get('uri', '')}:{hash(str(request))}"
        
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics and metrics"""
        return {
            "cache": self.token_cache.get_stats(),
            "resources": self.resource_mgr.get_stats(),
            "tools": self.tool_mgr.get_stats(),
            "token_usage": self.token_monitor.get_metrics()
        }