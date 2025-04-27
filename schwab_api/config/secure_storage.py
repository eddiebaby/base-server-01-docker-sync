"""
Secure Storage for Schwab API

This module provides secure storage for sensitive information like API keys
and OAuth tokens. It uses platform-specific encryption when available.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schwab_api.secure_storage')

# Import Windows-specific encryption if available
try:
    if platform.system() == 'Windows':
        from win32crypt import CryptProtectData, CryptUnprotectData
        WINDOWS_CRYPTO_AVAILABLE = True
    else:
        WINDOWS_CRYPTO_AVAILABLE = False
except ImportError:
    WINDOWS_CRYPTO_AVAILABLE = False
    logger.warning("Windows crypto module not available, falling back to basic encryption")

# For non-Windows platforms
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureStorage:
    """
    Secure storage for sensitive information.
    
    This class provides methods to securely store and retrieve sensitive
    information like API keys and OAuth tokens using platform-specific
    encryption where available.
    """
    
    def __init__(self, base_dir: str):
        """
        Initialize the secure storage.
        
        Args:
            base_dir (str): Base directory for storing encrypted files
        """
        self.base_dir = base_dir
        self._ensure_dir_exists()
        
        # Set up fallback encryption key for non-Windows systems
        self._setup_encryption_key()
        
    def _ensure_dir_exists(self) -> None:
        """Ensure the storage directory exists"""
        os.makedirs(self.base_dir, exist_ok=True)
        
    def _setup_encryption_key(self) -> None:
        """Set up encryption key for non-Windows systems"""
        if not WINDOWS_CRYPTO_AVAILABLE:
            # Create a deterministic key based on system information
            # This isn't as secure as Windows DPAPI but is better than plaintext
            system_info = (
                platform.node() +
                platform.machine() +
                str(os.getuid() if hasattr(os, 'getuid') else 0)
            ).encode()
            
            salt = b'SchwabAPISecureStorage'  # Not a secret, but makes key generation more robust
            
            # Generate a key from system information
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(system_info))
            self._crypto_key = key
        
    def _get_storage_path(self, name: str) -> str:
        """
        Get the path for a storage file.
        
        Args:
            name (str): Name of the stored data
            
        Returns:
            str: Full path to the storage file
        """
        # Ensure name is safe for use in a filename
        safe_name = ''.join(c for c in name if c.isalnum() or c in '._-')
        return os.path.join(self.base_dir, f"{safe_name}.bin")
    
    def store(self, name: str, data: Dict[str, Any]) -> bool:
        """
        Encrypt and store data.
        
        Args:
            name (str): Name to identify the stored data
            data (Dict[str, Any]): Data to store
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data).encode()
            
            # Encrypt data
            encrypted_data = self._encrypt(json_data)
            
            # Save to file
            storage_path = self._get_storage_path(name)
            with open(storage_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Set restrictive permissions
            if platform.system() != 'Windows':
                os.chmod(storage_path, 0o600)  # Owner read/write only
            else:
                # On Windows, use icacls to set permissions
                os.system(f'icacls "{storage_path}" /inheritance:r /grant:r "%USERNAME%:(R,W)"')
                
            logger.debug(f"Data stored securely as {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")
            return False
    
    def retrieve(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt data.
        
        Args:
            name (str): Name of the stored data
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved data or None if not found/error
        """
        storage_path = self._get_storage_path(name)
        
        if not os.path.exists(storage_path):
            logger.debug(f"No stored data found for {name}")
            return None
            
        try:
            with open(storage_path, 'rb') as f:
                encrypted_data = f.read()
                
            # Decrypt data
            json_data = self._decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(json_data.decode())
            
            logger.debug(f"Data retrieved for {name}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving data: {str(e)}")
            return None
    
    def _encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data using platform-specific methods.
        
        Args:
            data (bytes): Data to encrypt
            
        Returns:
            bytes: Encrypted data
        """
        if WINDOWS_CRYPTO_AVAILABLE:
            # Use Windows Data Protection API
            encrypted = CryptProtectData(
                data,
                None,  # description
                None,  # entropy
                None,  # reserved
                None,  # prompt_struct
                0      # flags
            )
            return encrypted
        else:
            # Use Fernet encryption with system-derived key
            fernet = Fernet(self._crypto_key)
            return fernet.encrypt(data)
    
    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data using platform-specific methods.
        
        Args:
            encrypted_data (bytes): Encrypted data
            
        Returns:
            bytes: Decrypted data
        """
        if WINDOWS_CRYPTO_AVAILABLE:
            # Use Windows Data Protection API
            return CryptUnprotectData(encrypted_data)[1]
        else:
            # Use Fernet encryption with system-derived key
            fernet = Fernet(self._crypto_key)
            return fernet.decrypt(encrypted_data)
            
    def delete(self, name: str) -> bool:
        """
        Delete stored data.
        
        Args:
            name (str): Name of the stored data
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        storage_path = self._get_storage_path(name)
        
        if not os.path.exists(storage_path):
            return True
            
        try:
            os.remove(storage_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting data: {str(e)}")
            return False