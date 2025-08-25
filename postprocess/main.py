#!/usr/bin/env python3
"""
NewsFrontier AI PostProcess Service - Refactored Modular Architecture

This service processes raw articles by:
- Analyzing content and extracting topics
- Generating embeddings for semantic search
- Clustering related articles
- Creating article derivatives (summaries, analysis, etc.)
- Generating personalized daily summaries
"""

import sys
import os
import time
import signal
import logging
import argparse
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import uvicorn

# Import modular services
from summary_generator import SummaryGenerator, PromptManager
from embedding_generator import EmbeddingGenerator, SimilarityCalculator
from image_generator import ImageGenerator
from clustering_service import ClusteringService, BackendClient
from daily_summary_service import DailySummaryService

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import get_llm_client
    from newsfrontier_lib.llm_client_new import get_enhanced_llm_client
    from newsfrontier_lib.s3_client_new import get_enhanced_s3_client
    from newsfrontier_lib.config_service import get_config, ConfigKeys
    from newsfrontier_lib.init_config import init_default_settings, test_encryption
    logger = logging.getLogger(__name__)
    logger.info("✅ Enhanced LLM library imported successfully")
except ImportError as e:
    print(f"❌ Enhanced LLM library import failed: {e}")
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
    """
    AI post-processing service for analyzing and enriching articles.
    
    Refactored to use modular architecture with separate services for:
    - Article summarization
    - Embedding generation
    - Image generation
    - Event clustering
    - Daily summary generation
    """
    
    def __init__(self):
        self.running = True
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_thread = None
        self.api_server = None
        
        logger.info(f"PostProcess initialized with backend URL: {self.backend_url}")
        
        # Initialize configuration service
        self.config = get_config()
        
        # Test encryption and initialize default settings
        self._setup_configuration()
        
        # System settings cache - loaded from database configuration
        self.similarity_threshold = self.config.get(ConfigKeys.CLUSTER_THRESHOLD, default=0.3)
        self.cluster_threshold = self.config.get(ConfigKeys.CLUSTER_THRESHOLD, default=0.7)
        
        # Initialize modular services
        self._initialize_services()
        
        # Topics cache - will be loaded from database each cycle
        self.cached_topics = []
    
    def _setup_configuration(self):
        """Setup database configuration and encryption."""
        try:
            # Test encryption functionality
            if not test_encryption():
                logger.warning("Encryption test failed - some features may not work properly")
            
            # Initialize default settings if needed
            init_default_settings()
            
            # Log configuration status
            daily_summary_enabled = self.config.get(ConfigKeys.DAILY_SUMMARY_ENABLED, default=True)
            cover_enabled = self.config.get(ConfigKeys.DAILY_SUMMARY_COVER_ENABLED, default=True)
            scraper_interval = self.config.get(ConfigKeys.SCRAPER_INTERVAL, default=60)
            postprocess_interval = self.config.get(ConfigKeys.POSTPROCESS_INTERVAL, default=30)
            
            logger.info("Configuration Status:")
            logger.info(f"  Daily Summary: {'✓' if daily_summary_enabled else '✗'}")
            logger.info(f"  Cover Images: {'✓' if cover_enabled else '✗'}")
            logger.info(f"  Scraper Interval: {scraper_interval} minutes")
            logger.info(f"  PostProcess Interval: {postprocess_interval} minutes")
            
        except Exception as e:
            logger.error(f"Configuration setup failed: {e}")
            # Continue with default settings
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_services(self):
        """Initialize all modular services."""
        try:
            # Get enhanced clients
            self.enhanced_llm_client = get_enhanced_llm_client()
            self.enhanced_s3_client = get_enhanced_s3_client()
            
            # Shared components
            self.prompt_manager = PromptManager()
            self.backend_client = BackendAPIClient(self.backend_url)
            
            # Core services
            self.embedding_generator = EmbeddingGenerator()
            self.similarity_calculator = SimilarityCalculator()
            self.summary_generator = SummaryGenerator(self.prompt_manager)
            self.image_generator = ImageGenerator(self.prompt_manager)
            
            # Advanced services
            self.clustering_service = ClusteringService(
                self.prompt_manager,
                self.similarity_calculator, 
                self.backend_client,
                self.cluster_threshold
            )
            
            self.daily_summary_service = DailySummaryService(
                self.prompt_manager,
                self.backend_client,
                self.image_generator
            )
            
            logger.info("✅ All modular services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.stop_api_server()
    
    def start_api_server(self, port: int = 8001):
        """Start the FastAPI server in a separate thread."""
        try:
            def run_server():
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
    
    def reload_prompts(self):
        """Reload AI prompts, system settings, and topics cache from database."""
        try:
            # Load system settings
            self.similarity_threshold = float(self._get_system_setting('similarity_threshold', '0.3'))
            self.cluster_threshold = float(self._get_system_setting('cluster_threshold', '0.7'))
            
            logger.info(f"Loaded similarity threshold: {self.similarity_threshold}")
            logger.info(f"Loaded cluster threshold: {self.cluster_threshold}")
            
            # Update clustering service threshold
            self.clustering_service.update_cluster_threshold(self.cluster_threshold)
            
            # Load topics cache
            self.reload_topics_cache()
            
            # Load prompts from database
            response = requests.get(f"{self.backend_url}/api/internal/prompts")
            response.raise_for_status()
            prompts = response.json()
            
            # Set prompts in prompt manager
            prompt_dict = {}
            for setting_key, prompt_value in prompts.items():
                if setting_key.startswith('prompt_'):
                    prompt_type = setting_key.replace('prompt_', '')
                    if prompt_value and prompt_value.strip():
                        prompt_dict[prompt_type] = prompt_value.strip()
                    else:
                        raise ValueError(f"Prompt '{prompt_type}' is empty or missing in database")
            
            # Validate required prompts exist
            required_prompts = ['summary_creation', 'cluster_detection']
            for prompt_type in required_prompts:
                if prompt_type not in prompt_dict:
                    raise ValueError(f"Required prompt '{prompt_type}' not found in database")
            
            self.prompt_manager.set_prompts(prompt_dict)
            logger.info("Successfully reloaded AI prompts from database")
            
        except Exception as e:
            logger.error(f"Failed to reload prompts from database: {e}")
            raise e
    
    def _get_system_setting(self, setting_key: str, default_value=None):
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
    
    def process_article(self, article: Dict[str, Any]) -> bool:
        """
        Process a single article through complete AI pipeline using modular services.
        
        Args:
            article: Article dictionary with content and metadata
            
        Returns:
            True if processing successful, False otherwise
        """
        article_id = article.get('id')
        title = article.get('title', 'Untitled')
        user_id = article.get('user_id')
        
        logger.info(f"Processing article: {title[:50]}...")
        
        try:
            # Step 1: Generate title embedding
            title_embedding = self.embedding_generator.generate_title_embedding(article)
            
            # Step 2: Create AI summary
            summary = self.summary_generator.create_article_summary(article)
            
            # Step 3: Generate summary embedding
            summary_embedding = None
            if summary:
                summary_embedding = self.embedding_generator.generate_summary_embedding(summary)
            
            # Check if processing completely failed
            if not title_embedding and not summary and not summary_embedding:
                logger.error(f"Failed to generate any content for article {article_id}")
                self._update_article_processing(article_id, error_message="Failed to generate any AI content")
                return False
            
            # Step 4: Update article with results
            self._update_article_processing(
                article_id,
                title_embedding=title_embedding,
                summary=summary,
                summary_embedding=summary_embedding
            )
            
            # Step 5: Topic matching and clustering (if we have embeddings)
            if title_embedding or summary_embedding:
                self._process_topic_matching_and_clustering(
                    article_id, title, title_embedding, summary_embedding, summary, user_id
                )
            
            logger.info(f"Successfully processed article: {title[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error processing article {article_id}: {e}")
            self._update_article_processing(article_id, error_message=str(e))
            return False
    
    def _process_topic_matching_and_clustering(self,
                                             article_id: int,
                                             title: str,
                                             title_embedding: Optional[List[float]],
                                             summary_embedding: Optional[List[float]],
                                             summary: Optional[str],
                                             user_id: Optional[int]):
        """Process topic matching and event clustering for an article."""
        try:
            # Find similar topics
            similar_topics = self.similarity_calculator.find_similar_topics(
                article_title_embedding=title_embedding,
                article_summary_embedding=summary_embedding,
                topics=self.cached_topics,
                threshold=self.similarity_threshold
            )
            
            if similar_topics:
                logger.info(f"Found {len(similar_topics)} similar topics for article {article_id}")
                
                # Create topic associations
                for topic in similar_topics:
                    self._create_article_topic_association(
                        article_id, topic['id'], topic['similarity_score']
                    )
                
                # Event clustering (if summary exists)
                if summary:
                    for topic in similar_topics:
                        topic_user_id = topic.get('user_id', user_id)
                        if not topic_user_id:
                            continue
                        
                        # Detect or create cluster
                        cluster_result = self.clustering_service.detect_or_create_cluster(
                            user_id=topic_user_id,
                            topic_id=topic['id'],
                            topic_name=topic.get('name', 'Unknown Topic'),
                            article_title=title,
                            article_summary=summary,
                            title_embedding=title_embedding,
                            summary_embedding=summary_embedding
                        )
                        
                        if cluster_result:
                            event_id = cluster_result.get('id')
                            relevance_score = cluster_result.get('relevance_score', 0.8)
                            
                            success = self.clustering_service.create_article_event_association(
                                article_id, event_id, relevance_score
                            )
                            
                            if success:
                                logger.info(f"Successfully clustered article {article_id} into event {event_id}")
            else:
                logger.info(f"Found 0 similar topics above threshold {self.similarity_threshold}")
                
        except Exception as e:
            logger.error(f"Error in topic matching and clustering: {e}")
    
    def _create_article_topic_association(self, article_id: int, topic_id: int, relevance_score: float) -> bool:
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
    
    def _update_article_processing(self, article_id: int, **kwargs) -> bool:
        """Update article with processing results via backend API."""
        try:
            data = {
                'title_embedding': kwargs.get('title_embedding'),
                'summary_embedding': kwargs.get('summary_embedding'),
                'embedding_model': self.embedding_generator.embedding_model,
                'summary': kwargs.get('summary'),
                'summary_model': get_llm_client().default_chat_model if get_llm_client() else None,
                'processed_at': datetime.now().isoformat(),
                'error_message': kwargs.get('error_message')
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
    
    def process_new_topic(self, topic_id: int, topic_name: str, topic_embedding: List[float], user_id: int) -> bool:
        """Process all existing articles for a new topic with similarity calculation."""
        logger.info(f"Processing new topic '{topic_name}' (ID: {topic_id}) for user {user_id}")
        
        try:
            # Use backend client to process existing articles
            return self.backend_client.backfill_existing_articles(
                topic_id=topic_id,
                topic_embedding=topic_embedding,
                user_id=user_id,
                threshold=self.similarity_threshold
            )
            
        except Exception as e:
            logger.error(f"Error processing new topic '{topic_name}': {e}")
            return False
    
    def run_processing_cycle(self):
        """Run a single processing cycle."""
        logger.info("Starting AI postprocessing cycle")
        
        # Reload prompts and settings
        try:
            self.reload_prompts()
        except Exception as e:
            logger.error(f"Failed to reload prompts, skipping this cycle: {e}")
            return
        
        # Get pending articles
        pending_articles = self.get_pending_articles()
        
        if not pending_articles:
            logger.info("No articles need processing at this time")
            return
        
        # Process articles
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
    
    def run_daily_summary_generation(self):
        """Generate daily summaries for all users."""
        try:
            stats = self.daily_summary_service.generate_summaries_for_all_users()
            logger.info(f"Daily summary generation completed: {stats}")
        except Exception as e:
            logger.error(f"Error in daily summary generation: {e}")
    
    def generate_user_daily_summary(self, user_id: int, username: str):
        """Generate daily summary for specific user."""
        try:
            success = self.daily_summary_service.generate_user_daily_summary(user_id, username)
            if success:
                logger.info(f"Successfully generated daily summary for user {user_id}")
            else:
                logger.error(f"Failed to generate daily summary for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error generating daily summary for user {user_id}: {e}")
            return False
    
    def run_daemon(self, with_api_server=True, api_port=8001):
        """Run the postprocessor as a daemon service with optional API server."""
        logger.info("Starting AI postprocessing daemon")
        
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
                
                # Check for daily summary generation (00:00-00:30)
                daily_summary_enabled = self.config.get(ConfigKeys.DAILY_SUMMARY_ENABLED, default=True)
                if (daily_summary_enabled and 
                    last_daily_summary_date != current_date and 
                    current_time.hour == 0 and current_time.minute < 30):
                    try:
                        logger.info("Starting daily summary generation for all users...")
                        self.run_daily_summary_generation()
                        last_daily_summary_date = current_date
                        logger.info("Daily summary generation completed")
                    except Exception as e:
                        logger.error(f"Error in daily summary generation: {e}")
                elif not daily_summary_enabled:
                    logger.debug("Daily summary generation is disabled")
                
                # Regular article processing cycle
                self.run_processing_cycle()
                
                # Wait before next cycle (2 minutes)
                for _ in range(120):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                if not self.running:
                    break
                # Wait for configurable interval before next cycle
                postprocess_interval = self.config.get(ConfigKeys.POSTPROCESS_INTERVAL, default=2)
                time.sleep(postprocess_interval * 60)  # Convert minutes to seconds
        
        logger.info("AI postprocessing daemon stopped")
        return True
    
    def run_once(self) -> bool:
        """Execute PostProcess service once and exit."""
        logger.info("Running AI postprocessor once")
        
        try:
            self.run_processing_cycle()
            return True
        except Exception as e:
            logger.error(f"Error in run_once: {e}")
            return False


class BackendAPIClient:
    """Extended backend client with additional methods for the main service."""
    
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        import requests
        self.requests = requests
    
    def backfill_existing_articles(self, topic_id: int, topic_embedding: List[float], user_id: int, threshold: float) -> bool:
        """Backfill existing articles for a new topic."""
        try:
            # This would implement the backfill logic
            # For now, return True as placeholder
            self.logger.info(f"Backfilling articles for topic {topic_id} with threshold {threshold}")
            return True
        except Exception as e:
            self.logger.error(f"Error in backfill_existing_articles: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for daily summary generation."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/users")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            self.logger.error(f"Error getting all users: {e}")
            return []
    
    def check_summary_exists(self, user_id: int, summary_date) -> bool:
        """Check if daily summary exists for user and date."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/user-summary/{user_id}/{summary_date}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error checking summary existence: {e}")
            return False
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data including custom prompts."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/user/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            return None
    
    def get_user_topics(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's topics."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/topics?user_id={user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error getting user topics: {e}")
            return []
    
    def get_topic_articles(self, topic_id: int, date) -> List[Dict[str, Any]]:
        """Get articles for topic on specific date."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/article-topics?topic_id={topic_id}&date={date}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.logger.error(f"Error getting topic articles: {e}")
            return []
    
    def get_topic_events(self, topic_id: int, date) -> List[Dict[str, Any]]:
        """Get events for topic on specific date."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/events?topic_id={topic_id}&created_date={date}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.logger.error(f"Error getting topic events: {e}")
            return []
    
    def get_recent_summaries(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent daily summaries for user."""
        try:
            response = self.requests.get(f"{self.backend_url}/api/internal/user-summaries/{user_id}?limit={limit}")
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            self.logger.error(f"Error getting recent summaries: {e}")
            return []
    
    def save_daily_summary(self, user_id: int, date, summary: str, cover_prompt: Optional[str], cover_s3key: Optional[str]) -> bool:
        """Save daily summary to database."""
        try:
            data = {
                'user_id': user_id,
                'date': date.isoformat(),
                'summary': summary,
                'cover_prompt': cover_prompt,
                'cover_arguments': None,
                'cover_seed': None,
                'cover_s3key': cover_s3key
            }
            
            response = self.requests.post(f"{self.backend_url}/api/internal/user-summaries", json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error saving daily summary: {e}")
            return False
    
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
            success = postprocessor_instance.generate_user_daily_summary(user_id, username)
            
            if success:
                logger.info(f"API: Successfully generated daily summary for user {user_id}")
                return {
                    "success": True,
                    "message": f"Daily summary generated for user {user_id}",
                    "user_id": user_id,
                    "username": username,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to generate daily summary")
                
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


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NewsFrontier AI PostProcess Service")
    parser.add_argument('--daemon', action='store_true', help='Run as daemon service')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    parser.add_argument('--backend-url', default=None, help='Override backend API URL')
    parser.add_argument('--no-api', action='store_true', 
                       help='Disable HTTP API server (daemon mode runs API server by default)')
    parser.add_argument('--api-port', type=int, default=8001, 
                       help='Port for HTTP API server (default: 8001)')
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Print configuration
    logger.info("=== NewsFrontier AI PostProcess Service ===")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Backend URL: {args.backend_url or os.getenv('BACKEND_URL', 'http://localhost:8000')}")
    logger.info("=" * 45)
    
    # Create postprocessor service
    postprocessor = AIPostProcessService()
    
    # Override backend URL if provided
    if args.backend_url:
        postprocessor.backend_url = args.backend_url
        postprocessor.backend_client.backend_url = args.backend_url
    
    try:
        if args.daemon:
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


if __name__ == "__main__":
    main()