#!/usr/bin/env python3
"""
Event Clustering Service Module

This module handles intelligent event clustering using a two-stage approach:
1. Embedding similarity comparison for fast clustering
2. LLM-based contextual analysis for complex decisions

It creates and manages event clusters for organizing related news articles.
"""

import json
import logging
from typing import Dict, Any, Optional, List

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import get_llm_client
    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import LLM library: {e}")
    raise


class ClusteringService:
    """
    Handles intelligent event clustering for news articles.
    
    This service uses a sophisticated two-stage clustering approach:
    1. Fast embedding-based similarity for direct matches
    2. LLM-based contextual analysis for complex clustering decisions
    
    Features:
    - Configurable similarity thresholds
    - Context-aware clustering decisions
    - Event cluster creation and management
    - Article-event association management
    """
    
    def __init__(self, prompt_manager, similarity_calculator, backend_client, cluster_threshold: float = 0.7):
        """
        Initialize the clustering service.
        
        Args:
            prompt_manager: Manager for retrieving prompts from database
            similarity_calculator: Calculator for embedding similarity
            backend_client: Client for backend API communication
            cluster_threshold: Threshold for embedding similarity clustering
        """
        self.prompt_manager = prompt_manager
        self.similarity_calculator = similarity_calculator
        self.backend_client = backend_client
        self.cluster_threshold = cluster_threshold
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized clustering service with threshold: {cluster_threshold}")
    
    def detect_or_create_cluster(self,
                               user_id: int,
                               topic_id: int,
                               topic_name: str,
                               article_title: str,
                               article_summary: str,
                               title_embedding: List[float],
                               summary_embedding: Optional[List[float]] = None) -> Optional[Dict[str, Any]]:
        """
        Advanced two-stage clustering algorithm.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID  
            topic_name: Topic name for context
            article_title: Article title
            article_summary: AI-generated article summary
            title_embedding: Article title embedding
            summary_embedding: Article summary embedding (optional)
            
        Returns:
            Event cluster dictionary with relevance_score or None if failed
            
        Two-Stage Process:
        1. Embedding Distance Check: Direct cosine similarity with existing events
        2. LLM Analysis: If no embedding match, uses AI for contextual decisions
        """
        try:
            # Stage 1: Get existing events for this user and topic
            existing_events = self._get_existing_events(user_id, topic_id)
            
            # Stage 1: Embedding-based similarity check
            if existing_events and (title_embedding or summary_embedding):
                similar_event = self._find_similar_event_by_embedding(
                    title_embedding, summary_embedding, existing_events
                )
                
                if similar_event:
                    self.logger.info(f"Direct embedding match found: event {similar_event['id']} "
                                   f"with similarity {similar_event['similarity_score']:.3f}")
                    return similar_event
                else:
                    self.logger.info(f"No embedding match >= threshold {self.cluster_threshold}, "
                                   "proceeding to LLM analysis")
            
            # Stage 2: LLM-based contextual clustering
            cluster_result = self._analyze_clustering_with_llm(
                user_id, topic_id, topic_name, article_title, 
                article_summary, existing_events
            )
            
            return cluster_result
            
        except Exception as e:
            self.logger.error(f"Error in detect_or_create_cluster: {e}")
            return None
    
    def _get_existing_events(self, user_id: int, topic_id: int) -> List[Dict[str, Any]]:
        """
        Get existing event clusters for specific user and topic.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID
            
        Returns:
            List of event cluster dictionaries
        """
        try:
            events = self.backend_client.get_events_for_topic(user_id, topic_id)
            self.logger.debug(f"Retrieved {len(events)} existing events for user {user_id}, topic {topic_id}")
            return events
        except Exception as e:
            self.logger.error(f"Error retrieving existing events: {e}")
            return []
    
    def _find_similar_event_by_embedding(self,
                                       title_embedding: Optional[List[float]],
                                       summary_embedding: Optional[List[float]],
                                       events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find most similar event using embedding comparison.
        
        Args:
            title_embedding: Article title embedding
            summary_embedding: Article summary embedding
            events: List of existing events with embeddings
            
        Returns:
            Most similar event above threshold or None
        """
        try:
            similar_event = self.similarity_calculator.find_similar_events(
                article_title_embedding=title_embedding,
                article_summary_embedding=summary_embedding,
                events=events,
                threshold=self.cluster_threshold
            )
            
            return similar_event
            
        except Exception as e:
            self.logger.error(f"Error finding similar events by embedding: {e}")
            return None
    
    def _analyze_clustering_with_llm(self,
                                   user_id: int,
                                   topic_id: int,
                                   topic_name: str,
                                   article_title: str,
                                   article_summary: str,
                                   existing_events: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Use LLM for contextual clustering analysis.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID
            topic_name: Topic name for context
            article_title: Article title
            article_summary: AI-generated summary
            existing_events: List of existing event clusters
            
        Returns:
            Event cluster (new or existing) or None if failed
        """
        try:
            # Format existing events for LLM context
            events_context = self._format_events_for_llm(existing_events)
            
            # Get cluster detection prompt from database - NO DEFAULT
            prompt_template = self.prompt_manager.get_prompt('cluster_detection')
            if not prompt_template:
                raise ValueError("Cluster detection prompt not available from database")
            
            # Format prompt with context
            formatted_prompt = prompt_template.format(
                user_id=user_id,
                topic_id=topic_id,
                topic_name=topic_name,
                existing_events=events_context,
                article_title=article_title,
                article_summary=article_summary
            )
            
            # Define JSON schema for structured output
            cluster_schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "event_description": {"type": "string"}
                },
                "required": ["title", "description", "event_description"]
            }
            
            # Call LLM for cluster analysis with structured output
            response = self.llm_client.create_analysis_completion(
                formatted_prompt,
                response_schema=cluster_schema,
                max_tokens=3000
            )
            
            if not response:
                self.logger.error("No response from LLM for cluster detection")
                return None
            
            # Parse LLM response and create new event cluster
            cluster_decision = json.loads(response.strip())
            new_event = self._create_new_event_cluster(
                user_id, topic_id, cluster_decision
            )
            
            if new_event:
                new_event['relevance_score'] = 1.0  # Perfect match for new cluster
                self.logger.info(f"Created new event cluster: {cluster_decision.get('title')}")
            
            return new_event
            
        except ValueError:
            # Re-raise prompt errors
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in LLM clustering analysis: {e}")
            return None
    
    def _format_events_for_llm(self, events: List[Dict[str, Any]]) -> str:
        """
        Format existing events for LLM context.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Formatted string describing existing events
        """
        if not events:
            return "No existing event clusters for this topic."
        
        events_list = []
        for event in events:
            events_list.append(f"Event ID {event['id']}: {event['title']}")
            if event.get('description'):
                events_list.append(f"  Description: {event['description']}")
        
        return "\n".join(events_list)
    
    def _create_new_event_cluster(self,
                                user_id: int,
                                topic_id: int,
                                cluster_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Create new event cluster from LLM decision.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID
            cluster_data: Dictionary with title, description, event_description
            
        Returns:
            Created event dictionary or None if failed
        """
        try:
            event_title = cluster_data.get('title')
            event_description = cluster_data.get('description')
            detailed_description = cluster_data.get('event_description')
            
            if not event_title:
                self.logger.error("LLM response missing event title for new cluster")
                return None
            
            # Create new event cluster via backend
            new_event = self.backend_client.create_event_cluster(
                user_id=user_id,
                topic_id=topic_id,
                title=event_title,
                description=event_description,
                event_description=detailed_description
            )
            
            return new_event
            
        except Exception as e:
            self.logger.error(f"Error creating new event cluster: {e}")
            return None
    
    def create_article_event_association(self,
                                       article_id: int,
                                       event_id: int,
                                       relevance_score: float) -> bool:
        """
        Link article to event cluster.
        
        Args:
            article_id: Article database ID
            event_id: Event cluster database ID
            relevance_score: Relevance score (0.0-1.0)
            
        Returns:
            True if association created successfully
        """
        try:
            success = self.backend_client.create_article_event_association(
                article_id, event_id, relevance_score
            )
            
            if success:
                self.logger.info(f"Created article-event association: "
                               f"article {article_id} -> event {event_id} "
                               f"(score: {relevance_score:.3f})")
            else:
                self.logger.error(f"Failed to create article-event association: "
                                f"article {article_id} -> event {event_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error creating article-event association: {e}")
            return False
    
    def update_cluster_threshold(self, new_threshold: float):
        """
        Update clustering similarity threshold.
        
        Args:
            new_threshold: New similarity threshold (0.0-1.0)
        """
        if 0.0 <= new_threshold <= 1.0:
            old_threshold = self.cluster_threshold
            self.cluster_threshold = new_threshold
            self.logger.info(f"Updated cluster threshold: {old_threshold} -> {new_threshold}")
        else:
            self.logger.warning(f"Invalid cluster threshold: {new_threshold}, must be 0.0-1.0")
    
    def get_clustering_stats(self) -> Dict[str, Any]:
        """
        Get statistics about clustering service.
        
        Returns:
            Dictionary with clustering service statistics
        """
        return {
            'cluster_threshold': self.cluster_threshold,
            'llm_client_available': self.llm_client.is_available() if self.llm_client else False,
            'cluster_prompt_available': self.prompt_manager.get_prompt('cluster_detection') is not None,
            'backend_client_available': self.backend_client is not None
        }


class BackendClient:
    """
    Client for backend API communication related to clustering.
    
    This class handles all API calls to the backend service
    for event management and article associations.
    """
    
    def __init__(self, backend_url: str):
        """
        Initialize backend client.
        
        Args:
            backend_url: Base URL for backend API
        """
        self.backend_url = backend_url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Import requests here to avoid dependency issues
        import requests
        self.requests = requests
    
    def get_events_for_topic(self, user_id: int, topic_id: int) -> List[Dict[str, Any]]:
        """
        Get existing event clusters for user and topic.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID
            
        Returns:
            List of event dictionaries
        """
        try:
            params = {'user_id': user_id, 'topic_id': topic_id}
            response = self.requests.get(
                f"{self.backend_url}/api/internal/events", 
                params=params
            )
            response.raise_for_status()
            
            events = response.json()
            self.logger.debug(f"Retrieved {len(events)} events for user {user_id}, topic {topic_id}")
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting events for topic: {e}")
            return []
    
    def create_event_cluster(self,
                           user_id: int,
                           topic_id: int,
                           title: str,
                           description: str,
                           event_description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create new event cluster.
        
        Args:
            user_id: User database ID
            topic_id: Topic database ID
            title: Event cluster title
            description: Brief event description
            event_description: Detailed event description
            
        Returns:
            Created event dictionary or None if failed
        """
        try:
            data = {
                'user_id': user_id,
                'topic_id': topic_id,
                'title': title,
                'description': description,
                'event_description': event_description
            }
            
            response = self.requests.post(
                f"{self.backend_url}/api/internal/events", 
                json=data
            )
            response.raise_for_status()
            
            event = response.json()
            self.logger.info(f"Created new event cluster: {title} (ID: {event.get('id')})")
            return event
            
        except Exception as e:
            self.logger.error(f"Error creating event cluster: {e}")
            return None
    
    def create_article_event_association(self,
                                       article_id: int,
                                       event_id: int,
                                       relevance_score: float) -> bool:
        """
        Create association between article and event cluster.
        
        Args:
            article_id: Article database ID
            event_id: Event cluster database ID
            relevance_score: Relevance score (0.0-1.0)
            
        Returns:
            True if association created successfully
        """
        try:
            data = {
                'rss_item_id': article_id,
                'event_id': event_id,
                'relevance_score': relevance_score
            }
            
            response = self.requests.post(
                f"{self.backend_url}/api/internal/article-events", 
                json=data
            )
            response.raise_for_status()
            
            self.logger.debug(f"Created article-event association: "
                            f"article {article_id} -> event {event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating article-event association: {e}")
            return False