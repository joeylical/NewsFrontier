"""
Configuration Initialization for NewsFrontier.

This script initializes the database with default configuration settings
and provides utilities for migrating from environment-based to database-based configuration.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .database import get_db
from .models import SystemSetting
from .config_service import ConfigKeys, get_config
from .crypto import get_key_manager, test_encryption

logger = logging.getLogger(__name__)


def init_default_settings() -> bool:
    """
    Initialize database with default configuration settings.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Test encryption first
        if not test_encryption():
            logger.error("Encryption test failed. Please check CRYPTO_MASTER_KEY in .env")
            return False
        
        config = get_config()
        key_manager = get_key_manager()
        
        # Default configuration settings
        default_settings = [
            # LLM Model Configuration
            {
                'key': ConfigKeys.LLM_SUMMARY_MODEL,
                'value': 'gemini-2.0-flash-lite',
                'type': 'string',
                'description': 'LLM model for article summaries (fast, efficient)',
                'public': True
            },
            {
                'key': ConfigKeys.LLM_ANALYSIS_MODEL,
                'value': 'gemini-2.5-pro',
                'type': 'string',
                'description': 'LLM model for analysis tasks (cluster detection, daily summaries)',
                'public': True
            },
            {
                'key': ConfigKeys.LLM_EMBEDDING_MODEL,
                'value': 'text-embedding-004',
                'type': 'string',
                'description': 'Model for generating embeddings',
                'public': True
            },
            {
                'key': ConfigKeys.LLM_IMAGE_MODEL,
                'value': 'imagen-3.0-generate-002',
                'type': 'string',
                'description': 'Model for image generation',
                'public': True
            },
            
            # LLM API Configuration
            {
                'key': ConfigKeys.LLM_API_URL,
                'value': 'https://generativelanguage.googleapis.com/v1beta/openai/',
                'type': 'string',
                'description': 'Primary LLM API endpoint',
                'public': False
            },
            {
                'key': ConfigKeys.EMBEDDING_API_URL,
                'value': 'https://api.openai.com/v1',
                'type': 'string',
                'description': 'Embedding API endpoint',
                'public': False
            },
            
            # Feature Toggles
            {
                'key': ConfigKeys.DAILY_SUMMARY_ENABLED,
                'value': 'true',
                'type': 'boolean',
                'description': 'Enable daily summary generation',
                'public': True
            },
            {
                'key': ConfigKeys.DAILY_SUMMARY_COVER_ENABLED,
                'value': 'true',
                'type': 'boolean',
                'description': 'Enable daily summary cover image generation',
                'public': True
            },
            
            # Processing Configuration
            {
                'key': ConfigKeys.SCRAPER_INTERVAL,
                'value': '60',
                'type': 'integer',
                'description': 'RSS scraper interval in minutes',
                'public': True
            },
            {
                'key': ConfigKeys.POSTPROCESS_INTERVAL,
                'value': '30',
                'type': 'integer',
                'description': 'Post-processing interval in minutes',
                'public': True
            },
            {
                'key': ConfigKeys.CLUSTER_THRESHOLD,
                'value': '0.8',
                'type': 'float',
                'description': 'Similarity threshold for article clustering',
                'public': True
            },
            {
                'key': ConfigKeys.MAX_PROCESSING_ATTEMPTS,
                'value': '3',
                'type': 'integer',
                'description': 'Maximum processing attempts for failed articles',
                'public': True
            },
            {
                'key': ConfigKeys.EMBEDDING_DIMENSION,
                'value': '768',
                'type': 'integer',
                'description': 'Embedding vector dimension',
                'public': True
            },
            
            # S3 Configuration (non-encrypted defaults)
            {
                'key': ConfigKeys.S3_REGION,
                'value': 'us-east-1',
                'type': 'string',
                'description': 'S3 region',
                'public': False
            },
            {
                'key': ConfigKeys.S3_BUCKET,
                'value': 'newsfrontier-assets',
                'type': 'string',
                'description': 'S3 bucket name',
                'public': False
            },
        ]
        
        # Initialize settings
        success_count = 0
        with get_db() as db:
            for setting_def in default_settings:
                try:
                    # Check if setting already exists
                    existing = db.query(SystemSetting).filter(
                        SystemSetting.setting_key == setting_def['key']
                    ).first()
                    
                    if not existing:
                        # Create new setting
                        setting = SystemSetting(
                            setting_key=setting_def['key'],
                            setting_value=setting_def['value'],
                            setting_type=setting_def['type'],
                            description=setting_def['description'],
                            is_public=setting_def['public']
                        )
                        db.add(setting)
                        success_count += 1
                        logger.info(f"Created setting: {setting_def['key']}")
                    else:
                        logger.debug(f"Setting already exists: {setting_def['key']}")
                
                except Exception as e:
                    logger.error(f"Failed to create setting {setting_def['key']}: {e}")
            
            db.commit()
        
        logger.info(f"Initialized {success_count} default settings")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize default settings: {e}")
        return False


