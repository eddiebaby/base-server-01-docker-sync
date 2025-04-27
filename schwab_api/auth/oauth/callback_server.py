"""
OAuth Callback Server for Schwab API

This module implements an HTTP server to handle OAuth callbacks.
"""

import os
import time
import logging
import threading
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Callable, Dict, Any, Tuple

from ..exceptions import CallbackError

# Configure logging
logger = logging.getLogger('schwab_api.oauth.callback')


class CallbackRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for OAuth callbacks.
    
    This handler processes OAuth callback requests and extracts the
    authorization code from the query parameters.
    """
    
    # Class variables to store callback data and function
    callback_data = None
    callback_function = None
    csrf_state = None
    
    def do_GET(self):
        """Process GET request with authorization code"""
        try:
            # Parse query parameters
            parsed_path = urlparse(self.path)
            params = parse_qs(parsed_path.query)
            
            # Check path to ensure it's a callback
            if not parsed_path.path.startswith('/callback'):
                self._send_error_response("Invalid callback path")
                return
                
            # Extract authorization code
            if 'code' in params:
                auth_code = params['code'][0]
                
                # Verify CSRF state if provided
                if CallbackRequestHandler.csrf_state:
                    if 'state' not in params or params['state'][0] != CallbackRequestHandler.csrf_state:
                        self._send_error_response("Invalid state parameter (CSRF protection)")
                        return
                        
                # Store the code for retrieval
                CallbackRequestHandler.callback_data = {'code': auth_code}
                
                # Send success response
                self._send_success_response()
                
                # Call the callback function if provided
                if CallbackRequestHandler.callback_function:
                    CallbackRequestHandler.callback_function(auth_code)
            elif 'error' in params:
                # OAuth error response
                error = params['error'][0]
                error_description = params.get('error_description', ['Unknown error'])[0]
                
                # Store the error for retrieval
                CallbackRequestHandler.callback_data = {
                    'error': error,
                    'error_description': error_description
                }
                
                # Send error response
                self._send_error_response(f"Authentication Error: {error} - {error_description}")
                
                # Call the callback function with None to indicate failure
                if CallbackRequestHandler.callback_function:
                    CallbackRequestHandler.callback_function(None)
            else:
                # No code or error
                self._send_error_response("No authorization code or error received")
                
                if CallbackRequestHandler.callback_function:
                    CallbackRequestHandler.callback_function(None)
                    
        except Exception as e:
            logger.error(f"Error in callback handler: {str(e)}")
            self._send_error_response(f"Server Error: {str(e)}")
            
            if CallbackRequestHandler.callback_function:
                CallbackRequestHandler.callback_function(None)
    
    def _send_success_response(self):
        """Send a success response to the browser"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_response = """
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #4CAF50; }
                p { color: #333; }
            </style>
        </head>
        <body>
            <h1>Authentication Successful!</h1>
            <p>You have successfully authenticated with Schwab API.</p>
            <p>You can now close this window and return to the application.</p>
            <script>
                // Close the window automatically after 5 seconds
                setTimeout(function() {
                    window.close();
                }, 5000);
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode())
    
    def _send_error_response(self, error_message):
        """Send an error response to the browser"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_response = f"""
        <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                h1 {{ color: #f44336; }}
                p {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Authentication Failed</h1>
            <p>{error_message}</p>
            <p>Please try again or contact support if the problem persists.</p>
        </body>
        </html>
        """
        
        self.wfile.write(html_response.encode())
    
    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        logger.debug(format % args)


class CallbackServer:
    """
    HTTP server to handle OAuth callbacks.
    
    This class sets up a local HTTP server to receive the OAuth callback,
    extract the authorization code, and provide it to the OAuth client.
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8000):
        """
        Initialize the callback server.
        
        Args:
            host (str): Host to bind the server to (default: 127.0.0.1)
            port (int): Port to bind the server to (default: 8000)
        """
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.csrf_state = None
    
    def start(self, callback_path: str = '/callback') -> Tuple[str, str]:
        """
        Start the callback server in a background thread.
        
        Args:
            callback_path (str): URL path for the callback
            
        Returns:
            Tuple[str, str]: (Callback URL, CSRF state token)
            
        Raises:
            CallbackError: If the server cannot be started
        """
        if self.server:
            logger.warning("Callback server already running")
            return f"http://{self.host}:{self.port}{callback_path}", self.csrf_state
            
        # Generate a random CSRF state token
        self.csrf_state = self._generate_state_token()
        
        # Clear any previous data
        CallbackRequestHandler.callback_data = None
        CallbackRequestHandler.csrf_state = self.csrf_state
        
        # Try to start the server
        try:
            # Try the specified port first
            try:
                self.server = HTTPServer((self.host, self.port), CallbackRequestHandler)
                actual_port = self.port
            except OSError:
                # If specified port is in use, try a random port
                logger.warning(f"Port {self.port} is in use, trying a random port")
                self.server = HTTPServer((self.host, 0), CallbackRequestHandler)
                actual_port = self.server.server_port
            
            # Start the server in a separate thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True
            )
            self.server_thread.start()
            
            callback_url = f"http://{self.host}:{actual_port}{callback_path}"
            logger.info(f"Callback server started at {callback_url}")
            
            return callback_url, self.csrf_state
            
        except Exception as e:
            logger.error(f"Failed to start callback server: {str(e)}")
            raise CallbackError(f"Failed to start callback server: {str(e)}")
    
    def stop(self) -> None:
        """
        Stop the callback server.
        
        This should be called after receiving the callback to free up the port.
        """
        if self.server:
            logger.info("Stopping callback server")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.server_thread = None
    
    def wait_for_callback(self, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """
        Wait for the authorization callback with timeout.
        
        Args:
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Callback data or None if timed out
        """
        if not self.server:
            raise CallbackError("Callback server not running")
            
        logger.info(f"Waiting for callback (timeout: {timeout}s)")
        
        # Wait for the callback
        start_time = time.time()
        while time.time() - start_time < timeout:
            if CallbackRequestHandler.callback_data:
                result = CallbackRequestHandler.callback_data.copy()
                return result
                
            time.sleep(0.5)
            
        logger.warning("Callback wait timed out")
        return None
    
    def register_callback(self, callback_function: Callable[[Optional[str]], None]) -> None:
        """
        Register a callback function to be called when the authorization code is received.
        
        Args:
            callback_function (Callable): Function to call with the auth code or None
        """
        CallbackRequestHandler.callback_function = callback_function
    
    def _generate_state_token(self, length: int = 32) -> str:
        """
        Generate a random state token for CSRF protection.
        
        Args:
            length (int): Length of the token
            
        Returns:
            str: Random token
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))