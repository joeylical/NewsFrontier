"""
SQLAlchemy ORM models for NewsFrontier database schema.

This module defines all database models corresponding to the tables
described in the project README.
"""

import os
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Float,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid as uuid_lib

from .database import Base

# Get embedding dimension from environment variable
def get_embedding_dimension() -> int:
    """Get embedding dimension from environment variable, default to 1536."""
    return int(os.getenv('EMBEDDING_DIMENSION', 1536))


class User(Base):
    """User authentication and profile information."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits_accrual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_summary_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("credits >= 0", name="check_credits_non_negative"),
        CheckConstraint("credits_accrual >= 0", name="check_credits_accrual_non_negative"),
    )
    
    # Relationships
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="user", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    summaries: Mapped[List["UserSummary"]] = relationship("UserSummary", back_populates="user", cascade="all, delete-orphan")
    rss_subscriptions: Mapped[List["RSSSubscription"]] = relationship("RSSSubscription", back_populates="user", cascade="all, delete-orphan")
    user_topics: Mapped[List["UserTopic"]] = relationship("UserTopic", back_populates="user", cascade="all, delete-orphan")


class RSSFeed(Base):
    """RSS feed source configuration."""
    __tablename__ = "rss_feeds"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid_lib.uuid4)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    last_fetch_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_fetch_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("last_fetch_status IN ('pending', 'success', 'failed', 'timeout')", 
                       name="check_last_fetch_status_valid"),
    )
    
    # Relationships
    subscriptions: Mapped[List["RSSSubscription"]] = relationship("RSSSubscription", back_populates="rss_feed", cascade="all, delete-orphan")
    fetch_records: Mapped[List["RSSFetchRecord"]] = relationship("RSSFetchRecord", back_populates="rss_feed", cascade="all, delete-orphan")


class RSSSubscription(Base):
    """User subscriptions to RSS feeds."""
    __tablename__ = "rss_subscriptions"
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    rss_uuid: Mapped[uuid_lib.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rss_feeds.uuid", ondelete="CASCADE"), primary_key=True)
    alias: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rss_subscriptions")
    rss_feed: Mapped["RSSFeed"] = relationship("RSSFeed", back_populates="subscriptions")


class RSSFetchRecord(Base):
    """Raw RSS content fetched from sources with deduplication support."""
    __tablename__ = "rss_fetch_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rss_feed_id: Mapped[int] = mapped_column(Integer, ForeignKey("rss_feeds.id", ondelete="CASCADE"), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    first_fetch_timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_fetch_timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_encoding: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    rss_feed: Mapped["RSSFeed"] = relationship("RSSFeed", back_populates="fetch_records")
    items_metadata: Mapped[List["RSSItemMetadata"]] = relationship("RSSItemMetadata", back_populates="fetch_record", cascade="all, delete-orphan")


class RSSItemMetadata(Base):
    """AI-extracted article data from RSS items."""
    __tablename__ = "rss_items_metadata"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rss_fetch_record_id: Mapped[int] = mapped_column(Integer, ForeignKey("rss_fetch_records.id", ondelete="CASCADE"), nullable=False)
    guid: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints and unique constraints
    __table_args__ = (
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", 
                       name="check_processing_status_valid"),
        CheckConstraint("processing_attempts >= 0 AND processing_attempts <= 10", 
                       name="check_processing_attempts_range"),
        UniqueConstraint("rss_fetch_record_id", "guid", name="unique_rss_item_guid_per_feed"),
    )
    
    # Relationships
    fetch_record: Mapped["RSSFetchRecord"] = relationship("RSSFetchRecord", back_populates="items_metadata")
    derivatives: Mapped[Optional["RSSItemDerivative"]] = relationship("RSSItemDerivative", back_populates="rss_item", uselist=False, cascade="all, delete-orphan")
    article_topics: Mapped[List["ArticleTopic"]] = relationship("ArticleTopic", back_populates="rss_item", cascade="all, delete-orphan")
    article_events: Mapped[List["ArticleEvent"]] = relationship("ArticleEvent", back_populates="rss_item", cascade="all, delete-orphan")


class RSSItemDerivative(Base):
    """AI-generated content derived from RSS items."""
    __tablename__ = "rss_item_derivatives"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rss_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("rss_items_metadata.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(get_embedding_dimension()), nullable=True)
    summary_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(get_embedding_dimension()), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    summary_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    embeddings_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed')", 
                       name="check_derivative_processing_status_valid"),
    )
    
    # Relationships
    rss_item: Mapped["RSSItemMetadata"] = relationship("RSSItemMetadata", back_populates="derivatives")


class Topic(Base):
    """User-defined topics for news categorization."""
    __tablename__ = "topics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    topic_vector: Mapped[Optional[List[float]]] = mapped_column(Vector(get_embedding_dimension()), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_user_topic_name"),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="topics")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="topic", cascade="all, delete-orphan")
    article_topics: Mapped[List["ArticleTopic"]] = relationship("ArticleTopic", back_populates="topic", cascade="all, delete-orphan")
    user_topics: Mapped[List["UserTopic"]] = relationship("UserTopic", back_populates="topic", cascade="all, delete-orphan")


class ArticleTopic(Base):
    """Many-to-many relationship between articles and topics."""
    __tablename__ = "article_topics"
    
    rss_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("rss_items_metadata.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("relevance_score >= 0.0 AND relevance_score <= 1.0", 
                       name="check_relevance_score_range"),
    )
    
    # Relationships
    rss_item: Mapped["RSSItemMetadata"] = relationship("RSSItemMetadata", back_populates="article_topics")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="article_topics")


class Event(Base):
    """News events extracted from article clustering."""
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(get_embedding_dimension()), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="events")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="events")
    article_events: Mapped[List["ArticleEvent"]] = relationship("ArticleEvent", back_populates="event", cascade="all, delete-orphan")


class ArticleEvent(Base):
    """Many-to-many relationship between articles and events."""
    __tablename__ = "article_events"
    
    rss_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("rss_items_metadata.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("relevance_score >= 0.0 AND relevance_score <= 1.0", 
                       name="check_event_relevance_score_range"),
    )
    
    # Relationships
    rss_item: Mapped["RSSItemMetadata"] = relationship("RSSItemMetadata", back_populates="article_events")
    event: Mapped["Event"] = relationship("Event", back_populates="article_events")


class UserTopic(Base):
    """Many-to-many relationship between users and topics with preferences."""
    __tablename__ = "user_topics"
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10", 
                       name="check_priority_range"),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_topics")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="user_topics")


class UserSummary(Base):
    """Daily personalized news summaries for users."""
    __tablename__ = "user_summaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_arguments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cover_s3key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="unique_user_summary_per_date"),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="summaries")


class SystemSetting(Base):
    """System-wide configuration settings."""
    __tablename__ = "system_settings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    setting_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    setting_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Check constraints
    __table_args__ = (
        CheckConstraint("setting_type IN ('string', 'integer', 'boolean', 'json', 'float')", 
                       name="check_setting_type_valid"),
    )


# Create indexes programmatically (these will be created via Alembic migrations or init.sql)
def create_performance_indexes():
    """
    Define indexes for performance optimization.
    This function documents the indexes but they should be created via SQL
    as shown in the init.sql file.
    """
    indexes = [
        # Vector search performance indexes
        Index('idx_rss_item_derivatives_title_embedding', RSSItemDerivative.title_embedding, 
              postgresql_using='ivfflat', postgresql_with={'lists': 100}),
        Index('idx_rss_item_derivatives_summary_embedding', RSSItemDerivative.summary_embedding,
              postgresql_using='ivfflat', postgresql_with={'lists': 100}),
        Index('idx_topics_topic_vector', Topic.topic_vector,
              postgresql_using='ivfflat', postgresql_with={'lists': 100}),
        
        # Query performance indexes
        Index('idx_rss_items_processing_status', RSSItemMetadata.processing_status),
        Index('idx_rss_items_published_at_desc', RSSItemMetadata.published_at.desc()),
        Index('idx_rss_item_derivatives_processing_status', RSSItemDerivative.processing_status),
        Index('idx_rss_feeds_last_fetch_status', RSSFeed.last_fetch_status),
        Index('idx_rss_feeds_last_fetch_at', RSSFeed.last_fetch_at),
        Index('idx_topics_user_id_active', Topic.user_id, Topic.is_active),
        Index('idx_events_topic_id_updated', Event.topic_id, Event.updated_at.desc()),
        Index('idx_user_summaries_date_desc', UserSummary.date.desc()),
        Index('idx_article_topics_relevance', ArticleTopic.relevance_score.desc()),
        Index('idx_article_events_relevance', ArticleEvent.relevance_score.desc()),
    ]
    return indexes