def migrate_from_env() -> bool:
    """
    Migrate configuration from environment variables to database.
    This will only migrate values that don't already exist in the database.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        config = get_config()
        key_manager = get_key_manager()
        
        if not key_manager.is_available():
            logger.error("Encryption not available for migration")
            return False
        
        # Environment to config mapping
        env_migrations = [
            # API Keys (encrypted)
            ('GOOGLE_API_KEY', ConfigKeys.GOOGLE_API_KEY, 'string', 'Google API Key', True),
            ('OPENAI_API_KEY', ConfigKeys.OPENAI_API_KEY, 'string', 'OpenAI API Key', True),
            
            # S3 Configuration (encrypted sensitive data)
            ('S3API_REGION', ConfigKeys.S3_REGION, 'string', 'S3 Region', False),
            ('S3API_ENDPOINT', ConfigKeys.S3_ENDPOINT, 'string', 'S3 Endpoint URL', True),
            ('S3API_BUCKET', ConfigKeys.S3_BUCKET, 'string', 'S3 Bucket Name', False),
            ('S3API_KEY_ID', ConfigKeys.S3_ACCESS_KEY_ID, 'string', 'S3 Access Key ID', True),
            ('S3API_KEY', ConfigKeys.S3_SECRET_KEY, 'string', 'S3 Secret Access Key', True),
            
            # LLM Configuration
            ('LLM_MODEL_SUMMARY', ConfigKeys.LLM_SUMMARY_MODEL, 'string', 'Summary LLM Model', False),
            ('LLM_MODEL_ANALYSIS', ConfigKeys.LLM_ANALYSIS_MODEL, 'string', 'Analysis LLM Model', False),
            ('EMBEDDING_MODEL', ConfigKeys.LLM_EMBEDDING_MODEL, 'string', 'Embedding Model', False),
            ('IMAGEGEN_MODEL', ConfigKeys.LLM_IMAGE_MODEL, 'string', 'Image Generation Model', False),
            
            # API URLs
            ('LLM_API_URL', ConfigKeys.LLM_API_URL, 'string', 'LLM API URL', False),
            ('EMBEDDING_API_URL', ConfigKeys.EMBEDDING_API_URL, 'string', 'Embedding API URL', False),
            
            # Processing Configuration
            ('EMBEDDING_DIMENSION', ConfigKeys.EMBEDDING_DIMENSION, 'integer', 'Embedding Dimension', False),
            ('MAX_PROCESSING_ATTEMPTS', ConfigKeys.MAX_PROCESSING_ATTEMPTS, 'integer', 'Max Processing Attempts', False),
        ]
        
        success_count = 0
        with get_db() as db:
            for env_key, config_key, setting_type, description, encrypt in env_migrations:
                try:
                    # Check if already exists in database
                    existing = db.query(SystemSetting).filter(
                        SystemSetting.setting_key == config_key
                    ).first()
                    
                    if existing:
                        logger.debug(f"Config already exists, skipping: {config_key}")
                        continue
                    
                    # Get value from environment
                    env_value = os.getenv(env_key)
                    if not env_value:
                        logger.debug(f"Environment variable not set: {env_key}")
                        continue
                    
                    # Prepare value for database
                    if encrypt:
                        # Encrypt the value
                        encrypted_value = key_manager.encrypt(env_value)
                        if not encrypted_value:
                            logger.error(f"Failed to encrypt value for {config_key}")
                            continue
                        store_value = encrypted_value
                    else:
                        store_value = env_value
                    
                    # Create database setting
                    setting = SystemSetting(
                        setting_key=config_key,
                        setting_value=store_value,
                        setting_type=setting_type,
                        description=description,
                        is_public=False  # Migrated settings are not public by default
                    )
                    db.add(setting)
                    success_count += 1
                    
                    logger.info(f"Migrated {env_key} -> {config_key} ({'encrypted' if encrypt else 'plain'})")
                
                except Exception as e:
                    logger.error(f"Failed to migrate {env_key}: {e}")
            
            db.commit()
        
        logger.info(f"Successfully migrated {success_count} environment variables to database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate from environment: {e}")
        return False


def set_api_key(key_name: str, api_key: str, description: str = None) -> bool:
    """
    Set an encrypted API key in the database.
    
    Args:
        key_name: Configuration key name (should end with '_encrypted')
        api_key: The API key to encrypt and store
        description: Optional description
        
    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    return config.set_encrypted(key_name, api_key, description=description, is_public=False)


