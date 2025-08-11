#!/usr/bin/env python3
"""
NewsFrontier AI PostProcess Service

This service processes raw articles by:
- Analyzing content and extracting topics
- Generating embeddings for semantic search
- Clustering related articles
- Creating article derivatives (summaries, analysis, etc.)
"""

import sys
import os
import time
import signal
import logging
import argparse
import threading
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib
import json

import requests
import numpy as np
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, HTTPException
import uvicorn

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import get_llm_client, generate_content_embedding, create_summary
    from newsfrontier_lib.s3_client import get_s3_client, upload_cover_image
    logger = logging.getLogger(__name__)
    logger.info("✅ LLM library imported successfully")
except ImportError as e:
    print(f"❌ LLM library import failed: {e}")
    import sys
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postprocess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIPostProcessService:
    """AI post-processing service for analyzing and enriching articles."""
    
    def __init__(self):
        self.running = True
        self.session = None
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_thread = None
        self.api_server = None
        logger.info(f"PostProcess initialized with backend URL: {self.backend_url}")
        
        # LLM client from shared library
        self.llm_client = get_llm_client()
        
        # Dynamic prompts - will be loaded from database
        self.prompts = {
            'summary_creation': None,
            'cluster_detection': None
        }
        
        # System settings cache - will be loaded from database
        self.similarity_threshold = 0.3  # Default value
        self.cluster_threshold = 0.7  # Default value for event embedding similarity
        
        # Topics cache - will be loaded from database each cycle
        self.cached_topics = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.stop_api_server()
        
    def start_api_server(self, port: int = 8001):
        """Start the FastAPI server in a separate thread."""
        try:
            def run_server():
                # Create FastAPI app with this instance
                app = create_api_app(self)
                uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
            
            self.api_thread = threading.Thread(target=run_server, daemon=True)
            self.api_thread.start()
            logger.info(f"Started FastAPI server on port {port} in background thread")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            
    def stop_api_server(self):
        """Stop the FastAPI server."""
        if self.api_thread and self.api_thread.is_alive():
            logger.info("Stopping API server...")
            # Note: uvicorn doesn't provide easy way to stop from thread
            # The daemon thread will be terminated when main process exits
        
    def get_system_setting(self, setting_key: str, default_value=None):
        """Get a system setting value from the backend API."""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/system-settings/{setting_key}")
            if response.status_code == 200:
                setting_data = response.json()
                return setting_data.get('setting_value', default_value)
            else:
                logger.warning(f"Failed to get system setting '{setting_key}', using default: {default_value}")
                return default_value
        except Exception as e:
            logger.warning(f"Error getting system setting '{setting_key}': {e}, using default: {default_value}")
            return default_value
    
    def reload_topics_cache(self):
        """Reload topics cache from database."""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/topics")
            response.raise_for_status()
            topics = response.json()
            self.cached_topics = topics
            logger.info(f"Loaded {len(topics)} topics into cache")
        except Exception as e:
            logger.warning(f"Failed to reload topics cache: {e}, using existing cache")
            # Keep existing cache on error
    
    def reload_prompts(self):
        """Reload AI prompts, system settings, and topics cache from database via internal API."""
        try:
            # Load similarity threshold from database
            threshold_value = self.get_system_setting('similarity_threshold', '0.3')
            self.similarity_threshold = float(threshold_value)
            logger.info(f"Loaded similarity threshold: {self.similarity_threshold}")
            
            # Load cluster threshold from database
            cluster_threshold_value = self.get_system_setting('cluster_threshold', '0.7')
            self.cluster_threshold = float(cluster_threshold_value)
            logger.info(f"Loaded cluster threshold: {self.cluster_threshold}")
            
            # Load all topics into cache
            self.reload_topics_cache()
            
            response = requests.get(f"{self.backend_url}/api/internal/prompts")
            response.raise_for_status()
            settings = response.json()
            
            # Default fallback prompts
            default_prompts = {
                'summary_creation': """You are a summarization assistant for news and documents.  
Extract only the main facts and key information from the given article.

Rules:  
1. Output 3–7 concise bullet-point sentences, one per line.  
2. Use short but information-rich sentences, in the same language as the original article.
3. Include key facts such as people, time, events, locations, and outcomes, ordered by importance.  
4. If the text contains anchors like <a id="P-67890">, convert them into clickable links in this format: <a href="#P-67890">➡</a>.  
5. For each bullet-point sentence, add a relevant reference link if applicable. Do not create empty <a> tags (e.g., <a href="#P-68954"></a>).  
6. Do not invent any content. Preserve all essential factual details from the article.  
7. Output must use valid HTML for indexing. Allowed tags are: <ul>, <ol>, <li>, <a> (only for internal anchor links), <b>, <i>, <p>, and <br/>. No other tags are allowed.  
8. Only create hyperlinks for internal anchors within the article (e.g., <a href="#P-12345">). Absolutely no external links or other types of hyperlinks are allowed.
9. Write the summary sentences in the style of subtitles or headlines.  Keep them concise and focused, highlighting the key points clearly, like short informative titles.  Use formatting such as <b> to emphasize the keyword style if needed.

Input:  
Title: Major Flooding Hits Midwest Causing Evacuations  
Article: Heavy rains led to major flooding in several Midwestern states, forcing thousands to evacuate. The Red River overflowed its banks near Fargo, North Dakota, causing extensive damage to homes and infrastructure. <a id="P-23456">Further relief efforts are underway</a>.

Output:  
<ul>
<li>Major flooding hits Midwest, thousands evacuate.</li>
<li><a href="#P-23457">Red River overflows near Fargo, ND.</a></li>
<li><a href="#P-23456">Relief efforts underway for affected residents.</a></li>
</ul>
---

Input:  
Title: {title}  
Article: {content}

Output:  
(Only the bullet-point sentences in allowed HTML format)
""",
                'cluster_detection': """You are an event clustering assistant for news analysis.

Your task is to analyze existing event clusters and a new article to determine if the new article belongs to an existing event cluster or represents a new event.

Context provided:
- User ID and Topic information
- List of existing event clusters with their titles and descriptions
- New article title and summary

Instructions:
1. Analyze the new article's content in relation to existing event clusters
2. If the article fits into an existing event cluster (same underlying event/story), respond with the event ID
3. If the article represents a new distinct event, respond with "create" and provide a title and description for the new event cluster
4. Consider events as the same if they are about the same underlying story/incident/development, even if from different time periods or perspectives

Response format:
If existing event: {{"action": "assign", "event_id": <event_id>, "relevance_score": <0.0-1.0>}}
If new event: {{"action": "create", "title": "<event_title>", "description": "<event_description>"}}

Do not output markdown markups. Output the json text directly.
---

User ID: {user_id}
Topic ID: {topic_id}
Topic Name: {topic_name}

Existing Event Clusters:
{existing_events}

New Article:
Title: {article_title}
Summary: {article_summary}

Analysis and Decision:"""
            }
            
            # Load prompts from settings, use defaults if not found
            for setting_key in settings:
                if setting_key.startswith('prompt_'):
                    prompt_type = setting_key.replace('prompt_', '')
                    if prompt_type in self.prompts:
                        prompt_value = settings[setting_key]
                        if prompt_value and prompt_value.strip():
                            self.prompts[prompt_type] = prompt_value.strip()
                        else:
                            self.prompts[prompt_type] = default_prompts.get(prompt_type)
                            
            # Ensure all prompts have values
            for prompt_type, prompt_value in self.prompts.items():
                if not prompt_value:
                    self.prompts[prompt_type] = default_prompts.get(prompt_type)
                    
            logger.info("Successfully reloaded AI prompts from database")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"Failed to reload prompts from database: {e}, using default prompts")
            # Use default prompts as fallback
            self.prompts = {
                'summary_creation': """
Please create a concise summary of this news article in 2-3 sentences. 
Focus on the main facts and key information.

Title: {title}

Article:
{content}

Summary:
"""
            }
        
    def setup_database(self):
        """Setup database connection."""
        try:
            # For now, we'll use the backend API instead of direct database access
            logger.info("Using backend API for database operations")
            return True
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            return False
            
    def get_pending_articles(self) -> List[Dict[str, Any]]:
        """Get articles that need processing from the backend API."""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/articles/pending-processing")
            response.raise_for_status()
            articles = response.json()
            logger.info(f"Found {len(articles)} articles pending processing")
            return articles
        except requests.RequestException as e:
            logger.error(f"Failed to get pending articles: {e}")
            return []

    def generate_title_embedding(self, article: Dict[str, Any]) -> Optional[List[float]]:
        """Generate embeddings only for article title using shared LLM library."""
        try:
            title = article.get('title', '')
            
            if not title:
                return None
                
            embedding = generate_content_embedding(title, "")
            if embedding:
                logger.info(f"Generated title embedding: {len(embedding)} dimensions")
            return embedding
                
        except Exception as e:
            logger.error(f"Error generating title embedding: {e}")
            return None
            
    def create_summary(self, article: Dict[str, Any]) -> Optional[str]:
        """Create a summary of the article using shared LLM library."""
        try:
            content = article.get('content', '')
            title = article.get('title', '')
            
            if not content or len(content) < 100:
                return None
                
            # Use prompt from database or fallback
            prompt_template = self.prompts.get('summary_creation')
            if not prompt_template:
                return None
                
            summary = create_summary(title, content, prompt_template)
            if summary:
                logger.info(f"Created AI summary: {len(summary)} characters")
            return summary
                
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return None
            
    def generate_summary_embedding(self, summary: str) -> Optional[List[float]]:
        """Generate embeddings for article summary using shared LLM library."""
        try:
            if not summary:
                return None
                
            embedding = generate_content_embedding(summary, "")
            if embedding:
                logger.info(f"Generated summary embedding: {len(embedding)} dimensions")
            return embedding
                
        except Exception as e:
            logger.error(f"Error generating summary embedding: {e}")
            return None
            
    def get_existing_topics(self, user_id: int = None) -> List[Dict[str, Any]]:
        """Get existing topics from cache, optionally filtered by user_id."""
        try:
            if user_id:
                # Filter cached topics by user_id
                filtered_topics = [topic for topic in self.cached_topics if topic.get('user_id') == user_id]
                logger.debug(f"Found {len(filtered_topics)} existing topics for user {user_id} from cache")
                return filtered_topics
            else:
                logger.debug(f"Found {len(self.cached_topics)} existing topics from cache")
                return self.cached_topics
        except Exception as e:
            logger.error(f"Error getting topics from cache: {e}")
            return []

    def find_similar_topics(self, title_embedding: List[float] = None, summary_embedding: List[float] = None, article_title: str = "", threshold: float = None) -> List[Dict[str, Any]]:
        """Find topics with cosine similarity above threshold using both title and summary embeddings."""
        try:
            # Use cached threshold or provided threshold
            if threshold is None:
                threshold = self.similarity_threshold
            
            # At least one embedding must be provided
            if not title_embedding and not summary_embedding:
                logger.warning("No embeddings provided for topic similarity comparison")
                return []
            
            existing_topics = self.get_existing_topics()
            similar_topics = []
            
            if not existing_topics:
                return similar_topics
            
            # Convert embeddings to numpy arrays if available
            title_embedding_np = None
            summary_embedding_np = None
            
            if title_embedding:
                title_embedding_np = np.array(title_embedding).reshape(1, -1)
            if summary_embedding:
                summary_embedding_np = np.array(summary_embedding).reshape(1, -1)
            
            for topic in existing_topics:
                topic_vector = topic.get('topic_vector')
                if not topic_vector:
                    continue
                
                topic_embedding = np.array(topic_vector).reshape(1, -1)
                
                # Calculate similarities for available embeddings
                title_similarity = None
                summary_similarity = None
                
                if title_embedding_np is not None:
                    title_similarity = cosine_similarity(title_embedding_np, topic_embedding)[0][0]
                
                if summary_embedding_np is not None:
                    summary_similarity = cosine_similarity(summary_embedding_np, topic_embedding)[0][0]

                final_similarity = 0
                # Use the higher similarity score as the final similarity
                if title_similarity is not None and summary_similarity is not None:
                    final_similarity = max(title_similarity, summary_similarity)
                    higher_source = "title" if title_similarity > summary_similarity else "summary"
                elif title_similarity is not None:
                    final_similarity = title_similarity
                    higher_source = "title"
                elif summary_similarity is not None:
                    final_similarity = summary_similarity
                    higher_source = "summary"
                else:
                    continue  # No valid similarities calculated
                
                distance = 1.0 - final_similarity
                
                topic_name = topic.get('name', 'Unknown')
                topic_id = topic.get('id', 'N/A')
                user_id = topic.get('user_id', 'N/A')
                
                if final_similarity >= threshold:
                    topic_copy = topic.copy()
                    topic_copy['similarity_score'] = float(final_similarity)
                    topic_copy['similarity_source'] = higher_source
                    if title_similarity is not None:
                        topic_copy['title_similarity'] = float(title_similarity)
                    if summary_similarity is not None:
                        topic_copy['summary_similarity'] = float(summary_similarity)
                    similar_topics.append(topic_copy)
            
            # Sort by similarity score descending (cosine similarity - higher is better)
            similar_topics.sort(key=lambda x: x['similarity_score'], reverse=True)
            # print(f"\n📊 RESULT: Found {len(similar_topics)} matching topics above threshold {threshold}")
            if similar_topics:
                # print("📋 Matched topics (sorted by relevance):")
                for i, topic in enumerate(similar_topics, 1):
                    source = topic.get('similarity_source', 'unknown')
                    # print(f"  {i}. '{topic['name']}' (similarity: {topic['similarity_score']:.4f}, source: {source})")
            # print("=" * 80)
            
            logger.info(f"Found {len(similar_topics)} similar topics above threshold {threshold}")
            return similar_topics
            
        except Exception as e:
            logger.error(f"Error finding similar topics: {e}")
            return []

    def create_article_topic_association(self, article_id: int, topic_id: int, relevance_score: float) -> bool:
        """Create association between article and topic."""
        try:
            data = {
                'rss_item_id': article_id,
                'topic_id': topic_id,
                'relevance_score': relevance_score
            }
            
            response = requests.post(
                f"{self.backend_url}/api/internal/article-topics",
                json=data
            )
            response.raise_for_status()
            
            logger.info(f"Created article-topic association: article {article_id} -> topic {topic_id} (score: {relevance_score:.3f})")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create article-topic association: {e}")
            return False

    def backfill_existing_articles(self, topic_id: int, topic_embedding: List[float], user_id: int = None, threshold: float = 0.65):
        """Find and associate existing articles with the new topic, generate summaries and create events."""
        try:
            # Get all articles with embeddings that have been completed (have derivatives)
            response = requests.get(f"{self.backend_url}/api/internal/articles/completed?limit=1000")
            response.raise_for_status()
            articles_response = response.json()
            articles = articles_response.get('data', [])
            
            if not articles:
                logger.info("No completed articles found for backfilling")
                return
            
            topic_embedding = np.array(topic_embedding).reshape(1, -1)
            associations_created = 0
            summaries_generated = 0
            events_created = 0
            
            # Process each article for similarity
            for article in articles:
                # Get full article details including derivatives
                try:
                    article_detail_response = requests.get(f"{self.backend_url}/api/internal/article/{article['id']}")
                    article_detail_response.raise_for_status()
                    full_article = article_detail_response.json()
                    
                    # Check if article has derivatives with title embedding
                    derivatives = full_article.get('derivatives', [])
                    if not derivatives:
                        continue
                        
                    # Use existing embeddings from derivative if available
                    derivative = derivatives[0] if derivatives else {}
                    article_title_embedding = derivative.get('title_embedding')
                    article_summary_embedding = derivative.get('summary_embedding')
                    
                    # If no title embedding exists, generate one
                    if not article_title_embedding:
                        article_title_embedding = self.generate_title_embedding(full_article)
                    
                    # Calculate similarities for available embeddings
                    title_similarity = None
                    summary_similarity = None
                    
                    if article_title_embedding:
                        title_embedding_array = np.array(article_title_embedding).reshape(1, -1)
                        title_similarity = cosine_similarity(topic_embedding, title_embedding_array)[0][0]
                    
                    if article_summary_embedding:
                        summary_embedding_array = np.array(article_summary_embedding).reshape(1, -1)
                        summary_similarity = cosine_similarity(topic_embedding, summary_embedding_array)[0][0]
                    
                    # Use the higher similarity score as the final similarity
                    if title_similarity is not None and summary_similarity is not None:
                        final_similarity = max(title_similarity, summary_similarity)
                    elif title_similarity is not None:
                        final_similarity = title_similarity
                    elif summary_similarity is not None:
                        final_similarity = summary_similarity
                    else:
                        continue  # No valid embeddings found
                    
                    if final_similarity >= threshold:
                        # Create article-topic association
                        success = self.create_article_topic_association(
                            article['id'], topic_id, float(final_similarity)
                        )
                        if success:
                            associations_created += 1
                            
                            # Generate summary if not already exists or needs regeneration
                            existing_summary = derivative.get('summary')
                            existing_title_embedding = derivative.get('title_embedding')
                            
                            # Check if we need to update embedding or summary
                            needs_embedding_update = not existing_title_embedding and article_title_embedding
                            needs_summary_update = not existing_summary
                            
                            if needs_summary_update:
                                new_summary = self.create_summary(full_article)
                                if new_summary:
                                    # Update article with summary and embedding
                                    self.update_article_processing(
                                        article['id'], 
                                        title_embedding=article_title_embedding, 
                                        summary=new_summary
                                    )
                                    summaries_generated += 1
                                    existing_summary = new_summary
                            elif needs_embedding_update:
                                # Only update embedding if summary already exists
                                self.update_article_processing(
                                    article['id'], 
                                    title_embedding=article_title_embedding
                                )
                            
                            # Create or assign to event cluster if summary exists and user_id provided
                            if existing_summary and user_id:
                                # Get topic name from the function parameter if available
                                actual_topic_name = getattr(self, '_current_topic_name', f"Topic {topic_id}")
                                cluster_result = self.detect_or_create_cluster(
                                    user_id=user_id,
                                    topic_id=topic_id,
                                    topic_name=actual_topic_name,
                                    article_title=full_article.get('title', ''),
                                    article_summary=existing_summary,
                                    title_embedding=article_title_embedding,
                                    summary_embedding=article_summary_embedding
                                )
                                
                                if cluster_result:
                                    event_id = cluster_result.get('id')
                                    relevance_score = cluster_result.get('relevance_score', 0.8)
                                    
                                    success = self.create_article_event_association(
                                        article_id=article['id'],
                                        event_id=event_id,
                                        relevance_score=relevance_score
                                    )
                                    
                                    if success:
                                        events_created += 1
                
                except Exception as e:
                    logger.error(f"Error processing article {article['id']} during backfill: {e}")
                    continue
            
            logger.info(f"Backfilled topic {topic_id}: {associations_created} associations, {summaries_generated} summaries, {events_created} events")
            
        except Exception as e:
            logger.error(f"Error backfilling existing articles: {e}")
            
    def process_new_topic(self, topic_id: int, topic_name: str, topic_embedding: List[float], user_id: int):
        """Process all existing articles for a new topic with similarity calculation, summary generation, and event creation."""
        logger.info(f"Processing new topic '{topic_name}' (ID: {topic_id}) for user {user_id}")
        
        try:
            # Store topic name for use in backfill function
            self._current_topic_name = topic_name
            
            # Use cached threshold
            self.backfill_existing_articles(
                topic_id=topic_id, 
                topic_embedding=topic_embedding, 
                user_id=user_id, 
                threshold=self.similarity_threshold
            )
            
            # Clean up
            if hasattr(self, '_current_topic_name'):
                delattr(self, '_current_topic_name')
            
            logger.info(f"Successfully processed new topic '{topic_name}' (ID: {topic_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error processing new topic '{topic_name}': {e}")
            return False

    def get_existing_events_for_topic(self, user_id: int, topic_id: int) -> List[Dict[str, Any]]:
        """Get existing event clusters for a specific user and topic."""
        try:
            params = {'user_id': user_id, 'topic_id': topic_id}
            response = requests.get(f"{self.backend_url}/api/internal/events", params=params)
            response.raise_for_status()
            events = response.json()
            logger.info(f"Found {len(events)} existing event clusters for user {user_id}, topic {topic_id}")
            return events
        except requests.RequestException as e:
            logger.error(f"Failed to get existing events: {e}")
            return []

    def create_event_cluster(self, user_id: int, topic_id: int, title: str, description: str, event_description: str = None) -> Optional[Dict[str, Any]]:
        """Create a new event cluster."""
        try:
            data = {
                'user_id': user_id,
                'topic_id': topic_id,
                'title': title,
                'description': description,
                'event_description': event_description
            }
            
            response = requests.post(f"{self.backend_url}/api/internal/events", json=data)
            response.raise_for_status()
            event = response.json()
            
            logger.info(f"Created new event cluster: {title} (ID: {event.get('id')})")
            return event
            
        except requests.RequestException as e:
            logger.error(f"Failed to create event cluster: {e}")
            return None

    def create_article_event_association(self, article_id: int, event_id: int, relevance_score: float) -> bool:
        """Create association between article and event cluster."""
        try:
            data = {
                'rss_item_id': article_id,
                'event_id': event_id,
                'relevance_score': relevance_score
            }
            
            response = requests.post(f"{self.backend_url}/api/internal/article-events", json=data)
            response.raise_for_status()
            
            logger.info(f"Created article-event association: article {article_id} -> event {event_id} (score: {relevance_score:.3f})")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create article-event association: {e}")
            return False

    def detect_or_create_cluster(self, user_id: int, topic_id: int, topic_name: str, article_title: str, article_summary: str, title_embedding: List[float], summary_embedding: List[float] = None) -> Optional[Dict[str, Any]]:
        """Use embedding distance first, then LLM to detect if article belongs to existing cluster or needs new cluster."""
        try:
            # Get existing events for this user and topic
            existing_events = self.get_existing_events_for_topic(user_id, topic_id)
            
            # FIRST: Check embedding distance with existing events
            if existing_events and (title_embedding or summary_embedding):
                logger.info(f"Checking embedding similarity for {len(existing_events)} existing events")
                
                best_match = None
                best_similarity = 0.0
                
                for event in existing_events:
                    event_embedding = event.get('event_embedding')
                    if event_embedding:
                        try:
                            # Calculate cosine similarity with both title and summary embeddings
                            title_similarity = 0.0
                            summary_similarity = 0.0
                            
                            if title_embedding:
                                title_similarity = cosine_similarity(
                                    np.array(title_embedding).reshape(1, -1),
                                    np.array(event_embedding).reshape(1, -1)
                                )[0][0]
                            
                            if summary_embedding:
                                summary_similarity = cosine_similarity(
                                    np.array(summary_embedding).reshape(1, -1),
                                    np.array(event_embedding).reshape(1, -1)
                                )[0][0]
                            
                            # Use the maximum similarity between title and summary
                            similarity = max(title_similarity, summary_similarity)
                            
                            logger.debug(f"Event {event['id']} - title_sim: {title_similarity:.3f}, summary_sim: {summary_similarity:.3f}, max_sim: {similarity:.3f}")
                            
                            if similarity > best_similarity:
                                best_similarity = similarity
                                best_match = event
                                
                        except Exception as e:
                            logger.warning(f"Failed to calculate similarity for event {event['id']}: {e}")
                
                # If similarity >= threshold, assign directly without LLM
                if best_match and best_similarity >= self.cluster_threshold:
                    logger.info(f"Direct assignment: Article matched to event {best_match['id']} with similarity {best_similarity:.3f} (threshold: {self.cluster_threshold})")
                    best_match['relevance_score'] = best_similarity
                    return best_match
                else:
                    logger.info(f"No embedding match >= threshold {self.cluster_threshold} (best: {best_similarity:.3f}), proceeding to LLM analysis")
            
            # SECOND: If no embedding match, proceed with LLM analysis
            # Format existing events for LLM context
            events_context = ""
            if existing_events:
                events_list = []
                for event in existing_events:
                    events_list.append(f"Event ID {event['id']}: {event['title']}")
                    if event.get('description'):
                        events_list.append(f"  Description: {event['description']}")
                events_context = "\n".join(events_list)
            else:
                events_context = "No existing event clusters for this topic."
            
            # Get cluster detection prompt
            prompt_template = self.prompts.get('cluster_detection')
            if not prompt_template:
                logger.error("No cluster detection prompt available")
                return None
                
            # Format prompt with context
            prompt = prompt_template.format(
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
                    # "action": {
                    #     "type": "string",
                    #     "enum": ["assign", "create", "ignore"]
                    # },
                    # "event_id": {
                    #     "type": "integer",
                    # },
                    # "topic_id": {
                    #     "type": "array",
                    #     "items": {
                    #         "type": "integer"
                    #     }
                    # },
                    "title": {
                        "type": "string",
                    },
                    "description": {
                        "type": "string",
                    },
                    "event_description": {
                        "type": "string",
                    },
                },
                "required": ["title", "description", "event_description"],
            }
            
            # Call LLM for cluster analysis with structured output using analysis model
            response = self.llm_client.create_analysis_completion(prompt,
                                                                  response_schema=cluster_schema,
                                                                  max_tokens=3000)
            
            if not response:
                logger.error("No response from LLM for cluster detection")
                return None
                
            # Parse LLM response
            try:
                decision = json.loads(response.strip())
                
                # if decision.get('action') == 'assign':
                #     # Assign to existing cluster
                #     event_id = decision.get('event_id')
                #     relevance_score = decision.get('relevance_score', 0.8)
                #    
                #     # Find the event in existing events to return it
                #     for event in existing_events:
                #         if event['id'] == event_id:
                #             event['relevance_score'] = relevance_score
                #             return event
                #    
                #     logger.warning(f"Event ID {event_id} not found in existing events")
                #     return None
                    
                # elif decision.get('action') == 'create':
                # now we always create a new event
                # Create new cluster
                event_title = decision.get('title')
                event_description = decision.get('description')
                detailed_event_description = decision.get('event_description')
                
                if not event_title:
                    logger.error("LLM response missing event title for new cluster")
                    return None
                
                # Create new event cluster
                new_event = self.create_event_cluster(
                    user_id=user_id,
                    topic_id=topic_id,
                    title=event_title,
                    description=event_description,
                    event_description=detailed_event_description,
                )
                
                if new_event:
                    new_event['relevance_score'] = 1.0  # Perfect match for new cluster
                    
                return new_event
                # elif decision.get('action') == 'ignore':
                #     # ignore the article
                #     return None
                #
                # else:
                #     logger.error(f"Unknown action in LLM response: {decision.get('action')}")
                #     return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"LLM response was: {response}")
                return None
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error in cluster detection: {e}")
            return None

    def update_article_processing(self, article_id: int, title_embedding: List[float] = None, summary: str = None, summary_embedding: List[float] = None, error_message: str = None) -> bool:
        """Update article with processing results via backend API."""
        try:
            data = {
                'title_embedding': title_embedding,
                'summary_embedding': summary_embedding,
                'embedding_model': self.llm_client.embedding_model,
                'summary': summary,
                'summary_model': self.llm_client.default_chat_model,
                'processed_at': datetime.now().isoformat(),
                'error_message': error_message
            }
            
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}
            
            response = requests.post(
                f"{self.backend_url}/api/internal/articles/{article_id}/process",
                json=data
            )
            response.raise_for_status()
            
            logger.info(f"Updated processing results for article {article_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update article processing: {e}")
            return False
            
    def process_article(self, article: Dict[str, Any]) -> bool:
        """Process a single article - always create title_embedding, summary and summary_embedding."""
        article_id = article.get('id')
        title = article.get('title', 'Untitled')
        user_id = article.get('user_id')  # Assuming articles have user_id
        
        logger.info(f"Processing article: {title[:50]}...")
        
        try:
            # Always generate title embedding
            title_embedding = self.generate_title_embedding(article)
            
            # Always create summary
            summary = self.create_summary(article)
            
            # Always generate summary embedding (if summary exists)
            summary_embedding = None
            if summary:
                summary_embedding = self.generate_summary_embedding(summary)
            
            # If all three components failed, mark as failed
            if not title_embedding and not summary and not summary_embedding:
                logger.error(f"Failed to generate title_embedding, summary, and summary_embedding for article {article_id}")
                self.update_article_processing(article_id, error_message="Failed to generate title_embedding, summary, and summary_embedding")
                return False
            
            # Update article with results (components may be None)
            self.update_article_processing(
                article_id, 
                title_embedding=title_embedding, 
                summary=summary,
                summary_embedding=summary_embedding
            )
            
            # Proceed with topic matching if we have at least one embedding
            if title_embedding or summary_embedding:
                # Find similar topics using both title and summary embeddings, taking the higher similarity
                similar_topics = self.find_similar_topics(
                    title_embedding=title_embedding, 
                    summary_embedding=summary_embedding, 
                    article_title=title
                )
                
                if similar_topics:
                    # Found similar topics - create associations
                    logger.info(f"Found {len(similar_topics)} similar topics for article {article_id}")
                    
                    # Create associations with similar topics
                    for topic in similar_topics:
                        self.create_article_topic_association(
                            article_id, topic['id'], topic['similarity_score']
                        )
                    
                    # Perform clustering for each user/topic combination if summary exists
                    if summary:
                        for topic in similar_topics:
                            # Get user_id from topic or article context
                            topic_user_id = topic.get('user_id', user_id)
                            if not topic_user_id:
                                logger.warning(f"No user_id found for topic {topic['id']}, skipping clustering")
                                continue
                                
                            # Detect or create cluster for this article
                            cluster_result = self.detect_or_create_cluster(
                                user_id=topic_user_id,
                                topic_id=topic['id'],
                                topic_name=topic.get('name', 'Unknown Topic'),
                                article_title=title,
                                article_summary=summary,
                                title_embedding=title_embedding,
                                summary_embedding=summary_embedding
                            )
                            
                            if cluster_result:
                                # Create article-event association
                                event_id = cluster_result.get('id')
                                relevance_score = cluster_result.get('relevance_score', 0.8)
                                
                                success = self.create_article_event_association(
                                    article_id=article_id,
                                    event_id=event_id,
                                    relevance_score=relevance_score
                                )
                                
                                if success:
                                    logger.info(f"Successfully clustered article {article_id} into event {event_id}")
                                else:
                                    logger.warning(f"Failed to associate article {article_id} with event {event_id}")
                            else:
                                logger.warning(f"Failed to cluster article {article_id} for topic {topic['id']}")
                else:
                    logger.info(f"Found 0 similar topics above threshold {self.similarity_threshold}")
            else:
                logger.info(f"No summary embedding generated - skipping topic matching")
            
            logger.info(f"Successfully processed article: {title[:50]}...")
            return True
                
        except Exception as e:
            logger.error(f"Error processing article {article_id}: {e}")
            # Update article with error
            self.update_article_processing(article_id, error_message=str(e))
            return False
            
    def run_processing_cycle(self):
        """Run a single processing cycle."""
        logger.info("Starting AI postprocessing cycle")
        
        # Reload AI prompts from database at start of each cycle
        self.reload_prompts()
        
        # Get articles that need processing
        pending_articles = self.get_pending_articles()
        
        if not pending_articles:
            logger.info("No articles need processing at this time")
            return
            
        # Process each article
        successful_articles = 0
        failed_articles = 0
        
        for article in pending_articles:
            if not self.running:
                logger.info("Postprocessor stopped during cycle")
                break
                
            try:
                if self.process_article(article):
                    successful_articles += 1
                else:
                    failed_articles += 1
                    
                # Small delay between articles
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Unexpected error processing article: {e}")
                failed_articles += 1
                
        logger.info(f"Processing cycle completed: {successful_articles} successful, {failed_articles} failed")
        
    def run_daemon(self, with_api_server=True, api_port=8001):
        """Run the postprocessor as a daemon service with optional API server."""
        logger.info("Starting AI postprocessing daemon")
        
        if not self.setup_database():
            logger.error("Failed to setup database connection")
            return False
        
        # Start API server if requested
        if with_api_server:
            self.start_api_server(port=api_port)
            
        # Track last daily summary generation date
        last_daily_summary_date = None
        
        # Main daemon loop
        while self.running:
            try:
                current_time = datetime.now()
                current_date = current_time.date()
                
                # Check if it's a new day and past midnight (00:00-01:00) for daily summary generation
                if (last_daily_summary_date != current_date and 
                    current_time.hour == 0 and current_time.minute < 30):
                    try:
                        logger.info("Starting daily summary generation for all users...")
                        self.run_daily_summary_generation()
                        last_daily_summary_date = current_date
                        logger.info("Daily summary generation completed")
                    except Exception as e:
                        logger.error(f"Error in daily summary generation: {e}")
                
                # Regular article processing cycle
                self.run_processing_cycle()
                
                # Wait before next cycle (default 2 minutes)
                for _ in range(120):  # 2 minutes = 120 seconds
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                if not self.running:
                    break
                time.sleep(60)  # Wait 1 minute before retry
                
        logger.info("AI postprocessing daemon stopped")
        return True
    
    def run_daily_summary_generation(self):
        """Generate daily summaries for all users."""
        try:
            # Get all users from backend
            response = requests.get(f"{self.backend_url}/api/internal/users")
            response.raise_for_status()
            users = response.json().get('data', [])
            
            logger.info(f"Starting daily summary generation for {len(users)} users")
            
            for user in users:
                try:
                    self.generate_user_daily_summary(user['id'], user.get('username', 'User'))
                except Exception as e:
                    logger.error(f"Failed to generate daily summary for user {user['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Error fetching users for daily summary generation: {e}")
    
    def generate_user_daily_summary(self, user_id: int, username: str):
        """Generate daily summary for a specific user."""
        try:
            today = datetime.now().date()
            logger.info(f"Generating daily summary for user {user_id} ({username}) for {today}")
            
            # Check if summary already exists for today
            existing_response = requests.get(
                f"{self.backend_url}/api/internal/user-summary/{user_id}/{today}"
            )
            if existing_response.status_code == 200:
                logger.info(f"Daily summary already exists for user {user_id} on {today}")
                return
            
            # Get user's subscriptions and topics
            user_context = self.get_user_daily_context(user_id, today)
            if not user_context:
                logger.info(f"No relevant content found for user {user_id}")
                return
            
            # Generate summary using LLM
            summary_content = self.create_daily_summary_content(user_context)
            if not summary_content:
                logger.error(f"Failed to generate summary content for user {user_id}")
                return
            
            # Generate cover image prompt
            cover_prompt = self.generate_cover_image_prompt(summary_content)
            
            # Save daily summary
            self.save_daily_summary(user_id, today, summary_content, cover_prompt)
            
            logger.info(f"Successfully generated daily summary for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error generating daily summary for user {user_id}: {e}")
    
    def get_user_daily_context(self, user_id: int, date) -> Optional[Dict]:
        """Get user context for daily summary generation."""
        try:
            # Get user's subscriptions and custom prompt
            user_response = requests.get(f"{self.backend_url}/api/internal/user/{user_id}")
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get user's topics
            topics_response = requests.get(f"{self.backend_url}/api/internal/topics?user_id={user_id}")
            topics_response.raise_for_status()
            user_topics = topics_response.json()  # Returns list directly
            
            if not user_topics:
                logger.info(f"User {user_id} has no topics defined")
                return None
            
            # Get today's relevant articles (published today, related to user's topics)
            relevant_articles = []
            for topic in user_topics:
                topic_articles_response = requests.get(
                    f"{self.backend_url}/api/internal/article-topics?topic_id={topic['id']}&date={date}"
                )
                if topic_articles_response.status_code == 200:
                    topic_articles = topic_articles_response.json()  # Returns list directly
                    relevant_articles.extend(topic_articles)
            
            # Get new events created today related to user's topics
            new_events = []
            for topic in user_topics:
                events_response = requests.get(
                    f"{self.backend_url}/api/internal/events?topic_id={topic['id']}&created_date={date}"
                )
                if events_response.status_code == 200:
                    topic_events = events_response.json()  # Returns list directly
                    # Add topic information to each event
                    for event in topic_events:
                        event['topic_name'] = topic.get('name', 'Unknown Topic')
                        event['topic_id'] = topic['id']
                    new_events.extend(topic_events)
            
            # Get recent daily summaries (last 5)
            recent_summaries_response = requests.get(
                f"{self.backend_url}/api/internal/user-summaries/{user_id}?limit=5"
            )
            recent_summaries = []
            if recent_summaries_response.status_code == 200:
                recent_summaries = recent_summaries_response.json().get('data', [])  # Wrapped in data
            
            return {
                'user_id': user_id,
                'username': user_data.get('username', 'User'),
                'custom_prompt': user_data.get('daily_summary_prompt', ''),
                'topics': user_topics,
                'relevant_articles': relevant_articles,
                'new_events': new_events,
                'recent_summaries': recent_summaries
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error getting user context for user {user_id}: {e}")
            return None
    
    def create_daily_summary_content(self, user_context: Dict) -> Optional[str]:
        """Create daily summary content using LLM."""
        try:
            # Get prompts from database
            prompts_response = requests.get(f"{self.backend_url}/api/internal/prompts")
            prompts_response.raise_for_status()
            prompts = prompts_response.json()
            
            system_prompt = prompts.get('prompt_daily_summary_system', '')
            
            if not system_prompt:
                logger.error("Daily summary system prompt not found in database")
                return None
            
            # Get user's personal daily summary prompt (can be empty)
            user_daily_prompt = (user_context.get('custom_prompt') or '').strip()
            
            # Format articles for context
            articles_text = self.format_articles_for_summary(user_context['relevant_articles'])
            events_text = self.format_events_for_summary(user_context['new_events'])
            recent_summaries_text = self.format_recent_summaries(user_context['recent_summaries'])
            
            # Format system prompt with required fields
            formatted_system_prompt = system_prompt.format(
                articles=articles_text,
                summaries=recent_summaries_text,
                events=events_text
            )
            
            # Add user's personal prompt if provided
            if user_daily_prompt:
                try:
                    user_prompt = user_daily_prompt.format(
                        recent_summaries=recent_summaries_text,
                        articles=articles_text,
                        new_events=events_text,
                        username=user_context.get('username', 'User')
                    )
                    # Combine system and user prompts
                    full_prompt = f"{formatted_system_prompt}\n\nAdditional User Instructions:\n{user_prompt}"
                except Exception as e:
                    logger.warning(f"Error formatting user prompt: {e}, using system prompt only")
                    full_prompt = formatted_system_prompt
            else:
                # Use only system prompt (user_daily_prompt can be empty)
                full_prompt = formatted_system_prompt
            summary = self.llm_client.create_analysis_completion(
                prompt=full_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            return summary
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error creating daily summary content: {e}")
            return None
    
    def format_articles_for_summary(self, articles: List[Dict]) -> str:
        """Format articles for summary context."""
        if not articles:
            logger.info(f"Fetch 0 articles for daily summary")
            return "No relevant articles found for today."
        
        formatted_articles = []
        logger.info(f"Fetch {len(articles)} articles for daily summary")
        for article in articles[:10]:  # Limit to 10 most relevant articles
            article_info = article.get('rss_item', {})
            title = article_info.get('title', 'Untitled')
            article_id = article_info.get('id', '')
            summary = ''
            
            # Get article summary if available
            derivatives = article_info.get('derivatives', [])
            if derivatives:
                summary = derivatives[0].get('summary', '')
            
            # Use local dashboard link format instead of external URL
            article_link = f"/dashboard/article/{article_id}" if article_id else "#"
            formatted_articles.append(f"- **[{title}]({article_link})**")
            if summary:
                formatted_articles.append(f"  Summary: {summary}")
        
        return "\n".join(formatted_articles)
    
    def format_events_for_summary(self, events: List[Dict]) -> str:
        """Format new events for summary context."""
        if not events:
            logger.info(f"Fetch 0 events for daily summary")
            return "No new events detected today."
        
        formatted_events = []
        logger.info(f"Fetch {len(events)} events for daily summary")
        for event in events:
            title = event.get('title', 'Untitled Event')
            event_id = event.get('id', '')
            description = event.get('description', '')
            topic_name = event.get('topic_name', 'Unknown Topic')
            topic_id = event.get('topic_id', '')
            
            # Use local dashboard link format for events (clusters) and topics
            event_link = f"/dashboard/clusters/{event_id}" if event_id else "#"
            topic_link = f"/dashboard/topics/{topic_id}" if topic_id else "#"
            
            formatted_events.append(f"- **Topic: [{topic_name}]({topic_link})**")
            formatted_events.append(f"  - **Event: [{title}]({event_link})**")
            if description:
                formatted_events.append(f"    {description}")
        
        return "\n".join(formatted_events)
    
    def format_recent_summaries(self, summaries: List[Dict]) -> str:
        """Format recent summaries for context."""
        if not summaries:
            logger.info(f"Fetch 0 summaries for daily summary")
            return "No recent summaries available."
        
        formatted_summaries = []
        logger.info(f"Fetch {len(summaries)} summaries for daily summary")
        for summary in summaries:
            date = summary.get('date', 'Unknown date')
            content = summary.get('summary', '')[:200] + "..." if len(summary.get('summary', '')) > 200 else summary.get('summary', '')
            formatted_summaries.append(f"- {date}: {content}")
        
        return "\n".join(formatted_summaries)
    
    def generate_cover_image_prompt(self, summary_content: str) -> Optional[str]:
        """Generate cover image prompt for the daily summary."""
        try:
            # Get cover image generation prompt from database
            prompts_response = requests.get(f"{self.backend_url}/api/internal/prompts")
            prompts_response.raise_for_status()
            prompts = prompts_response.json()
            
            cover_prompt_template = prompts.get('prompt_cover_image_generation', '')
            if not cover_prompt_template:
                logger.warning("Cover image generation prompt not found in database")
                return None
            
            # Format the prompt with summary content
            user_prompt = cover_prompt_template.format(summary_content=summary_content[:2000])
            
            # Generate cover prompt using LLM
            # Combine system and user prompts into single prompt
            full_prompt = user_prompt
            cover_prompt = self.llm_client.create_summary_completion(
                prompt=full_prompt,
                max_tokens=500,
                temperature=1
            )
            
            return cover_prompt
            
        except Exception as e:
            logger.error(f"Error generating cover image prompt: {e}")
            return None
    
    def save_daily_summary(self, user_id: int, date, summary_content: str, cover_prompt: Optional[str]):
        """Save daily summary to database via backend API with cover image generation."""
        try:
            # Generate cover image if prompt is available
            cover_s3key = None
            if cover_prompt:
                cover_s3key = self.generate_and_upload_cover_image(cover_prompt, date)
            
            data = {
                'user_id': user_id,
                'date': date.isoformat(),
                'summary': summary_content,
                'cover_prompt': cover_prompt,
                'cover_arguments': None,  # Could be used for image generation parameters
                'cover_seed': None,      # Could be used for reproducible image generation
                'cover_s3key': cover_s3key
            }
            
            response = requests.post(
                f"{self.backend_url}/api/internal/user-summaries",
                json=data
            )
            response.raise_for_status()
            
            logger.info(f"Successfully saved daily summary for user {user_id} on {date}")
            if cover_s3key:
                logger.info(f"Cover image uploaded to S3: {cover_s3key}")
            
        except Exception as e:
            logger.error(f"Error saving daily summary for user {user_id}: {e}")
    
    def generate_and_upload_cover_image(self, cover_prompt: str, date) -> Optional[str]:
        """Generate cover image and upload to S3."""
        try:
            # Generate image using LLM client
            logger.info("Generating cover image...")
            
            # Get image generation settings from environment
            aspect_ratio = os.getenv('IMAGEGEN_ASPECT_RATIO', '16:9')
            person_generation = os.getenv('IMAGEGEN_PERSON_GENERATE', 'dont_allow')
            
            image_bytes = self.llm_client.generate_image(
                prompt=cover_prompt,
                aspect_ratio=aspect_ratio,
                person_generation=person_generation
            )
            
            if not image_bytes:
                logger.error("Failed to generate cover image")
                return None
            
            # Upload to S3
            logger.info("Uploading cover image to S3...")
            s3_client = get_s3_client()
            
            if not s3_client.is_available():
                logger.warning("S3 client not available, skipping image upload")
                return None
            
            date_str = date.strftime("%Y%m%d") if hasattr(date, 'strftime') else str(date).replace('-', '')
            s3_key = upload_cover_image(image_bytes, date_str)
            
            if s3_key:
                logger.info(f"Successfully uploaded cover image: {s3_key}")
                return s3_key
            else:
                logger.error("Failed to upload cover image to S3")
                return None
                
        except Exception as e:
            logger.error(f"Error generating/uploading cover image: {e}")
            return None
        
    def run_once(self):
        """Run the postprocessor once and exit."""
        logger.info("Running AI postprocessor once")
        
        if not self.setup_database():
            logger.error("Failed to setup database connection")
            return False
            
        self.run_processing_cycle()
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NewsFrontier AI PostProcess Service")
    parser.add_argument(
        '--daemon', 
        action='store_true', 
        help='Run as daemon service'
    )
    parser.add_argument(
        '--once', 
        action='store_true', 
        help='Run once and exit'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with mock article data'
    )
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help='Set logging level'
    )
    parser.add_argument(
        '--backend-url',
        default=None,
        help='Override backend API URL'
    )
    parser.add_argument(
        '--no-api',
        action='store_true',
        help='Disable HTTP API server (daemon mode runs API server by default)'
    )
    parser.add_argument(
        '--api-port',
        type=int,
        default=8001,
        help='Port for HTTP API server (default: 8001)'
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Print configuration for debugging
    logger.info("=== NewsFrontier AI PostProcess Service ===")
    logger.info(f"Log level: {args.log_level}")
    llm_client = get_llm_client()
    logger.info(f"LLM API URL: {os.getenv('LLM_API_URL', 'Not set')}")
    logger.info(f"LLM API Key: {'Set' if os.getenv('LLM_API_KEY') else 'Not set'}")
    logger.info(f"LLM Model: {llm_client.default_chat_model}")
    logger.info(f"Embedding Model: {llm_client.embedding_model}")
    logger.info(f"LLM Client Available: {llm_client.is_available()}")
    logger.info(f"Backend URL: {args.backend_url or os.getenv('BACKEND_URL', 'http://localhost:8000')}")
    logger.info("=" * 45)
    
    # Create postprocessor service
    postprocessor = AIPostProcessService()
    
    # Override backend URL if provided
    if args.backend_url:
        postprocessor.backend_url = args.backend_url
    
    try:
        if args.test:
            success = run_test_mode(postprocessor)
        elif args.daemon:
            # Run daemon with API server (unless disabled)
            success = postprocessor.run_daemon(
                with_api_server=not args.no_api, 
                api_port=args.api_port
            )
        elif args.once:
            success = postprocessor.run_once()
        else:
            # Default to daemon mode with API server
            logger.info("No mode specified, defaulting to daemon mode with API server")
            success = postprocessor.run_daemon(
                with_api_server=not args.no_api, 
                api_port=args.api_port
            )
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Postprocessor interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def run_test_mode(postprocessor: AIPostProcessService) -> bool:
    """Run postprocessor in test mode with mock data."""
    logger.info("Running in test mode with mock article data")
    
    # Create mock article data
    mock_article = {
        'id': 1,
        'title': 'OpenAI Announces GPT-5: The Next Generation of AI Language Models',
        'content': """OpenAI today announced the development of GPT-5, the next iteration of their groundbreaking generative AI language model series. The new model promises significant improvements in reasoning capabilities, reduced hallucinations, and better understanding of context across longer conversations.

According to OpenAI's CEO Sam Altman, GPT-5 will feature enhanced multimodal capabilities, allowing it to process and generate not just text, but also images, audio, and video content seamlessly. The model has been trained on a more diverse dataset and incorporates advanced safety measures to prevent misuse.

The company expects GPT-5 to be available to developers through their API in early 2025, with consumer applications following shortly after. This development represents a major step forward in artificial intelligence technology and is expected to have significant impacts across various industries including education, healthcare, and software development.

Industry experts are calling this announcement a potential game-changer in the AI landscape, with competitors like Google and Anthropic likely to accelerate their own development efforts in response.""",
        'url': 'https://example.com/gpt5-announcement',
        'published_at': '2024-01-15T10:00:00Z',
        'source': 'TechNews'
    }
    
    try:
        logger.info("Testing title embedding generation...")
        embedding = postprocessor.generate_title_embedding(mock_article)
        if embedding:
            logger.info(f"Generated title embedding with {len(embedding)} dimensions")
        else:
            logger.warning("Failed to generate title embedding")
        
        logger.info("Testing summary creation...")
        summary = postprocessor.create_summary(mock_article)
        if summary:
            logger.info(f"Generated summary: {summary}")
        else:
            logger.warning("Failed to create summary")
        
        logger.info("Test mode completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test mode failed: {e}")
        return False


# HTTP API endpoints for external triggers

class NewTopicRequest(BaseModel):
    topic_id: int
    topic_name: str
    topic_embedding: List[float]
    user_id: int

def create_api_app(postprocessor_instance: AIPostProcessService) -> FastAPI:
    """Create FastAPI app with postprocessor instance."""
    app = FastAPI(title="PostProcess API", version="1.0.0")
    
    @app.post("/api/process-new-topic")
    async def process_new_topic_endpoint(request: NewTopicRequest):
        """HTTP endpoint to process a new topic against existing articles."""
        if not postprocessor_instance:
            raise HTTPException(status_code=503, detail="Postprocessor service not initialized")
        
        try:
            success = postprocessor_instance.process_new_topic(
                topic_id=request.topic_id,
                topic_name=request.topic_name,
                topic_embedding=request.topic_embedding,
                user_id=request.user_id
            )
            
            if success:
                return {"message": f"Successfully processed new topic '{request.topic_name}'", "status": "completed"}
            else:
                raise HTTPException(status_code=500, detail="Failed to process new topic")
                
        except Exception as e:
            logger.error(f"Error in process_new_topic endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        status = {
            "service": "postprocess",
            "status": "healthy" if postprocessor_instance else "initializing",
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    @app.post("/api/generate-user-summary/{user_id}")
    async def generate_user_summary_api(user_id: int):
        """API endpoint to trigger daily summary generation for a specific user."""
        try:
            logger.info(f"API: Received request to generate daily summary for user {user_id}")
            
            if not postprocessor_instance:
                logger.error("Postprocessor instance not available")
                raise HTTPException(status_code=503, detail="Postprocessor service not ready")
            
            # Get user info first
            user_response = requests.get(f"{postprocessor_instance.backend_url}/api/internal/user/{user_id}")
            if user_response.status_code != 200:
                logger.error(f"User {user_id} not found or error fetching user data")
                raise HTTPException(status_code=404, detail=f"User {user_id} not found")
            
            user_data = user_response.json()
            username = user_data.get('username', 'User')
            
            # Generate daily summary
            postprocessor_instance.generate_user_daily_summary(user_id, username)
            
            logger.info(f"API: Successfully generated daily summary for user {user_id}")
            return {
                "success": True,
                "message": f"Daily summary generated for user {user_id}",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API: Error generating daily summary for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate daily summary: {str(e)}")
    
    @app.post("/api/process")
    async def process_articles_api():
        """API endpoint to trigger manual article processing cycle."""
        try:
            logger.info("API: Received request to process pending articles")
            
            if not postprocessor_instance:
                logger.error("Postprocessor instance not available")
                raise HTTPException(status_code=503, detail="Postprocessor service not ready")
            
            # Run a processing cycle
            postprocessor_instance.run_processing_cycle()
            
            logger.info("API: Successfully completed article processing cycle")
            return {
                "success": True,
                "message": "Article processing cycle completed successfully",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"API: Error processing articles: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process articles: {str(e)}")
    
    return app

if __name__ == "__main__":
    main()
