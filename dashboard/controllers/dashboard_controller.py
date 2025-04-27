#!/usr/bin/env python3
"""
Dashboard Controller Module
:TechnologyVersion: Python 3.10+, Flask 2.0+
:ComponentRole: Controller in MVC pattern
:Context: Web dashboard for system monitoring

This module implements controllers for the dashboard views and API endpoints.
It follows the MVC pattern by handling HTTP requests, interacting with models,
and returning appropriate responses.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Tuple, List
from flask import (
    Blueprint, render_template, jsonify, request,
    Response, redirect, url_for, session, abort,
    current_app
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Blueprint for dashboard routes
dashboard_bp = Blueprint("dashboard", __name__)

# System monitor instance will be set from the main app
system_monitor = None

def init_controller(monitor_instance):
    """
    Initialize the controller with required dependencies
    
    Args:
        monitor_instance: SystemMonitor instance
    """
    global system_monitor
    system_monitor = monitor_instance
    logger.info("Dashboard controller initialized with system monitor")

@dashboard_bp.route('/')
def dashboard_view():
    """
    Render main dashboard page
    
    Returns:
        Rendered dashboard template
    """
    refresh_interval = current_app.config.get('REFRESH_INTERVAL', 60)
    return render_template('dashboard.html', refresh_interval=refresh_interval)

def _sanitize_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize and validate metrics data
    
    Args:
        data: Raw metrics data from system monitor
        
    Returns:
        Sanitized metrics data
    """
    # Create a deep copy to avoid modifying the original
    sanitized = {}
    
    # Validate and sanitize timestamp
    if 'timestamp' in data and isinstance(data['timestamp'], str):
        try:
            # Ensure timestamp is valid ISO format
            datetime.fromisoformat(data['timestamp'])
            sanitized['timestamp'] = data['timestamp']
        except ValueError:
            # Use current time if timestamp is invalid
            sanitized['timestamp'] = datetime.now().isoformat()
    else:
        sanitized['timestamp'] = datetime.now().isoformat()
    
    # Validate system status
    valid_statuses = ['healthy', 'warning', 'critical']
    if 'system_status' in data and data['system_status'] in valid_statuses:
        sanitized['system_status'] = data['system_status']
    else:
        sanitized['system_status'] = 'unknown'
    
    # Pass through other data with basic validation
    for key in ['system', 'database', 'pipeline']:
        if key in data and isinstance(data[key], dict):
            sanitized[key] = data[key]
    
    return sanitized

def aggregate_monitoring_data() -> Dict[str, Any]:
    """
    Aggregate all monitoring data from the system monitor
    
    Returns:
        Dict containing aggregated monitoring data
    """
    try:
        if system_monitor is None:
            logger.error("System monitor not initialized")
            return {
                'error': 'System monitor not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        # Collect all metrics from system monitor
        raw_metrics = system_monitor.collect_all_metrics()
        
        # Sanitize and validate the metrics
        metrics = _sanitize_metrics(raw_metrics)
        
        # Add summary information
        metrics['summary'] = {
            'status': metrics.get('system_status', 'unknown'),
            'db_connection': (
                metrics.get('database', {}).get('connection_status', 'disconnected')
            ),
            'last_updated': metrics.get('timestamp'),
            'alert_count': len(metrics.get('system', {}).get('recent_errors', []))
        }
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error aggregating monitoring data: {str(e)}")
        return {
            'error': f"Failed to aggregate monitoring data: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

# API Routes
@dashboard_bp.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    API endpoint to get all system metrics
    
    Returns:
        JSON response with all metrics
    """
    try:
        metrics = aggregate_monitoring_data()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@dashboard_bp.route('/api/database-stats', methods=['GET'])
def get_database_stats():
    """
    API endpoint to get database statistics
    
    Returns:
        JSON response with database statistics
    """
    try:
        if system_monitor is None:
            return jsonify({
                'error': 'System monitor not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        stats = system_monitor.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@dashboard_bp.route('/api/pipeline-metrics', methods=['GET'])
def get_pipeline_metrics():
    """
    API endpoint to get pipeline metrics
    
    Returns:
        JSON response with pipeline metrics
    """
    try:
        if system_monitor is None:
            return jsonify({
                'error': 'System monitor not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        metrics = system_monitor.get_pipeline_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@dashboard_bp.route('/api/system-health', methods=['GET'])
def get_system_health():
    """
    API endpoint to get system health information
    
    Returns:
        JSON response with system health data
    """
    try:
        if system_monitor is None:
            return jsonify({
                'error': 'System monitor not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
            
        health = system_monitor.get_system_health()
        return jsonify(health)
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500