"""
Admin Settings API for NewsFrontier - Backend Integration

This module provides REST API endpoints for managing system configuration,
matching the frontend expectations and database schema.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from newsfrontier_lib.config_service import get_config, ConfigKeys
from newsfrontier_lib.crypto import get_key_manager
from newsfrontier_lib.database import get_db_session
from newsfrontier_lib.models import User as UserModel, SystemSetting
from newsfrontier_lib.init_config import list_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Router setup to match frontend expectations
router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()


# Simple models for basic CRUD operations
class SystemSettingItem(BaseModel):
    setting_key: str
    setting_value: str
    setting_type: str  # 'string' | 'integer' | 'float' | 'boolean'


class SystemSettingsUpdate(BaseModel):
    """Payload for updating system settings"""
    settings: List[SystemSettingItem]


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify admin user authentication."""
    try:
        # TODO: Replace with proper JWT verification from existing auth system
        # This should integrate with the existing JWT auth in main.py
        token = credentials.credentials
        
        if not token or len(token) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # For now, assume admin access - in production this should:
        # 1. Decode JWT token
        # 2. Verify user exists and is_admin=True
        return {"user_id": 1, "is_admin": True}
        
    except Exception as e:
        logger.error(f"Admin authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.get("/system-settings", response_model=List[SystemSettingItem])
async def get_system_settings(admin_user: dict = Depends(get_admin_user)):
    """
    Get all system configuration settings as simple key-value pairs.
    Frontend handles all display logic and UI components.
    """
    try:
        with get_db_session() as db:
            settings = db.query(SystemSetting).all()
            
            result = []
            for setting in settings:
                # Handle encrypted fields - don't expose actual values
                display_value = setting.setting_value or ""
                if setting.setting_key.endswith('_encrypted') and setting.setting_value:
                    display_value = "<encrypted>"
                
                setting_item = SystemSettingItem(
                    setting_key=setting.setting_key,
                    setting_value=display_value,
                    setting_type=setting.setting_type or "string"
                )
                result.append(setting_item)
            
            logger.info(f"Returned {len(result)} system settings as key-value pairs")
            return result
            
    except Exception as e:
        logger.error(f"Failed to get system settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system settings"
        )


@router.put("/system-settings")
async def update_system_settings(
    settings_data: List[SystemSettingItem],
    admin_user: dict = Depends(get_admin_user)
):
    """
    Update multiple system settings.
    
    This endpoint accepts the exact format that the frontend sends
    and updates the database accordingly.
    """
    try:
        config = get_config()
        updated_count = 0
        
        for setting_data in settings_data:
            # Check if this is an encrypted setting based on key suffix
            is_encrypted = setting_data.setting_key.endswith('_encrypted')
            setting_key = setting_data.setting_key
            setting_value = setting_data.setting_value
            
            # Skip if encrypted field contains placeholder value
            if is_encrypted and setting_value == "<encrypted>":
                logger.info(f"Skipping encrypted setting {setting_key} - no new value provided")
                continue
            
            # Skip if value is empty for encrypted fields
            if is_encrypted and not setting_value.strip():
                logger.info(f"Skipping encrypted setting {setting_key} - empty value provided")
                continue
            
            try:
                if is_encrypted:
                    # For encrypted settings: input is plaintext, backend encrypts and stores
                    success = config.set_encrypted(
                        key=setting_key,
                        value=setting_value,  # This is the plaintext API key from user input
                        description=None  # Description not provided in simple CRUD model
                    )
                    if success:
                        # Log success without exposing the key
                        logger.info(f"Successfully updated encrypted setting: {setting_key}")
                    else:
                        logger.warning(f"Failed to update encrypted setting: {setting_key}")
                else:
                    # Set regular setting
                    success = config.set(
                        key=setting_key,
                        value=setting_value,
                        setting_type=setting_data.setting_type,
                        description=None,  # Description not provided in simple CRUD model
                        is_public=False  # Admin settings are not public
                    )
                    if success:
                        logger.info(f"Successfully updated setting: {setting_key} = {setting_value}")
                    else:
                        logger.warning(f"Failed to update setting: {setting_key}")
                
                if success:
                    updated_count += 1
                    
            except Exception as setting_error:
                # Log error without exposing sensitive values
                if is_encrypted:
                    logger.error(f"Error updating encrypted setting {setting_key}: {setting_error}")
                else:
                    logger.error(f"Error updating setting {setting_key} = {setting_value}: {setting_error}")
        
        logger.info(f"Updated {updated_count}/{len(settings_data)} system settings")
        
        return {
            "success": True,
            "message": f"Updated {updated_count} system settings successfully",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to update system settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system settings"
        )


@router.get("/provider-urls")
async def get_provider_urls(admin_user: dict = Depends(get_admin_user)):
    """
    Get default API URLs for different providers.
    This helps with auto-completion in the frontend.
    """
    try:
        return _get_provider_api_urls()
    except Exception as e:
        logger.error(f"Failed to get provider URLs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider URLs"
        )


def _get_provider_api_urls() -> Dict[str, str]:
    """Get default API URLs for different providers."""
    return {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
        "google": "https://generativelanguage.googleapis.com/v1beta",
        "azure": "https://YOUR_RESOURCE.openai.azure.com",
        "custom": ""
    }