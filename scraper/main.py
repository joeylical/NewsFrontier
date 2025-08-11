#!/usr/bin/env python3
"""
NewsFrontier RSS Scraper Service

This service fetches RSS feeds, parses them, and stores articles in the database
for further processing by the AI postprocess service.
"""

import sys
import os
import time
import signal
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib

import requests
import feedparser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RSSScraperService:
    """RSS scraper service for fetching and processing RSS feeds."""
    
    def __init__(self):
        self.running = True
        self.session = None
        self.backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
        logger.info(f"Scraper initialized with backend URL: {self.backend_url}")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def setup_database(self):
        """Setup database connection."""
        try:
            # For now, we'll use the backend API instead of direct database access
            # This is simpler for the initial implementation
            logger.info("Using backend API for database operations")
            return True
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            return False
            
    def get_pending_feeds(self) -> List[Dict[str, Any]]:
        """Get feeds that need to be fetched from the backend API."""
        try:
            response = requests.get(f"{self.backend_url}/api/internal/feeds/pending")
            response.raise_for_status()
            feeds = response.json()
            logger.info(f"Found {len(feeds)} feeds pending fetch")
            return feeds
        except requests.RequestException as e:
            logger.error(f"Failed to get pending feeds: {e}")
            return []
            
    def fetch_rss_feed(self, feed_url: str, feed_id: int) -> Optional[Dict[str, Any]]:
        """Fetch and parse an RSS feed."""
        try:
            logger.info(f"Fetching RSS feed: {feed_url}")
            
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'NewsFrontier RSS Reader 1.0 (https://newsfrontier.example.com)',
                'Accept': 'application/rss+xml, application/xml, text/xml',
            }
            
            # Fetch the RSS feed
            response = requests.get(feed_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse the RSS content
            feed_data = feedparser.parse(response.content)
            
            if feed_data.bozo and feed_data.bozo_exception:
                logger.warning(f"RSS feed parsing issues for {feed_url}: {feed_data.bozo_exception}")
            
            # Calculate content hash for deduplication
            content_hash = hashlib.sha256(response.content).hexdigest()
            
            return {
                'raw_content': response.text,
                'content_hash': content_hash,
                'http_status': response.status_code,
                'content_encoding': response.encoding,
                'parsed_feed': feed_data,
                'feed_id': feed_id
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            return None
            
    def extract_articles(self, feed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract articles from parsed RSS feed data."""
        articles = []
        parsed_feed = feed_data['parsed_feed']
        
        for entry in parsed_feed.entries:
            try:
                # Extract article data
                article = {
                    'guid': getattr(entry, 'id', getattr(entry, 'guid', entry.link if hasattr(entry, 'link') else None)),
                    'title': getattr(entry, 'title', 'Untitled'),
                    'content': self._extract_content(entry),
                    'url': getattr(entry, 'link', None),
                    'author': getattr(entry, 'author', None),
                    'published_at': self._parse_published_date(entry),
                    'category': self._extract_category(entry)
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error extracting article data: {e}")
                continue
                
        logger.info(f"Extracted {len(articles)} articles from feed")
        return articles
        
    def _extract_content(self, entry) -> Optional[str]:
        """Extract content from RSS entry."""
        # Try different content fields in order of preference
        content_fields = ['content', 'summary', 'description']
        
        for field in content_fields:
            if hasattr(entry, field):
                content = getattr(entry, field)
                if isinstance(content, list) and content:
                    return content[0].get('value', '')
                elif isinstance(content, str):
                    return content
                    
        return None
        
    def _parse_published_date(self, entry) -> Optional[str]:
        """Parse published date from RSS entry."""
        date_fields = ['published_parsed', 'updated_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_tuple = getattr(entry, field)
                if time_tuple:
                    try:
                        dt = datetime(*time_tuple[:6])
                        return dt.isoformat()
                    except Exception:
                        continue
                        
        return None
        
    def _extract_category(self, entry) -> Optional[str]:
        """Extract category from RSS entry."""
        if hasattr(entry, 'tags') and entry.tags:
            return entry.tags[0].get('term', None)
        elif hasattr(entry, 'category'):
            return entry.category
        return None
        
    def update_feed_status(self, feed_id: int, status: str, fetch_time: datetime = None) -> bool:
        """Update feed fetch status via backend API."""
        try:
            if fetch_time is None:
                fetch_time = datetime.now()
                
            data = {
                'status': status,
                'fetch_time': fetch_time.isoformat()
            }
            
            response = requests.post(
                f"{self.backend_url}/api/internal/feeds/{feed_id}/status",
                json=data
            )
            response.raise_for_status()
            
            logger.info(f"Updated feed {feed_id} status to {status}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to update feed status: {e}")
            return False
            
    def create_fetch_record(self, feed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update RSS fetch record via backend API."""
        try:
            fetch_record_data = {
                'rss_feed_id': feed_data['feed_id'],
                'raw_content': feed_data['raw_content'],
                'content_hash': feed_data['content_hash'],
                'http_status': feed_data['http_status'],
                'content_encoding': feed_data['content_encoding']
            }
            
            response = requests.post(
                f"{self.backend_url}/api/internal/fetch-records",
                json=fetch_record_data
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('is_duplicate'):
                logger.info(f"Updated existing fetch record: {result['id']} (duplicate content)")
            else:
                logger.info(f"Created new fetch record: {result['id']}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"Failed to create/update fetch record: {e}")
            return None
    
    def create_articles(self, articles: List[Dict[str, Any]], fetch_record_id: int) -> bool:
        """Create articles via backend API."""
        try:
            # Add fetch_record_id to each article
            for article in articles:
                article['rss_fetch_record_id'] = fetch_record_id
                
            response = requests.post(
                f"{self.backend_url}/api/internal/articles",
                json=articles
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Created articles: {result}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create articles: {e}")
            return False
            
    def process_feed(self, feed: Dict[str, Any]) -> bool:
        """Process a single RSS feed."""
        feed_id = feed['id']
        feed_url = feed['url']
        feed_title = feed.get('title', 'Unknown Feed')
        
        logger.info(f"Processing feed: {feed_title} ({feed_url})")
        
        try:
            # Fetch and parse the RSS feed
            feed_data = self.fetch_rss_feed(feed_url, feed_id)
            if not feed_data:
                self.update_feed_status(feed_id, 'failed')
                return False
                
            # Create or update RSS fetch record with raw content
            fetch_record_result = self.create_fetch_record(feed_data)
            if not fetch_record_result:
                logger.error(f"Failed to create/update fetch record for {feed_title}")
                self.update_feed_status(feed_id, 'failed')
                return False
            
            # Check if this is duplicate content
            if fetch_record_result.get('is_duplicate', False):
                logger.info(f"Duplicate content detected for {feed_title}, skipping article processing")
                self.update_feed_status(feed_id, 'success')
                return True
            
            # Extract articles from the feed (only for new content)
            articles = self.extract_articles(feed_data)
            
            if articles:
                # Create articles via API with proper fetch_record_id
                fetch_record_id = fetch_record_result['id']
                success = self.create_articles(articles, fetch_record_id)
                if success:
                    self.update_feed_status(feed_id, 'success')
                    logger.info(f"Successfully processed {len(articles)} articles from {feed_title}")
                    return True
                else:
                    self.update_feed_status(feed_id, 'failed')
                    return False
            else:
                # No new articles, but fetch was successful
                self.update_feed_status(feed_id, 'success')
                logger.info(f"No new articles found in {feed_title}")
                return True
                
        except Exception as e:
            logger.error(f"Error processing feed {feed_title}: {e}")
            self.update_feed_status(feed_id, 'failed')
            return False
            
    def run_scraper_cycle(self):
        """Run a single scraper cycle."""
        logger.info("Starting RSS scraper cycle")
        
        # Get feeds that need fetching
        pending_feeds = self.get_pending_feeds()
        
        if not pending_feeds:
            logger.info("No feeds need fetching at this time")
            return
            
        # Process each feed
        successful_feeds = 0
        failed_feeds = 0
        
        for feed in pending_feeds:
            if not self.running:
                logger.info("Scraper stopped during cycle")
                break
                
            try:
                if self.process_feed(feed):
                    successful_feeds += 1
                else:
                    failed_feeds += 1
                    
                # Small delay between feeds to be nice to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error processing feed: {e}")
                failed_feeds += 1
                
        logger.info(f"Scraper cycle completed: {successful_feeds} successful, {failed_feeds} failed")
        
    def run_daemon(self):
        """Run the scraper as a daemon service."""
        logger.info("Starting RSS scraper daemon")
        
        if not self.setup_database():
            logger.error("Failed to setup database connection")
            return False
            
        # Main daemon loop
        while self.running:
            try:
                self.run_scraper_cycle()
                
                # Wait before next cycle (default 5 minutes)
                for _ in range(30):  # 5 minutes = 300 seconds
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                if not self.running:
                    break
                time.sleep(60)  # Wait 1 minute before retry
                
        logger.info("RSS scraper daemon stopped")
        return True
        
    def run_once(self):
        """Run the scraper once and exit."""
        logger.info("Running RSS scraper once")
        
        if not self.setup_database():
            logger.error("Failed to setup database connection")
            return False
            
        self.run_scraper_cycle()
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NewsFrontier RSS Scraper Service")
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
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help='Set logging level'
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create scraper service
    scraper = RSSScraperService()
    
    try:
        if args.daemon:
            success = scraper.run_daemon()
        elif args.once:
            success = scraper.run_once()
        else:
            # Default to daemon mode
            logger.info("No mode specified, defaulting to daemon mode")
            success = scraper.run_daemon()
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
