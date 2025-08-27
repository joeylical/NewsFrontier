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
# Google imports removed - this client is deprecated
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class LLMClient:
    """Deprecated LLM client - please use EnhancedLLMClient instead."""
    
    def __init__(self):
        """Initialize the deprecated LLM client."""
        logger.warning("LLMClient is deprecated, please use get_enhanced_llm_client() instead")
        
        # Log deprecation warning
        logger.warning("All Google Generative AI functionality has been removed")
        logger.warning("This client will return None for all operations")
    
    
    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return False  # Always return False since Google API is removed
    
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> Optional[List[float]]:
        """Deprecated method - returns None."""
        logger.warning("generate_embedding is deprecated, use get_enhanced_llm_client() instead")
        return None
    
    
    def create_summary_completion(self, 
                                 prompt: str, 
                                 max_tokens: int = 250,
                                 temperature: float = 0.3) -> Optional[str]:
        """Deprecated method - returns None."""
        logger.warning("create_summary_completion is deprecated, use get_enhanced_llm_client() instead")
        return None
    
    def create_analysis_completion(self, 
                                  prompt: str, 
                                  max_tokens: int = 500,
                                  temperature: float = 0.3,
                                  response_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Deprecated method - returns None."""
        logger.warning("create_analysis_completion is deprecated, use get_enhanced_llm_client() instead")
        return None

    def create_completion(self, 
                         prompt: str, 
                         model: Optional[str] = None,
                         max_tokens: int = 250,
                         temperature: float = 0.3,
                         response_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Deprecated method - returns None."""
        logger.warning("create_completion is deprecated, use get_enhanced_llm_client() instead")
        return None
    
    def generate_image(self, prompt: str, aspect_ratio: str = "16:9", person_generation: str = "dont_allow") -> Optional[bytes]:
        """Deprecated method - returns None."""
        logger.warning("generate_image is deprecated, use get_enhanced_llm_client() instead")
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
