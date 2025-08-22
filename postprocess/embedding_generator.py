#!/usr/bin/env python3
"""
Embedding Generation Module

This module handles vector embedding generation for articles, topics, and events
using Google Gemini embedding models. It provides semantic similarity capabilities
for content matching and clustering.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.metrics.pairwise import cosine_similarity

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import generate_content_embedding
    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import LLM library: {e}")
    raise


class EmbeddingGenerator:
    """
    Handles vector embedding generation for text content.
    
    This class provides methods for generating embeddings from article titles,
    summaries, and other text content using Google Gemini embedding models.
    Supports 768-dimensional embeddings for semantic similarity calculations.
    """
    
    def __init__(self, embedding_model: str = "gemini-embedding-001"):
        """
        Initialize the embedding generator.
        
        Args:
            embedding_model: Name of the embedding model to use
        """
        self.embedding_model = embedding_model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized embedding generator with model: {embedding_model}")
    
    def generate_title_embedding(self, article: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate vector embedding for article title.
        
        Args:
            article: Dictionary containing article data with 'title' key
            
        Returns:
            768-dimensional embedding vector or None if failed
            
        Features:
            - Uses Google Gemini embedding model
            - Optimized for semantic title matching
            - Returns consistent 768-dimensional vectors
        """
        try:
            title = article.get('title', '')
            
            if not title or not title.strip():
                self.logger.warning("Article has no title for embedding generation")
                return None
                
            # Generate embedding using shared LLM library
            embedding = generate_content_embedding(title, "")
            
            if embedding:
                self.logger.debug(f"Generated title embedding: {len(embedding)} dimensions")
                return embedding
            else:
                self.logger.warning("Failed to generate title embedding - LLM returned None")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating title embedding: {e}")
            return None
    
    def generate_summary_embedding(self, summary: str) -> Optional[List[float]]:
        """
        Generate vector embedding for article summary.
        
        Args:
            summary: AI-generated summary text
            
        Returns:
            768-dimensional embedding vector or None if failed
            
        Features:
            - Uses same embedding model as titles for consistency
            - Enables dual embedding comparison for improved accuracy
            - Handles HTML content in summaries
        """
        try:
            if not summary or not summary.strip():
                self.logger.warning("No summary provided for embedding generation")
                return None
                
            # Generate embedding using shared LLM library
            embedding = generate_content_embedding(summary, "")
            
            if embedding:
                self.logger.debug(f"Generated summary embedding: {len(embedding)} dimensions")
                return embedding
            else:
                self.logger.warning("Failed to generate summary embedding - LLM returned None")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating summary embedding: {e}")
            return None
    
    def generate_topic_embedding(self, topic_name: str) -> Optional[List[float]]:
        """
        Generate vector embedding for topic name.
        
        Args:
            topic_name: Name of the topic
            
        Returns:
            768-dimensional embedding vector or None if failed
            
        Features:
            - Generates embeddings for user-defined topics
            - Used for semantic topic matching against articles
            - Consistent with article embedding generation
        """
        try:
            if not topic_name or not topic_name.strip():
                self.logger.warning("No topic name provided for embedding generation")
                return None
                
            # Generate embedding using shared LLM library
            embedding = generate_content_embedding(topic_name, "")
            
            if embedding:
                self.logger.info(f"Generated topic embedding for '{topic_name}': {len(embedding)} dimensions")
                return embedding
            else:
                self.logger.warning(f"Failed to generate topic embedding for '{topic_name}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating topic embedding for '{topic_name}': {e}")
            return None
    
    def generate_event_embedding(self, event_description: str) -> Optional[List[float]]:
        """
        Generate vector embedding for event description.
        
        Args:
            event_description: Description of the event cluster
            
        Returns:
            768-dimensional embedding vector or None if failed
            
        Features:
            - Generates embeddings for event clusters
            - Used for event similarity calculations
            - Supports clustering algorithm requirements
        """
        try:
            if not event_description or not event_description.strip():
                self.logger.warning("No event description provided for embedding generation")
                return None
                
            # Generate embedding using shared LLM library
            embedding = generate_content_embedding(event_description, "")
            
            if embedding:
                self.logger.debug(f"Generated event embedding: {len(embedding)} dimensions")
                return embedding
            else:
                self.logger.warning("Failed to generate event embedding")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating event embedding: {e}")
            return None
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate embedding vector format and dimensions.
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if embedding is valid, False otherwise
            
        Validation Criteria:
            - Must be a list of numbers
            - Must have exactly 768 dimensions (Google Gemini standard)
            - Must contain finite values (no NaN or infinity)
        """
        if not embedding:
            return False
            
        # Check type and length
        if not isinstance(embedding, list) or len(embedding) != 768:
            self.logger.error(f"Invalid embedding dimensions: expected 768, got {len(embedding) if isinstance(embedding, list) else 'non-list'}")
            return False
            
        # Check for finite values
        try:
            np_embedding = np.array(embedding)
            if not np.all(np.isfinite(np_embedding)):
                self.logger.error("Embedding contains non-finite values (NaN or infinity)")
                return False
        except Exception as e:
            self.logger.error(f"Error validating embedding values: {e}")
            return False
            
        return True


class SimilarityCalculator:
    """
    Handles similarity calculations between embedding vectors.
    
    This class provides methods for calculating cosine similarity
    between embeddings and finding similar content based on
    configurable thresholds.
    """
    
    def __init__(self, default_threshold: float = 0.3):
        """
        Initialize similarity calculator.
        
        Args:
            default_threshold: Default similarity threshold for matching
        """
        self.default_threshold = default_threshold
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
            
        Raises:
            ValueError: If embeddings have different dimensions
        """
        try:
            if len(embedding1) != len(embedding2):
                raise ValueError(f"Embedding dimension mismatch: {len(embedding1)} vs {len(embedding2)}")
            
            # Convert to numpy arrays and reshape for sklearn
            emb1 = np.array(embedding1).reshape(1, -1)
            emb2 = np.array(embedding2).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(emb1, emb2)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def find_similar_topics(self, 
                          article_title_embedding: Optional[List[float]] = None,
                          article_summary_embedding: Optional[List[float]] = None,
                          topics: List[Dict[str, Any]] = None,
                          threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Find topics similar to article using dual embedding comparison.
        
        Args:
            article_title_embedding: Article title embedding vector
            article_summary_embedding: Article summary embedding vector
            topics: List of topic dictionaries with 'topic_vector' key
            threshold: Similarity threshold override
            
        Returns:
            List of similar topics sorted by relevance score
            
        Features:
            - Dual embedding strategy: compares both title and summary embeddings
            - Maximum similarity: uses higher of title/summary similarity scores
            - Threshold filtering: configurable similarity threshold
            - Sorted results: returns topics ordered by relevance
        """
        if not topics:
            return []
            
        threshold = threshold or self.default_threshold
        similar_topics = []
        
        # Validate at least one embedding is provided
        if not article_title_embedding and not article_summary_embedding:
            self.logger.warning("No embeddings provided for topic similarity comparison")
            return []
        
        for topic in topics:
            topic_vector = topic.get('topic_vector')
            if not topic_vector:
                continue
            
            # Calculate similarities for available embeddings
            title_similarity = None
            summary_similarity = None
            
            if article_title_embedding:
                title_similarity = self.calculate_cosine_similarity(
                    article_title_embedding, topic_vector
                )
            
            if article_summary_embedding:
                summary_similarity = self.calculate_cosine_similarity(
                    article_summary_embedding, topic_vector
                )
            
            # Use the maximum similarity as final similarity
            final_similarity = 0.0
            similarity_source = "none"
            
            if title_similarity is not None and summary_similarity is not None:
                if title_similarity > summary_similarity:
                    final_similarity = title_similarity
                    similarity_source = "title"
                else:
                    final_similarity = summary_similarity
                    similarity_source = "summary"
            elif title_similarity is not None:
                final_similarity = title_similarity
                similarity_source = "title"
            elif summary_similarity is not None:
                final_similarity = summary_similarity
                similarity_source = "summary"
            else:
                continue  # No valid similarities calculated
            
            # Check threshold
            if final_similarity >= threshold:
                topic_copy = topic.copy()
                topic_copy['similarity_score'] = float(final_similarity)
                topic_copy['similarity_source'] = similarity_source
                if title_similarity is not None:
                    topic_copy['title_similarity'] = float(title_similarity)
                if summary_similarity is not None:
                    topic_copy['summary_similarity'] = float(summary_similarity)
                similar_topics.append(topic_copy)
        
        # Sort by similarity score descending
        similar_topics.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        self.logger.info(f"Found {len(similar_topics)} similar topics above threshold {threshold}")
        return similar_topics
    
    def find_similar_events(self,
                          article_title_embedding: Optional[List[float]] = None,
                          article_summary_embedding: Optional[List[float]] = None,
                          events: List[Dict[str, Any]] = None,
                          threshold: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        Find most similar event cluster using embedding comparison.
        
        Args:
            article_title_embedding: Article title embedding vector
            article_summary_embedding: Article summary embedding vector
            events: List of event dictionaries with 'event_embedding' key
            threshold: Similarity threshold for event matching
            
        Returns:
            Most similar event above threshold or None
            
        Features:
            - Uses dual embedding comparison like topic matching
            - Returns best match above threshold
            - Used in two-stage clustering algorithm
        """
        if not events or (not article_title_embedding and not article_summary_embedding):
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for event in events:
            event_embedding = event.get('event_embedding')
            if not event_embedding:
                continue
            
            # Calculate similarities
            title_similarity = 0.0
            summary_similarity = 0.0
            
            if article_title_embedding:
                title_similarity = self.calculate_cosine_similarity(
                    article_title_embedding, event_embedding
                )
            
            if article_summary_embedding:
                summary_similarity = self.calculate_cosine_similarity(
                    article_summary_embedding, event_embedding
                )
            
            # Use maximum similarity
            max_similarity = max(title_similarity, summary_similarity)
            
            if max_similarity > best_similarity:
                best_similarity = max_similarity
                best_match = event
        
        # Return match if above threshold
        if best_match and best_similarity >= threshold:
            best_match['similarity_score'] = best_similarity
            self.logger.info(f"Found similar event with similarity {best_similarity:.3f}")
            return best_match
        
        self.logger.info(f"No similar events found above threshold {threshold} (best: {best_similarity:.3f})")
        return None