"""
Text processing utilities for NewsFrontier.

This module provides utilities for cleaning HTML, text processing,
and preparing content for LLM processing.
"""

import re
import html
from typing import Optional
from bs4 import BeautifulSoup


def clean_html_text(html_content: str) -> str:
    """
    Remove HTML tags and clean text content.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Clean text with HTML tags removed and proper spacing
    """
    if not html_content:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text and clean it
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    return text


def clean_text_for_llm(text: str) -> str:
    """
    Clean and prepare text for LLM processing.
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text suitable for LLM processing
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    # Clean up common artifacts
    text = re.sub(r'\[Read more.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Continue reading.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Click here.*?(?=\.|$)', '', text, flags=re.IGNORECASE)
    
    # Remove URLs (optional)
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    return text.strip()


def extract_main_content(html_content: str) -> str:
    """
    Extract main content from HTML, trying to identify article content.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Main content text
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
        element.decompose()
    
    # Try to find main content areas
    content_selectors = [
        'article',
        '[class*="content"]',
        '[class*="article"]',
        '[class*="post"]',
        '[id*="content"]',
        '[id*="article"]',
        'main',
        '.entry-content',
        '.post-content',
        '.article-body'
    ]
    
    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content and len(main_content.get_text().strip()) > 100:
            break
    
    # Fallback to body if no specific content area found
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Clean the extracted content
    text = main_content.get_text()
    
    # Clean up whitespace and formatting
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    return clean_text_for_llm(text)


def prepare_text_for_processing(content: str, title: str = "") -> str:
    """
    Prepare text content for AI processing by cleaning and formatting.
    
    Args:
        content: Raw content (may contain HTML)
        title: Article title (optional)
        
    Returns:
        Clean text ready for AI processing
    """
    # Check if content appears to be HTML
    if '<' in content and '>' in content:
        clean_content = extract_main_content(content)
    else:
        clean_content = clean_text_for_llm(content)
    
    # Combine with title if provided
    if title and title.strip():
        clean_title = clean_text_for_llm(title)
        if clean_title and clean_title not in clean_content[:200]:
            return f"{clean_title}\n\n{clean_content}"
    
    return clean_content