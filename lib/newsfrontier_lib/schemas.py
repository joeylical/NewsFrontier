"""
Pydantic schemas for API request/response validation.

These schemas define the data structures used for API communication
and validation in the NewsFrontier application.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    daily_summary_prompt: Optional[str] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_admin: bool
    credits: int
    credits_accrual: int
    daily_summary_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# RSS Feed schemas
class RSSFeedBase(BaseModel):
    url: str = Field(..., max_length=2048)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class RSSFeedCreate(RSSFeedBase):
    fetch_interval_minutes: int = Field(default=60, ge=1, le=10080)  # 1 min to 1 week

class RSSFeedUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    fetch_interval_minutes: Optional[int] = Field(None, ge=1, le=10080)

class RSSFeedResponse(RSSFeedBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    last_fetch_at: Optional[datetime] = None
    last_fetch_status: str
    fetch_interval_minutes: int


# RSS Subscription schemas
class RSSSubscriptionBase(BaseModel):
    alias: Optional[str] = Field(None, max_length=255)
    is_active: bool = True

class RSSSubscriptionCreate(RSSSubscriptionBase):
    rss_uuid: UUID

class RSSSubscriptionUpdate(RSSSubscriptionBase):
    pass

class RSSSubscriptionResponse(RSSSubscriptionBase):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    rss_uuid: UUID
    created_at: datetime
    rss_feed: RSSFeedResponse


# Article schemas
class RSSItemBase(BaseModel):
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)

class RSSItemResponse(RSSItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    guid: Optional[str] = None
    published_at: Optional[datetime] = None
    processing_status: str
    created_at: datetime
    
    # Include AI-generated summary if available
    summary: Optional[str] = None

class RSSItemDetailResponse(RSSItemResponse):
    """Extended article response with AI derivatives."""
    model_config = ConfigDict(from_attributes=True)
    
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_attempts: int
    llm_model_version: Optional[str] = None
    embedding_model_version: Optional[str] = None


# Topic schemas
class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True

class TopicCreate(TopicBase):
    pass

class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None

class TopicResponse(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# Event schemas
class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None

class EventCreate(EventBase):
    topic_id: int

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None

class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    topic_id: int
    last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Include related articles count
    article_count: Optional[int] = None

class EventDetailResponse(EventResponse):
    """Extended event response with related articles."""
    model_config = ConfigDict(from_attributes=True)
    
    articles: List[RSSItemResponse] = []
    topic: TopicResponse


# User Summary schemas
class UserSummaryBase(BaseModel):
    summary: Optional[str] = None
    cover_arguments: Optional[str] = None
    cover_prompt: Optional[str] = None
    cover_seed: Optional[int] = None
    cover_s3key: Optional[str] = None

class UserSummaryCreate(UserSummaryBase):
    date: date

class UserSummaryUpdate(UserSummaryBase):
    pass

class UserSummaryResponse(UserSummaryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    date: date
    created_at: datetime


# System Settings schemas
class SystemSettingBase(BaseModel):
    setting_key: str = Field(..., min_length=1, max_length=100)
    setting_value: Optional[str] = None
    setting_type: str = Field(default="string", pattern=r"^(string|integer|boolean|json|float)$")
    description: Optional[str] = None
    is_public: bool = False

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    setting_value: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class SystemSettingResponse(SystemSettingBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    updated_at: datetime
    updated_by: Optional[int] = None
    created_at: datetime


# Authentication schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    expires: datetime
    user: UserResponse

class RegisterRequest(UserCreate):
    pass

class RegisterResponse(BaseModel):
    user_id: int
    message: str


# Analytics and Dashboard schemas
class DailyAnalytics(BaseModel):
    date: date
    total_articles: int
    clusters_count: int
    top_topics: List[str]
    summary: Optional[str] = None
    trending_keywords: List[str]

class TopicAnalytics(BaseModel):
    topic: TopicResponse
    clusters: List[EventResponse]

class ClusterDetail(BaseModel):
    cluster: EventDetailResponse


# API Response wrappers
class ApiResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[BaseModel]
    total: int
    page: int
    per_page: int
    pages: int

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    details: Optional[dict] = None


# Article Topic schemas
class ArticleTopicBase(BaseModel):
    """Base schema for article topics."""
    rss_item_id: int
    topic_id: int
    relevance_score: Optional[float] = None

class ArticleTopicCreate(ArticleTopicBase):
    """Schema for creating article topics."""
    pass

class ArticleTopicResponse(ArticleTopicBase):
    """Schema for article topic responses."""
    model_config = ConfigDict(from_attributes=True)
    
    created_at: datetime
    topic: Optional[TopicResponse] = None
    rss_item: Optional[RSSItemResponse] = None

class ArticleTopicSearch(BaseModel):
    """Schema for searching article topics."""
    rss_item_id: Optional[int] = None
    topic_id: Optional[int] = None
    min_relevance_score: Optional[float] = None
    max_relevance_score: Optional[float] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0
