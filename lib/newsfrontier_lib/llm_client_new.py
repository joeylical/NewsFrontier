"""
Enhanced LLM Client for NewsFrontier - Database-configurable LLM operations with LiteLLM.

This module provides a unified interface for LLM operations with configuration
stored in the database and support for multiple LLM providers through LiteLLM.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

# Try importing litellm
try:
    import litellm
    from litellm import embedding, completion
    LITELLM_AVAILABLE = True
except ImportError:
    litellm = None
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available, falling back to direct API calls")

# Google imports removed - using LiteLLM only

from .config_service import get_config, ConfigKeys

logger = logging.getLogger(__name__)


class EnhancedLLMClient:
    """Enhanced LLM client with database configuration and LiteLLM support."""
    
    def __init__(self):
        """Initialize the Enhanced LLM client with database configuration."""
        self.config = get_config()
        
        # Initialize clients
        self._setup_clients()
        
        # Log model configuration
        self._log_configuration()
    
    def _setup_clients(self):
        """Initialize LiteLLM client based on configuration."""
        try:
            # Setup LiteLLM if available
            if LITELLM_AVAILABLE:
                self._setup_litellm()
            else:
                logger.error("LiteLLM not available - no LLM client can be initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup LLM clients: {e}")
    
    def _setup_litellm(self):
        """Setup LiteLLM configuration."""
        if not LITELLM_AVAILABLE:
            return
        
        try:
            # Get API keys from encrypted storage
            google_api_key = self.config.get_encrypted(ConfigKeys.GOOGLE_API_KEY)
            openai_api_key = self.config.get_encrypted(ConfigKeys.OPENAI_API_KEY)
            anthropic_api_key = self.config.get_encrypted(ConfigKeys.ANTHROPIC_API_KEY)
            
            # Set environment variables for LiteLLM
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key  
            if anthropic_api_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
            
            # Configure LiteLLM settings
            litellm.drop_params = True  # Drop unsupported parameters
            litellm.set_verbose = False  # Reduce verbosity
            
            logger.info("LiteLLM configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup LiteLLM: {e}")
    
    
    def _get_litellm_model_name(self, model_name: str, model_type: str = "text") -> str:
        """
        Convert model name to LiteLLM format based on provider.
        
        Args:
            model_name: The model name from configuration
            model_type: Type of model ("text", "embedding", "image")
            
        Returns:
            LiteLLM formatted model name
        """
        if not model_name:
            return model_name
            
        # Get provider configuration
        default_provider = self.config.get(ConfigKeys.DEFAULT_LLM_PROVIDER, default='openai')
        
        # Check if model already has a provider prefix
        if '/' in model_name:
            return model_name
        
        # Check if this is a known LiteLLM supported model that doesn't need provider prefix
        litellm_supported_models = {
            # OpenAI models
            'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini',
            'text-embedding-ada-002', 'text-embedding-3-small', 'text-embedding-3-large',
            'dall-e-2', 'dall-e-3',
            # Anthropic models  
            'claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-opus-20240229',
            'claude-3-5-sonnet-20240620', 'claude-3-5-haiku-20241022'
        }
        
        if model_name in litellm_supported_models:
            return model_name  # LiteLLM will auto-detect provider
        
        # For Google models, determine if we should use vertex_ai or google prefix
        if model_name.startswith(('gemini-', 'text-embedding-', 'imagen-')):
            # Check if we have custom endpoint settings that suggest using vertex_ai
            custom_endpoint = self._get_model_endpoint(model_type)
            if custom_endpoint and 'googleapis.com' in custom_endpoint:
                return f"vertex_ai/{model_name}"
            else:
                return f"gemini/{model_name}" if model_name.startswith('gemini-') else f"vertex_ai/{model_name}"
        
        # For other models, use the default provider
        if default_provider and default_provider != 'custom':
            return f"{default_provider}/{model_name}"
        
        return model_name
    
    def _get_model_endpoint(self, model_type: str) -> Optional[str]:
        """
        Get custom API endpoint for model type if configured.
        
        Args:
            model_type: Type of model ("summary", "analysis", "embedding", "image")
            
        Returns:
            Custom endpoint URL or None if using default
        """
        # Check if model should use default API configuration
        use_default_key = f'llm_{model_type}_use_default'
        use_default = self.config.get(use_default_key, default='true')
        
        if use_default.lower() in ('true', '1', 'yes', 'on'):
            # Use default endpoint - let LiteLLM handle it
            return None
        else:
            # Use custom endpoint
            custom_endpoint_key = f'llm_{model_type}_api_url'
            return self.config.get(custom_endpoint_key)
    
    def _log_configuration(self):
        """Log current model configuration."""
        default_provider = self.config.get(ConfigKeys.DEFAULT_LLM_PROVIDER, default='openai')
        summary_model = self.config.get(ConfigKeys.LLM_SUMMARY_MODEL, default="gpt-3.5-turbo")
        analysis_model = self.config.get(ConfigKeys.LLM_ANALYSIS_MODEL, default="gpt-4")
        embedding_model = self.config.get(ConfigKeys.LLM_EMBEDDING_MODEL, default="text-embedding-ada-002")
        image_model = self.config.get(ConfigKeys.LLM_IMAGE_MODEL, default="dall-e-3")
        
        logger.info(f"Enhanced LLM Model Configuration:")
        logger.info(f"  Default Provider: {default_provider}")
        logger.info(f"  Summary Model: {summary_model} -> {self._get_litellm_model_name(summary_model, 'summary')}")
        logger.info(f"  Analysis Model: {analysis_model} -> {self._get_litellm_model_name(analysis_model, 'analysis')}")
        logger.info(f"  Embedding Model: {embedding_model} -> {self._get_litellm_model_name(embedding_model, 'embedding')}")
        logger.info(f"  Image Model: {image_model} -> {self._get_litellm_model_name(image_model, 'image')}")
        logger.info(f"  LiteLLM Available: {LITELLM_AVAILABLE}")
    
    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return LITELLM_AVAILABLE
    
    def generate_embedding(self, text: str, task_type: str = "retrieval_query") -> Optional[List[float]]:
        """
        Generate embedding for given text using configured model.
        
        Args:
            text: Text to generate embedding for
            task_type: Task type for embedding (retrieval_query, retrieval_document, etc.)
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            return None
            
        try:
            embedding_model = self.config.get(ConfigKeys.LLM_EMBEDDING_MODEL, 
                                            default="text-embedding-ada-002")
            
            # Convert to LiteLLM format
            litellm_model = self._get_litellm_model_name(embedding_model, "embedding")
            
            # Use LiteLLM only
            if LITELLM_AVAILABLE:
                # Check if we should use custom endpoint
                custom_endpoint = self._get_model_endpoint("embedding")
                
                embedding_params = {
                    "model": litellm_model,
                    "input": [text[:2048]],  # Truncate if too long
                }
                
                # Add custom endpoint if specified
                if custom_endpoint:
                    embedding_params["api_base"] = custom_endpoint
                
                response = embedding(**embedding_params)
                if response and response.data and len(response.data) > 0:
                    return response.data[0].embedding
            else:
                logger.error("LiteLLM not available for embedding generation")
                return None
            
        except Exception as e:
            logger.error(f"Error generating embedding with model {embedding_model}: {e}")
            return None
    
    
    def create_summary_completion(self, 
                                 prompt: str, 
                                 max_tokens: int = 250,
                                 temperature: float = 0.3) -> Optional[str]:
        """Create text completion using the summary model."""
        summary_model = self.config.get(ConfigKeys.LLM_SUMMARY_MODEL, 
                                       default="gemini-1.5-flash")
        return self.create_completion(
            prompt=prompt,
            model=summary_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def create_analysis_completion(self, 
                                  prompt: str, 
                                  max_tokens: int = 500,
                                  temperature: float = 0.3,
                                  response_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create text completion using the analysis model for cluster detection and daily summaries."""
        analysis_model = self.config.get(ConfigKeys.LLM_ANALYSIS_MODEL, 
                                        default="gemini-1.5-pro")
        return self.create_completion(
            prompt=prompt,
            model=analysis_model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_schema=response_schema
        )

    def create_completion(self, 
                         prompt: str, 
                         model: Optional[str] = None,
                         max_tokens: int = 250,
                         temperature: float = 0.3,
                         response_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create text completion using configured LLM.
        
        Args:
            prompt: The prompt to complete
            model: Model to use (defaults to summary model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            response_schema: Optional JSON schema for structured output
            
        Returns:
            Generated text or None if failed
        """
        if not prompt or not prompt.strip():
            logger.warning("prompt is empty")
            return None
        
        if not model:
            model = self.config.get(ConfigKeys.LLM_SUMMARY_MODEL, default="gpt-3.5-turbo")
            
        try:
            # Truncate prompt if too long
            max_chars = 30000
            if len(prompt) > max_chars:
                prompt = prompt[:max_chars]
                logger.debug(f"Truncated prompt to {max_chars} characters")
            
            # Determine model type for endpoint lookup
            model_type = "summary"  # default
            if model == self.config.get(ConfigKeys.LLM_ANALYSIS_MODEL):
                model_type = "analysis"
            
            # Convert to LiteLLM format
            litellm_model = self._get_litellm_model_name(model, model_type)
            
            # Use LiteLLM only
            if LITELLM_AVAILABLE:
                # Prepare messages for LiteLLM
                messages = [{"role": "user", "content": prompt}]
                
                # Prepare completion parameters
                completion_params = {
                    "model": litellm_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                
                # Add response format for structured output
                if response_schema:
                    completion_params["response_format"] = {"type": "json_object"}
                
                # Check if we should use custom endpoint
                custom_endpoint = self._get_model_endpoint(model_type)
                if custom_endpoint:
                    completion_params["api_base"] = custom_endpoint
                
                # Make completion request
                response = completion(**completion_params)
                
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        logger.debug(f"Generated completion with {litellm_model}: {len(content)} characters")
                        return content.strip()
                
                logger.error(f"LiteLLM completion failed for model {litellm_model}")
                return None
            else:
                logger.error("LiteLLM not available for text completion")
                return None
            
        except Exception as e:
            logger.error(f"Text completion failed with model {model}: {e}")
            return None
    
    
    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", person_generation: str = "dont_allow") -> Optional[bytes]:
        """Image generation not supported - Google API removed."""
        logger.warning("Image generation not supported - Google API has been removed")
        return None


# Global instance for easy access
enhanced_llm_client = EnhancedLLMClient()


def get_enhanced_llm_client() -> EnhancedLLMClient:
    """Get the global enhanced LLM client instance."""
    return enhanced_llm_client


def generate_topic_embedding(topic_name: str, task_type: str = "retrieval_query") -> Optional[List[float]]:
    """Generate embedding for a topic name (backward compatibility)."""
    return enhanced_llm_client.generate_embedding(topic_name, task_type=task_type)


def generate_content_embedding(title: str, content: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
    """Generate embedding for article content."""
    text_for_embedding = f"{title}\n\n{content}" if title and content else (title or content)
    return enhanced_llm_client.generate_embedding(text_for_embedding, task_type=task_type)


def create_summary(title: str, content: str, prompt_template: str) -> Optional[str]:
    """Create a summary of content using the provided prompt template and summary model."""
    if not content or len(content) < 100:
        logger.warning("Content too short for summary generation")
        return None
        
    if not enhanced_llm_client.is_available():
        logger.warning("Enhanced LLM client not available for summary generation")
        return None
        
    prompt = prompt_template.format(title=title, content=content)
    return enhanced_llm_client.create_summary_completion(prompt, max_tokens=250, temperature=0.3)