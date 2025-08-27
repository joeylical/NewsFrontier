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
            
            # Set environment variables for LiteLLM
            if google_api_key:
                os.environ["GOOGLE_API_KEY"] = google_api_key
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key
            
            # Configure LiteLLM settings
            litellm.drop_params = True  # Drop unsupported parameters
            litellm.set_verbose = False  # Reduce verbosity
            
            logger.info("LiteLLM configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup LiteLLM: {e}")
    
    
    def _log_configuration(self):
        """Log current model configuration."""
        summary_model = self.config.get(ConfigKeys.LLM_SUMMARY_MODEL, default="gemini-1.5-flash")
        analysis_model = self.config.get(ConfigKeys.LLM_ANALYSIS_MODEL, default="gemini-1.5-pro")
        embedding_model = self.config.get(ConfigKeys.LLM_EMBEDDING_MODEL, default="text-embedding-004")
        image_model = self.config.get(ConfigKeys.LLM_IMAGE_MODEL, default="imagen-3.0-generate-002")
        
        logger.info(f"Enhanced LLM Model Configuration:")
        logger.info(f"  Summary Model: {summary_model}")
        logger.info(f"  Analysis Model: {analysis_model}")
        logger.info(f"  Embedding Model: {embedding_model}")
        logger.info(f"  Image Model: {image_model}")
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
                                            default="text-embedding-004")
            
            # Use LiteLLM only
            if LITELLM_AVAILABLE:
                response = embedding(
                    model=f"vertex_ai/{embedding_model}",
                    input=[text[:2048]],  # Truncate if too long
                )
                if response and response.data and len(response.data) > 0:
                    return response.data[0].embedding
            else:
                logger.error("LiteLLM not available for embedding generation")
                return None
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
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
            model = self.config.get(ConfigKeys.LLM_SUMMARY_MODEL, default="gemini-1.5-flash")
            
        try:
            # Truncate prompt if too long
            max_chars = 30000
            if len(prompt) > max_chars:
                prompt = prompt[:max_chars]
                logger.debug(f"Truncated prompt to {max_chars} characters")
            
            # Use LiteLLM only
            if LITELLM_AVAILABLE:
                # Prepare messages for LiteLLM
                messages = [{"role": "user", "content": prompt}]
                
                # Make completion request
                response = completion(
                    model=f"vertex_ai/{model}",
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"} if response_schema else None
                )
                
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        logger.debug(f"Generated LiteLLM completion: {len(content)} characters")
                        return content.strip()
                
                logger.error("LiteLLM completion failed")
                return None
            else:
                logger.error("LiteLLM not available for text completion")
                return None
            
        except Exception as e:
            logger.error(f"Text completion failed: {e}")
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