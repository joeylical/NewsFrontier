#!/usr/bin/env python3
"""
Article Summary Generation Module

This module handles AI-powered article summarization using configurable prompts
from the database. It generates concise, bullet-point summaries with internal
anchor links for navigation.
"""

import logging
from typing import Dict, Any, Optional

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import create_summary
    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import LLM library: {e}")
    raise


class SummaryGenerator:
    """
    Handles article summary generation using AI models.
    
    This class encapsulates all logic related to creating AI-powered summaries
    of news articles, including prompt management and error handling.
    """
    
    def __init__(self, prompt_manager):
        """
        Initialize the summary generator.
        
        Args:
            prompt_manager: Manager for retrieving prompts from database
        """
        self.prompt_manager = prompt_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_article_summary(self, article: Dict[str, Any]) -> Optional[str]:
        """
        Create AI-powered summary of article content.
        
        Args:
            article: Dictionary containing article data with keys:
                - title: Article title
                - content: Article content (HTML)
                
        Returns:
            HTML-formatted bullet-point summary or None if failed
            
        Raises:
            ValueError: If summary creation prompt not available from database
            
        Features:
            - Generates 3-7 concise bullet-point sentences
            - Includes internal anchor links for navigation
            - Preserves factual accuracy and key information
            - Uses configurable prompt from database (no default fallback)
        """
        try:
            content = article.get('content', '')
            title = article.get('title', '')
            
            # Validate content length
            if not content or len(content) < 100:
                self.logger.info(f"Article content too short for summarization: {len(content)} chars")
                return None
                
            # Get prompt from database - NO DEFAULT FALLBACK
            prompt_template = self.prompt_manager.get_prompt('summary_creation')
            if not prompt_template:
                raise ValueError("Summary creation prompt not available from database")
                
            # Generate summary using shared LLM library
            summary = create_summary(title, content, prompt_template)
            
            if summary:
                self.logger.info(f"Created AI summary: {len(summary)} characters")
                return summary
            else:
                self.logger.warning("LLM returned empty summary")
                return None
                
        except ValueError:
            # Re-raise prompt errors to be handled by caller
            raise
        except Exception as e:
            self.logger.error(f"Error creating summary: {e}")
            return None
    
    def validate_summary_content(self, summary: str) -> bool:
        """
        Validate generated summary content.
        
        Args:
            summary: Generated summary text
            
        Returns:
            True if summary meets quality criteria, False otherwise
            
        Validation Criteria:
            - Contains HTML list tags (<ul>, <ol>, <li>)
            - Has reasonable length (50-2000 characters)
            - Contains meaningful content (not just whitespace)
        """
        if not summary or not summary.strip():
            return False
            
        # Check length bounds
        if len(summary.strip()) < 50 or len(summary.strip()) > 2000:
            self.logger.warning(f"Summary length outside bounds: {len(summary)} chars")
            return False
            
        # Check for HTML list structure
        if not any(tag in summary for tag in ['<li>', '<ul>', '<ol>']):
            self.logger.warning("Summary missing expected HTML list structure")
            return False
            
        return True
    
    def get_summary_stats(self, summary: str) -> Dict[str, Any]:
        """
        Generate statistics about the summary content.
        
        Args:
            summary: Generated summary text
            
        Returns:
            Dictionary with summary statistics:
                - character_count: Total characters
                - word_count: Approximate word count
                - bullet_points: Number of list items
                - anchor_links: Number of internal anchor links
        """
        if not summary:
            return {
                'character_count': 0,
                'word_count': 0,
                'bullet_points': 0,
                'anchor_links': 0
            }
        
        # Count bullet points (list items)
        bullet_points = summary.count('<li>')
        
        # Count internal anchor links
        anchor_links = summary.count('<a href="#')
        
        # Estimate word count (rough approximation)
        # Remove HTML tags for word counting
        import re
        text_content = re.sub(r'<[^>]+>', '', summary)
        word_count = len(text_content.split())
        
        return {
            'character_count': len(summary),
            'word_count': word_count,
            'bullet_points': bullet_points,
            'anchor_links': anchor_links
        }


class PromptManager:
    """
    Manages AI prompts retrieved from database.
    
    This class handles prompt caching and retrieval to avoid
    repeated database calls during processing.
    """
    
    def __init__(self):
        """Initialize prompt manager with empty cache."""
        self.prompt_cache = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def set_prompts(self, prompts_dict: Dict[str, str]):
        """
        Set prompts from database.
        
        Args:
            prompts_dict: Dictionary of prompt types to prompt text
        """
        self.prompt_cache = prompts_dict.copy()
        self.logger.info(f"Loaded {len(prompts_dict)} prompts into cache")
    
    def get_prompt(self, prompt_type: str) -> Optional[str]:
        """
        Get prompt by type.
        
        Args:
            prompt_type: Type of prompt to retrieve (e.g., 'summary_creation')
            
        Returns:
            Prompt text or None if not available
        """
        prompt = self.prompt_cache.get(prompt_type)
        if not prompt:
            self.logger.error(f"Prompt '{prompt_type}' not found in cache")
        return prompt
    
    def clear_cache(self):
        """Clear prompt cache."""
        self.prompt_cache.clear()
        self.logger.info("Cleared prompt cache")