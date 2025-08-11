"""
LLM Client for NewsFrontier - Common LLM operations.

This module provides a unified interface for LLM operations used across
backend and postprocess services.
"""

import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
import tiktoken
import google.generativeai as genai
from google.genai import types
try:
    from google import genai as google_genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    google_genai = None
    GOOGLE_GENAI_AVAILABLE = False
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client for embedding generation and text completions."""
    
    def __init__(self):
        """Initialize the LLM client with environment configuration."""
        self.genai_client = None
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        self.embedding_dimensions = int(os.getenv('EMBEDDING_DIMENSION', 768))
        self.summary_model = os.getenv("LLM_MODEL_SUMMARY", "gemini-1.5-flash")
        self.analysis_model = os.getenv("LLM_MODEL_ANALYSIS", "gemini-1.5-pro")
        # Keep default_chat_model for backward compatibility
        self.default_chat_model = self.summary_model
        
        # Setup Google Gen AI client for image generation
        self.google_genai_client = None
        self._setup_google_client()
        self._setup_google_genai_client()
        
        # Log model configuration
        logger.info(f"LLM Model Configuration:")
        logger.info(f"  Summary Model: {self.summary_model}")
        logger.info(f"  Analysis Model: {self.analysis_model}")
        logger.info(f"  Embedding Model: {self.embedding_model}")
    
    def _setup_google_client(self):
        """Initialize Google Generative AI client with environment configuration."""
        try:
            if self.google_api_key:
                genai.configure(api_key=self.google_api_key)
                self.genai_client = genai
                logger.info("Google Generative AI client initialized successfully")
            else:
                logger.warning("GOOGLE_API_KEY not provided, AI features will be limited")
        except Exception as e:
            logger.error(f"Failed to initialize Google client: {e}")
            self.genai_client = None
    
    def _setup_google_genai_client(self):
        """Initialize Google Gen AI client for image generation."""
        try:
            if GOOGLE_GENAI_AVAILABLE and self.google_api_key:
                self.google_genai_client = google_genai.Client(api_key=self.google_api_key)
                logger.info("Google Gen AI client initialized successfully for image generation")
            else:
                logger.warning("Google Gen AI not available or API key missing, image generation will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gen AI client: {e}")
            self.google_genai_client = None
    
    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return self.genai_client is not None
    
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[List[float]]:
        """
        Generate embedding for given text.
        
        Args:
            text: Text to generate embedding for
            task_type: Task type for embedding (RETRIEVAL_QUERY, RETRIEVAL_DOCUMENT, SEMANTIC_SIMILARITY, etc.)
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            return None
            
        try:
            if self.genai_client:
                return self._generate_embedding_google(text, task_type)
            else:
                logger.warning("Google AI client not available for embedding generation")
                return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def _generate_embedding_google(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[List[float]]:
        """Generate embedding using Google Generative AI API."""
        try:
            # Truncate text if too long (Google has character limits)
            max_chars = 2048
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.debug(f"Truncated text to {max_chars} characters for embedding")
            
            result = self.genai_client.embed_content(
                model=self.embedding_model,
                content=text,
                output_dimensionality=self.embedding_dimensions,
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
        return self.create_completion(
            prompt=prompt,
            model=self.summary_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def create_analysis_completion(self, 
                                  prompt: str, 
                                  max_tokens: int = 500,
                                  temperature: float = 0.3,
                                  response_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create text completion using the analysis model for cluster detection and daily summaries."""
        return self.create_completion(
            prompt=prompt,
            model=self.analysis_model,
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
        Create text completion using LLM.
        
        Args:
            prompt: The prompt to complete
            model: Model to use (defaults to configured model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            response_schema: Optional JSON schema for structured output
            
        Returns:
            Generated text or None if failed
        """
        if not self.genai_client:
            logger.warning("Google AI client not available for completion")
            return None
            
        if not prompt or not prompt.strip():
            logger.warning("prompt is empty")
            return None
            
        try:
            # Truncate prompt if too long
            max_chars = 30000
            if len(prompt) > max_chars:
                prompt = prompt[:max_chars]
                logger.debug(f"Truncated prompt to {max_chars} characters")
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type="application/json" if response_schema else None,
                response_schema=response_schema
            )
            
            model_instance = self.genai_client.GenerativeModel(
                model_name=model or self.default_chat_model,
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
                        logger.debug(f"Generated completion: {len(completion)} characters")
                        return completion
            
            logger.warning("Response has no valid content")
            logger.warning(response)
            return None
            
        except Exception as e:
            logger.error(f"Text completion failed: {e}")
            return None
    
    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", person_generation: str = "dont_allow") -> Optional[bytes]:
        """Generate image using Google's Imagen model."""
        if not self.google_genai_client:
            logger.warning("Google Gen AI client not available for image generation")
            return None
            
        if not prompt or not prompt.strip():
            logger.warning("Image prompt is empty")
            return None
            
        try:
            # Get model and configuration from environment
            model_name = os.getenv('IMAGEGEN_MODEL', 'imagen-3.0-generate-002')
            
            # Create the configuration
            config = google_genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                include_rai_reason=True,
                safety_filter_level="BLOCK_LOW_AND_ABOVE"
            )
            
            # Generate image using the Google Gen AI client
            response = self.google_genai_client.models.generate_images(
                model=model_name,
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
llm_client = LLMClient()


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    return llm_client


def generate_topic_embedding(topic_name: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[List[float]]:
    """Generate embedding for a topic name (backward compatibility)."""
    return llm_client.generate_embedding(topic_name, task_type=task_type)


def generate_content_embedding(title: str, content: str, task_type: str = "RETRIEVAL_DOCUMENT") -> Optional[List[float]]:
    """Generate embedding for article content."""
    text_for_embedding = f"{title}\n\n{content}" if title and content else (title or content)
    return llm_client.generate_embedding(text_for_embedding, task_type=task_type)


def create_summary(title: str, content: str, prompt_template: str) -> Optional[str]:
    """Create a summary of content using the provided prompt template and summary model."""
    if not content or len(content) < 100:
        logger.warning("Content too short for summary generation")
        return None
        
    if not llm_client.is_available():
        logger.warning("LLM client not available for summary generation")
        return None
        
    prompt = prompt_template.format(title=title, content=content)
    return llm_client.create_summary_completion(prompt, max_tokens=250, temperature=0.3)