def get_api_key(key_name: str) -> Optional[str]:
    """
    Get a decrypted API key from the database.
    
    Args:
        key_name: Configuration key name
        
    Returns:
        Decrypted API key or None if not found/failed
    """
    config = get_config()
    return config.get_encrypted(key_name, fallback_env=True)


def list_settings(include_encrypted: bool = False, public_only: bool = False) -> Dict[str, Any]:
    """
    List all configuration settings.
    
    Args:
        include_encrypted: Whether to include encrypted values (returned as '<encrypted>')
        public_only: Whether to return only public settings
        
    Returns:
        Dictionary of configuration settings
    """
    try:
        config = get_config()
        settings = config.get_all(include_encrypted=False, public_only=public_only)
        
        # Add indication for encrypted values
        if include_encrypted:
            with get_db() as db:
                encrypted_settings = db.query(SystemSetting).filter(
                    SystemSetting.setting_key.like('%_encrypted')
                ).all()
                
                for setting in encrypted_settings:
                    if not public_only or setting.is_public:
                        settings[setting.setting_key] = '<encrypted>'
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to list settings: {e}")
        return {}


def main():
    """Main function for running configuration initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize NewsFrontier configuration')
    parser.add_argument('--init', action='store_true', help='Initialize default settings')
    parser.add_argument('--migrate', action='store_true', help='Migrate from environment variables')
    parser.add_argument('--list', action='store_true', help='List current settings')
    parser.add_argument('--test-crypto', action='store_true', help='Test encryption functionality')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    if args.test_crypto:
        if test_encryption():
            print("✓ Encryption test passed")
        else:
            print("✗ Encryption test failed")
        return
    
    if args.init:
        print("Initializing default settings...")
        if init_default_settings():
            print("✓ Default settings initialized")
        else:
            print("✗ Failed to initialize default settings")
    
    if args.migrate:
        print("Migrating from environment variables...")
        if migrate_from_env():
            print("✓ Environment migration completed")
        else:
            print("✗ Environment migration failed")
    
    if args.list:
        print("Current configuration settings:")
        settings = list_settings(include_encrypted=True, public_only=False)
        for key, value in settings.items():
            print(f"  {key}: {value}")


if __name__ == '__main__':
    main()