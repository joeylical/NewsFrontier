"""
Configuration Service for NewsFrontier - Database-driven configuration with encryption.

This module provides a centralized configuration service that reads settings from
the database and handles encrypted storage of sensitive data like API keys.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from .database import get_db
from .models import SystemSetting
from .crypto import get_key_manager

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing application configuration from database."""
    
    def __init__(self):
        """Initialize configuration service."""
        self.key_manager = get_key_manager()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
        self._last_cache_refresh = 0
        
    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed."""
        import time
        return time.time() - self._last_cache_refresh > self._cache_ttl
    
    def _refresh_cache(self):
        """Refresh configuration cache from database."""
        try:
            import time
            with get_db() as db:
                settings = db.query(SystemSetting).all()
                new_cache = {}
                
                for setting in settings:
                    key = setting.setting_key
                    value = setting.setting_value
                    setting_type = setting.setting_type
                    
                    # Parse value based on type
                    if value is None:
                        parsed_value = None
                    elif setting_type == 'boolean':
                        parsed_value = value.lower() in ('true', '1', 'yes', 'on')
                    elif setting_type == 'integer':
                        try:
                            parsed_value = int(value)
                        except ValueError:
                            logger.warning(f"Invalid integer value for {key}: {value}")
                            parsed_value = None
                    elif setting_type == 'float':
                        try:
                            parsed_value = float(value)
                        except ValueError:
                            logger.warning(f"Invalid float value for {key}: {value}")
                            parsed_value = None
                    elif setting_type == 'json':
                        try:
                            parsed_value = json.loads(value)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON value for {key}: {value}")
                            parsed_value = None
                    else:  # string
                        parsed_value = value
                    
                    new_cache[key] = parsed_value
                
                self._cache = new_cache
                self._last_cache_refresh = time.time()
                logger.debug(f"Configuration cache refreshed with {len(self._cache)} settings")
                
        except Exception as e:
            logger.error(f"Failed to refresh configuration cache: {e}")
    
    def get(self, key: str, default: Any = None, fallback_env: bool = True) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if not found
            fallback_env: Whether to fallback to environment variable if not in database
            
        Returns:
            Configuration value
        """
        # Refresh cache if needed
        if self._should_refresh_cache():
            self._refresh_cache()
        
        # Check cache first
        if key in self._cache:
            return self._cache[key]
        
        # Fallback to environment variable if enabled
        if fallback_env:
            env_value = os.getenv(key)
            if env_value is not None:
                return env_value
        
        return default
    
    def get_encrypted(self, key: str, default: Any = None, fallback_env: bool = True) -> Optional[str]:
        """
        Get and decrypt an encrypted configuration value.
        
        Args:
            key: Configuration key for encrypted value
            default: Default value if not found
            fallback_env: Whether to fallback to environment variable if not in database
            
        Returns:
            Decrypted value or default
        """
        encrypted_value = self.get(key, default=None, fallback_env=False)
        
        if encrypted_value:
            # Try to decrypt
            decrypted = self.key_manager.decrypt(encrypted_value)
            if decrypted is not None:
                return decrypted
            else:
                logger.warning(f"Failed to decrypt value for key: {key}")
        
        # Fallback to environment variable if enabled
        if fallback_env:
            env_value = os.getenv(key)
            if env_value is not None:
                return env_value
        
        return default
    
    def set(self, key: str, value: Any, setting_type: str = 'string', 
            description: str = None, is_public: bool = False, encrypt: bool = False) -> bool:
        """
        Set configuration value in database.
        
        Args:
            key: Configuration key
            value: Configuration value
            setting_type: Type of setting ('string', 'integer', 'boolean', 'json', 'float')
            description: Optional description
            is_public: Whether setting is public (visible to non-admin users)
            encrypt: Whether to encrypt the value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db() as db:
                # Prepare value for storage
                if value is None:
                    str_value = None
                elif setting_type == 'json':
                    str_value = json.dumps(value, separators=(',', ':'))
                else:
                    str_value = str(value)
                
                # Encrypt if requested and key manager is available
                if encrypt and str_value and self.key_manager.is_available():
                    str_value = self.key_manager.encrypt(str_value)
                    if str_value is None:
                        logger.error(f"Failed to encrypt value for key: {key}")
                        return False
                
                # Check if setting exists
                setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
                
                if setting:
                    # Update existing setting
                    setting.setting_value = str_value
                    setting.setting_type = setting_type
                    if description is not None:
                        setting.description = description
                    setting.is_public = is_public
                else:
                    # Create new setting
                    setting = SystemSetting(
                        setting_key=key,
                        setting_value=str_value,
                        setting_type=setting_type,
                        description=description,
                        is_public=is_public
                    )
                    db.add(setting)
                
                db.commit()
                
                # Update cache
                if key in self._cache or str_value is not None:
                    if setting_type == 'boolean' and str_value:
                        self._cache[key] = str_value.lower() in ('true', '1', 'yes', 'on')
                    elif setting_type == 'integer' and str_value:
                        try:
                            self._cache[key] = int(str_value)
                        except ValueError:
                            self._cache[key] = None
                    elif setting_type == 'float' and str_value:
                        try:
                            self._cache[key] = float(str_value)
                        except ValueError:
                            self._cache[key] = None
                    elif setting_type == 'json' and str_value:
                        try:
                            self._cache[key] = json.loads(str_value)
                        except json.JSONDecodeError:
                            self._cache[key] = None
                    else:
                        self._cache[key] = str_value
                
                logger.info(f"Configuration set: {key} = {'<encrypted>' if encrypt else str_value}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False
    
    def set_encrypted(self, key: str, value: str, description: str = None, is_public: bool = False) -> bool:
        """
        Set an encrypted configuration value.
        
        Args:
            key: Configuration key
            value: Plain text value to encrypt and store
            description: Optional description
            is_public: Whether setting is public
            
        Returns:
            True if successful, False otherwise
        """
        return self.set(key, value, setting_type='string', description=description, 
                       is_public=is_public, encrypt=True)
    
    def delete(self, key: str) -> bool:
        """
        Delete configuration key from database.
        
        Args:
            key: Configuration key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db() as db:
                setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()
                if setting:
                    db.delete(setting)
                    db.commit()
                    
                    # Remove from cache
                    if key in self._cache:
                        del self._cache[key]
                    
                    logger.info(f"Configuration deleted: {key}")
                    return True
                else:
                    logger.warning(f"Configuration key not found: {key}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete configuration {key}: {e}")
            return False
    
    def get_all(self, include_encrypted: bool = False, public_only: bool = False) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Args:
            include_encrypted: Whether to include encrypted values (will be returned encrypted)
            public_only: Whether to return only public settings
            
        Returns:
            Dictionary of all configuration values
        """
        try:
            with get_db() as db:
                query = db.query(SystemSetting)
                if public_only:
                    query = query.filter(SystemSetting.is_public == True)
                
                settings = query.all()
                result = {}
                
                for setting in settings:
                    key = setting.setting_key
                    value = setting.setting_value
                    setting_type = setting.setting_type
                    
                    # Skip encrypted values if not requested
                    if not include_encrypted and key.endswith('_encrypted'):
                        continue
                    
                    # Parse value based on type
                    if value is None:
                        parsed_value = None
                    elif setting_type == 'boolean':
                        parsed_value = value.lower() in ('true', '1', 'yes', 'on')
                    elif setting_type == 'integer':
                        try:
                            parsed_value = int(value)
                        except ValueError:
                            parsed_value = None
                    elif setting_type == 'float':
                        try:
                            parsed_value = float(value)
                        except ValueError:
                            parsed_value = None
                    elif setting_type == 'json':
                        try:
                            parsed_value = json.loads(value)
                        except json.JSONDecodeError:
                            parsed_value = None
                    else:  # string
                        parsed_value = value
                    
                    result[key] = parsed_value
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get all configurations: {e}")
            return {}


# Global instance for easy access
config_service = ConfigurationService()


def get_config() -> ConfigurationService:
    """Get the global configuration service instance."""
    return config_service


def get_setting(key: str, default: Any = None, fallback_env: bool = True) -> Any:
    """Get configuration setting (convenience function)."""
    return config_service.get(key, default=default, fallback_env=fallback_env)


def get_encrypted_setting(key: str, default: Any = None, fallback_env: bool = True) -> Optional[str]:
    """Get encrypted configuration setting (convenience function)."""
    return config_service.get_encrypted(key, default=default, fallback_env=fallback_env)


def set_setting(key: str, value: Any, setting_type: str = 'string', 
                description: str = None, is_public: bool = False, encrypt: bool = False) -> bool:
    """Set configuration setting (convenience function)."""
    return config_service.set(key, value, setting_type=setting_type, 
                             description=description, is_public=is_public, encrypt=encrypt)


def set_encrypted_setting(key: str, value: str, description: str = None, is_public: bool = False) -> bool:
    """Set encrypted configuration setting (convenience function)."""
    return config_service.set_encrypted(key, value, description=description, is_public=is_public)


# Configuration keys constants for common settings
class ConfigKeys:
    """Common configuration key constants."""
    
    # LLM Configuration
    LLM_SUMMARY_MODEL = 'llm_summary_model'
    LLM_ANALYSIS_MODEL = 'llm_analysis_model' 
    LLM_EMBEDDING_MODEL = 'llm_embedding_model'
    LLM_IMAGE_MODEL = 'llm_image_model'
    
    # Encrypted API Keys
    GOOGLE_API_KEY = 'google_api_key_encrypted'
    OPENAI_API_KEY = 'openai_api_key_encrypted'
    
    # LLM API Endpoints
    LLM_API_URL = 'llm_api_url'
    EMBEDDING_API_URL = 'embedding_api_url'
    
    # S3 Configuration (encrypted)
    S3_REGION = 's3_region'
    S3_ENDPOINT = 's3_endpoint_encrypted'
    S3_BUCKET = 's3_bucket'
    S3_ACCESS_KEY_ID = 's3_access_key_id_encrypted'
    S3_SECRET_KEY = 's3_secret_key_encrypted'
    
    # Feature toggles
    DAILY_SUMMARY_ENABLED = 'daily_summary_enabled'
    DAILY_SUMMARY_COVER_ENABLED = 'daily_summary_cover_enabled'
    
    # Processing intervals (minutes)
    SCRAPER_INTERVAL = 'scraper_interval_minutes'
    POSTPROCESS_INTERVAL = 'postprocess_interval_minutes'
    
    # Processing configuration
    CLUSTER_THRESHOLD = 'cluster_threshold'
    MAX_PROCESSING_ATTEMPTS = 'max_processing_attempts'
    EMBEDDING_DIMENSION = 'embedding_dimension'