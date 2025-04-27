#!/usr/bin/env python3
"""
Configuration Manager for Database and Application Settings
:TechnologyVersion Python 3.10+
:ConfigurationAbstraction :DesignPattern
:SecurityPattern for secure credential management

This module implements the :ConfigurationAbstraction pattern to securely
manage configuration settings from multiple sources (environment variables,
.env files, and JSON config files) with proper precedence rules.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('config_manager')

class ConfigManager:
    """
    Configuration manager implementing the :ConfigurationAbstraction pattern.
    Handles loading configuration from multiple sources with proper precedence:
    1. Environment variables (highest priority)
    2. .env file
    3. JSON configuration file
    4. Default values (lowest priority)
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                        Defaults to the 'config' directory in the project root.
        """
        # Set default config directory if not provided
        if config_dir is None:
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = config_dir
            
        # Ensure config directory exists
        if not self.config_dir.exists():
            logger.warning(f"Configuration directory {self.config_dir} does not exist")
            
        self.env_file_path = self.config_dir / '.env'
        self._env_vars = {}
        
    def load_env_file(self) -> Dict[str, str]:
        """
        Load environment variables from .env file.
        
        Returns:
            Dictionary of environment variables loaded from .env file
        """
        if not self.env_file_path.exists():
            logger.debug(f"No .env file found at {self.env_file_path}")
            return {}
            
        env_vars = {}
        try:
            logger.debug(f"Loading environment variables from {self.env_file_path}")
            with open(self.env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                        
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                            
                        env_vars[key] = value
                        
            logger.debug(f"Loaded {len(env_vars)} variables from .env file")
            self._env_vars = env_vars
            return env_vars
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            return {}
            
    def load_json_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        Args:
            config_file: Name of the JSON configuration file
            
        Returns:
            Dictionary of configuration values
        """
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            logger.warning(f"Configuration file {config_path} not found")
            return {}
            
        try:
            logger.debug(f"Loading configuration from {config_path}")
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON configuration file {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration file {config_path}: {e}")
            return {}
            
    def get_db_config(self, config_file: Optional[str] = None, 
                     defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get database configuration with proper precedence:
        1. Environment variables (PGDB_*)
        2. .env file variables (PGDB_*)
        3. JSON configuration file
        4. Default values
        
        Args:
            config_file: Optional JSON configuration file name
            defaults: Default configuration values
            
        Returns:
            Dictionary of database configuration values
        """
        # Start with default values
        if defaults is None:
            config = {
                "host": "localhost",
                "port": 5432,
                "database": "postgres",
                "user": "postgres",
                "password": "",
            }
        else:
            config = defaults.copy()
            
        # Load from JSON config file if provided
        if config_file:
            json_config = self.load_json_config(config_file)
            if 'database' in json_config:
                config.update(json_config['database'])
                
        # Load from .env file
        env_vars = self.load_env_file()
        for key in config:
            env_key = f"PGDB_{key.upper()}"
            if env_key in env_vars:
                config[key] = env_vars[env_key]
                
        # Environment variables take highest precedence
        for key in config:
            env_key = f"PGDB_{key.upper()}"
            if env_key in os.environ:
                config[key] = os.environ[env_key]
                
        # Validate required configuration
        if not config.get('password'):
            logger.warning("Database password not set. Set PGDB_PASSWORD in environment or .env file")
            
        return config
        
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with proper precedence.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check environment variables first
        env_key = key.upper()
        if env_key in os.environ:
            return os.environ[env_key]
            
        # Check .env file
        if not self._env_vars:
            self.load_env_file()
        if env_key in self._env_vars:
            return self._env_vars[env_key]
            
        # Return default value
        return default

    def get_schwab_oauth_config(self, config_file: Optional[str] = None,
                               defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get Schwab API OAuth configuration with proper precedence:
        1. Environment variables (SCHWAB_*)
        2. .env file variables (SCHWAB_*)
        3. JSON configuration file
        4. Default values
        
        Args:
            config_file: Optional JSON configuration file name
            defaults: Default configuration values
            
        Returns:
            Dictionary of Schwab API OAuth configuration values
        """
        # Start with default values
        if defaults is None:
            config = {
                "client_id": "",
                "client_secret": "",
                "redirect_uri": "http://localhost:8000/callback",
                "api_base_url": "https://api.schwabapi.com/v1",
                "auth_url": "https://api.schwabapi.com/v1/oauth/authorize",
                "token_url": "https://api.schwabapi.com/v1/oauth/token",
                "scopes": "market_data accounts_trading",
            }
        else:
            config = defaults.copy()
            
        # Load from JSON config file if provided
        if config_file:
            json_config = self.load_json_config(config_file)
            if 'schwab_oauth' in json_config:
                config.update(json_config['schwab_oauth'])
                
        # Load from .env file
        env_vars = self.load_env_file()
        for key in config:
            env_key = f"SCHWAB_{key.upper()}"
            if env_key in env_vars:
                config[key] = env_vars[env_key]
                
        # Environment variables take highest precedence
        for key in config:
            env_key = f"SCHWAB_{key.upper()}"
            if env_key in os.environ:
                config[key] = os.environ[env_key]
                
        # Validate required configuration
        if not config.get('client_id') or not config.get('client_secret'):
            logger.warning("Schwab API client ID or secret not set. Set SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET in environment or .env file")
            
        return config

# Singleton instance for global use
config_manager = ConfigManager()