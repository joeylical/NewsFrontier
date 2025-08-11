from fastapi import FastAPI, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from uuid import UUID
import jwt
from passlib.context import CryptContext
import json
import logging
import sys
import traceback
import hashlib
import numpy as np
import os
import requests
from text_processor import process_text_with_anchors, extract_paragraphs_with_anchors, get_text_processing_info

# Import database and models
try:
    from newsfrontier_lib.database import get_session
    from newsfrontier_lib import crud
    from newsfrontier_lib.models import (
        User as UserModel, RSSFeed as RSSFeedModel, 
        RSSItemMetadata, RSSFetchRecord, Event, ArticleEvent, Topic, ArticleTopic, 
        RSSSubscription
    )
    from sqlalchemy import func
    from newsfrontier_lib.schemas import (
        RSSFeedCreate, RSSFeedUpdate, RSSFeedResponse,
        RSSSubscriptionCreate, RSSSubscriptionUpdate, RSSSubscriptionResponse,
        RSSItemResponse, TopicCreate, TopicUpdate, TopicResponse,
        EventResponse, UserSummaryResponse, UserResponse
    )
    from newsfrontier_lib import generate_topic_embedding as lib_generate_topic_embedding
    print("✅ Database modules imported successfully")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error during database import: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="NewsFrontier API", version="0.1.0")

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    logger.info(f"Incoming request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Request failed: {request.method} {request.url} - Error: {str(e)} - Time: {process_time:.3f}s")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.method} {request.url}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    
    return HTTPException(status_code=500, detail="Internal server error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)  # Don't auto-error if no header
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# AI Configuration (kept for backward compatibility)
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 1536))

# Removed fake_users_db - now using database operations

# Removed fake_articles_db - now using database operations with RSS items

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    expires: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class RegisterResponse(BaseModel):
    user_id: int
    message: str

class TodayResponse(BaseModel):
    date: str
    total_articles: int
    clusters_count: int
    top_topics: List[str]
    summary: str
    trending_keywords: List[str]

class AvailableDatesResponse(BaseModel):
    month: str  # YYYY-MM format
    available_dates: List[str]  # List of dates in YYYY-MM-DD format that have summaries

# Daily Summary Models
class DailySummaryCreateRequest(BaseModel):
    user_id: int
    date: str
    summary: str
    cover_prompt: Optional[str] = None
    cover_arguments: Optional[str] = None
    cover_seed: Optional[int] = None
    cover_s3key: Optional[str] = None

class DailySummaryResponse(BaseModel):
    id: int
    user_id: int
    date: str
    summary: Optional[str]
    cover_prompt: Optional[str]
    cover_arguments: Optional[str]
    cover_seed: Optional[int]
    cover_s3key: Optional[str]
    created_at: str

class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    daily_summary_prompt: Optional[str]

class TopicDto(BaseModel):
    id: int
    name: str
    keywords: List[str]
    active: bool

class TopicsResponse(BaseModel):
    topics: List[TopicDto]

class TopicRequest(BaseModel):
    name: str
    keywords: List[str]
    active: bool = True

class TopicCreateResponse(BaseModel):
    id: int
    message: str

class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: str
    updated_at: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    credits: int
    credits_accrual: int
    daily_summary_prompt: Optional[str]
    created_at: str
    updated_at: str

class Cluster(BaseModel):
    id: int
    title: str
    article_count: int
    summary: str

class TopicDetailResponse(BaseModel):
    topic: TopicDto
    clusters: List[Cluster]

class ArticleDerivative(BaseModel):
    summary: Optional[str] = None
    summary_generated_at: Optional[str] = None
    llm_model_version: Optional[str] = None
    processing_status: str = "pending"

class Article(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    processing_status: str = "pending"  # pending, processing, completed, failed
    created_at: str
    derivative: Optional[ArticleDerivative] = None

class ArticleList(BaseModel):
    id: int
    title: str
    source: str
    timestamp: str

class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    has_next: bool
    has_prev: bool

class ArticlesResponse(BaseModel):
    data: List[Article]
    pagination: PaginationInfo

class ClusterDetail(BaseModel):
    id: int
    title: str
    summary: str
    articles: List[Article]

class ClusterDetailResponse(BaseModel):
    cluster: ClusterDetail

class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: Optional[str]
    setting_type: str
    description: Optional[str]
    is_public: bool
    updated_at: str
    created_at: str

class SystemSettingUpdate(BaseModel):
    setting_key: str
    setting_value: str
    setting_type: str

# Internal API BaseModel classes
class FeedStatusUpdate(BaseModel):
    fetch_status: str
    last_fetch_at: Optional[str] = None
    error_message: Optional[str] = None

class FeedFetchData(BaseModel):
    url: str
    raw_content: str
    content_hash: str
    http_status: int
    content_encoding: Optional[str] = None

class ArticleProcessingUpdate(BaseModel):
    title_embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    summary: Optional[str] = None
    summary_model: Optional[str] = None
    processed_at: Optional[str] = None
    error_message: Optional[str] = None

class ArticleDerivativesData(BaseModel):
    rss_item_id: int
    summary: Optional[str] = None
    title_embedding: Optional[List[float]] = None
    summary_embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    summary_model: Optional[str] = None

class ArticleTopicData(BaseModel):
    rss_item_id: int
    topic_id: int
    relevance_score: float

class EventData(BaseModel):
    user_id: int
    topic_id: int
    title: str
    description: Optional[str] = None
    event_description: Optional[str] = None

class ArticleEventData(BaseModel):
    rss_item_id: int
    event_id: int
    relevance_score: Optional[float] = None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    token = None
    
    # First try to get token from Authorization header
    if credentials:
        token = credentials.credentials
    else:
        # If no Authorization header, try to get token from cookie
        token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="No authentication token provided")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin(username: str = Depends(verify_token), db = Depends(get_session)):
    """Verify that the authenticated user is an admin."""
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

def generate_topic_embedding(topic_name: str) -> Optional[List[float]]:
    """Generate embedding for a topic name using the shared LLM library."""
    try:
        embedding = lib_generate_topic_embedding(topic_name)
        if embedding:
            logger.info(f"Generated embedding for topic '{topic_name}': {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Embedding generation failed for topic '{topic_name}': {e}")
        return None

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response, db = Depends(get_session)):
    logger.info(f"Login attempt for user: {request.username}")
    
    
    # Get user from database
    user = crud.user.get_by_username(db, username=request.username)
    if not user or not pwd_context.verify(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": request.username})
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600  # Convert hours to seconds
    )
    
    logger.info(f"Successful login for user: {request.username}")
    return LoginResponse(
        token=access_token,
        user_id=user.id,
        expires=expires.isoformat() + "Z"
    )

@app.post("/api/logout")
async def logout(response: Response, username: str = Depends(verify_token)):
    # Clear the auth cookie
    response.delete_cookie(key="auth_token", samesite="lax")
    return {"message": "Logged out successfully"}

@app.get("/api/user/me", response_model=UserResponse)
async def get_current_user(username: str = Depends(verify_token), db = Depends(get_session)):
    
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        credits=user.credits,
        credits_accrual=user.credits_accrual,
        daily_summary_prompt=user.daily_summary_prompt,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else ""
    )

