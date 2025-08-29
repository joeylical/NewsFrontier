"""
Multi-Model LLM Client for NewsFrontier - Database-driven multi-model support.

This module provides a unified interface for LLM operations with multiple
model configurations stored in the database and dynamic LiteLLM routing.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session

# Try importing litellm
try:
    import litellm
    from litellm import embedding, completion
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available, LLM operations will be disabled")

from .database import get_db_session
from .models import LLMModel
from .crud import llm_model
from .crypto import get_key_manager

logger = logging.getLogger(__name__)


class MultiModelLLMClient:
    """Multi-model LLM client with database-driven configuration."""
    
    def __init__(self):
        """Initialize the multi-model LLM client."""
        self.key_manager = get_key_manager()
        self._model_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_refresh = 0
        
        # Initialize LiteLLM
        if LITELLM_AVAILABLE:
            self._setup_litellm()
            logger.info("Multi-model LLM client initialized")
        else:
            logger.error("LiteLLM not available - multi-model client disabled")
    
    def _setup_litellm(self):
        """Setup LiteLLM configuration."""
        try:
            # Configure LiteLLM settings
            litellm.drop_params = True  # Drop unsupported parameters
            litellm.set_verbose = False  # Reduce verbosity
            logger.info("LiteLLM configured for multi-model support")
        except Exception as e:
            logger.error(f"Failed to setup LiteLLM: {e}")
    
    def _should_refresh_cache(self) -> bool:
        """Check if model cache should be refreshed."""
        import time
        return time.time() - self._last_cache_refresh > self._cache_ttl
    
    def _refresh_model_cache(self):
        """Refresh model cache from database."""
        try:
            import time
            with get_db_session() as db:
                # Get all active models
                models = db.query(LLMModel).filter(LLMModel.is_active == True).all()
                new_cache = {
                    'models_by_name': {},
                    'models_by_type': {},
                    'default_models': {}
                }
                
                for model in models:
                    # Cache by name
                    new_cache['models_by_name'][model.name] = model
                    
                    # Cache by type
                    if model.model_type not in new_cache['models_by_type']:
                        new_cache['models_by_type'][model.model_type] = []
                    new_cache['models_by_type'][model.model_type].append(model)
                    
                    # Cache default models
                    if model.is_default:
                        new_cache['default_models'][model.model_type] = model
                
                # Sort models by display order within each type
                for model_type in new_cache['models_by_type']:
                    new_cache['models_by_type'][model_type].sort(
                        key=lambda m: (m.display_order, m.name)
                    )
                
                self._model_cache = new_cache
                self._last_cache_refresh = time.time()
                
                logger.debug(f"Model cache refreshed: {len(models)} active models")
                
        except Exception as e:
            logger.error(f"Failed to refresh model cache: {e}")
    
    def _get_model(self, model_name: Optional[str] = None, model_type: Optional[str] = None) -> Optional[LLMModel]:
        """
        Get model by name or type.
        
        Args:
            model_name: Specific model name
            model_type: Model type (if no name specified, gets default or first model)
            
        Returns:
            LLM model configuration or None
        """
        # Refresh cache if needed
        if self._should_refresh_cache():
            self._refresh_model_cache()
        
        # Get by name if specified
        if model_name:
            return self._model_cache.get('models_by_name', {}).get(model_name)
        
        # Get by type
        if model_type:
            # Try default first
            default_model = self._model_cache.get('default_models', {}).get(model_type)
            if default_model:
                return default_model
            
            # Fall back to first model of type
            models_of_type = self._model_cache.get('models_by_type', {}).get(model_type, [])
            return models_of_type[0] if models_of_type else None
        
        return None
    
    def _prepare_api_key(self, model: LLMModel) -> Optional[str]:
        """
        Decrypt and prepare API key for a model.
        
        Args:
            model: LLM model configuration
            
        Returns:
            Decrypted API key or None
        """
        if not model.api_key_encrypted:
            return None
        
        if not self.key_manager.is_available():
            logger.error("Encryption not available for API key decryption")
            return None
        
        decrypted_key = self.key_manager.decrypt(model.api_key_encrypted)
        if not decrypted_key:
            logger.error(f"Failed to decrypt API key for model {model.name}")
            return None
        
        return decrypted_key
    
    def _build_litellm_model_name(self, model: LLMModel) -> str:
        """
        Build LiteLLM model name from configuration.
        
        Args:
            model: LLM model configuration
            
        Returns:
            LiteLLM formatted model name
        """
        # If model_name already has provider prefix, use as-is
        if '/' in model.model_name:
            return model.model_name
        
        # For custom provider, use model name directly
        if model.provider.lower() == 'custom':
            return model.model_name
        
        # Build provider/model format for LiteLLM
        return f"{model.provider}/{model.model_name}"
    
    def _prepare_api_params(self, model: LLMModel) -> Dict[str, Any]:
        """
        Prepare API parameters for a model.
        
        Args:
            model: LLM model configuration
            
        Returns:
            Dictionary of API parameters
        """
        params = {}
        
        # Add API key if available
        api_key = self._prepare_api_key(model)
        if api_key:
            # Set environment variable for LiteLLM
            env_key_mapping = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY',
                'google': 'GOOGLE_API_KEY',
                'vertex_ai': 'GOOGLE_API_KEY',
                'azure': 'AZURE_API_KEY',
                'bedrock': 'AWS_ACCESS_KEY_ID',
                'cohere': 'COHERE_API_KEY',
                'huggingface': 'HUGGINGFACE_API_KEY'
            }
            
            env_key = env_key_mapping.get(model.provider.lower(), f"{model.provider.upper()}_API_KEY")
            os.environ[env_key] = api_key
        
        # Add custom API base URL if specified
        if model.api_base_url:
            params['api_base'] = model.api_base_url
        
        # Parse additional config from JSON if available
        if model.config_json:
            try:
                config = json.loads(model.config_json)
                params.update(config)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid config JSON for model {model.name}: {e}")
        
        return params
    
    def is_available(self) -> bool:
        """Check if multi-model LLM client is available."""
        return LITELLM_AVAILABLE
    
    def list_available_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Args:
            model_type: Filter by model type (optional)
            
        Returns:
            List of available models with metadata
        """
        if self._should_refresh_cache():
            self._refresh_model_cache()
        
        models_info = []
        
        for model_name, model in self._model_cache.get('models_by_name', {}).items():
            if model_type and model.model_type != model_type:
                continue
            
            models_info.append({
                'name': model.name,
                'model_type': model.model_type,
                'provider': model.provider,
                'model_name': model.model_name,
                'is_default': model.is_default,
                'description': model.description,
                'has_api_key': bool(model.api_key_encrypted)
            })
        
        return sorted(models_info, key=lambda x: (x['model_type'], x['name']))
    
    def generate_embedding(self, 
                          text: str, 
                          model_name: Optional[str] = None,
                          **kwargs) -> Optional[List[float]]:
        """
        Generate embedding using specified or default embedding model.
        
        Args:
            text: Text to generate embedding for
            model_name: Specific model name (optional, uses default embedding model)
            **kwargs: Additional parameters
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None
        
        if not LITELLM_AVAILABLE:
            logger.error("LiteLLM not available for embedding generation")
            return None
        
        # Get model configuration
        model = self._get_model(model_name=model_name, model_type='embedding')
        if not model:
            logger.error(f"No embedding model found: {model_name or 'default'}")
            return None
        
        try:
            # Prepare API parameters
            api_params = self._prepare_api_params(model)
            litellm_model = self._build_litellm_model_name(model)
            
            # Prepare embedding parameters
            embedding_params = {
                'model': litellm_model,
                'input': [text[:8000]],  # Truncate if too long
                **api_params,
                **kwargs
            }
            
            logger.debug(f"Generating embedding with model {model.name} ({litellm_model})")
            
            # Make embedding request
            response = embedding(**embedding_params)
            
            if response and response.data and len(response.data) > 0:
                embedding_vector = response.data[0].embedding
                logger.debug(f"Generated embedding: {len(embedding_vector)} dimensions")
                return embedding_vector
            
            logger.error(f"Empty response from embedding model {model.name}")
            return None
            
        except Exception as e:
            logger.error(f"Embedding generation failed with model {model.name}: {e}")
            return None
    
    def create_completion(self,
                         prompt: str,
                         model_name: Optional[str] = None,
                         max_tokens: int = 1000,
                         temperature: float = 0.7,
                         **kwargs) -> Optional[str]:
        """
        Create text completion using specified or default chat model.
        
        Args:
            prompt: The prompt to complete
            model_name: Specific model name (optional, uses default chat model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text or None if failed
        """
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt provided for completion")
            return None
        
        if not LITELLM_AVAILABLE:
            logger.error("LiteLLM not available for text completion")
            return None
        
        # Get model configuration
        model = self._get_model(model_name=model_name, model_type='chat')
        if not model:
            logger.error(f"No chat model found: {model_name or 'default'}")
            return None
        
        try:
            # Prepare API parameters
            api_params = self._prepare_api_params(model)
            litellm_model = self._build_litellm_model_name(model)
            
            # Truncate prompt if too long
            max_chars = 50000
            if len(prompt) > max_chars:
                prompt = prompt[:max_chars]
                logger.debug(f"Truncated prompt to {max_chars} characters")
            
            # Prepare completion parameters
            completion_params = {
                'model': litellm_model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens,
                'temperature': temperature,
                **api_params,
                **kwargs
            }
            
            logger.debug(f"Creating completion with model {model.name} ({litellm_model})")
            
            # Make completion request
            response = completion(**completion_params)
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.debug(f"Generated completion: {len(content)} characters")
                    return content.strip()
            
            logger.error(f"Empty response from chat model {model.name}")
            return None
            
        except Exception as e:
            logger.error(f"Text completion failed with model {model.name}: {e}")
            return None


# Global instance
multi_model_llm_client = MultiModelLLMClient()


def get_multi_model_llm_client() -> MultiModelLLMClient:
    """Get the global multi-model LLM client instance."""
    return multi_model_llm_client


# Backward compatibility functions
def generate_topic_embedding(topic_name: str, model_name: Optional[str] = None) -> Optional[List[float]]:
    """Generate embedding for a topic name."""
    return multi_model_llm_client.generate_embedding(topic_name, model_name=model_name)


def generate_content_embedding(title: str, content: str, model_name: Optional[str] = None) -> Optional[List[float]]:
    """Generate embedding for article content."""
    text_for_embedding = f"{title}\n\n{content}" if title and content else (title or content)
    return multi_model_llm_client.generate_embedding(text_for_embedding, model_name=model_name)


def create_summary(title: str, content: str, prompt_template: str, model_name: Optional[str] = None) -> Optional[str]:
    """Create a summary of content using the specified or default chat model."""
    if not content or len(content) < 100:
        logger.warning("Content too short for summary generation")
        return None
    
    if not multi_model_llm_client.is_available():
        logger.warning("Multi-model LLM client not available for summary generation")
        return None
    
    prompt = prompt_template.format(title=title, content=content)
    return multi_model_llm_client.create_completion(
        prompt=prompt, 
        model_name=model_name,
        max_tokens=500,
        temperature=0.3
    )