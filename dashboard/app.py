#!/usr/bin/env python3
"""
Dashboard Application Module
:TechnologyVersion: Python 3.10+, Flask 2.0+
:ComponentRole: Main application entry point in MVC pattern
:Context: Web dashboard for system monitoring

This module implements a Flask web application that integrates all components
of the MVC pattern for the system monitoring dashboard.
"""

import os
import json
import logging
import secrets
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Union

from flask import (
    Flask, render_template, jsonify, request, 
    Response, redirect, url_for, session, 
    send_from_directory, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, 
    login_required, current_user, UserMixin
)
from werkzeug.security import check_password_hash, generate_password_hash

# Import from project
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config.config_manager import config_manager
from db.connection_manager import ConnectionManager

# Import local modules
from models.system_monitor import SystemMonitor
from controllers.dashboard_controller import dashboard_bp, init_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Load configuration
app_config = config_manager.get_config_value('DASHBOARD_CONFIG', default='dashboard_config.json')
try:
    app.config.update(config_manager.load_json_config(app_config))
except Exception as e:
    logger.error(f"Error loading dashboard configuration: {str(e)}")
    app.config.update({
        'SECRET_KEY': secrets.token_hex(24),
        'REFRESH_INTERVAL': 60,  # seconds
        'DEBUG': False,
        'SESSION_COOKIE_SECURE': True,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'USERS': {}
    })

# Ensure required security settings
if 'SECRET_KEY' not in app.config:
    app.config['SECRET_KEY'] = secrets.token_hex(24)
if 'SESSION_COOKIE_SECURE' not in app.config:
    app.config['SESSION_COOKIE_SECURE'] = True
if 'SESSION_COOKIE_HTTPONLY' not in app.config:
    app.config['SESSION_COOKIE_HTTPONLY'] = True
if 'SESSION_COOKIE_SAMESITE' not in app.config:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.username = user_id

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    if user_id in app.config.get('USERS', {}):
        return User(user_id)
    return None

# Initialize DatabaseConnectionManager
try:
    db_config = config_manager.get_db_config()
    connection_manager = ConnectionManager(db_config)
    logger.info("Database connection manager initialized")
except Exception as e:
    logger.warning(f"Failed to initialize database connection manager: {str(e)}")
    connection_manager = None

# Create SystemMonitor instance
system_monitor = SystemMonitor(connection_manager, config_manager)

# Initialize controller with system monitor
init_controller(system_monitor)

# Register blueprint
app.register_blueprint(dashboard_bp)

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access"""
    return render_template('error.html',
                          error_type='Authentication Error',
                          error_message='You are not authorized to access this resource.',
                          suggestion='Please log in with appropriate credentials.'), 401

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html',
                          error_type='Page Not Found',
                          error_message='The requested resource was not found.',
                          suggestion='Please check the URL or go back to the dashboard.'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle server errors"""
    logger.error(f"Server error: {str(error)}")
    return render_template('error.html',
                          error_type='Server Error',
                          error_message='An unexpected error occurred.',
                          suggestion='Please try again later or contact the administrator.'), 500

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_view'))
        
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            error = 'Username and password are required'
        else:
            # Validate credentials using the configuration
            users = app.config.get('USERS', {})
            
            if username not in users:
                error = 'Invalid username'
            elif not check_password_hash(users.get(username, ''), password):
                error = 'Invalid password'
            else:
                user = User(username)
                login_user(user, remember=True)
                
                next_page = request.args.get('next')
                if not next_page or next_page.startswith('//'):
                    next_page = url_for('dashboard.dashboard_view')
                    
                return redirect(next_page)
    
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    """Log out user"""
    logout_user()
    return redirect(url_for('login'))

# Routes - Static files
@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# Command-line execution
if __name__ == '__main__':
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    # Add development user if in debug mode and no users defined
    if debug and not app.config.get('USERS'):
        logger.warning("Debug mode enabled with no users defined, adding default admin user")
        app.config['USERS'] = {
            'admin': generate_password_hash('change_me_immediately')
        }
    
    logger.info(f"Starting dashboard application on {host}:{port}")
    app.run(host=host, port=port, debug=debug)