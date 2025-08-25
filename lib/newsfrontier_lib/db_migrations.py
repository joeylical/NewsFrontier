"""
Database migrations for NewsFrontier encrypted configuration.

This module provides database migration functions to set up encrypted
configuration storage and initialize default settings.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .database import get_db
from .models import SystemSetting
from .config_service import ConfigKeys
from .crypto import get_key_manager

logger = logging.getLogger(__name__)


def create_encrypted_config_settings() -> bool:
    """
    Create encrypted configuration settings in the database.
    
    This migration adds encrypted API key storage and other sensitive configuration.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        key_manager = get_key_manager()
        if not key_manager.is_available():
            logger.error("Encryption not available for migration")
            return False
        
        # Define encrypted settings to create
        encrypted_settings = [
            # API Keys (encrypted)
            {
                'key': ConfigKeys.GOOGLE_API_KEY,
                'type': 'string',
                'description': 'Google API Key (encrypted)',
                'is_public': False,
                'default_value': None
            },
            {
                'key': ConfigKeys.OPENAI_API_KEY,
                'type': 'string',
                'description': 'OpenAI API Key (encrypted)',
                'is_public': False,
                'default_value': None
            },
            
            # S3 Configuration (encrypted sensitive data)
            {
                'key': ConfigKeys.S3_ENDPOINT,
                'type': 'string',
                'description': 'S3 Endpoint URL (encrypted)',
                'is_public': False,
                'default_value': None
            },
            {
                'key': ConfigKeys.S3_ACCESS_KEY_ID,
                'type': 'string',
                'description': 'S3 Access Key ID (encrypted)',
                'is_public': False,
                'default_value': None
            },
            {
                'key': ConfigKeys.S3_SECRET_KEY,
                'type': 'string',
                'description': 'S3 Secret Access Key (encrypted)',
                'is_public': False,
                'default_value': None
            }
        ]
        
        with get_db() as db:
            success_count = 0
            
            for setting_def in encrypted_settings:
                try:
                    # Check if setting already exists
                    existing = db.query(SystemSetting).filter(
                        SystemSetting.setting_key == setting_def['key']
                    ).first()
                    
                    if existing:
                        logger.debug(f"Encrypted setting already exists: {setting_def['key']}")
                        continue
                    
                    # Create new encrypted setting
                    setting = SystemSetting(
                        setting_key=setting_def['key'],
                        setting_value=setting_def['default_value'],  # None for empty encrypted settings
                        setting_type=setting_def['type'],
                        description=setting_def['description'],
                        is_public=setting_def['is_public']
                    )
                    
                    db.add(setting)
                    success_count += 1
                    logger.info(f"Created encrypted setting: {setting_def['key']}")
                    
                except IntegrityError as e:
                    logger.warning(f"Setting {setting_def['key']} already exists: {e}")
                    db.rollback()
                except Exception as e:
                    logger.error(f"Failed to create encrypted setting {setting_def['key']}: {e}")
                    db.rollback()
            
            db.commit()
            logger.info(f"Created {success_count} encrypted configuration settings")
            return True
            
    except Exception as e:
        logger.error(f"Failed to create encrypted configuration settings: {e}")
        return False


