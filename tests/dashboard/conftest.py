"""
Dashboard Test Configuration and Fixtures
:TechnologyVersion: Python 3.10+, pytest
:ComponentRole: Test configuration and fixtures
:Context: Shared test resources for dashboard tests
"""

import os
import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, create_autospec

from flask import Flask
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.sql.schema import MetaData, Table

# Import project modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.models.system_monitor import SystemMonitor
from dashboard.controllers.dashboard_controller import dashboard_bp, init_controller
from config.config_manager import config_manager
from db.connection_manager import ConnectionManager

class TestUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test_secret_key',
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'USERS': {
            'test_user': generate_password_hash('test_password')
        }
    })
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        if user_id in app.config['USERS']:
            return TestUser(user_id)
        return None
    
    # Unregister any existing blueprints
    if 'dashboard' in app.blueprints:
        del app.blueprints['dashboard']
    
    # Register blueprint with unique name
    app.register_blueprint(dashboard_bp, name='dashboard_test')
    
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def mock_db_connection():
    """Mock database connection manager"""
    mock_conn = MagicMock()
    mock_engine = create_autospec(Engine)
    mock_conn.get_engine = MagicMock(return_value=mock_engine)
    return mock_conn

@pytest.fixture
def mock_config():
    """Mock configuration manager"""
    mock_conf = MagicMock()
    mock_conf.get_config_value = MagicMock(return_value='test_config.json')
    mock_conf.load_json_config = MagicMock(return_value={
        'metrics': {
            'database': {
                'enabled': True,
                'table_count_limit': 10,
                'recent_data_limit': 5
            },
            'system': {
                'enabled': True,
                'error_history_limit': 20
            }
        }
    })
    return mock_conf

@pytest.fixture
def mock_db_stats():
    """Mock database statistics"""
    return {
        'connection_status': 'connected',
        'table_counts': {
            'users': 100,
            'logs': 500
        },
        'recent_data': {
            'users': [
                {'id': 1, 'username': 'test_user'},
                {'id': 2, 'username': 'test_user2'}
            ],
            'logs': [
                {'id': 1, 'message': 'test log', 'timestamp': datetime.now().isoformat()},
                {'id': 2, 'message': 'test log 2', 'timestamp': datetime.now().isoformat()}
            ]
        }
    }

@pytest.fixture
def mock_scalar_result():
    """Mock SQLAlchemy scalar result"""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 100
    return mock_result

@pytest.fixture
def mock_row_result():
    """Mock SQLAlchemy row result"""
    class MockRow(dict):
        def __iter__(self):
            return iter(self.items())
    
    return [
        MockRow({'id': 1, 'username': 'test_user'}),
        MockRow({'id': 2, 'username': 'test_user2'})
    ]

@pytest.fixture
def auth_headers():
    """Authentication headers for protected endpoints"""
    return {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def system_monitor(mock_db_connection, mock_config):
    """
    Create a system monitor instance for testing
    This fixture is used by 18 tests across the dashboard test suite
    
    :Pattern: :DependencyInjectionPattern for testing
    :Context: Provides mocked SystemMonitor with test configuration
    """
    monitor = SystemMonitor(mock_db_connection, mock_config)
    
    # Add collect_all_metrics method that's used in controller but not fully implemented
    monitor.collect_all_metrics = MagicMock(return_value={
        'system_status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': {'connection_status': 'connected'},
        'system': {'recent_errors': []}
    })
    
    # Add get_pipeline_metrics method
    monitor.get_pipeline_metrics = MagicMock(return_value={
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'jobs': {'completed': 10, 'running': 2, 'failed': 0}
    })
    
    # Add get_system_health method
    monitor.get_system_health = MagicMock(return_value={
        'status': 'healthy',
        'cpu': 25.0,
        'memory': 40.0,
        'disk': 30.0
    })
    
    # Initialize the controller with this monitor
    init_controller(monitor)
    
    return monitor