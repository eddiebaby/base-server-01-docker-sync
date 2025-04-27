"""
Dashboard Controller Test Module
:TechnologyVersion: Python 3.10+, pytest, Flask 2.0+
:ComponentRole: Test suite for dashboard controller
:Context: Testing dashboard API endpoints and views
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask import url_for
from flask_login import current_user, login_user

from dashboard.controllers.dashboard_controller import init_controller, dashboard_bp

# RECURSIVE TESTING STRATEGY
# Test recursive error handling and template rendering patterns

def test_recursive_template_inheritance(client, app, system_monitor):
    """Test recursive template inheritance and rendering
    Tests base case (simple template) and recursive case (nested templates)
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Base case - simple template
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login.html' in response.data
        
        # Recursive case - dashboard with nested templates
        # Mock login
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        # Verify all nested templates are rendered
        assert b'base.html' in response.data
        assert b'header.html' in response.data
        assert b'sidebar.html' in response.data
        assert b'footer.html' in response.data

def test_recursive_api_error_handling(client, app, system_monitor):
    """Test recursive API error handling
    Tests base case (success) and recursive error propagation
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Mock login
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        # Base case - successful API call
        system_monitor.get_database_stats = MagicMock(return_value={'status': 'ok'})
        response = client.get('/api/database-stats')
        assert response.status_code == 200
        
        # Recursive case - nested errors
        def raise_nested():
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        
        system_monitor.get_database_stats = MagicMock(side_effect=raise_nested)
        response = client.get('/api/database-stats')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Outer error' in data['error']

# CUMULATIVE TESTING STRATEGY
# Build comprehensive test suite for all endpoints

def test_dashboard_view_authentication(client, app):
    """Test dashboard view authentication"""
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Unauthenticated access
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        
        # Authenticated access
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        response = client.get('/')
        assert response.status_code == 200
        assert b'dashboard.html' in response.data

def test_login_functionality(client, app):
    """Test login endpoint"""
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Test GET request
        response = client.get('/login')
        assert response.status_code == 200
        
        # Test POST with invalid credentials
        response = client.post('/login', data={
            'username': 'invalid',
            'password': 'wrong'
        })
        assert response.status_code == 200
        assert b'Invalid username' in response.data
        
        # Test POST with valid credentials
        response = client.post('/login', data={
            'username': 'test_user',
            'password': 'test_password'
        })
        assert response.status_code == 302  # Redirect to dashboard
        
        # Verify session
        with client.session_transaction() as session:
            assert session.get('user_id') == 'test_user'

def test_logout_functionality(client, app):
    """Test logout endpoint"""
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Setup authenticated session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        response = client.get('/logout')
        assert response.status_code == 302  # Redirect to login
        
        # Verify session cleared
        with client.session_transaction() as session:
            assert 'user_id' not in session

def test_metrics_api(client, app, system_monitor):
    """Test metrics API endpoint"""
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Setup authenticated session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        # Test successful response
        mock_metrics = {
            'system_status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
        system_monitor.collect_all_metrics = MagicMock(return_value=mock_metrics)
        
        response = client.get('/api/metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['system_status'] == 'healthy'

def test_database_stats_api(client, app, system_monitor):
    """Test database statistics API endpoint"""
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Setup authenticated session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        # Test successful response
        mock_stats = {
            'connection_status': 'connected',
            'table_counts': {'users': 100}
        }
        system_monitor.get_database_stats = MagicMock(return_value=mock_stats)
        
        response = client.get('/api/database-stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['connection_status'] == 'connected'

# Security Tests

def test_csrf_protection(client, app):
    """Test CSRF protection
    :Problem: :CrossSiteRequestForgeryVulnerability
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Attempt login without CSRF token
        response = client.post('/login', data={
            'username': 'test_user',
            'password': 'test_password'
        })
        assert response.status_code == 400  # Bad Request

def test_session_security(client, app):
    """Test session security settings
    :Problem: :SecurityVulnerability in session management
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        response = client.get('/')
        
        # Verify secure session settings
        assert app.config['SESSION_COOKIE_SECURE'] is True
        assert app.config['SESSION_COOKIE_HTTPONLY'] is True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'

def test_xss_prevention(client, app, system_monitor):
    """Test XSS prevention in template rendering
    :Problem: :CrossSiteScriptingVulnerability
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Setup authenticated session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        # Inject malicious script in metrics
        mock_metrics = {
            'system_status': '<script>alert("xss")</script>',
            'timestamp': datetime.now().isoformat()
        }
        system_monitor.collect_all_metrics = MagicMock(return_value=mock_metrics)
        
        response = client.get('/')
        assert response.status_code == 200
        # Verify script tags are escaped
        assert b'<script>alert' not in response.data
        assert b'&lt;script&gt;' in response.data

def test_api_error_sanitization(client, app, system_monitor):
    """Test API error message sanitization
    :Problem: :DataLeakage in error responses
    """
    # Register routes
    app.register_blueprint(dashboard_bp)
    
    with app.test_request_context():
        # Setup authenticated session
        with client.session_transaction() as session:
            session['user_id'] = 'test_user'
            session['_fresh'] = True
        
        # Simulate error with sensitive information
        system_monitor.get_database_stats = MagicMock(
            side_effect=Exception("Error connecting to db at root:password@localhost")
        )
        
        response = client.get('/api/database-stats')
        assert response.status_code == 500
        data = json.loads(response.data)
        # Verify sensitive info is not leaked
        assert 'root:password' not in data['error']
        assert 'localhost' not in data['error']