def migrate_env_to_encrypted_db() -> bool:
    """
    Migrate environment variables to encrypted database settings.
    
    This function reads API keys from environment variables and stores them
    encrypted in the database.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        key_manager = get_key_manager()
        if not key_manager.is_available():
            logger.error("Encryption not available for environment migration")
            return False
        
        # Environment variable to encrypted config mapping
        env_to_config = [
            ('GOOGLE_API_KEY', ConfigKeys.GOOGLE_API_KEY),
            ('OPENAI_API_KEY', ConfigKeys.OPENAI_API_KEY),
            ('S3API_ENDPOINT', ConfigKeys.S3_ENDPOINT),
            ('S3API_KEY_ID', ConfigKeys.S3_ACCESS_KEY_ID),
            ('S3API_KEY', ConfigKeys.S3_SECRET_KEY),
        ]
        
        with get_db() as db:
            migrated_count = 0
            
            for env_key, config_key in env_to_config:
                try:
                    # Get value from environment
                    env_value = os.getenv(env_key)
                    if not env_value:
                        logger.debug(f"Environment variable not set: {env_key}")
                        continue
                    
                    # Check if already exists in database
                    existing = db.query(SystemSetting).filter(
                        SystemSetting.setting_key == config_key
                    ).first()
                    
                    if existing and existing.setting_value:
                        logger.debug(f"Encrypted config already has value: {config_key}")
                        continue
                    
                    # Encrypt the value
                    encrypted_value = key_manager.encrypt(env_value)
                    if not encrypted_value:
                        logger.error(f"Failed to encrypt value for {config_key}")
                        continue
                    
                    if existing:
                        # Update existing setting
                        existing.setting_value = encrypted_value
                        logger.info(f"Updated encrypted setting: {config_key}")
                    else:
                        # Create new setting (shouldn't happen if create_encrypted_config_settings was run first)
                        setting = SystemSetting(
                            setting_key=config_key,
                            setting_value=encrypted_value,
                            setting_type='string',
                            description=f"Migrated from {env_key} (encrypted)",
                            is_public=False
                        )
                        db.add(setting)
                        logger.info(f"Created new encrypted setting: {config_key}")
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate {env_key} to {config_key}: {e}")
            
            db.commit()
            logger.info(f"Successfully migrated {migrated_count} environment variables to encrypted database settings")
            
            if migrated_count > 0:
                logger.info("SECURITY NOTICE: Consider removing migrated API keys from environment variables")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to migrate environment variables: {e}")
        return False


def verify_encrypted_settings() -> Dict[str, bool]:
    """
    Verify that encrypted settings can be read and decrypted.
    
    Returns:
        Dictionary mapping setting keys to verification status
    """
    verification_results = {}
    
    try:
        key_manager = get_key_manager()
        if not key_manager.is_available():
            logger.error("Encryption not available for verification")
            return verification_results
        
        encrypted_keys = [
            ConfigKeys.GOOGLE_API_KEY,
            ConfigKeys.OPENAI_API_KEY,
            ConfigKeys.S3_ENDPOINT,
            ConfigKeys.S3_ACCESS_KEY_ID,
            ConfigKeys.S3_SECRET_KEY,
        ]
        
        with get_db() as db:
            for key in encrypted_keys:
                try:
                    # Get encrypted setting from database
                    setting = db.query(SystemSetting).filter(
                        SystemSetting.setting_key == key
                    ).first()
                    
                    if not setting:
                        verification_results[key] = False
                        logger.warning(f"Encrypted setting not found: {key}")
                        continue
                    
                    if not setting.setting_value:
                        verification_results[key] = False
                        logger.info(f"Encrypted setting has no value: {key}")
                        continue
                    
                    # Try to decrypt the value
                    decrypted_value = key_manager.decrypt(setting.setting_value)
                    if decrypted_value is not None:
                        verification_results[key] = True
                        logger.debug(f"Successfully verified encrypted setting: {key}")
                    else:
                        verification_results[key] = False
                        logger.error(f"Failed to decrypt setting: {key}")
                        
                except Exception as e:
                    verification_results[key] = False
                    logger.error(f"Error verifying encrypted setting {key}: {e}")
        
        # Log summary
        successful = sum(verification_results.values())
        total = len(verification_results)
        logger.info(f"Encrypted settings verification: {successful}/{total} successful")
        
        return verification_results
        
    except Exception as e:
        logger.error(f"Failed to verify encrypted settings: {e}")
        return verification_results


def run_all_migrations() -> bool:
    """
    Run all database migrations for encrypted configuration.
    
    Returns:
        True if all migrations successful, False otherwise
    """
    logger.info("Running encrypted configuration migrations...")
    
    # Step 1: Create encrypted configuration settings
    logger.info("Step 1: Creating encrypted configuration settings...")
    if not create_encrypted_config_settings():
        logger.error("Failed to create encrypted configuration settings")
        return False
    
    # Step 2: Migrate environment variables to encrypted database
    logger.info("Step 2: Migrating environment variables to encrypted database...")
    if not migrate_env_to_encrypted_db():
        logger.error("Failed to migrate environment variables")
        return False
    
    # Step 3: Verify encrypted settings
    logger.info("Step 3: Verifying encrypted settings...")
    verification_results = verify_encrypted_settings()
    
    # Check if any critical settings failed
    critical_failures = [k for k, v in verification_results.items() if not v and k in [
        ConfigKeys.GOOGLE_API_KEY, ConfigKeys.OPENAI_API_KEY
    ]]
    
    if critical_failures:
        logger.warning(f"Critical encrypted settings not available: {critical_failures}")
        logger.warning("Some AI features may not work until API keys are properly configured")
    
    logger.info("✅ Encrypted configuration migrations completed successfully")
    return True


def main():
    """CLI entry point for running migrations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NewsFrontier encrypted configuration migrations')
    parser.add_argument('--create', action='store_true', help='Create encrypted configuration settings')
    parser.add_argument('--migrate', action='store_true', help='Migrate environment variables to encrypted database')
    parser.add_argument('--verify', action='store_true', help='Verify encrypted settings')
    parser.add_argument('--all', action='store_true', help='Run all migrations')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    if args.create:
        success = create_encrypted_config_settings()
        exit(0 if success else 1)
    elif args.migrate:
        success = migrate_env_to_encrypted_db()
        exit(0 if success else 1)
    elif args.verify:
        results = verify_encrypted_settings()
        all_successful = all(results.values())
        exit(0 if all_successful else 1)
    elif args.all:
        success = run_all_migrations()
        exit(0 if success else 1)
    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()