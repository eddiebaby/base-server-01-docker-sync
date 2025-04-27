#!/usr/bin/env python3
"""
SystemMonitor Module
:TechnologyVersion: Python 3.10+
:ComponentRole: Model in MVC pattern
:Context: System monitoring data collection for dashboard

This module implements the SystemMonitor class that collects system metrics,
database statistics, and pipeline performance data.
"""

import os
import sys
import json
import logging
import platform
import datetime
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple

# For system monitoring
try:
    import psutil
    import sqlalchemy as sa
except ImportError as e:
    logging.error(f"Required package not found: {str(e)}")
    logging.info("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "sqlalchemy"])
    import psutil
    import sqlalchemy as sa

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Exception raised for database connection issues"""
    pass

class SystemMonitor:
    """
    SystemMonitor class for collecting system metrics and statistics
    
    Uses the MVC pattern (Model component) to provide data to the dashboard controller
    """
    
    def __init__(self, connection_manager, config_manager):
        """
        Initialize the SystemMonitor with connection and configuration managers
        
        Args:
            connection_manager: Database connection manager
            config_manager: Configuration manager
        """
        self.connection_manager = connection_manager
        self.config_manager = config_manager
        self.db_engine = None
        self.last_error = None
        self.recent_errors: List[Dict[str, Any]] = []
        
        # Load configuration
        self._load_config()
        
        # Initialize database connection if connection manager is provided
        if self.connection_manager:
            try:
                self.db_engine = self.connection_manager.get_engine()
                logger.info("Database connection initialized")
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Failed to initialize database connection: {str(e)}")
                # Don't raise here, as we want the monitor to work even without DB
    
    def _load_config(self) -> None:
        """Load configuration from config manager"""
        try:
            dashboard_config = self.config_manager.get_config_value('DASHBOARD_CONFIG', 'dashboard_config.json')
            self.config = self.config_manager.load_json_config(dashboard_config)
            
            # Set default values if config is not available
            if not self.config:
                self.config = {
                    'metrics': {
                        'database': {
                            'enabled': True,
                            'table_count_limit': 100,
                            'recent_data_limit': 5
                        },
                        'pipeline': {
                            'enabled': True,
                            'graph_points': 10,
                            'error_threshold': 10
                        },
                        'system': {
                            'enabled': True,
                            'cpu_warning_threshold': 80,
                            'memory_warning_threshold': 80,
                            'disk_warning_threshold': 85,
                            'error_history_limit': 20
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Set default config
            self.config = {
                'metrics': {
                    'database': {'enabled': True, 'table_count_limit': 100, 'recent_data_limit': 5},
                    'pipeline': {'enabled': True, 'graph_points': 10, 'error_threshold': 10},
                    'system': {'enabled': True, 'error_history_limit': 20}
                }
            }
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect all system metrics and return as a dictionary
        
        Returns:
            Dict containing all metrics (system, database, pipeline)
        """
        metrics = {
            'timestamp': datetime.datetime.now().isoformat(),
            'system_status': self._determine_system_status()
        }
        
        # Collect system metrics if enabled
        if self.config.get('metrics', {}).get('system', {}).get('enabled', True):
            try:
                metrics['system'] = self.get_system_health()
            except Exception as e:
                logger.error(f"Error collecting system metrics: {str(e)}")
                self._record_error("SystemMonitor", f"Failed to collect system metrics: {str(e)}")
                metrics['system'] = {'error': str(e)}
        
        # Collect database metrics if enabled
        if self.config.get('metrics', {}).get('database', {}).get('enabled', True):
            try:
                metrics['database'] = self.get_database_stats()
            except Exception as e:
                logger.error(f"Error collecting database metrics: {str(e)}")
                self._record_error("Database", f"Failed to collect database metrics: {str(e)}")
                metrics['database'] = {'error': str(e), 'connection_status': 'disconnected'}
        
        # Collect pipeline metrics if enabled
        if self.config.get('metrics', {}).get('pipeline', {}).get('enabled', True):
            try:
                metrics['pipeline'] = self.get_pipeline_metrics()
            except Exception as e:
                logger.error(f"Error collecting pipeline metrics: {str(e)}")
                self._record_error("Pipeline", f"Failed to collect pipeline metrics: {str(e)}")
                metrics['pipeline'] = {'error': str(e)}
        
        return metrics
    
    def _determine_system_status(self) -> str:
        """
        Determine the overall system status based on all metrics
        
        Returns:
            Status string: 'healthy', 'warning', or 'critical'
        """
        if self.last_error or len(self.recent_errors) > 3:
            return 'critical'
        
        try:
            # Check CPU usage
            cpu_threshold = self.config.get('metrics', {}).get('system', {}).get('cpu_warning_threshold', 80)
            if psutil.cpu_percent(interval=0.1) > cpu_threshold:
                return 'warning'
            
            # Check memory usage
            memory_threshold = self.config.get('metrics', {}).get('system', {}).get('memory_warning_threshold', 80)
            if psutil.virtual_memory().percent > memory_threshold:
                return 'warning'
            
            # Check disk usage
            disk_threshold = self.config.get('metrics', {}).get('system', {}).get('disk_warning_threshold', 85)
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    if usage.percent > disk_threshold:
                        return 'warning'
                except (PermissionError, OSError):
                    # Skip partitions that can't be accessed
                    continue
            
            # Check database connection
            if self.db_engine is None:
                return 'warning'
            
            return 'healthy'
        except Exception as e:
            logger.error(f"Error determining system status: {str(e)}")
            self._record_error("SystemMonitor", f"Failed to determine system status: {str(e)}")
            return 'critical'
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health information including CPU, memory, disk, and recent errors
        
        Returns:
            Dict containing system health metrics
        """
        health_data = {}
        
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            
            health_data['cpu'] = {
                'core_count': cpu_count,
                'average_usage': cpu_percent,
                'per_core': [p for p in psutil.cpu_percent(interval=0.1, percpu=True)],
                'threshold': self.config.get('metrics', {}).get('system', {}).get('cpu_warning_threshold', 80)
            }
            
            # Memory information
            mem = psutil.virtual_memory()
            health_data['memory'] = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'threshold': self.config.get('metrics', {}).get('system', {}).get('memory_warning_threshold', 80)
            }
            
            # Disk information
            disk_data = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_data[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                        'filesystem': partition.fstype
                    }
                except (PermissionError, OSError):
                    # Skip partitions that can't be accessed
                    continue
            
            health_data['disk'] = disk_data
            health_data['disk_threshold'] = self.config.get('metrics', {}).get('system', {}).get('disk_warning_threshold', 85)
            
            # Recent errors
            health_data['recent_errors'] = self.recent_errors
            
            # System information
            health_data['system_info'] = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'uptime': self._get_uptime()
            }
            
            return health_data
        
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            self._record_error("SystemMonitor", f"Failed to get system health: {str(e)}")
            return {'error': str(e)}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics including connection status, table counts, and recent data
        
        Returns:
            Dict containing database statistics
            
        Raises:
            DatabaseConnectionError: If database connection fails
        """
        stats = {
            'connection_status': 'disconnected',
            'table_counts': {},
            'recent_data': {}
        }
        
        if not self.db_engine:
            if self.connection_manager:
                try:
                    self.db_engine = self.connection_manager.get_engine()
                except Exception as e:
                    logger.error(f"Failed to initialize database connection: {str(e)}")
                    self._record_error("Database", f"Connection failed: {str(e)}")
                    raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
            else:
                # If no connection manager is provided, return mock data
                return self._get_mock_database_stats()
        
        try:
            # Test connection
            with self.db_engine.connect() as conn:
                stats['connection_status'] = 'connected'
                
                # Get table names
                metadata = sa.MetaData()
                metadata.reflect(bind=conn)
                
                # Get table counts
                table_count_limit = self.config.get('metrics', {}).get('database', {}).get('table_count_limit', 100)
                for table_name in metadata.tables:
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                    try:
                        result = conn.execute(sa.text(count_query))
                        count = result.scalar()
                        stats['table_counts'][table_name] = count
                    except Exception as e:
                        logger.warning(f"Error counting table {table_name}: {str(e)}")
                        stats['table_counts'][table_name] = -1
                
                # Get recent data for each table
                data_limit = self.config.get('metrics', {}).get('database', {}).get('recent_data_limit', 5)
                for table_name in metadata.tables:
                    query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {data_limit}"
                    try:
                        result = conn.execute(sa.text(query))
                        rows = [dict(row) for row in result]
                        stats['recent_data'][table_name] = rows
                    except Exception as e:
                        # The table might not have an id column or might be empty
                        try:
                            # Try alternate query without id column
                            query = f"SELECT * FROM {table_name} LIMIT {data_limit}"
                            result = conn.execute(sa.text(query))
                            rows = [dict(row) for row in result]
                            stats['recent_data'][table_name] = rows
                        except Exception as e2:
                            logger.warning(f"Error getting recent data for table {table_name}: {str(e2)}")
                            stats['recent_data'][table_name] = []
                
                return stats
        
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            self._record_error("Database", f"Failed to get database stats: {str(e)}")
            stats['error'] = str(e)
            raise DatabaseConnectionError(f"Database query failed: {str(e)}")
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """
        Get pipeline performance metrics
        
        Returns:
            Dict containing pipeline metrics
        """
        try:
            # For now, we'll return mock pipeline data
            # In a real system, this would collect data from the pipeline
            pipeline_metrics = {
                'pipeline_status': {
                    'main_etl': {
                        'status': 'running',
                        'last_run': datetime.datetime.now().isoformat(),
                        'processed_count': 1250,
                        'error_count': 2
                    },
                    'data_enrichment': {
                        'status': 'idle',
                        'last_run': (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
                        'processed_count': 500,
                        'error_count': 0
                    },
                    'reporting': {
                        'status': 'warning',
                        'last_run': (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat(),
                        'processed_count': 150,
                        'error_count': 5
                    }
                },
                'processing_rates': {
                    'main_etl': {
                        'items_per_second': 42.5,
                        'items_per_minute': 2550
                    },
                    'data_enrichment': {
                        'items_per_second': 16.7,
                        'items_per_minute': 1000
                    },
                    'reporting': {
                        'items_per_second': 8.3,
                        'items_per_minute': 500
                    }
                },
                'error_rates': {
                    'main_etl': {
                        'error_count': 12,
                        'error_percentage': 0.96
                    },
                    'data_enrichment': {
                        'error_count': 0,
                        'error_percentage': 0
                    },
                    'reporting': {
                        'error_count': 23,
                        'error_percentage': 15.3
                    }
                }
            }
            
            # In a real system, we'd fetch this from logs, monitoring systems, etc.
            return pipeline_metrics
        
        except Exception as e:
            logger.error(f"Error getting pipeline metrics: {str(e)}")
            self._record_error("Pipeline", f"Failed to get pipeline metrics: {str(e)}")
            return {'error': str(e)}
    
    def _get_mock_database_stats(self) -> Dict[str, Any]:
        """Generate mock database statistics for when DB is not available"""
        return {
            'connection_status': 'disconnected',
            'table_counts': {
                'users': 125,
                'sessions': 348,
                'logs': 5279,
                'metrics': 1893
            },
            'recent_data': {
                'users': [
                    {'id': 1, 'username': 'admin', 'created_at': datetime.datetime.now().isoformat()},
                    {'id': 2, 'username': 'user1', 'created_at': datetime.datetime.now().isoformat()}
                ],
                'logs': [
                    {'id': 5279, 'level': 'INFO', 'message': 'System started', 
                     'timestamp': datetime.datetime.now().isoformat()},
                    {'id': 5278, 'level': 'WARNING', 'message': 'Low disk space', 
                     'timestamp': (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat()}
                ]
            },
            'error': 'Using mock data: Database connection not available'
        }
    
    def _record_error(self, component: str, message: str) -> None:
        """
        Record an error to the recent errors list
        
        Args:
            component: Component where the error occurred
            message: Error message
        """
        error = {
            'timestamp': datetime.datetime.now().isoformat(),
            'component': component,
            'error': message
        }
        
        self.recent_errors.insert(0, error)
        
        # Limit the number of stored errors
        error_limit = self.config.get('metrics', {}).get('system', {}).get('error_history_limit', 20)
        if len(self.recent_errors) > error_limit:
            self.recent_errors = self.recent_errors[:error_limit]
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            return psutil.boot_time()
        except Exception:
            return 0