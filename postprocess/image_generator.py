#!/usr/bin/env python3
"""
Image Generation Module

This module handles AI-powered cover image generation for daily summaries.
It creates descriptive prompts and generates images using Google Imagen models,
with S3 upload capabilities for storage.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import date

# Import LLM and S3 functionality from shared library
try:
    from newsfrontier_lib import get_llm_client, get_s3_client, upload_cover_image
    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import required libraries: {e}")
    raise


class ImageGenerator:
    """
    Handles AI-powered cover image generation and upload.
    
    This class provides methods for generating descriptive prompts
    for cover images and creating images using Google Imagen models.
    Includes S3 upload capabilities for image storage.
    """
    
    def __init__(self, prompt_manager):
        """
        Initialize the image generator.
        
        Args:
            prompt_manager: Manager for retrieving prompts from database
        """
        self.prompt_manager = prompt_manager
        self.llm_client = get_llm_client()
        self.s3_client = get_s3_client()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Image generation settings from environment
        self.aspect_ratio = os.getenv('IMAGEGEN_ASPECT_RATIO', '16:9')
        self.person_generation = os.getenv('IMAGEGEN_PERSON_GENERATE', 'dont_allow')
        self.image_model = os.getenv('IMAGEGEN_MODEL', 'imagen-3.0-generate-002')
        
        self.logger.info(f"Initialized image generator with model: {self.image_model}")
        self.logger.info(f"Image settings - Aspect ratio: {self.aspect_ratio}, Person generation: {self.person_generation}")
    
    def generate_cover_image_prompt(self, summary_content: str) -> Optional[str]:
        """
        Generate AI image description for daily summary cover.
        
        Args:
            summary_content: Generated summary content to base image on
            
        Returns:
            Image description prompt or None if failed
            
        Raises:
            ValueError: If cover image generation prompt not available from database
            
        Features:
            - Uses cover image generation prompt from database (no default)
            - Formats prompt with summary content (limited to 2000 chars)
            - Generates descriptive prompt using summary model
            - Creates visually descriptive prompts for image generation
        """
        try:
            if not summary_content or not summary_content.strip():
                self.logger.warning("No summary content provided for cover image prompt generation")
                return None
            
            # Get cover image generation prompt from database - NO DEFAULT
            cover_prompt_template = self.prompt_manager.get_prompt('cover_image_generation')
            if not cover_prompt_template:
                raise ValueError("Cover image generation prompt not available from database")
            
            # Limit summary content for prompt formatting
            limited_summary = summary_content[:2000] if len(summary_content) > 2000 else summary_content
            
            # Format the prompt with summary content
            formatted_prompt = cover_prompt_template.format(summary_content=limited_summary)
            
            # Generate cover prompt using LLM summary model
            cover_prompt = self.llm_client.create_summary_completion(
                prompt=formatted_prompt,
                max_tokens=500,
                temperature=1.0  # Higher temperature for creative image descriptions
            )
            
            if cover_prompt:
                self.logger.info(f"Generated cover image prompt: {len(cover_prompt)} characters")
                return cover_prompt.strip()
            else:
                self.logger.warning("LLM returned empty cover image prompt")
                return None
                
        except ValueError:
            # Re-raise prompt errors to be handled by caller
            raise
        except Exception as e:
            self.logger.error(f"Error generating cover image prompt: {e}")
            return None
    
    def generate_and_upload_cover_image(self, cover_prompt: str, summary_date: date) -> Optional[str]:
        """
        Generate cover image and upload to S3 storage.
        
        Args:
            cover_prompt: AI-generated image description
            summary_date: Date for file naming
            
        Returns:
            S3 key for uploaded image or None if failed
            
        Features:
            - Uses Google Imagen model for image generation
            - Configurable aspect ratio and person generation settings
            - Uploads to S3 with date-based naming
            - Graceful error handling with detailed logging
        """
        try:
            if not cover_prompt or not cover_prompt.strip():
                self.logger.warning("No cover prompt provided for image generation")
                return None
            
            # Generate image using LLM client
            self.logger.info("Generating cover image using Imagen model...")
            
            image_bytes = self.llm_client.generate_image(
                prompt=cover_prompt,
                aspect_ratio=self.aspect_ratio,
                person_generation=self.person_generation
            )
            
            if not image_bytes:
                self.logger.error("Failed to generate cover image - LLM returned no data")
                return None
            
            self.logger.info(f"Generated cover image: {len(image_bytes)} bytes")
            
            # Check S3 availability
            if not self.s3_client.is_available():
                self.logger.warning("S3 client not available, skipping image upload")
                return None
            
            # Upload to S3
            self.logger.info("Uploading cover image to S3...")
            
            # Format date for file naming
            date_str = summary_date.strftime("%Y%m%d") if hasattr(summary_date, 'strftime') else str(summary_date).replace('-', '')
            
            s3_key = upload_cover_image(image_bytes, date_str)
            
            if s3_key:
                self.logger.info(f"Successfully uploaded cover image: {s3_key}")
                return s3_key
            else:
                self.logger.error("Failed to upload cover image to S3")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating/uploading cover image: {e}")
            return None
    
    def validate_image_prompt(self, prompt: str) -> bool:
        """
        Validate image generation prompt.
        
        Args:
            prompt: Image generation prompt to validate
            
        Returns:
            True if prompt meets criteria, False otherwise
            
        Validation Criteria:
            - Not empty or whitespace only
            - Reasonable length (10-2000 characters)
            - Contains descriptive language
        """
        if not prompt or not prompt.strip():
            return False
        
        # Check length bounds
        prompt_length = len(prompt.strip())
        if prompt_length < 10 or prompt_length > 2000:
            self.logger.warning(f"Image prompt length outside bounds: {prompt_length} chars")
            return False
        
        # Check for basic descriptive content
        # Look for adjectives, nouns, or visual terms
        visual_terms = [
            'color', 'bright', 'dark', 'light', 'image', 'visual', 'scene',
            'background', 'foreground', 'style', 'modern', 'abstract',
            'illustration', 'graphic', 'design', 'artistic'
        ]
        
        prompt_lower = prompt.lower()
        has_visual_terms = any(term in prompt_lower for term in visual_terms)
        
        if not has_visual_terms:
            self.logger.info("Image prompt may lack visual descriptive terms")
            # Don't fail validation, but log for monitoring
        
        return True
    
    def get_image_generation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about image generation capabilities.
        
        Returns:
            Dictionary with image generation statistics and settings
        """
        return {
            'llm_client_available': self.llm_client.is_available() if self.llm_client else False,
            's3_client_available': self.s3_client.is_available() if self.s3_client else False,
            'image_model': self.image_model,
            'aspect_ratio': self.aspect_ratio,
            'person_generation': self.person_generation,
            'prompt_available': self.prompt_manager.get_prompt('cover_image_generation') is not None
        }


