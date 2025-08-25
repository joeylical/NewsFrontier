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

# Keep fallback imports
import google.generativeai as genai
from google.genai import types
try:
    from google import genai as google_genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    google_genai = None
    GOOGLE_GENAI_AVAILABLE = False

from .config_service import get_config, ConfigKeys

logger = logging.getLogger(__name__)


class EnhancedLLMClient:
    """Enhanced LLM client with database configuration and LiteLLM support."""
    
    def __init__(self):
        """Initialize the Enhanced LLM client with database configuration."""
        self.config = get_config()
        self.genai_client = None
        self.google_genai_client = None
        
        # Initialize clients
        self._setup_clients()
        
        # Log model configuration
        self._log_configuration()
    
    def _setup_clients(self):
        """Initialize various LLM clients based on configuration."""
        try:
            # Setup LiteLLM if available
            if LITELLM_AVAILABLE:
                self._setup_litellm()
            
            # Setup Google clients as fallback
            self._setup_google_client()
            self._setup_google_genai_client()
            
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
    
    def _setup_google_client(self):
        """Initialize Google Generative AI client."""
        try:
            google_api_key = self.config.get_encrypted(ConfigKeys.GOOGLE_API_KEY, 
                                                      fallback_env=True)
            if google_api_key:
                genai.configure(api_key=google_api_key)
                self.genai_client = genai
                logger.info("Google Generative AI client initialized successfully")
            else:
                logger.warning("GOOGLE_API_KEY not available, Google AI features will be limited")
        except Exception as e:
            logger.error(f"Failed to initialize Google client: {e}")
            self.genai_client = None
    
    def _setup_google_genai_client(self):
        """Initialize Google Gen AI client for image generation."""
        try:
            if GOOGLE_GENAI_AVAILABLE:
                google_api_key = self.config.get_encrypted(ConfigKeys.GOOGLE_API_KEY, 
                                                          fallback_env=True)
                if google_api_key:
                    self.google_genai_client = google_genai.Client(api_key=google_api_key)
                    logger.info("Google Gen AI client initialized successfully for image generation")
                else:
                    logger.warning("Google API key missing, image generation will be disabled")
            else:
                logger.warning("Google Gen AI not available, image generation will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gen AI client: {e}")
            self.google_genai_client = None
    
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
        return (LITELLM_AVAILABLE or 
                self.genai_client is not None or 
                self.google_genai_client is not None)
    
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
            
            # Try LiteLLM first if available
            if LITELLM_AVAILABLE:
                try:
                    response = embedding(
                        model=f"vertex_ai/{embedding_model}",
                        input=[text[:2048]],  # Truncate if too long
                    )
                    if response and response.data and len(response.data) > 0:
                        return response.data[0].embedding
                except Exception as e:
                    logger.warning(f"LiteLLM embedding failed, falling back: {e}")
            
            # Fallback to Google client
            if self.genai_client:
                return self._generate_embedding_google(text, task_type)
            
            logger.error("No embedding client available")
            return None
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def _generate_embedding_google(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[List[float]]:
        """Generate embedding using Google Generative AI API."""
        try:
            # Truncate text if too long
            max_chars = 2048
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Truncated text to {max_chars} characters for embedding")
            
            embedding_model = self.config.get(ConfigKeys.LLM_EMBEDDING_MODEL, 
                                            default="models/text-embedding-004")
            embedding_dim = self.config.get(ConfigKeys.EMBEDDING_DIMENSION, default=768)
            
            result = self.genai_client.embed_content(
                model=embedding_model,
                content=text,
                output_dimensionality=embedding_dim,
                task_type=task_type
            )
            
            embedding = result['embedding']
            logger.debug(f"Generated Google embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Google embedding generation failed: {e}")
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
            
            # Try LiteLLM first if available
            if LITELLM_AVAILABLE:
                try:
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
                    
                except Exception as e:
                    logger.warning(f"LiteLLM completion failed, falling back to Google: {e}")
            
            # Fallback to Google client
            if self.genai_client:
                return self._create_completion_google(prompt, model, max_tokens, temperature, response_schema)
            
            logger.error("No completion client available")
            return None
            
        except Exception as e:
            logger.error(f"Text completion failed: {e}")
            return None
    
    def _create_completion_google(self, prompt: str, model: str, max_tokens: int, 
                                 temperature: float, response_schema: Optional[Dict[str, Any]]) -> Optional[str]:
        """Create completion using Google client."""
        try:
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type="application/json" if response_schema else None,
                response_schema=response_schema
            )
            
            model_instance = self.genai_client.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )
            
            response = model_instance.generate_content(prompt)
            
            # Check if response has candidates and is not blocked
            if response.candidates:
                candidate = response.candidates[0]
                # Check if candidate was blocked due to safety
                if candidate.finish_reason and candidate.finish_reason.name == 'SAFETY':
                    logger.warning("Response was blocked by safety filters")
                    return None
                
                # Try to get text from candidate parts
                if candidate.content and candidate.content.parts:
                    text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]
                    if text_parts:
                        completion = ''.join(text_parts).strip()
                        logger.debug(f"Generated Google completion: {len(completion)} characters")
                        return completion
            
            logger.warning("Response has no valid content")
            return None
            
        except Exception as e:
            logger.error(f"Google text completion failed: {e}")
            return None
    
    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", person_generation: str = "dont_allow") -> Optional[bytes]:
        """Generate image using configured image model."""
        if not self.google_genai_client:
            logger.warning("Google Gen AI client not available for image generation")
            return None
            
        if not prompt or not prompt.strip():
            logger.warning("Image prompt is empty")
            return None
            
        try:
            # Get image model from configuration
            image_model = self.config.get(ConfigKeys.LLM_IMAGE_MODEL, default='imagen-3.0-generate-002')
            
            # Create the configuration
            config = google_genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                include_rai_reason=True,
                safety_filter_level="BLOCK_LOW_AND_ABOVE"
            )
            
            # Generate image using the Google Gen AI client
            response = self.google_genai_client.models.generate_images(
                model=image_model,
                prompt=prompt,
                config=config
            )
            
            if response and hasattr(response, 'generated_images') and response.generated_images:
                # Get the first generated image
                generated_image = response.generated_images[0]
                
                # Extract image bytes
                if hasattr(generated_image, 'image') and generated_image.image:
                    # Get the image bytes (the exact attribute may vary)
                    image_data = generated_image.image
                    if hasattr(image_data, 'data'):
                        image_bytes = image_data.data
                    elif hasattr(image_data, '_bytes'):
                        image_bytes = image_data._bytes
                    elif hasattr(image_data, 'image_bytes'):
                        image_bytes = image_data.image_bytes
                    else:
                        # Try to access directly
                        image_bytes = bytes(image_data)
                    
                    logger.info(f"Generated image: {len(image_bytes)} bytes")
                    return image_bytes
                else:
                    logger.error("No image data found in response")
                    return None
            else:
                logger.error("No generated images in response")
                return None
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Image generation failed: {e}")
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