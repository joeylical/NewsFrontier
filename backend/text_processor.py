"""
Text processing utilities for NewsFrontier backend.
Handles sentence tokenization and HTML anchor insertion.
"""

import random
import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)





def generate_paragraph_anchor_id() -> str:
    """Generate a random paragraph anchor ID in format P-xxxxx where xxxxx is a random number."""
    random_num = random.randint(10000, 99999)
    return f"P-{random_num}"


def process_text_with_anchors(text: Optional[str]) -> Optional[str]:
    """
    Process text by adding HTML anchors for <p> tags.
    
    Rules:
    - Check for <p> tags in content
    - When multiple <p> tags found, create anchor "P-xxxx" for each <p> tag position
    
    Args:
        text: The input text to process
        
    Returns:
        Processed text with HTML anchors, or None if input is None/empty
    """
    if not text or not text.strip():
        return text
    
    try:
        # Find all <p> tags in the content
        p_tag_pattern = r'<p[^>]*>'
        p_matches = list(re.finditer(p_tag_pattern, text, re.IGNORECASE))
        
        # Only process if there are multiple <p> tags
        if len(p_matches) <= 1:
            return text
        
        # Process text by inserting anchors before each <p> tag
        result = text
        offset = 0
        
        for match in p_matches:
            anchor_id = generate_paragraph_anchor_id()
            anchor_tag = f'<a id="{anchor_id}"></a>'
            
            # Insert anchor before the <p> tag
            insert_pos = match.start() + offset
            result = result[:insert_pos] + anchor_tag + result[insert_pos:]
            offset += len(anchor_tag)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing text with anchors: {str(e)}")
        # Return original text if processing fails
        return text


def extract_paragraphs_with_anchors(text: Optional[str]) -> List[dict]:
    """
    Extract paragraphs from text and return list with anchor information.
    Works with content that has <p> tags.
    
    Args:
        text: The input text to process
        
    Returns:
        List of dictionaries with 'anchor_id', 'text', and 'position' keys
    """
    if not text or not text.strip():
        return []
    
    try:
        # Find all <p> tags and their content
        p_tag_pattern = r'<p[^>]*>(.*?)</p>'
        p_matches = re.findall(p_tag_pattern, text, re.DOTALL | re.IGNORECASE)
        
        # Only process if there are multiple <p> tags
        if len(p_matches) <= 1:
            return []
        
        result = []
        for i, paragraph_content in enumerate(p_matches):
            paragraph_content = paragraph_content.strip()
            if paragraph_content:
                anchor_id = generate_paragraph_anchor_id()
                result.append({
                    'anchor_id': anchor_id,
                    'text': paragraph_content,
                    'position': i + 1
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting paragraphs with anchors: {str(e)}")
        return []


def extract_anchor_ids_from_text(text: Optional[str]) -> List[str]:
    """
    Extract all anchor IDs from text (both SEN-xxxxx and P-xxxxx formats).
    
    Args:
        text: Text containing anchor tags
        
    Returns:
        List of anchor IDs found in the text
    """
    if not text:
        return []
    
    import re
    pattern = r'<a\s+id="((?:SEN|P)-\d+)"[^>]*>'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    
    return matches


def validate_anchor_format(anchor_id: str) -> bool:
    """
    Validate if anchor ID follows the SEN-xxxxx or P-xxxxx format.
    
    Args:
        anchor_id: The anchor ID to validate
        
    Returns:
        True if format is valid, False otherwise
    """
    import re
    pattern = r'^(SEN|P)-\d{5}$'
    return bool(re.match(pattern, anchor_id))


def get_text_processing_info(text: Optional[str]) -> dict:
    """
    Get information about how text would be processed.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with processing information
    """
    if not text or not text.strip():
        return {"strategy": "none", "length": 0, "reason": "empty_text"}
    
    text_length = len(text.strip())
    
    try:
        # Find all <p> tags in the content
        p_tag_pattern = r'<p[^>]*>'
        p_matches = list(re.finditer(p_tag_pattern, text, re.IGNORECASE))
        
        if len(p_matches) <= 1:
            return {
                "strategy": "none", 
                "length": text_length, 
                "p_tag_count": len(p_matches),
                "reason": "single_or_no_p_tags"
            }
        else:
            return {
                "strategy": "p_tags", 
                "length": text_length, 
                "p_tag_count": len(p_matches),
                "reason": "multiple_p_tags"
            }
    except Exception as e:
        return {
            "strategy": "none", 
            "length": text_length, 
            "reason": f"error: {str(e)}"
        }