class ImagePromptFormatter:
    """
    Utility class for formatting and enhancing image generation prompts.
    
    This class provides methods for improving image prompts with
    style guidelines and technical specifications.
    """
    
    def __init__(self):
        """Initialize prompt formatter."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def enhance_prompt_with_style(self, base_prompt: str, style_preferences: Optional[Dict[str, str]] = None) -> str:
        """
        Enhance image prompt with style guidelines.
        
        Args:
            base_prompt: Base image description
            style_preferences: Optional style preferences dict
            
        Returns:
            Enhanced prompt with style guidelines
            
        Style Enhancements:
            - Professional news imagery style
            - Modern, clean design aesthetics
            - Appropriate color schemes
            - News-appropriate visual elements
        """
        if not base_prompt:
            return base_prompt
        
        # Default style preferences for news imagery
        default_style = {
            'aesthetic': 'professional, clean, modern',
            'color_scheme': 'balanced colors, not overly saturated',
            'composition': 'well-balanced composition',
            'quality': 'high-quality, crisp, clear'
        }
        
        style_prefs = style_preferences or default_style
        
        # Build style suffix
        style_elements = []
        for key, value in style_prefs.items():
            if value:
                style_elements.append(value)
        
        if style_elements:
            style_suffix = f" Style: {', '.join(style_elements)}."
            enhanced_prompt = f"{base_prompt.rstrip('.')}. {style_suffix}"
        else:
            enhanced_prompt = base_prompt
        
        self.logger.debug(f"Enhanced prompt from {len(base_prompt)} to {len(enhanced_prompt)} characters")
        return enhanced_prompt
    
    def add_technical_specifications(self, prompt: str, aspect_ratio: str = "16:9") -> str:
        """
        Add technical specifications to image prompt.
        
        Args:
            prompt: Base image prompt
            aspect_ratio: Desired aspect ratio
            
        Returns:
            Prompt with technical specifications
        """
        if not prompt:
            return prompt
        
        # Add technical specifications
        tech_spec = f" Technical specifications: {aspect_ratio} aspect ratio, suitable for web display."
        
        enhanced_prompt = f"{prompt.rstrip('.')}. {tech_spec}"
        
        return enhanced_prompt
    
    def filter_inappropriate_content(self, prompt: str) -> str:
        """
        Filter potentially inappropriate content from image prompts.
        
        Args:
            prompt: Image prompt to filter
            
        Returns:
            Filtered prompt with inappropriate content removed
        """
        if not prompt:
            return prompt
        
        # List of terms to avoid in news imagery
        inappropriate_terms = [
            'violent', 'gore', 'explicit', 'graphic violence',
            'disturbing', 'shocking', 'traumatic'
        ]
        
        filtered_prompt = prompt
        for term in inappropriate_terms:
            if term.lower() in filtered_prompt.lower():
                self.logger.warning(f"Filtered inappropriate term from image prompt: {term}")
                # Replace with more appropriate alternatives
                filtered_prompt = filtered_prompt.replace(term, 'dramatic')
        
        return filtered_prompt