@app.put("/api/user/settings")
async def update_user_settings(
    settings_data: dict,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Update user settings."""
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user settings
    update_data = {}
    if "daily_summary_prompt" in settings_data:
        update_data["daily_summary_prompt"] = settings_data["daily_summary_prompt"]
    
    if update_data:
        updated_user = crud.user.update(db, db_obj=user, obj_in=update_data)
        return {"message": "User settings updated successfully"}
    else:
        return {"message": "No settings to update"}

@app.post("/api/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db = Depends(get_session)):
    
    # Check if username already exists
    existing_user = crud.user.get_by_username(db, username=request.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = crud.user.get_by_email(db, email=request.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    user_data = {
        "username": request.username,
        "email": request.email,
        "password_hash": pwd_context.hash(request.password),
        "is_admin": False
    }
    
    new_user = crud.user.create(db, obj_in=user_data)
    
    return RegisterResponse(
        user_id=new_user.id,
        message="Registration successful"
    )

@app.get("/api/today", response_model=TodayResponse)
async def get_today(
    date_param: Optional[str] = None,
    username: str = Depends(verify_token), 
    db = Depends(get_session)
):
    
    # Get the target date - use provided date or default to today
    if date_param:
        try:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = date.today()
    
    # Calculate statistics from database
    from sqlalchemy import func, and_
    
    # Get total articles for the target date
    date_start = datetime.combine(target_date, datetime.min.time())
    date_end = datetime.combine(target_date, datetime.max.time())
    
    total_articles = db.query(func.count(RSSItemMetadata.id)).filter(
        and_(
            RSSItemMetadata.created_at >= date_start,
            RSSItemMetadata.created_at <= date_end
        )
    ).scalar() or 0
    
    # Get clusters count (events count as proxy for clusters)
    clusters_count = db.query(func.count(Event.id)).filter(
        and_(
            Event.created_at >= date_start,
            Event.created_at <= date_end
        )
    ).scalar() or 0
    
    # Get top topics (most active topics)
    top_topics_query = db.query(Topic.name).join(ArticleTopic).join(RSSItemMetadata).filter(
        and_(
            RSSItemMetadata.created_at >= date_start,
            RSSItemMetadata.created_at <= date_end,
            Topic.is_active == True
        )
    ).group_by(Topic.name).order_by(func.count(ArticleTopic.topic_id).desc()).limit(3)
    
    top_topics = [row[0] for row in top_topics_query.all()]
    if not top_topics:
        top_topics = []
    
    # Get user summary for the target date if exists
    user = crud.user.get_by_username(db, username=username)
    summary = f"No summary generated yet for {target_date.isoformat()}."
    if user:
        user_summary = crud.user_summary.get_by_date(db, user_id=user.id, date=target_date)
        if user_summary and user_summary.summary:
            summary = user_summary.summary
    
    # For trending keywords, get most common categories as a proxy
    trending_keywords_query = db.query(RSSItemMetadata.category).filter(
        and_(
            RSSItemMetadata.created_at >= date_start,
            RSSItemMetadata.created_at <= date_end,
            RSSItemMetadata.category.isnot(None)
        )
    ).group_by(RSSItemMetadata.category).order_by(func.count().desc()).limit(3)
    
    trending_keywords = [row[0] for row in trending_keywords_query.all() if row[0]]
    if not trending_keywords:
        trending_keywords = []
    
    return TodayResponse(
        date=target_date.isoformat(),
        total_articles=total_articles,
        clusters_count=clusters_count,
        top_topics=top_topics,
        summary=summary,
        trending_keywords=trending_keywords
    )

@app.get("/api/available-dates", response_model=AvailableDatesResponse)
async def get_available_dates(
    year: int,
    month: int,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Get all dates in a given month that have daily summaries available"""
    
    # Validate month and year
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if year < 2000 or year > 3000:
        raise HTTPException(status_code=400, detail="Year must be reasonable")
    
    # Get user
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate start and end dates for the month
    from calendar import monthrange
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    
    # Query for all dates where this user has summaries
    from newsfrontier_lib.models import UserSummary
    from sqlalchemy import and_
    summaries = db.query(UserSummary.date).filter(
        and_(
            UserSummary.user_id == user.id,
            UserSummary.date >= start_date,
            UserSummary.date <= end_date,
            UserSummary.summary.isnot(None),
            UserSummary.summary != ""
        )
    ).order_by(UserSummary.date).all()
    
    # Format dates as strings
    available_dates = [summary_date[0].isoformat() for summary_date in summaries]
    
    return AvailableDatesResponse(
        month=f"{year:04d}-{month:02d}",
        available_dates=available_dates
    )

@app.get("/api/cover-image")
async def get_cover_image(
    date_param: Optional[str] = None,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Get cover image URL for today or specified date"""
    
    # Get user
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Parse date parameter
    try:
        if date_param:
            target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        else:
            target_date = datetime.now().date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get user summary for the date
    from newsfrontier_lib.models import UserSummary
    summary = db.query(UserSummary).filter(
        UserSummary.user_id == user.id,
        UserSummary.date == target_date
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="No summary found for the specified date")
    
    if not summary.cover_s3key:
        raise HTTPException(status_code=404, detail="No cover image available for the specified date")
    
    # Generate presigned URL for the cover image
    try:
        from newsfrontier_lib.s3_client import get_cover_image_url
        cover_url = get_cover_image_url(summary.cover_s3key)
        
        if not cover_url:
            raise HTTPException(status_code=500, detail="Failed to generate cover image URL")
        
        return {
            "date": target_date.isoformat(),
            "cover_url": cover_url,
            "s3_key": summary.cover_s3key
        }
        
    except Exception as e:
        logger.error(f"Error generating cover image URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover image URL")

@app.get("/api/topics", response_model=TopicsResponse)
async def get_topics(username: str = Depends(verify_token), db = Depends(get_session)):
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's topics from database
    db_topics = crud.topic.get_user_topics(db, user_id=user.id)
    
    # Convert to response format (note: no keywords field in database, using empty list)
    topics = [
        TopicDto(
            id=topic.id, 
            name=topic.name, 
            keywords=[], 
            active=topic.is_active
        )
        for topic in db_topics
    ]
    
    return TopicsResponse(topics=topics)

@app.post("/api/topics", response_model=TopicCreateResponse)
async def create_topic(request: TopicRequest, username: str = Depends(verify_token), db = Depends(get_session)):
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if topic with same name already exists for this user
    existing_topic = crud.topic.get_by_name(db, user_id=user.id, name=request.name)
    if existing_topic:
        raise HTTPException(status_code=400, detail="Topic with this name already exists")
    
    # Generate embedding for the topic
    try:
        topic_embedding = generate_topic_embedding(request.name)
        logger.info(f"Generated embedding for topic '{request.name}'")
    except Exception as e:
        logger.error(f"Failed to generate embedding for topic '{request.name}': {e}")
        # Continue without embedding if generation fails
        topic_embedding = None
    
    # Create new topic with embedding
    topic_data = {
        "user_id": user.id,
        "name": request.name,
        "topic_vector": topic_embedding,
        "is_active": request.active
    }
    
    new_topic = crud.topic.create(db, obj_in=topic_data)
    
    # Trigger article processing for the new topic if embedding was generated
    if topic_embedding:
        try:
            # Make async call to postprocess service to analyze existing articles
            import threading
            
            def trigger_topic_processing():
                try:
                    postprocess_url = os.getenv("POSTPROCESS_URL", "http://localhost:8001")
                    process_data = {
                        "topic_id": new_topic.id,
                        "topic_name": new_topic.name,
                        "topic_embedding": topic_embedding,
                        "user_id": user.id
                    }
                    
                    response = requests.post(
                        f"{postprocess_url}/api/process-new-topic", 
                        json=process_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully triggered article processing for topic '{new_topic.name}' (ID: {new_topic.id})")
                    else:
                        logger.warning(f"Failed to trigger article processing for topic '{new_topic.name}': HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error triggering article processing for topic '{new_topic.name}': {e}")
            
            # Start background thread to avoid blocking the response
            processing_thread = threading.Thread(target=trigger_topic_processing, daemon=True)
            processing_thread.start()
            
        except Exception as e:
            logger.error(f"Error setting up background processing for topic '{new_topic.name}': {e}")
    
    return TopicCreateResponse(
        id=new_topic.id,
        message=f"Topic created successfully{' with embedding' if topic_embedding else ''}. Processing existing articles in background."
    )

@app.put("/api/topics/{topic_id}", response_model=TopicCreateResponse)
async def update_topic(topic_id: int, request: TopicRequest, username: str = Depends(verify_token), db = Depends(get_session)):
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing topic
    existing_topic = crud.topic.get(db, topic_id)
    if not existing_topic or existing_topic.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check if name is being changed to one that already exists
    if request.name != existing_topic.name:
        name_conflict = crud.topic.get_by_name(db, user_id=user.id, name=request.name)
        if name_conflict:
            raise HTTPException(status_code=400, detail="Topic with this name already exists")
    
    # Generate new embedding if topic name changed
    topic_embedding = existing_topic.topic_vector
    if request.name != existing_topic.name:
        try:
            topic_embedding = generate_topic_embedding(request.name)
            logger.info(f"Generated new embedding for updated topic '{request.name}'")
        except Exception as e:
            logger.error(f"Failed to generate embedding for updated topic '{request.name}': {e}")
            # Keep existing embedding if generation fails
    
    # Update topic data
    update_data = {
        "name": request.name,
        "topic_vector": topic_embedding,
        "is_active": request.active
    }
    
    updated_topic = crud.topic.update(db, db_obj=existing_topic, obj_in=update_data)
    
    return TopicCreateResponse(
        id=updated_topic.id,
        message=f"Topic updated successfully{' with new embedding' if request.name != existing_topic.name and topic_embedding else ''}"
    )

@app.delete("/api/topics/{topic_id}")
async def delete_topic(topic_id: int, username: str = Depends(verify_token), db = Depends(get_session)):
    """
    Delete a topic and all its associated data.
    
    This will automatically delete:
    - All events related to this topic
    - All article-topic relationships  
    - All user-topic relationships
    
    Due to the cascade delete relationships defined in the database models.
    """
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get existing topic
    existing_topic = crud.topic.get(db, topic_id)
    if not existing_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Verify ownership - users can only delete their own topics
    if existing_topic.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own topics")
    
    try:
        # Count related data for logging
        events_count = len(existing_topic.events) if existing_topic.events else 0
        article_topics_count = len(existing_topic.article_topics) if existing_topic.article_topics else 0
        user_topics_count = len(existing_topic.user_topics) if existing_topic.user_topics else 0
        
        topic_name = existing_topic.name
        
        # Delete the topic (cascade deletes will handle related data automatically)
        success = crud.topic.remove(db, id=topic_id)
        
        if success:
            logger.info(f"Successfully deleted topic '{topic_name}' (ID: {topic_id}) for user {user.username}")
            logger.info(f"Cascade deleted: {events_count} events, {article_topics_count} article relationships, {user_topics_count} user relationships")
            
            return {
                "message": "Topic deleted successfully",
                "topic_id": topic_id,
                "topic_name": topic_name,
                "deleted_relationships": {
                    "events": events_count,
                    "article_topics": article_topics_count,
                    "user_topics": user_topics_count
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete topic")
            
    except Exception as e:
        logger.error(f"Error deleting topic {topic_id} for user {user.username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")

@app.get("/api/topic/{topic_id}", response_model=TopicDetailResponse)
async def get_topic_detail(topic_id: int, username: str = Depends(verify_token), db = Depends(get_session)):
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get topic from database
    db_topic = crud.topic.get(db, topic_id)
    if not db_topic or db_topic.user_id != user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Convert topic to response format
    topic = TopicDto(
        id=db_topic.id,
        name=db_topic.name,
        keywords=[],  # No keywords field in database
        active=db_topic.is_active
    )
    
    # Get events (clusters) for this topic
    events = crud.event.get_topic_events(db, topic_id=topic_id, limit=50)
    clusters = [
        Cluster(
            id=event.id,
            title=event.title,
            article_count=len(event.article_events),  # Count of articles in this event
            summary=event.description or "No summary available"
        )
        for event in events
    ]
    
    return TopicDetailResponse(
        topic=topic,
        clusters=clusters
    )

@app.get("/api/cluster/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster_detail(cluster_id: int, username: str = Depends(verify_token), db = Depends(get_session)):
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get event (cluster) from database
    event = crud.event.get(db, cluster_id)
    if not event or event.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Get articles associated with this event
    from sqlalchemy.orm import joinedload
    event_with_articles = db.query(Event).options(
        joinedload(Event.article_events).joinedload(ArticleEvent.rss_item)
    ).filter(Event.id == cluster_id).first()
    
    articles = []
    if event_with_articles and event_with_articles.article_events:
        articles = [
            Article(
                id=ae.rss_item.id,
                title=ae.rss_item.title,
                content=ae.rss_item.content,
                url=ae.rss_item.url,
                published_at=ae.rss_item.published_at.isoformat() + "Z" if ae.rss_item.published_at else None,
                author=ae.rss_item.author,
                category=ae.rss_item.category,
                processing_status=ae.rss_item.processing_status,
                created_at=ae.rss_item.created_at.isoformat() + "Z"
            )
            for ae in event_with_articles.article_events
            if ae.rss_item
        ]
    
    cluster = ClusterDetail(
        id=event.id,
        title=event.title,
        summary=event.description or "No summary available",
        articles=articles
    )
    
    return ClusterDetailResponse(cluster=cluster)

@app.get("/api/articles", response_model=ArticlesResponse)
async def get_articles(
    page: int = 1,
    limit: int = 20,
    status: str = "completed",  # Default to completed articles only
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """
    Get completed articles with pagination support
    """
    
    # Input validation
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20
    
    # Calculate skip for pagination
    skip = (page - 1) * limit
    
    # Get articles from database
    from sqlalchemy import func
    total_query = db.query(func.count(RSSItemMetadata.id)).filter(
        RSSItemMetadata.processing_status == status
    )
    total = total_query.scalar()
    
    articles_query = db.query(RSSItemMetadata).filter(
        RSSItemMetadata.processing_status == status
    ).order_by(RSSItemMetadata.created_at.desc()).offset(skip).limit(limit)
    
    db_articles = articles_query.all()
    
    # Convert to Pydantic models
    articles = [
        Article(
            id=article.id,
            title=article.title,
            content=article.content,
            url=article.url,
            published_at=article.published_at.isoformat() + "Z" if article.published_at else None,
            author=article.author,
            category=article.category,
            processing_status=article.processing_status,
            created_at=article.created_at.isoformat() + "Z"
        )
        for article in db_articles
    ]
    
    # Create pagination info
    has_next = skip + limit < total
    has_prev = page > 1
    
    pagination = PaginationInfo(
        page=page,
        limit=limit,
        total=total,
        has_next=has_next,
        has_prev=has_prev
    )
    
    return ArticlesResponse(
        data=articles,
        pagination=pagination
    )

@app.get("/api/article/{article_id}")
async def get_article_detail(
    article_id: int, 
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """
    Get detailed information about a specific article including AI-generated summary
    """
    from sqlalchemy.orm import joinedload
    
    # Get article with its derivatives from database
    article = db.query(RSSItemMetadata).options(
        joinedload(RSSItemMetadata.derivatives)
    ).filter(RSSItemMetadata.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Create derivative data if available
    derivative_data = None
    if article.derivatives:
        derivative_data = ArticleDerivative(
            summary=article.derivatives.summary,
            summary_generated_at=article.derivatives.summary_generated_at.isoformat() + "Z" if article.derivatives.summary_generated_at else None,
            llm_model_version=article.derivatives.llm_model_version,
            processing_status=article.derivatives.processing_status
        )
    
    return Article(
        id=article.id,
        title=article.title,
        content=article.content,
        url=article.url,
        published_at=article.published_at.isoformat() + "Z" if article.published_at else None,
        author=article.author,
        category=article.category,
        processing_status=article.processing_status,
        created_at=article.created_at.isoformat() + "Z",
        derivative=derivative_data
    )

@app.post("/api/article/{article_id}/reprocess-anchors")
async def reprocess_article_anchors(
    article_id: int,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """
    Reprocess an existing article to add sentence anchors
    """
    # Get article from database
    article = crud.rss_item.get(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if content exists
    if not article.content:
        raise HTTPException(status_code=400, detail="Article has no content to process")
    
    # Process content with anchors
    try:
        processed_content = process_text_with_anchors(article.content)
        
        # Update article with processed content
        article.content = processed_content
        db.commit()
        db.refresh(article)
        
        # Extract sentence information for response
        sentence_info = extract_paragraphs_with_anchors(article.content)
        
        return {
            "message": "Article content reprocessed with sentence anchors",
            "article_id": article_id,
            "sentences_processed": len(sentence_info),
            "anchor_ids": [s["anchor_id"] for s in sentence_info]
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing article {article_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess article: {str(e)}")

@app.get("/api/article/{article_id}/sentences")
async def get_article_sentences(
    article_id: int,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """
    Get sentence breakdown of an article with anchor information
    """
    # Get article from database
    article = crud.rss_item.get(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if not article.content:
        return {"sentences": [], "total_sentences": 0}
    
    # Extract sentence information
    sentence_info = extract_paragraphs_with_anchors(article.content)
    
    return {
        "article_id": article_id,
        "sentences": sentence_info,
        "total_sentences": len(sentence_info)
    }

@app.get("/api/article/{article_id}/processing-info")
async def get_article_processing_info(
    article_id: int,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """
    Get information about how article content would be processed
    """
    # Get article from database
    article = crud.rss_item.get(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get processing information
    processing_info = get_text_processing_info(article.content)
    
    return {
        "article_id": article_id,
        "processing_info": processing_info,
        "has_content": bool(article.content),
        "content_preview": article.content[:200] if article.content else None
    }

# RSS Feeds Management API Endpoints
@app.get("/api/feeds")
async def get_user_feeds(
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Get user's RSS feed subscriptions."""
    logger.info(f"Getting RSS feeds for user: {username}")
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        logger.error(f"User not found in database: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's RSS subscriptions with feed details
    subscriptions = crud.rss_subscription.get_user_subscriptions(db, user_id=user.id)
    
    result = []
    for subscription in subscriptions:
        # Get the RSS feed details
        feed = crud.rss_feed.get_by_uuid(db, uuid=str(subscription.rss_uuid))
        if feed:
            result.append({
                "id": feed.id,
                "uuid": str(feed.uuid),
                "url": feed.url,
                "title": feed.title,
                "description": feed.description,
                "created_at": feed.created_at.isoformat(),
                "updated_at": feed.updated_at.isoformat(),
                "last_fetch_at": feed.last_fetch_at.isoformat() if feed.last_fetch_at else None,
                "last_fetch_status": feed.last_fetch_status,
                "fetch_interval_minutes": feed.fetch_interval_minutes
            })
    
    return result

@app.post("/api/feeds")
async def create_rss_feed(
    feed_data: dict,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Add a new RSS feed subscription for the user."""
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        logger.error(f"User not found in database: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate required fields
    url = feed_data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="RSS feed URL is required")
    
    # Check if feed already exists
    existing_feed = crud.rss_feed.get_by_url(db, url=url)
    
    if existing_feed:
        # Feed exists, create subscription if not already subscribed
        existing_subscription = crud.rss_subscription.get_user_subscription(
            db, user_id=user.id, rss_uuid=str(existing_feed.uuid)
        )
        
        if existing_subscription:
            raise HTTPException(status_code=400, detail="Already subscribed to this RSS feed")
        
        # Create new subscription
        crud.rss_subscription.create_subscription(
            db, 
            user_id=user.id, 
            rss_uuid=existing_feed.uuid,
            alias=feed_data.get("alias"),
            is_active=True
        )
        
        return {
            "id": existing_feed.id,
            "uuid": str(existing_feed.uuid),
            "url": existing_feed.url,
            "title": existing_feed.title,
            "description": existing_feed.description,
            "created_at": existing_feed.created_at.isoformat(),
            "updated_at": existing_feed.updated_at.isoformat(),
            "last_fetch_at": existing_feed.last_fetch_at.isoformat() if existing_feed.last_fetch_at else None,
            "last_fetch_status": existing_feed.last_fetch_status,
            "fetch_interval_minutes": existing_feed.fetch_interval_minutes
        }
    else:
        # Create new RSS feed
        new_feed_data = {
            "url": url,
            "title": feed_data.get("title"),
            "description": feed_data.get("description"),
            "fetch_interval_minutes": feed_data.get("fetch_interval_minutes", 60)
        }
        
        feed = crud.rss_feed.create(db, obj_in=new_feed_data)
        
        # Create subscription for the user
        crud.rss_subscription.create_subscription(
            db, 
            user_id=user.id, 
            rss_uuid=feed.uuid,
            alias=feed_data.get("alias"),
            is_active=True
        )
        
        return {
            "id": feed.id,
            "uuid": str(feed.uuid),
            "url": feed.url,
            "title": feed.title,
            "description": feed.description,
            "created_at": feed.created_at.isoformat(),
            "updated_at": feed.updated_at.isoformat(),
            "last_fetch_at": feed.last_fetch_at.isoformat() if feed.last_fetch_at else None,
            "last_fetch_status": feed.last_fetch_status,
            "fetch_interval_minutes": feed.fetch_interval_minutes
        }

@app.put("/api/feeds/{feed_uuid}")
async def update_rss_feed(
    feed_uuid: UUID,
    feed_data: dict,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Update RSS feed subscription settings."""
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        logger.error(f"User not found in database: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has subscription to this feed
    subscription = crud.rss_subscription.get_user_subscription(
        db, user_id=user.id, rss_uuid=str(feed_uuid)
    )
    if not subscription:
        raise HTTPException(status_code=404, detail="RSS feed subscription not found")
    
    # Update subscription
    updated_subscription = crud.rss_subscription.update_subscription(
        db,
        user_id=user.id,
        rss_uuid=str(feed_uuid),
        alias=feed_data.get("alias"),
        is_active=feed_data.get("is_active")
    )
    
    if not updated_subscription:
        raise HTTPException(status_code=404, detail="Failed to update subscription")
    
    # Get the feed details to return
    feed = crud.rss_feed.get_by_uuid(db, uuid=str(feed_uuid))
    if not feed:
        raise HTTPException(status_code=404, detail="RSS feed not found")
    
    return {
        "id": feed.id,
        "uuid": str(feed.uuid),
        "url": feed.url,
        "title": feed.title,
        "description": feed.description,
        "created_at": feed.created_at.isoformat(),
        "updated_at": feed.updated_at.isoformat(),
        "last_fetch_at": feed.last_fetch_at.isoformat() if feed.last_fetch_at else None,
        "last_fetch_status": feed.last_fetch_status,
        "fetch_interval_minutes": feed.fetch_interval_minutes
    }

@app.delete("/api/feeds/{feed_uuid}")
async def delete_rss_feed(
    feed_uuid: UUID,
    username: str = Depends(verify_token),
    db = Depends(get_session)
):
    """Remove RSS feed subscription."""
    
    # Get user from database
    user = crud.user.get_by_username(db, username=username)
    if not user:
        logger.error(f"User not found in database: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's subscription to this feed
    success = crud.rss_subscription.delete_subscription(
        db, user_id=user.id, rss_uuid=str(feed_uuid)
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="RSS feed subscription not found")
    
    return {"message": "Feed subscription removed successfully"}

# RSS Feed Status and Processing API
@app.get("/api/feeds/{feed_uuid}/status")
async def get_feed_status(
    feed_uuid: UUID,
    username: str = Depends(verify_token)
):
    """Get detailed status of RSS feed processing."""
    
    # TODO: Implement database query for feed status with proper database dependency
    raise HTTPException(status_code=501, detail="Not implemented yet")

@app.post("/api/feeds/{feed_uuid}/fetch")
async def trigger_feed_fetch(
    feed_uuid: UUID,
    username: str = Depends(verify_token)
):
    """Manually trigger RSS feed fetch."""
    
    # TODO: Implement manual feed fetch trigger with proper database dependency
    # This should integrate with the scraper component
    raise HTTPException(status_code=501, detail="Not implemented yet")

# Article Processing API for Scraper Integration
@app.get("/api/internal/feeds/pending")
async def get_feeds_pending_fetch(db = Depends(get_session)):
    """Internal API for scraper: Get feeds that need fetching."""
    
    # Get feeds that are due for fetching
    feeds = crud.rss_feed.get_feeds_due_for_fetch(db)
    return [
        {
            "id": feed.id,
            "uuid": str(feed.uuid),
            "url": feed.url,
            "title": feed.title,
            "last_fetch_at": feed.last_fetch_at.isoformat() if feed.last_fetch_at else None,
            "fetch_interval_minutes": feed.fetch_interval_minutes
        }
        for feed in feeds
    ]

@app.post("/api/internal/feeds/{feed_id}/status")
async def update_feed_fetch_status(
    feed_id: int,
    status_data: dict,
    db = Depends(get_session)
):
    """Internal API for scraper: Update feed fetch status."""
    
    # Update feed fetch status
    status = status_data.get("status", "failed")
    fetch_time_str = status_data.get("fetch_time")
    
    if fetch_time_str:
        try:
            fetch_time = datetime.fromisoformat(fetch_time_str.replace('Z', '+00:00'))
        except ValueError:
            fetch_time = datetime.utcnow()
    else:
        fetch_time = datetime.utcnow()
    
    feed = crud.rss_feed.update_fetch_status(
        db, feed_id=feed_id, status=status, fetch_time=fetch_time
    )
    
    if not feed:
        raise HTTPException(status_code=404, detail="RSS feed not found")
    
    return {"message": "Feed status updated successfully", "feed_id": feed.id}

@app.post("/api/internal/fetch-records")
async def create_or_update_fetch_record(
    fetch_data: dict,
    db = Depends(get_session)
):
    """Internal API for scraper: Create new or update existing RSS fetch record."""
    
    # Validate required fields
    required_fields = ["rss_feed_id", "raw_content", "content_hash"]
    for field in required_fields:
        if field not in fetch_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    try:
        rss_feed_id = fetch_data["rss_feed_id"]
        content_hash = fetch_data["content_hash"]
        
        # Check if a record with the same feed_id and content_hash exists
        existing_record = db.query(RSSFetchRecord).filter(
            RSSFetchRecord.rss_feed_id == rss_feed_id,
            RSSFetchRecord.content_hash == content_hash
        ).first()
        
        if existing_record:
            # Update last_fetch_timestamp for existing record
            existing_record.last_fetch_timestamp = func.now()
            existing_record.http_status = fetch_data.get("http_status", existing_record.http_status)
            existing_record.content_encoding = fetch_data.get("content_encoding", existing_record.content_encoding)
            
            db.commit()
            db.refresh(existing_record)
            
            return {
                "id": existing_record.id,
                "rss_feed_id": existing_record.rss_feed_id,
                "content_hash": existing_record.content_hash,
                "first_fetch_timestamp": existing_record.first_fetch_timestamp.isoformat(),
                "last_fetch_timestamp": existing_record.last_fetch_timestamp.isoformat(),
                "is_duplicate": True,
                "message": "Existing fetch record updated with new fetch timestamp"
            }
        else:
            # Create new fetch record
            record_data = {
                "rss_feed_id": rss_feed_id,
                "raw_content": fetch_data["raw_content"],
                "content_hash": content_hash,
                "http_status": fetch_data.get("http_status"),
                "content_encoding": fetch_data.get("content_encoding")
            }
            
            fetch_record = RSSFetchRecord(**record_data)
            db.add(fetch_record)
            db.commit()
            db.refresh(fetch_record)
            
            return {
                "id": fetch_record.id,
                "rss_feed_id": fetch_record.rss_feed_id,
                "content_hash": fetch_record.content_hash,
                "first_fetch_timestamp": fetch_record.first_fetch_timestamp.isoformat(),
                "last_fetch_timestamp": fetch_record.last_fetch_timestamp.isoformat(),
                "is_duplicate": False,
                "message": "New fetch record created successfully"
            }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create/update fetch record: {str(e)}")

@app.post("/api/internal/articles")
async def create_articles(
    articles_data: List[dict],
    db = Depends(get_session)
):
    """Internal API for scraper: Create new articles from RSS feeds."""
    
    # Create articles from scraper data
    created_count = 0
    failed_count = 0
    
    for article_data in articles_data:
        try:
            # Validate required fields
            required_fields = ["rss_fetch_record_id", "title"]
            for field in required_fields:
                if field not in article_data:
                    print(f"Missing required field {field} in article data")
                    failed_count += 1
                    continue
            
            # Check if article already exists (by RSS feed UUID and GUID)
            if article_data.get("guid"):
                # Get RSS feed UUID from fetch_record_id
                fetch_record = crud.rss_fetch_record.get(db, article_data["rss_fetch_record_id"])
                if fetch_record:
                    rss_feed = crud.rss_feed.get(db, fetch_record.rss_feed_id)
                    if rss_feed:
                        existing_item = crud.rss_item.get_by_rss_feed_uuid_and_guid(
                            db, 
                            rss_feed_uuid=str(rss_feed.uuid),
                            guid=article_data["guid"]
                        )
                        if existing_item:
                            continue  # Skip duplicates
            
            # Parse published_at if provided
            published_at = None
            if article_data.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(
                        article_data["published_at"].replace('Z', '+00:00')
                    )
                except ValueError:
                    pass
            
            # Process content with sentence anchors
            original_content = article_data.get("content")
            processed_content = process_text_with_anchors(original_content) if original_content else None
            
            # Create RSSItemMetadata
            item_data = {
                "rss_fetch_record_id": article_data["rss_fetch_record_id"],
                "guid": article_data.get("guid"),
                "title": article_data["title"],
                "content": processed_content,
                "url": article_data.get("url"),
                "published_at": published_at,
                "author": article_data.get("author"),
                "category": article_data.get("category"),
                "processing_status": "pending"
            }
            
            crud.rss_item.create(db, obj_in=item_data)
            created_count += 1
            
        except Exception as e:
            print(f"Failed to create article: {e}")
            failed_count += 1
    
    return {
        "message": f"Created {created_count} articles successfully",
        "created": created_count,
        "failed": failed_count,
        "total": len(articles_data)
    }

@app.get("/api/internal/articles/pending-processing")
async def get_articles_pending_processing(
    limit: int = 50,
    db = Depends(get_session)
):
    """Internal API for postprocess: Get articles that need AI processing."""
    
    # Get pending articles from database
    articles = crud.rss_item.get_pending_processing(db, limit=limit)
    return [
        {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "url": article.url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "processing_status": article.processing_status,
            "processing_attempts": article.processing_attempts
        }
        for article in articles
    ]

@app.post("/api/internal/articles/{article_id}/process")
async def update_article_processing_status(
    article_id: int,
    status_data: ArticleProcessingUpdate,
    db = Depends(get_session)
):
    """Internal API for postprocess: Update article processing status and store analysis data."""
    
    # Check if article exists
    article = crud.rss_item.get(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Extract processing data from postprocess service
    title_embedding = status_data.title_embedding
    embedding_model = status_data.embedding_model
    summary = status_data.summary
    summary_model = status_data.summary_model
    processed_at = status_data.processed_at
    error_message = status_data.error_message
    
    # Determine processing status based on data provided
    if title_embedding or summary:
        status = "completed"
    elif error_message:
        status = "failed"
    else:
        status = status_data.get("status", "failed")
    
    # Update article processing status
    article = crud.rss_item.update_processing_status(
        db, item_id=article_id, status=status, error_message=error_message
    )
    
    # Store derivatives if provided
    if title_embedding or summary:
        from sqlalchemy.orm import Session
        from newsfrontier_lib.models import RSSItemDerivative
        
        # Check if derivative already exists
        existing_derivative = db.query(RSSItemDerivative).filter(
            RSSItemDerivative.rss_item_id == article_id
        ).first()
        
        derivative_data = {
            "rss_item_id": article_id,
            "summary": summary,
            "title_embedding": title_embedding,
            "summary_embedding": title_embedding,  # Use same embedding for both for now
            "processing_status": "completed" if summary else "processing",
            "summary_generated_at": datetime.utcnow() if summary else None,
            "embeddings_generated_at": datetime.utcnow() if title_embedding else None,
            "llm_model_version": summary_model,
            "embedding_model_version": embedding_model
        }
        
        if existing_derivative:
            # Update existing derivative
            for field, value in derivative_data.items():
                if field != "rss_item_id" and value is not None:
                    setattr(existing_derivative, field, value)
            db.commit()
            db.refresh(existing_derivative)
        else:
            # Create new derivative
            derivative = RSSItemDerivative(**derivative_data)
            db.add(derivative)
            db.commit()
            db.refresh(derivative)
            
            db.commit()
            db.refresh(article)
    
    response_data = {
        "message": "Article processing completed successfully",
        "article_id": article.id,
        "status": status
    }
    
    # Add details about what was stored
    if title_embedding:
        response_data["embedding_stored"] = True
        response_data["embedding_dimensions"] = len(title_embedding) if isinstance(title_embedding, list) else None
    if summary:
        response_data["summary_stored"] = True
        response_data["summary_length"] = len(summary) if summary else 0
        
    return response_data

@app.post("/api/internal/articles/{article_id}/derivatives")
async def create_article_derivatives(
    article_id: int,
    derivatives_data: dict,
    db = Depends(get_session)
):
    """Internal API for postprocess: Store AI-generated article derivatives."""
    
    # Verify article exists
    article = crud.rss_item.get(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Extract derivative data
    summary = derivatives_data.get("summary")
    title_embedding = derivatives_data.get("title_embedding")
    summary_embedding = derivatives_data.get("summary_embedding")
    llm_model_version = derivatives_data.get("llm_model_version")
    embedding_model_version = derivatives_data.get("embedding_model_version")
    
    # Create or update RSSItemDerivative
    # First check if derivative already exists
    from sqlalchemy.orm import Session
    from newsfrontier_lib.models import RSSItemDerivative
    
    existing_derivative = db.query(RSSItemDerivative).filter(
        RSSItemDerivative.rss_item_id == article_id
    ).first()
    
    derivative_data = {
        "rss_item_id": article_id,
        "summary": summary,
        "title_embedding": title_embedding,
        "summary_embedding": summary_embedding,
        "processing_status": "completed" if summary else "failed",
        "summary_generated_at": datetime.utcnow() if summary else None,
        "embeddings_generated_at": datetime.utcnow() if (title_embedding and summary_embedding) else None,
        "llm_model_version": llm_model_version,
        "embedding_model_version": embedding_model_version
    }
    
    if existing_derivative:
        # Update existing
        for field, value in derivative_data.items():
            if field != "rss_item_id":  # Don't update the primary key relationship
                setattr(existing_derivative, field, value)
        db.commit()
        db.refresh(existing_derivative)
    else:
        # Create new
        derivative = RSSItemDerivative(**derivative_data)
        db.add(derivative)
        db.commit()
        db.refresh(derivative)
    
    return {
        "message": "Article derivatives created successfully",
        "article_id": article_id,
        "has_summary": bool(summary),
        "has_embeddings": bool(title_embedding and summary_embedding)
    }

@app.get("/api/internal/prompts")
async def get_prompts(db = Depends(get_session)):
    """Internal API for postprocess: Get AI processing prompts."""
    
    prompt_keys = [
        'prompt_summary_creation',
        'prompt_cluster_detection',
        'prompt_daily_summary_system',
        'prompt_cover_image_generation'
    ]
    
    # Get all prompt settings from database and return as dictionary
    prompts = {}
    for key in prompt_keys:
        setting = crud.system_setting.get_by_key(db, key=key)
        if setting:
            prompts[setting.setting_key] = setting.setting_value
    
    return prompts

@app.get("/api/internal/topics")
async def get_all_topics_internal(
    user_id: Optional[int] = None, 
    db = Depends(get_session)
):
    """Internal API for postprocess: Get all topics with embeddings."""
    
    # Get topics from database with optional user filtering
    if user_id:
        topics = crud.topic.get_user_topics(db, user_id=user_id)
    else:
        topics = crud.topic.get_multi(db, limit=1000)
    
    result = []
    for topic in topics:
        topic_data = {
            "id": topic.id,
            "name": topic.name,
            "user_id": topic.user_id,
            "is_active": topic.is_active,
            "created_at": topic.created_at.isoformat() if topic.created_at else None,
            "updated_at": topic.updated_at.isoformat() if topic.updated_at else None
        }
        
        # Include topic vector (embedding) if available
        if hasattr(topic, 'topic_vector') and topic.topic_vector is not None:
            topic_data["topic_vector"] = topic.topic_vector.tolist()
        
        result.append(topic_data)
    
    return result

@app.post("/api/internal/topics/similar")
async def find_similar_topics(
    similarity_data: dict,
    db = Depends(get_session)
):
    """Internal API: Find topics similar to given embedding."""
    embedding = similarity_data.get("embedding")
    user_id = similarity_data.get("user_id")
    threshold = similarity_data.get("threshold", 0.3)
    
    if not embedding:
        raise HTTPException(status_code=400, detail="Embedding is required")
    
    # Convert to numpy array if needed
    import numpy as np
    if isinstance(embedding, list):
        embedding = np.array(embedding)
    
    # Get topics for user
    if user_id:
        topics = crud.topic.get_user_topics(db, user_id=user_id)
    else:
        topics = crud.topic.get_multi(db, limit=1000)
    
    similar_topics = []
    for topic in topics:
        if hasattr(topic, 'topic_vector') and topic.topic_vector is not None:
            # Calculate cosine similarity
            topic_vec = topic.topic_vector
            similarity = np.dot(embedding, topic_vec) / (np.linalg.norm(embedding) * np.linalg.norm(topic_vec))
            
            if similarity >= threshold:
                similar_topics.append({
                    "id": topic.id,
                    "name": topic.name,
                    "user_id": topic.user_id,
                    "similarity": float(similarity),
                    "is_active": topic.is_active
                })
    
    # Sort by similarity (highest first)
    similar_topics.sort(key=lambda x: x["similarity"], reverse=True)
    
    return similar_topics

@app.get("/api/internal/topics/{topic_id}/events")
async def get_events_by_topic(
    topic_id: int,
    db = Depends(get_session)
):
    """Internal API: Get events for a specific topic."""
    
    # Verify topic exists
    topic = crud.topic.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Get events related to this topic through article-topic relationships
    from sqlalchemy.orm import joinedload
    from sqlalchemy import and_
    
    # Query events that have articles associated with this topic
    events_query = db.query(Event).join(
        ArticleEvent, Event.id == ArticleEvent.event_id
    ).join(
        ArticleTopic, ArticleEvent.rss_item_id == ArticleTopic.rss_item_id
    ).filter(
        ArticleTopic.topic_id == topic_id
    ).distinct()
    
    events = events_query.all()
    
    return [
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None
        }
        for event in events
    ]

@app.get("/api/internal/article-topics")
async def get_article_topics(
    rss_item_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    min_relevance_score: Optional[float] = None,
    max_relevance_score: Optional[float] = None,
    date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db = Depends(get_session)
):
    """Internal API: Search article-topics with filters."""
    
    # If date filter is provided, need to filter by article publication date
    if date:
        try:
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            # Query with date filtering on related RSS items
            query = db.query(ArticleTopic).join(RSSItemMetadata)
            
            if rss_item_id:
                query = query.filter(ArticleTopic.rss_item_id == rss_item_id)
            if topic_id:
                query = query.filter(ArticleTopic.topic_id == topic_id)
            if min_relevance_score is not None:
                query = query.filter(ArticleTopic.relevance_score >= min_relevance_score)
            if max_relevance_score is not None:
                query = query.filter(ArticleTopic.relevance_score <= max_relevance_score)
            
            # Filter by article publication date
            query = query.filter(
                RSSItemMetadata.published_at >= start_datetime,
                RSSItemMetadata.published_at < end_datetime
            )
            
            article_topics = query.order_by(ArticleTopic.created_at.desc()).offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"Error parsing date filter: {e}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Search article-topics using CRUD function (no date filter)
        article_topics = crud.article_topic.search(
            db,
            rss_item_id=rss_item_id,
            topic_id=topic_id,
            min_relevance_score=min_relevance_score,
            max_relevance_score=max_relevance_score,
            limit=limit,
            offset=offset
        )
    
    result = []
    for at in article_topics:
        at_data = {
            "rss_item_id": at.rss_item_id,
            "topic_id": at.topic_id,
            "relevance_score": at.relevance_score,
            "created_at": at.created_at.isoformat() if at.created_at else None
        }
        
        # Include related topic if available
        if hasattr(at, 'topic') and at.topic:
            at_data["topic"] = {
                "id": at.topic.id,
                "name": at.topic.name,
                "user_id": at.topic.user_id,
                "is_active": at.topic.is_active
            }
        
        # Include related article if available  
        if hasattr(at, 'rss_item') and at.rss_item:
            at_data["rss_item"] = {
                "id": at.rss_item.id,
                "title": at.rss_item.title,
                "url": at.rss_item.url,
                "published_at": at.rss_item.published_at.isoformat() if at.rss_item.published_at else None
            }
        
        result.append(at_data)
    
    return result

@app.post("/api/internal/article-topics")
async def create_article_topic(
    article_topic_data: ArticleTopicData,
    db = Depends(get_session)
):
    """Internal API: Create new article-topic relationship."""
    
    # Extract validated fields
    rss_item_id = article_topic_data.rss_item_id
    topic_id = article_topic_data.topic_id
    
    # Verify article exists
    article = crud.rss_item.get(db, rss_item_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Verify topic exists
    topic = crud.topic.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check if relationship already exists
    existing = crud.article_topic.get_by_ids(
        db, 
        rss_item_id=rss_item_id, 
        topic_id=topic_id
    )
    if existing:
        raise HTTPException(
            status_code=409, 
            detail="Article-topic relationship already exists"
        )
    
    # Create article-topic relationship
    relevance_score = article_topic_data.relevance_score
    article_topic = crud.article_topic.create_article_topic(
        db,
        rss_item_id=rss_item_id,
        topic_id=topic_id,
        relevance_score=relevance_score
    )
    
    return {
        "message": "Article-topic relationship created successfully",
        "rss_item_id": article_topic.rss_item_id,
        "topic_id": article_topic.topic_id,
        "relevance_score": article_topic.relevance_score,
        "created_at": article_topic.created_at.isoformat()
    }

# Internal Events (Clusters) API
@app.get("/api/internal/events")
async def get_events_internal(
    user_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    created_date: Optional[str] = None,
    db = Depends(get_session)
):
    """Internal API: Get event clusters filtered by user and/or topic."""
    
    query = db.query(Event)
    
    if user_id:
        query = query.filter(Event.user_id == user_id)
    if topic_id:
        query = query.filter(Event.topic_id == topic_id)
    
    # Add date filtering if provided
    if created_date:
        try:
            from datetime import datetime, timedelta
            date_obj = datetime.strptime(created_date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            query = query.filter(
                Event.created_at >= start_datetime,
                Event.created_at < end_datetime
            )
        except Exception as e:
            logger.error(f"Error parsing created_date filter: {e}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    events = query.order_by(Event.updated_at.desc()).all()
    
    return [
        {
            "id": event.id,
            "user_id": event.user_id,
            "topic_id": event.topic_id,
            "title": event.title,
            "description": event.description,
            "event_description": event.event_description,
            "event_embedding": event.event_embedding.tolist() if event.event_embedding is not None else None,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
            "last_updated_at": event.last_updated_at.isoformat()
        }
        for event in events
    ]

@app.post("/api/internal/events")
async def create_event_internal(
    event_data: EventData,
    db = Depends(get_session)
):
    """Internal API: Create new event cluster."""
    
    # Extract validated fields
    user_id = event_data.user_id
    topic_id = event_data.topic_id
    title = event_data.title
    
    # Verify user exists
    user = crud.user.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify topic exists
    topic = crud.topic.get(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Generate embedding for event_description if provided
    event_embedding = None
    if event_data.event_description:
        try:
            from newsfrontier_lib import generate_content_embedding
            event_embedding = generate_content_embedding(title, event_data.event_description)
            event_embedding = event_embedding.tolist() if hasattr(event_embedding, 'tolist') else event_embedding
        except Exception as e:
            logger.error(f"Failed to generate event embedding: {e}")
    
    # Create event
    event_create_data = {
        "user_id": user_id,
        "topic_id": topic_id,
        "title": title,
        "description": event_data.description,
        "event_description": event_data.event_description,
        "event_embedding": event_embedding
    }
    
    event = crud.event.create(db, obj_in=event_create_data)
    
    return {
        "id": event.id,
        "user_id": event.user_id,
        "topic_id": event.topic_id,
        "title": event.title,
        "description": event.description,
        "event_description": event.event_description,
        "event_embedding": event.event_embedding.tolist() if event.event_embedding is not None else None,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat(),
        "last_updated_at": event.last_updated_at.isoformat()
    }

@app.post("/api/internal/article-events")
async def create_article_event_internal(
    article_event_data: ArticleEventData,
    db = Depends(get_session)
):
    """Internal API: Create new article-event relationship."""
    
    logger.info(f"Creating article-event relationship: {article_event_data}")
    # Extract validated fields
    rss_item_id = article_event_data.rss_item_id
    event_id = article_event_data.event_id
    
    if not rss_item_id or not event_id:
        raise HTTPException(
            status_code=400,
            detail="Both rss_item_id and event_id are required"
        )
    
    # Verify article exists
    article = crud.rss_item.get(db, rss_item_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Verify event exists
    event = crud.event.get(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if relationship already exists
    existing = crud.article_event.get_by_ids(
        db,
        rss_item_id=rss_item_id,
        event_id=event_id
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Article-event relationship already exists"
        )
    
    # Create article-event relationship
    relevance_score = article_event_data.relevance_score
    article_event = crud.article_event.create_article_event(
        db,
        rss_item_id=rss_item_id,
        event_id=event_id,
        relevance_score=relevance_score
    )
    
    return {
        "message": "Article-event relationship created successfully",
        "rss_item_id": article_event.rss_item_id,
        "event_id": article_event.event_id,
        "relevance_score": article_event.relevance_score,
        "created_at": article_event.created_at.isoformat()
    }

@app.get("/api/internal/articles/completed")
async def get_completed_articles_internal(
    limit: int = 1000,
    db = Depends(get_session)
):
    """Internal API: Get articles that have been completed with derivatives."""
    articles = crud.rss_item.get_completed_articles(db, limit=limit)
    return {
        "data": [
            {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "processing_status": article.processing_status
            }
            for article in articles
        ]
    }

@app.get("/api/internal/article/{article_id}")
async def get_article_detail_internal(
    article_id: int,
    db = Depends(get_session)
):
    """Internal API: Get full article details including derivatives."""
    article = crud.rss_item.get(db, id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get derivatives
    derivatives = crud.rss_item_derivative.get_by_article_id(db, rss_item_id=article_id)
    
    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "url": article.url,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "processing_status": article.processing_status,
        "derivatives": [
            {
                "id": deriv.id,
                "summary": deriv.summary,
                "title_embedding": deriv.title_embedding.tolist(),
                "summary_embedding": deriv.summary_embedding.tolist(),
                "processing_status": deriv.processing_status,
                "summary_generated_at": deriv.summary_generated_at.isoformat() if deriv.summary_generated_at else None,
                "embeddings_generated_at": deriv.embeddings_generated_at.isoformat() if deriv.embeddings_generated_at else None
            }
            for deriv in derivatives
        ]
    }

@app.get("/api/internal/articles/{article_id}")
async def get_article_detail_internal_plural(
    article_id: int,
    db = Depends(get_session)
):
    """Internal API: Get article details (plural endpoint for compatibility)."""
    # Reuse the same logic as the singular version
    article = crud.rss_item.get(db, id=article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # For cluster detection test, we need basic article info without derivatives
    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "url": article.url,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "author": article.author,
        "category": article.category,
        "processing_status": article.processing_status,
        "user_id": getattr(article, 'user_id', None)  # Add user_id if available
    }

# Daily Summary Internal API Endpoints
@app.get("/api/internal/users")
async def get_all_users_internal(db = Depends(get_session)):
    """Internal API: Get all users for daily summary generation."""
    try:
        users = crud.user.get_multi(db, limit=10000)
        return {
            "data": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "daily_summary_prompt": user.daily_summary_prompt
                }
                for user in users
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/internal/user/{user_id}")
async def get_user_internal(user_id: int, db = Depends(get_session)):
    """Internal API: Get user details by ID."""
    try:
        user = crud.user.get(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "daily_summary_prompt": user.daily_summary_prompt,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/internal/user-summaries/{user_id}")
async def get_user_summaries_internal(
    user_id: int,
    limit: int = 10,
    db = Depends(get_session)
):
    """Internal API: Get recent daily summaries for a user."""
    try:
        summaries = crud.user_summary.get_recent_summaries(db, user_id=user_id, days=30)
        
        # Sort by date descending and limit
        sorted_summaries = sorted(summaries, key=lambda x: x.date, reverse=True)[:limit]
        
        return {
            "data": [
                {
                    "id": summary.id,
                    "user_id": summary.user_id,
                    "date": summary.date.isoformat(),
                    "summary": summary.summary,
                    "cover_prompt": summary.cover_prompt,
                    "cover_arguments": summary.cover_arguments,
                    "cover_seed": summary.cover_seed,
                    "cover_s3key": summary.cover_s3key,
                    "created_at": summary.created_at.isoformat() if summary.created_at else None
                }
                for summary in sorted_summaries
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching user summaries for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/internal/user-summary/{user_id}/{date}")
async def get_user_summary_by_date_internal(
    user_id: int,
    date: str,
    db = Depends(get_session)
):
    """Internal API: Check if daily summary exists for user on specific date."""
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        
        summary = crud.user_summary.get_by_date(db, user_id=user_id, date=date_obj)
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        return {
            "id": summary.id,
            "user_id": summary.user_id,
            "date": summary.date.isoformat(),
            "summary": summary.summary,
            "cover_prompt": summary.cover_prompt,
            "cover_arguments": summary.cover_arguments,
            "cover_seed": summary.cover_seed,
            "cover_s3key": summary.cover_s3key,
            "created_at": summary.created_at.isoformat() if summary.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user summary for user {user_id} on {date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/internal/user-summaries")
async def create_user_summary_internal(
    request: DailySummaryCreateRequest,
    db = Depends(get_session)
):
    """Internal API: Create new daily summary."""
    try:
        from datetime import datetime
        date_obj = datetime.strptime(request.date, "%Y-%m-%d").date()
        
        # Check if summary already exists
        existing = crud.user_summary.get_by_date(db, user_id=request.user_id, date=date_obj)
        if existing:
            raise HTTPException(status_code=409, detail="Summary already exists for this date")
        
        # Create new summary
        summary_data = {
            'user_id': request.user_id,
            'date': date_obj,
            'summary': request.summary,
            'cover_prompt': request.cover_prompt,
            'cover_arguments': request.cover_arguments,
            'cover_seed': request.cover_seed,
            'cover_s3key': request.cover_s3key
        }
        
        summary = crud.user_summary.create(db, obj_in=summary_data)
        
        return {
            "id": summary.id,
            "user_id": summary.user_id,
            "date": summary.date.isoformat(),
            "summary": summary.summary,
            "cover_prompt": summary.cover_prompt,
            "cover_arguments": summary.cover_arguments,
            "cover_seed": summary.cover_seed,
            "cover_s3key": summary.cover_s3key,
            "created_at": summary.created_at.isoformat() if summary.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/internal/system-settings/{setting_key}")
async def get_system_setting_internal(setting_key: str, db = Depends(get_session)):
    """Internal API: Get a specific system setting by key."""
    try:
        setting = crud.system_setting.get_by_key(db, key=setting_key)
        if not setting:
            raise HTTPException(status_code=404, detail=f"System setting '{setting_key}' not found")
        
        return {
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value,
            "setting_type": setting.setting_type,
            "description": setting.description,
            "is_public": setting.is_public
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system setting '{setting_key}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Admin System Settings API
@app.get("/api/admin/system-settings", response_model=List[SystemSettingResponse])
async def get_system_settings(admin_user = Depends(verify_admin), db = Depends(get_session)):
    """Get all system settings (Admin only)."""
    logger.info(f"Admin user {admin_user.username} requesting system settings")
    
    # Get all system settings from database
    settings = crud.system_setting.get_multi(db, limit=1000)  # Get all settings with generous limit
    
    return [
        SystemSettingResponse(
            id=setting.id,
            setting_key=setting.setting_key,
            setting_value=setting.setting_value,
            setting_type=setting.setting_type,
            description=setting.description,
            is_public=setting.is_public,
            updated_at=setting.updated_at.isoformat() if setting.updated_at else "",
            created_at=setting.created_at.isoformat() if setting.created_at else ""
        )
        for setting in settings
    ]

@app.put("/api/admin/system-settings")
async def update_system_settings(
    settings_updates: List[SystemSettingUpdate],
    admin_user = Depends(verify_admin), 
    db = Depends(get_session)
):
    """Update multiple system settings (Admin only)."""
    logger.info(f"Admin user {admin_user.username} updating system settings")
    
    updated_count = 0
    failed_updates = []
    
    for update in settings_updates:
        try:
            # Validate setting type
            if update.setting_type not in ['string', 'integer', 'boolean', 'json', 'float']:
                failed_updates.append({
                    "setting_key": update.setting_key,
                    "error": f"Invalid setting type: {update.setting_type}"
                })
                continue
            
            # Type validation for specific types
            if update.setting_type == 'integer':
                try:
                    int(update.setting_value)
                except ValueError:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Invalid integer value"
                    })
                    continue
            elif update.setting_type == 'float':
                try:
                    float(update.setting_value)
                except ValueError:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Invalid float value"
                    })
                    continue
            elif update.setting_type == 'boolean':
                if update.setting_value.lower() not in ['true', 'false']:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Boolean value must be 'true' or 'false'"
                    })
                    continue
            elif update.setting_type == 'json':
                try:
                    json.loads(update.setting_value)
                except json.JSONDecodeError:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Invalid JSON value"
                    })
                    continue
            
            # Get existing setting
            existing_setting = crud.system_setting.get_by_key(db, key=update.setting_key)
            
            if existing_setting:
                # Update existing setting
                updated_setting = crud.system_setting.set_setting_value(
                    db,
                    key=update.setting_key,
                    value=update.setting_value,
                    setting_type=update.setting_type,
                    updated_by=admin_user.id
                )
                if updated_setting:
                    updated_count += 1
                    logger.info(f"Updated setting: {update.setting_key} = {update.setting_value}")
                else:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Failed to update setting"
                    })
            else:
                # Create new setting (this should rarely happen as settings are pre-populated)
                setting_data = {
                    "setting_key": update.setting_key,
                    "setting_value": update.setting_value,
                    "setting_type": update.setting_type,
                    "description": f"Custom setting: {update.setting_key}",
                    "is_public": False,
                    "updated_by": admin_user.id
                }
                
                new_setting = crud.system_setting.create(db, obj_in=setting_data)
                if new_setting:
                    updated_count += 1
                    logger.info(f"Created new setting: {update.setting_key} = {update.setting_value}")
                else:
                    failed_updates.append({
                        "setting_key": update.setting_key,
                        "error": "Failed to create new setting"
                    })
                    
        except Exception as e:
            logger.error(f"Error updating setting {update.setting_key}: {str(e)}")
            failed_updates.append({
                "setting_key": update.setting_key,
                "error": f"Unexpected error: {str(e)}"
            })
    
    response = {
        "message": f"Updated {updated_count} settings successfully",
        "updated_count": updated_count,
        "total_count": len(settings_updates)
    }
    
    if failed_updates:
        response["failed_updates"] = failed_updates
        response["failed_count"] = len(failed_updates)
    
    return response

# Debug API Endpoints
@app.post("/api/debug/regenerate-daily-summary")
async def regenerate_daily_summary_debug(
    user_token = Depends(get_current_user),
    db = Depends(get_session)
):
    """Debug endpoint to trigger daily summary regeneration for current user."""
    try:
        from datetime import datetime
        import requests
        
        user_id = user_token.id
        today = datetime.now().date()
        
        logger.info(f"Debug: Regenerating daily summary for user {user_id} on {today}")
        
        # Delete existing summary for today if it exists
        existing_summary = crud.user_summary.get_by_date(db, user_id=user_id, date=today)
        if existing_summary:
            crud.user_summary.remove(db, id=existing_summary.id)
            logger.info(f"Debug: Deleted existing summary for user {user_id} on {today}")
        
        # Try to trigger postprocess service to regenerate summary
        postprocess_url = os.getenv("POSTPROCESS_URL", "http://localhost:8001")
        try:
            # Call internal API to trigger summary generation for specific user
            response = requests.post(
                f"{postprocess_url}/api/generate-user-summary/{user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Debug: Successfully triggered summary regeneration for user {user_id}")
                return {
                    "success": True,
                    "message": f"Daily summary regeneration triggered for user {user_id}",
                    "date": today.isoformat(),
                    "postprocess_triggered": True
                }
            else:
                logger.warning(f"Debug: Postprocess service returned status {response.status_code}")
                return {
                    "success": True,
                    "message": f"Existing summary deleted for user {user_id}, but postprocess service may not be available",
                    "date": today.isoformat(),
                    "postprocess_triggered": False,
                    "postprocess_status": response.status_code
                }
        except requests.RequestException as e:
            logger.warning(f"Debug: Could not reach postprocess service: {e}")
            return {
                "success": True,
                "message": f"Existing summary deleted for user {user_id}, but postprocess service is not available",
                "date": today.isoformat(),
                "postprocess_triggered": False,
                "postprocess_error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Debug: Error regenerating daily summary for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate daily summary: {str(e)}")

@app.post("/api/debug/fetch-rss")
async def fetch_rss_debug(
    user_token = Depends(get_current_user),
    db = Depends(get_session)
):
    """Debug endpoint to trigger RSS feed collection."""
    try:
        import requests
        
        logger.info(f"Debug: Triggering RSS feed collection requested by user {user_token.id}")
        
        # For now, scraper service doesn't have API endpoints
        # This is a placeholder that suggests manual action
        logger.info("Debug: RSS feed collection requested - currently requires manual intervention")
        return {
            "success": True,
            "message": "RSS feed collection request logged. Currently requires manual scraper restart or wait for next scheduled cycle.",
            "scraper_triggered": False,
            "note": "Scraper service API endpoints not yet implemented. Consider restarting the scraper service manually."
        }
            
    except Exception as e:
        logger.error(f"Debug: Error triggering RSS feed collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger RSS collection: {str(e)}")

@app.post("/api/debug/process-articles")
async def process_articles_debug(
    user_token = Depends(get_current_user),
    db = Depends(get_session)
):
    """Debug endpoint to trigger article processing."""
    try:
        import requests
        
        logger.info(f"Debug: Triggering article processing requested by user {user_token.id}")
        
        # Try to trigger postprocess service
        postprocess_url = os.getenv("POSTPROCESS_URL", "http://localhost:8001")
        try:
            response = requests.post(
                f"{postprocess_url}/api/process",
                timeout=120
            )
            
            if response.status_code == 200:
                logger.info("Debug: Successfully triggered article processing")
                return {
                    "success": True,
                    "message": "Article processing triggered successfully",
                    "postprocess_triggered": True
                }
            else:
                logger.warning(f"Debug: Postprocess service returned status {response.status_code}")
                return {
                    "success": False,
                    "message": f"Postprocess service responded with status {response.status_code}",
                    "postprocess_triggered": False,
                    "postprocess_status": response.status_code
                }
        except requests.RequestException as e:
            logger.warning(f"Debug: Could not reach postprocess service: {e}")
            return {
                "success": False,
                "message": "Postprocess service is not available",
                "postprocess_triggered": False,
                "postprocess_error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Debug: Error triggering article processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger article processing: {str(e)}")

# System Health and Status API
@app.get("/api/system/health")
async def get_system_health():
    """System health check endpoint."""
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Test database connection
        test_db = next(get_session())
        health_status["database"] = "healthy"
        test_db.close()
    except Exception:
        health_status["database"] = "unhealthy"
    
    return health_status

@app.get("/api/system/stats")
async def get_system_stats(db = Depends(get_session)):
    """Get system statistics for monitoring."""
    
    from sqlalchemy import func, and_
    from datetime import datetime, date
    
    # Calculate real statistics from database
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Total RSS feeds
    total_feeds = db.query(func.count(RSSFeed.id)).scalar() or 0
    
    # Total articles
    total_articles = db.query(func.count(RSSItemMetadata.id)).scalar() or 0
    
    # Articles pending processing
    articles_pending_processing = db.query(func.count(RSSItemMetadata.id)).filter(
        RSSItemMetadata.processing_status == 'pending'
    ).scalar() or 0
    
    # Articles processed today
    articles_processed_today = db.query(func.count(RSSItemMetadata.id)).filter(
        and_(
            RSSItemMetadata.processing_completed_at >= today_start,
            RSSItemMetadata.processing_completed_at <= today_end,
            RSSItemMetadata.processing_status == 'completed'
        )
    ).scalar() or 0
    
    # Active users (users who have logged in recently or have active subscriptions)
    active_users = db.query(func.count(User.id.distinct())).join(RSSSubscription).filter(
        RSSSubscription.is_active == True
    ).scalar() or 0
    
    return {
        "total_feeds": total_feeds,
        "total_articles": total_articles,
        "articles_pending_processing": articles_pending_processing,
        "articles_processed_today": articles_processed_today,
        "active_users": active_users,
        "last_updated": datetime.utcnow().isoformat()
    }

# Enhanced Topic Management endpoints removed - using main topic endpoints above

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "NewsFrontier API is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 NewsFrontier API is starting up!")
    
    # Test database connection
    try:
        db = next(get_session())
        logger.info("✅ Database connection test successful")
        db.close()
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🔄 NewsFrontier API is shutting down...")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting NewsFrontier API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
