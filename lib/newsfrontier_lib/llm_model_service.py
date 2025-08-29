"""
LLM Model Service for NewsFrontier - Multi-model configuration and validation.

This module provides services for managing LLM model configurations,
including LiteLLM provider validation and model type checking.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

# Try importing litellm for provider validation
try:
    import litellm
    from litellm import model_list
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available, provider validation will be limited")

from .database import get_db_session
from .models import LLMModel
from .schemas import LLMModelCreate, LLMModelUpdate, LLMModelResponse
from .crypto import get_key_manager

logger = logging.getLogger(__name__)


class LLMModelService:
    """Service for managing LLM model configurations."""
    
    def __init__(self):
        """Initialize the LLM model service."""
        self.key_manager = get_key_manager()
        self._supported_providers_cache = None
        self._supported_models_cache = None
    
    def get_supported_providers(self) -> Set[str]:
        """
        Get list of supported LiteLLM providers.
        
        Returns:
            Set of supported provider names
        """
        if self._supported_providers_cache is not None:
            return self._supported_providers_cache
        
        providers = set()
        
        if LITELLM_AVAILABLE:
            try:
                # Get all supported providers from LiteLLM
                all_models = model_list
                for model_info in all_models:
                    if isinstance(model_info, dict) and 'litellm_provider' in model_info:
                        providers.add(model_info['litellm_provider'])
                
                # Add common providers that might not be in model_list
                providers.update([
                    'openai', 'anthropic', 'google', 'vertex_ai', 'azure', 
                    'bedrock', 'cohere', 'huggingface', 'ollama', 'custom'
                ])
                
            except Exception as e:
                logger.warning(f"Failed to get providers from LiteLLM: {e}")
                # Fallback to common providers
                providers = {
                    'openai', 'anthropic', 'google', 'vertex_ai', 'azure',
                    'bedrock', 'cohere', 'huggingface', 'ollama', 'custom'
                }
        else:
            # Fallback when LiteLLM is not available
            providers = {
                'openai', 'anthropic', 'google', 'vertex_ai', 'azure',
                'bedrock', 'cohere', 'huggingface', 'ollama', 'custom'
            }
        
        self._supported_providers_cache = providers
        return providers
    
    def validate_provider(self, provider: str) -> bool:
        """
        Validate if a provider is supported by LiteLLM.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            True if provider is supported, False otherwise
        """
        if not provider:
            return False
        
        supported_providers = self.get_supported_providers()
        return provider.lower() in [p.lower() for p in supported_providers]
    
    def validate_model_configuration(self, provider: str, model_name: str, model_type: str) -> Dict[str, Any]:
        """
        Validate a model configuration against LiteLLM capabilities.
        
        Args:
            provider: Provider name
            model_name: Model name
            model_type: Model type (chat, embedding, etc.)
            
        Returns:
            Validation result with status and messages
        """
        result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check provider
        if not self.validate_provider(provider):
            result['errors'].append(f"Provider '{provider}' is not supported by LiteLLM")
            result['valid'] = False
        
        # Check model name format
        if not model_name or not model_name.strip():
            result['errors'].append("Model name cannot be empty")
            result['valid'] = False
        
        # Model type specific validations
        if model_type == 'embedding':
            if 'embedding' not in model_name.lower() and provider in ['openai']:
                result['warnings'].append(f"Model '{model_name}' might not be an embedding model for provider '{provider}'")
        
        elif model_type == 'chat':
            if any(keyword in model_name.lower() for keyword in ['embedding', 'whisper', 'dall-e']):
                result['warnings'].append(f"Model '{model_name}' might not be a chat model")
        
        # Provider specific suggestions
        if provider == 'openai' and model_type == 'chat':
            common_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o']
            if model_name not in common_models:
                result['suggestions'].append(f"Common OpenAI chat models: {', '.join(common_models)}")
        
        return result
    
    def create_model(self, db: Session, model_data: LLMModelCreate) -> LLMModel:
        """
        Create a new LLM model configuration.
        
        Args:
            db: Database session
            model_data: Model creation data
            
        Returns:
            Created LLM model
        """
        # Validate configuration
        validation = self.validate_model_configuration(
            model_data.provider, 
            model_data.model_name, 
            model_data.model_type
        )
        
        if not validation['valid']:
            raise ValueError(f"Invalid model configuration: {'; '.join(validation['errors'])}")
        
        # Encrypt API key if provided
        api_key_encrypted = None
        if model_data.api_key and self.key_manager.is_available():
            api_key_encrypted = self.key_manager.encrypt(model_data.api_key)
            if not api_key_encrypted:
                raise ValueError("Failed to encrypt API key")
        
        # Create model instance
        db_model = LLMModel(
            name=model_data.name,
            model_type=model_data.model_type,
            provider=model_data.provider,
            model_name=model_data.model_name,
            api_key_encrypted=api_key_encrypted,
            api_base_url=model_data.api_base_url,
            is_active=model_data.is_active,
            config_json=model_data.config_json,
            description=model_data.description
        )
        
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        return db_model
    
    
    def get_models_by_type(self, db: Session, model_type: str, active_only: bool = True) -> List[LLMModel]:
        """
        Get models by type.
        
        Args:
            db: Database session
            model_type: Model type to filter by
            active_only: Whether to only return active models
            
        Returns:
            List of models
        """
        query = db.query(LLMModel).filter(LLMModel.model_type == model_type)
        
        if active_only:
            query = query.filter(LLMModel.is_active == True)
        
        return query.order_by(LLMModel.name).all()
    
    def get_first_model(self, db: Session, model_type: str) -> Optional[LLMModel]:
        """
        Get the first active model for a given type (by name order).
        
        Args:
            db: Database session
            model_type: Model type
            
        Returns:
            First model or None if not found
        """
        return db.query(LLMModel).filter(
            LLMModel.model_type == model_type,
            LLMModel.is_active == True
        ).order_by(LLMModel.name).first()
    
    def update_model(self, db: Session, model_id: int, model_data: LLMModelUpdate) -> Optional[LLMModel]:
        """
        Update an existing LLM model.
        
        Args:
            db: Database session
            model_id: Model ID to update
            model_data: Updated model data
            
        Returns:
            Updated model or None if not found
        """
        model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return None
        
        # Validate configuration if provider/model changed
        update_data = model_data.dict(exclude_unset=True)
        if 'provider' in update_data or 'model_name' in update_data or 'model_type' in update_data:
            provider = update_data.get('provider', model.provider)
            model_name = update_data.get('model_name', model.model_name)
            model_type = update_data.get('model_type', model.model_type)
            
            validation = self.validate_model_configuration(provider, model_name, model_type)
            if not validation['valid']:
                raise ValueError(f"Invalid model configuration: {'; '.join(validation['errors'])}")
        
        # Handle API key encryption if provided
        if model_data.api_key is not None and model_data.api_key.strip():
            if self.key_manager.is_available():
                api_key_encrypted = self.key_manager.encrypt(model_data.api_key)
                if not api_key_encrypted:
                    raise ValueError("Failed to encrypt API key")
                update_data['api_key_encrypted'] = api_key_encrypted
            else:
                raise ValueError("Key manager not available for API key encryption")
        
        
        # Update model attributes
        for field, value in update_data.items():
            if field != 'api_key':  # Skip the unencrypted api_key field
                setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        
        return model
    
    def delete_model(self, db: Session, model_id: int) -> bool:
        """
        Delete an LLM model.
        
        Args:
            db: Database session
            model_id: Model ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            return False
        
        db.delete(model)
        db.commit()
        
        return True


# Global instance
llm_model_service = LLMModelService()


def get_llm_model_service() -> LLMModelService:
    """Get the global LLM model service instance."""
    return llm_model_service