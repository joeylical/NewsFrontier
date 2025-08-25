"""
Encryption/Decryption utilities for NewsFrontier - Secure API key storage.

This module provides encryption and decryption functionality for securely
storing API keys and other sensitive configuration data in the database.
"""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class KeyManager:
    """Manages encryption/decryption of API keys and sensitive data."""
    
    def __init__(self):
        """Initialize the KeyManager with master key from environment."""
        self._fernet = None
        self._setup_encryption()
    
    def _setup_encryption(self):
        """Setup encryption using master key from environment."""
        try:
            # Get master key from environment
            master_key = os.getenv("CRYPTO_MASTER_KEY")
            if not master_key:
                logger.error("CRYPTO_MASTER_KEY not found in environment variables")
                return
            
            # Use a fixed salt for consistency (in production, consider storing salt separately)
            salt = b"newsfrontier_salt_2035"  # 22 bytes salt
            
            # Derive key from master key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            
            # Create Fernet instance
            self._fernet = Fernet(key)
            logger.info("Encryption system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            self._fernet = None
    
    def is_available(self) -> bool:
        """Check if encryption is available."""
        return self._fernet is not None
    
    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64 encoded encrypted string, or None if encryption failed
        """
        if not self.is_available():
            logger.error("Encryption not available - check CRYPTO_MASTER_KEY")
            return None
        
        if not plaintext:
            return None
        
        try:
            # Encrypt the plaintext
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            # Return base64 encoded string for database storage
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Decrypted plaintext string, or None if decryption failed
        """
        if not self.is_available():
            logger.error("Decryption not available - check CRYPTO_MASTER_KEY")
            return None
        
        if not encrypted_text:
            return None
        
        try:
            # Decode base64 string
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
            # Decrypt the bytes
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            # Return plaintext string
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> Optional[str]:
        """
        Encrypt a dictionary by converting to JSON string first.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64 encoded encrypted JSON string, or None if failed
        """
        if not data:
            return None
        
        try:
            import json
            json_string = json.dumps(data, separators=(',', ':'))
            return self.encrypt(json_string)
        except Exception as e:
            logger.error(f"Dictionary encryption failed: {e}")
            return None
    
    def decrypt_dict(self, encrypted_text: str) -> Optional[dict]:
        """
        Decrypt an encrypted JSON string back to dictionary.
        
        Args:
            encrypted_text: Base64 encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary, or None if failed
        """
        if not encrypted_text:
            return None
        
        try:
            import json
            json_string = self.decrypt(encrypted_text)
            if json_string:
                return json.loads(json_string)
            return None
        except Exception as e:
            logger.error(f"Dictionary decryption failed: {e}")
            return None


# Global instance for easy access
key_manager = KeyManager()


def get_key_manager() -> KeyManager:
    """Get the global KeyManager instance."""
    return key_manager


def encrypt_api_key(api_key: str) -> Optional[str]:
    """
    Encrypt an API key for secure storage.
    
    Args:
        api_key: The API key to encrypt
        
    Returns:
        Encrypted API key string, or None if failed
    """
    return key_manager.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> Optional[str]:
    """
    Decrypt an encrypted API key.
    
    Args:
        encrypted_key: The encrypted API key string
        
    Returns:
        Decrypted API key, or None if failed
    """
    return key_manager.decrypt(encrypted_key)


def generate_master_key() -> str:
    """
    Generate a new master key for encryption.
    This should only be used during initial setup.
    
    Returns:
        A random 32-character string suitable for use as CRYPTO_MASTER_KEY
    """
    import secrets
    import string
    
    # Generate a random 32-character string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def test_encryption() -> bool:
    """
    Test encryption/decryption functionality.
    
    Returns:
        True if encryption/decryption works correctly, False otherwise
    """
    if not key_manager.is_available():
        logger.error("Encryption test failed: KeyManager not available")
        return False
    
    # Test string encryption
    test_string = "test-api-key-12345"
    encrypted = key_manager.encrypt(test_string)
    if not encrypted:
        logger.error("Encryption test failed: Could not encrypt test string")
        return False
    
    decrypted = key_manager.decrypt(encrypted)
    if decrypted != test_string:
        logger.error(f"Encryption test failed: Decrypted text doesn't match. Expected: {test_string}, Got: {decrypted}")
        return False
    
    # Test dictionary encryption
    test_dict = {"api_key": "test-key-123", "endpoint": "https://api.example.com"}
    encrypted_dict = key_manager.encrypt_dict(test_dict)
    if not encrypted_dict:
        logger.error("Encryption test failed: Could not encrypt test dictionary")
        return False
    
    decrypted_dict = key_manager.decrypt_dict(encrypted_dict)
    if decrypted_dict != test_dict:
        logger.error(f"Encryption test failed: Decrypted dict doesn't match. Expected: {test_dict}, Got: {decrypted_dict}")
        return False
    
    logger.info("Encryption test passed successfully")
    return True
