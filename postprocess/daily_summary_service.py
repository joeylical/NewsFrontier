#!/usr/bin/env python3
"""
Daily Summary Generation Service Module

This module handles the generation of personalized daily summaries for users.
It gathers user context, formats content, generates AI-powered summaries,
and manages cover image generation and storage.
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List

# Import LLM functionality from shared library
try:
    from newsfrontier_lib import get_llm_client
    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import LLM library: {e}")
    raise


class DailySummaryService:
    """
    Handles personalized daily summary generation for users.
    
    This service provides comprehensive daily summary generation including:
    - User context gathering (topics, articles, events)
    - Content formatting with local dashboard links
    - AI-powered summary generation with custom prompts
    - Cover image generation and upload
    - Summary storage with metadata
    """
    
    def __init__(self, prompt_manager, backend_client, image_generator):
        """
        Initialize the daily summary service.
        
        Args:
            prompt_manager: Manager for retrieving prompts from database
            backend_client: Client for backend API communication
            image_generator: Service for cover image generation
        """
        self.prompt_manager = prompt_manager
        self.backend_client = backend_client
        self.image_generator = image_generator
        self.llm_client = get_llm_client()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_user_daily_summary(self, user_id: int, username: str, summary_date: Optional[date] = None) -> bool:
        """
        Generate daily summary for specific user.
        
        Args:
            user_id: User database ID
            username: Username for logging
            summary_date: Date for summary (defaults to today)
            
        Returns:
            True if summary generated successfully, False otherwise
            
        Process:
        1. Check for existing summary (avoid duplicates)
        2. Gather user context (topics, articles, events)
        3. Generate summary content using LLM
        4. Generate cover image prompt (optional)
        5. Save summary with metadata
        """
        try:
            if summary_date is None:
                summary_date = datetime.now().date()
                
            self.logger.info(f"Generating daily summary for user {user_id} ({username}) for {summary_date}")
            
            # Check for existing summary
            if self._summary_exists(user_id, summary_date):
                self.logger.info(f"Daily summary already exists for user {user_id} on {summary_date}")
                return True
            
            # Gather user context
            user_context = self._get_user_daily_context(user_id, summary_date)
            if not user_context:
                self.logger.info(f"No relevant content found for user {user_id}")
                return False
            
            # Generate summary content
            summary_content = self._create_daily_summary_content(user_context)
            if not summary_content:
                self.logger.error(f"Failed to generate summary content for user {user_id}")
                return False
            
            # Generate cover image prompt (optional - can fail without stopping)
            cover_prompt = None
            try:
                cover_prompt = self.image_generator.generate_cover_image_prompt(summary_content)
            except Exception as e:
                self.logger.warning(f"Failed to generate cover image prompt for user {user_id}: {e}")
            
            # Save daily summary
            success = self._save_daily_summary(user_id, summary_date, summary_content, cover_prompt)
            
            if success:
                self.logger.info(f"Successfully generated daily summary for user {user_id}")
            else:
                self.logger.error(f"Failed to save daily summary for user {user_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary for user {user_id}: {e}")
            return False
    
    def generate_summaries_for_all_users(self) -> Dict[str, int]:
        """
        Generate daily summaries for all users.
        
        Returns:
            Dictionary with generation statistics
            
        Features:
        - Processes each user individually
        - Comprehensive error handling per user
        - Returns detailed statistics
        """
        try:
            users = self.backend_client.get_all_users()
            
            self.logger.info(f"Starting daily summary generation for {len(users)} users")
            
            stats = {
                'total_users': len(users),
                'successful': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for user in users:
                try:
                    user_id = user['id']
                    username = user.get('username', 'User')
                    
                    success = self.generate_user_daily_summary(user_id, username)
                    
                    if success:
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to generate daily summary for user {user.get('id', 'unknown')}: {e}")
                    stats['failed'] += 1
            
            self.logger.info(f"Daily summary generation completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in generate_summaries_for_all_users: {e}")
            return {'total_users': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
    
    def _summary_exists(self, user_id: int, summary_date: date) -> bool:
        """
        Check if daily summary already exists for user and date.
        
        Args:
            user_id: User database ID
            summary_date: Date to check
            
        Returns:
            True if summary exists, False otherwise
        """
        try:
            return self.backend_client.check_summary_exists(user_id, summary_date)
        except Exception as e:
            self.logger.error(f"Error checking if summary exists: {e}")
            return False
    
    def _get_user_daily_context(self, user_id: int, summary_date: date) -> Optional[Dict[str, Any]]:
        """
        Gather user data for daily summary generation.
        
        Args:
            user_id: User database ID
            summary_date: Date for summary generation
            
        Returns:
            Dictionary with user context or None if insufficient data
            
        Context Includes:
        - User profile and custom prompt
        - User-defined topics
        - Relevant articles published today
        - New events created today
        - Recent daily summaries (last 5 for context)
        """
        try:
            # Get user info and custom prompt
            user_data = self.backend_client.get_user_data(user_id)
            if not user_data:
                self.logger.error(f"User {user_id} not found")
                return None
            
            # Get user's topics
            user_topics = self.backend_client.get_user_topics(user_id)
            if not user_topics:
                self.logger.info(f"User {user_id} has no topics defined")
                return None
            
            # Get today's relevant articles
            relevant_articles = self._get_relevant_articles(user_topics, summary_date)
            
            # Get new events created today
            new_events = self._get_new_events(user_topics, summary_date)
            
            # Get recent daily summaries for context
            recent_summaries = self.backend_client.get_recent_summaries(user_id, limit=5)
            
            context = {
                'user_id': user_id,
                'username': user_data.get('username', 'User'),
                'custom_prompt': user_data.get('daily_summary_prompt', ''),
                'topics': user_topics,
                'relevant_articles': relevant_articles,
                'new_events': new_events,
                'recent_summaries': recent_summaries
            }
            
            self.logger.debug(f"Gathered context for user {user_id}: "
                            f"{len(relevant_articles)} articles, {len(new_events)} events")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting user daily context for user {user_id}: {e}")
            return None
    
    def _get_relevant_articles(self, user_topics: List[Dict[str, Any]], summary_date: date) -> List[Dict[str, Any]]:
        """
        Get relevant articles for user topics on specific date.
        
        Args:
            user_topics: List of user topic dictionaries
            summary_date: Date to filter articles
            
        Returns:
            List of relevant article dictionaries
        """
        relevant_articles = []
        
        for topic in user_topics:
            try:
                topic_articles = self.backend_client.get_topic_articles(
                    topic['id'], summary_date
                )
                relevant_articles.extend(topic_articles)
            except Exception as e:
                self.logger.error(f"Error getting articles for topic {topic['id']}: {e}")
        
        return relevant_articles
    
    def _get_new_events(self, user_topics: List[Dict[str, Any]], summary_date: date) -> List[Dict[str, Any]]:
        """
        Get new events created today for user topics.
        
        Args:
            user_topics: List of user topic dictionaries
            summary_date: Date to filter events
            
        Returns:
            List of new event dictionaries
        """
        new_events = []
        
        for topic in user_topics:
            try:
                topic_events = self.backend_client.get_topic_events(
                    topic['id'], summary_date
                )
                # Add topic information to each event
                for event in topic_events:
                    event['topic_name'] = topic.get('name', 'Unknown Topic')
                    event['topic_id'] = topic['id']
                new_events.extend(topic_events)
            except Exception as e:
                self.logger.error(f"Error getting events for topic {topic['id']}: {e}")
        
        return new_events
    
    def _create_daily_summary_content(self, user_context: Dict[str, Any]) -> Optional[str]:
        """
        Generate daily summary content using LLM.
        
        Args:
            user_context: User data and content context
            
        Returns:
            Generated summary content or None if failed
            
        Raises:
            ValueError: If daily summary system prompt not available from database
        """
        try:
            # Get daily summary system prompt from database - NO DEFAULT
            system_prompt = self.prompt_manager.get_prompt('daily_summary_system')
            if not system_prompt:
                raise ValueError("Daily summary system prompt not available from database")
            
            # Format content for LLM
            articles_text = self._format_articles_for_summary(user_context['relevant_articles'])
            events_text = self._format_events_for_summary(user_context['new_events'])
            recent_summaries_text = self._format_recent_summaries(user_context['recent_summaries'])
            
            # Format system prompt with context
            formatted_system_prompt = system_prompt.format(
                articles=articles_text,
                summaries=recent_summaries_text,
                events=events_text
            )
            
            # Add user's personal prompt if provided
            user_daily_prompt = (user_context.get('custom_prompt') or '').strip()
            if user_daily_prompt:
                try:
                    formatted_user_prompt = user_daily_prompt.format(
                        recent_summaries=recent_summaries_text,
                        articles=articles_text,
                        new_events=events_text,
                        username=user_context.get('username', 'User')
                    )
                    full_prompt = f"{formatted_system_prompt}\n\nAdditional User Instructions:\n{formatted_user_prompt}"
                except Exception as e:
                    self.logger.warning(f"Error formatting user prompt: {e}, using system prompt only")
                    full_prompt = formatted_system_prompt
            else:
                full_prompt = formatted_system_prompt
            
            # Generate summary using analysis model
            summary = self.llm_client.create_analysis_completion(
                prompt=full_prompt,
                max_tokens=4000,
                temperature=0.7
            )
            
            if summary:
                self.logger.info(f"Generated daily summary content: {len(summary)} characters")
            else:
                self.logger.warning("LLM returned empty daily summary")
            
            return summary
            
        except ValueError:
            # Re-raise prompt errors
            raise
        except Exception as e:
            self.logger.error(f"Error creating daily summary content: {e}")
            return None
    
    def _format_articles_for_summary(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format articles for summary context with local dashboard links.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Formatted markdown text with local links
        """
        if not articles:
            self.logger.info("No articles found for daily summary")
            return "No relevant articles found for today."
        
        formatted_articles = []
        self.logger.info(f"Formatting {len(articles)} articles for daily summary")
        
        # Limit to 10 most relevant articles
        for article in articles[:10]:
            article_info = article.get('rss_item', {})
            title = article_info.get('title', 'Untitled')
            article_id = article_info.get('id', '')
            summary = ''
            
            # Get article summary if available
            derivatives = article_info.get('derivatives', [])
            if derivatives:
                summary = derivatives[0].get('summary', '')
            
            # Create local dashboard link
            article_link = f"/dashboard/article/{article_id}" if article_id else "#"
            formatted_articles.append(f"- **[{title}]({article_link})**")
            if summary:
                formatted_articles.append(f"  Summary: {summary}")
        
        return "\n".join(formatted_articles)
    
    def _format_events_for_summary(self, events: List[Dict[str, Any]]) -> str:
        """
        Format new events for summary context.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Formatted markdown text with event information
        """
        if not events:
            self.logger.info("No events found for daily summary")
            return "No new events detected today."
        
        formatted_events = []
        self.logger.info(f"Formatting {len(events)} events for daily summary")
        
        for event in events:
            title = event.get('title', 'Untitled Event')
            event_id = event.get('id', '')
            description = event.get('description', '')
            topic_name = event.get('topic_name', 'Unknown Topic')
            topic_id = event.get('topic_id', '')
            
            # Create local dashboard links
            event_link = f"/dashboard/clusters/{event_id}" if event_id else "#"
            topic_link = f"/dashboard/topics/{topic_id}" if topic_id else "#"
            
            formatted_events.append(f"- **Topic: [{topic_name}]({topic_link})**")
            formatted_events.append(f"  - **Event: [{title}]({event_link})**")
            if description:
                formatted_events.append(f"    {description}")
        
        return "\n".join(formatted_events)
    
    def _format_recent_summaries(self, summaries: List[Dict[str, Any]]) -> str:
        """
        Format recent summaries for historical context.
        
        Args:
            summaries: List of recent summary dictionaries
            
        Returns:
            Formatted text with summary excerpts
        """
        if not summaries:
            self.logger.info("No recent summaries found for context")
            return "No recent summaries available."
        
        formatted_summaries = []
        self.logger.info(f"Formatting {len(summaries)} recent summaries for context")
        
        for summary in summaries:
            summary_date = summary.get('date', 'Unknown date')
            content = summary.get('summary', '')
            # Truncate long summaries for context
            if len(content) > 200:
                content = content[:200] + "..."
            formatted_summaries.append(f"- {summary_date}: {content}")
        
        return "\n".join(formatted_summaries)
    
    def _save_daily_summary(self,
                          user_id: int,
                          summary_date: date,
                          summary_content: str,
                          cover_prompt: Optional[str]) -> bool:
        """
        Save daily summary to database with optional cover image.
        
        Args:
            user_id: User database ID
            summary_date: Summary date
            summary_content: Generated summary text
            cover_prompt: Image description (optional)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Generate and upload cover image if prompt available
            cover_s3key = None
            if cover_prompt:
                cover_s3key = self.image_generator.generate_and_upload_cover_image(
                    cover_prompt, summary_date
                )
            
            # Save summary via backend
            success = self.backend_client.save_daily_summary(
                user_id=user_id,
                date=summary_date,
                summary=summary_content,
                cover_prompt=cover_prompt,
                cover_s3key=cover_s3key
            )
            
            if success:
                self.logger.info(f"Successfully saved daily summary for user {user_id} on {summary_date}")
                if cover_s3key:
                    self.logger.info(f"Cover image uploaded to S3: {cover_s3key}")
            else:
                self.logger.error(f"Failed to save daily summary for user {user_id}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving daily summary for user {user_id}: {e}")
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get statistics about daily summary service.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            'llm_client_available': self.llm_client.is_available() if self.llm_client else False,
            'daily_summary_prompt_available': self.prompt_manager.get_prompt('daily_summary_system') is not None,
            'backend_client_available': self.backend_client is not None,
            'image_generator_available': self.image_generator is not None
        }