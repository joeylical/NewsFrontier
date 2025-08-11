"""
CRUD (Create, Read, Update, Delete) operations for database models.

This module provides common database operations for all models
in the NewsFrontier application.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INTERVAL
from datetime import datetime, date, timedelta

from .database import Base
from .models import (
    User, RSSFeed, RSSSubscription, RSSFetchRecord, RSSItemMetadata, 
    RSSItemDerivative, Topic, ArticleTopic, Event, ArticleEvent,
    UserTopic, UserSummary, SystemSetting
)
from .schemas import UserCreate, UserUpdate

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "id",
        order_desc: bool = False
    ) -> List[ModelType]:
        query = db.query(self.model)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            query = query.order_by(desc(column) if order_desc else asc(column))
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        if hasattr(obj_in, 'dict'):
            obj_in_data = obj_in.dict()
        else:
            obj_in_data = obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        if hasattr(obj_in, 'dict'):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        if hasattr(db_obj, 'updated_at'):
            db_obj.updated_at = datetime.utcnow()
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def authenticate(self, db: Session, *, username: str, password_hash: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        # Note: In practice, you should verify the password hash here
        return user

    def is_admin(self, user: User) -> bool:
        return user.is_admin

    def get_admins(self, db: Session) -> List[User]:
        return db.query(User).filter(User.is_admin == True).all()


class CRUDRSSFeed(CRUDBase[RSSFeed, dict, dict]):
    def get_by_url(self, db: Session, *, url: str) -> Optional[RSSFeed]:
        return db.query(RSSFeed).filter(RSSFeed.url == url).first()

    def get_by_uuid(self, db: Session, *, uuid: str) -> Optional[RSSFeed]:
        return db.query(RSSFeed).filter(RSSFeed.uuid == uuid).first()

    def get_feeds_due_for_fetch(self, db: Session) -> List[RSSFeed]:
        """Get RSS feeds that are due for fetching based on their interval."""
        current_time = datetime.utcnow()
        return db.query(RSSFeed).filter(
            or_(
                RSSFeed.last_fetch_status.in_(['pending', 'failed']),
                RSSFeed.last_fetch_at.is_(None),
                RSSFeed.last_fetch_at < (
                    current_time - func.cast('1 minute', INTERVAL) * RSSFeed.fetch_interval_minutes
                )
            )
        ).all()

    def update_fetch_status(
        self, 
        db: Session, 
        *, 
        feed_id: int, 
        status: str, 
        fetch_time: datetime = None
    ) -> RSSFeed:
        feed = self.get(db, feed_id)
        if feed:
            feed.last_fetch_status = status
            feed.last_fetch_at = fetch_time or datetime.utcnow()
            db.commit()
            db.refresh(feed)
        return feed


class CRUDRSSItem(CRUDBase[RSSItemMetadata, dict, dict]):
    def get_by_guid(
        self, 
        db: Session, 
        *, 
        fetch_record_id: int, 
        guid: str
    ) -> Optional[RSSItemMetadata]:
        return db.query(RSSItemMetadata).filter(
            and_(
                RSSItemMetadata.rss_fetch_record_id == fetch_record_id,
                RSSItemMetadata.guid == guid
            )
        ).first()

    def get_by_rss_feed_uuid_and_guid(
        self, 
        db: Session, 
        *, 
        rss_feed_uuid: str, 
        guid: str
    ) -> Optional[RSSItemMetadata]:
        """Check if article with same RSS feed UUID + guid already exists."""
        return db.query(RSSItemMetadata).join(RSSFetchRecord).join(RSSFeed).filter(
            and_(
                RSSFeed.uuid == rss_feed_uuid,
                RSSItemMetadata.guid == guid
            )
        ).first()

    def get_pending_processing(self, db: Session, *, limit: int = 50) -> List[RSSItemMetadata]:
        """Get articles that need AI processing."""
        return db.query(RSSItemMetadata).filter(
            or_(
                RSSItemMetadata.processing_status == 'pending',
                RSSItemMetadata.processing_status == 'failed'
            )
        ).filter(
            RSSItemMetadata.processing_attempts < 5
        ).order_by(RSSItemMetadata.created_at.asc()).limit(limit).all()

    def get_recent_articles(
        self, 
        db: Session, 
        *, 
        hours: int = 24, 
        limit: int = 100
    ) -> List[RSSItemMetadata]:
        """Get recently published articles."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(RSSItemMetadata).filter(
            RSSItemMetadata.published_at >= cutoff_time
        ).order_by(RSSItemMetadata.published_at.desc()).limit(limit).all()

    def update_processing_status(
        self, 
        db: Session, 
        *, 
        item_id: int, 
        status: str,
        error_message: str = None
    ) -> RSSItemMetadata:
        item = self.get(db, item_id)
        if item:
            # Only increment attempts for processing or failure
            if status in ['processing', 'failed']:
                item.processing_attempts += 1
            
            item.processing_status = status
            
            if status == 'processing':
                item.processing_started_at = datetime.utcnow()
            elif status in ['completed', 'failed']:
                item.processing_completed_at = datetime.utcnow()
                if error_message:
                    item.last_error_message = error_message
            
            db.commit()
            db.refresh(item)
        return item

    def get_completed_articles(self, db: Session, *, limit: int = 1000) -> List[RSSItemMetadata]:
        """Get articles that have been completed processing."""
        return db.query(RSSItemMetadata).filter(
            RSSItemMetadata.processing_status == 'completed'
        ).order_by(RSSItemMetadata.created_at.desc()).limit(limit).all()


class CRUDTopic(CRUDBase[Topic, dict, dict]):
    def get_user_topics(self, db: Session, *, user_id: int) -> List[Topic]:
        return db.query(Topic).filter(
            and_(Topic.user_id == user_id, Topic.is_active == True)
        ).order_by(Topic.created_at.desc()).all()

    def get_by_name(self, db: Session, *, user_id: int, name: str) -> Optional[Topic]:
        return db.query(Topic).filter(
            and_(Topic.user_id == user_id, Topic.name == name)
        ).first()


class CRUDEvent(CRUDBase[Event, dict, dict]):
    def get_topic_events(
        self, 
        db: Session, 
        *, 
        topic_id: int, 
        limit: int = 50
    ) -> List[Event]:
        return db.query(Event).filter(
            Event.topic_id == topic_id
        ).order_by(Event.updated_at.desc()).limit(limit).all()

    def get_user_recent_events(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        days: int = 7,
        limit: int = 100
    ) -> List[Event]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.updated_at >= cutoff_date
            )
        ).order_by(Event.updated_at.desc()).limit(limit).all()


class CRUDArticleEvent(CRUDBase[ArticleEvent, dict, dict]):
    def get_by_ids(
        self, 
        db: Session, 
        *, 
        rss_item_id: int, 
        event_id: int
    ) -> Optional[ArticleEvent]:
        return db.query(ArticleEvent).filter(
            and_(
                ArticleEvent.rss_item_id == rss_item_id,
                ArticleEvent.event_id == event_id
            )
        ).first()

    def create_article_event(
        self,
        db: Session,
        *,
        rss_item_id: int,
        event_id: int,
        relevance_score: Optional[float] = None
    ) -> ArticleEvent:
        article_event = ArticleEvent(
            rss_item_id=rss_item_id,
            event_id=event_id,
            relevance_score=relevance_score
        )
        db.add(article_event)
        db.commit()
        db.refresh(article_event)
        return article_event

    def get_by_event(
        self, 
        db: Session, 
        *, 
        event_id: int
    ) -> List[ArticleEvent]:
        """Get all articles associated with an event."""
        return db.query(ArticleEvent).filter(
            ArticleEvent.event_id == event_id
        ).all()


class CRUDUserSummary(CRUDBase[UserSummary, dict, dict]):
    def get_by_date(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        date: date
    ) -> Optional[UserSummary]:
        return db.query(UserSummary).filter(
            and_(UserSummary.user_id == user_id, UserSummary.date == date)
        ).first()

    def get_recent_summaries(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        days: int = 30
    ) -> List[UserSummary]:
        cutoff_date = date.today() - timedelta(days=days)
        return db.query(UserSummary).filter(
            and_(
                UserSummary.user_id == user_id,
                UserSummary.date >= cutoff_date
            )
        ).order_by(UserSummary.date.desc()).all()


class CRUDSystemSetting(CRUDBase[SystemSetting, dict, dict]):
    def get_by_key(self, db: Session, *, key: str) -> Optional[SystemSetting]:
        return db.query(SystemSetting).filter(SystemSetting.setting_key == key).first()

    def get_public_settings(self, db: Session) -> List[SystemSetting]:
        return db.query(SystemSetting).filter(SystemSetting.is_public == True).all()

    def get_setting_value(self, db: Session, *, key: str, default: Any = None) -> Any:
        setting = self.get_by_key(db, key=key)
        if not setting:
            return default
        
        # Convert based on setting_type
        if setting.setting_type == 'integer':
            return int(setting.setting_value) if setting.setting_value else default
        elif setting.setting_type == 'float':
            return float(setting.setting_value) if setting.setting_value else default
        elif setting.setting_type == 'boolean':
            return setting.setting_value.lower() == 'true' if setting.setting_value else default
        elif setting.setting_type == 'json':
            import json
            return json.loads(setting.setting_value) if setting.setting_value else default
        else:  # string
            return setting.setting_value if setting.setting_value is not None else default

    def set_setting_value(
        self, 
        db: Session, 
        *, 
        key: str, 
        value: Any,
        setting_type: str = 'string',
        description: str = None,
        is_public: bool = False,
        updated_by: int = None
    ) -> SystemSetting:
        setting = self.get_by_key(db, key=key)
        
        # Convert value to string for storage
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
            setting_type = 'boolean'
        elif isinstance(value, (int, float)):
            str_value = str(value)
            setting_type = 'integer' if isinstance(value, int) else 'float'
        elif isinstance(value, (dict, list)):
            import json
            str_value = json.dumps(value)
            setting_type = 'json'
        else:
            str_value = str(value) if value is not None else None
        
        if setting:
            setting.setting_value = str_value
            setting.setting_type = setting_type
            if description:
                setting.description = description
            if updated_by:
                setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(setting)
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=str_value,
                setting_type=setting_type,
                description=description,
                is_public=is_public,
                updated_by=updated_by
            )
            db.add(setting)
            db.commit()
            db.refresh(setting)
        
        return setting


class CRUDRSSSubscription(CRUDBase[RSSSubscription, dict, dict]):
    def get_user_subscriptions(self, db: Session, *, user_id: int) -> List[RSSSubscription]:
        """Get all RSS subscriptions for a user with their feed details."""
        return db.query(RSSSubscription).filter(
            RSSSubscription.user_id == user_id
        ).all()
    
    def get_user_subscription(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        rss_uuid: str
    ) -> Optional[RSSSubscription]:
        """Get a specific RSS subscription for a user."""
        return db.query(RSSSubscription).filter(
            and_(
                RSSSubscription.user_id == user_id,
                RSSSubscription.rss_uuid == rss_uuid
            )
        ).first()
    
    def create_subscription(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        rss_uuid: str,
        alias: str = None,
        is_active: bool = True
    ) -> RSSSubscription:
        """Create a new RSS subscription for a user."""
        subscription = RSSSubscription(
            user_id=user_id,
            rss_uuid=rss_uuid,
            alias=alias,
            is_active=is_active
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    def update_subscription(
        self,
        db: Session,
        *,
        user_id: int,
        rss_uuid: str,
        alias: str = None,
        is_active: bool = None
    ) -> Optional[RSSSubscription]:
        """Update an existing RSS subscription."""
        subscription = self.get_user_subscription(db, user_id=user_id, rss_uuid=rss_uuid)
        if not subscription:
            return None
        
        if alias is not None:
            subscription.alias = alias
        if is_active is not None:
            subscription.is_active = is_active
        
        db.commit()
        db.refresh(subscription)
        return subscription
    
    def delete_subscription(
        self,
        db: Session,
        *,
        user_id: int,
        rss_uuid: str
    ) -> bool:
        """Delete an RSS subscription."""
        subscription = self.get_user_subscription(db, user_id=user_id, rss_uuid=rss_uuid)
        if not subscription:
            return False
        
        db.delete(subscription)
        db.commit()
        return True


class CRUDRSSFetchRecord(CRUDBase[RSSFetchRecord, dict, dict]):
    def create_fetch_record(
        self,
        db: Session,
        *,
        rss_feed_id: int,
        raw_content: str,
        content_hash: str,
        http_status: int = None,
        content_encoding: str = None
    ) -> RSSFetchRecord:
        """Create a new RSS fetch record."""
        record = RSSFetchRecord(
            rss_feed_id=rss_feed_id,
            raw_content=raw_content,
            content_hash=content_hash,
            http_status=http_status,
            content_encoding=content_encoding
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    
    def get_latest_for_feed(self, db: Session, *, rss_feed_id: int) -> Optional[RSSFetchRecord]:
        """Get the latest fetch record for a specific RSS feed."""
        return db.query(RSSFetchRecord).filter(
            RSSFetchRecord.rss_feed_id == rss_feed_id
        ).order_by(RSSFetchRecord.fetch_timestamp.desc()).first()


class CRUDArticleTopic(CRUDBase[ArticleTopic, dict, dict]):
    def create_article_topic(
        self,
        db: Session,
        *,
        rss_item_id: int,
        topic_id: int,
        relevance_score: Optional[float] = None
    ) -> ArticleTopic:
        """Create a new article-topic relationship."""
        article_topic = ArticleTopic(
            rss_item_id=rss_item_id,
            topic_id=topic_id,
            relevance_score=relevance_score
        )
        db.add(article_topic)
        db.commit()
        db.refresh(article_topic)
        return article_topic
    
    def get_by_ids(
        self, 
        db: Session, 
        *, 
        rss_item_id: int, 
        topic_id: int
    ) -> Optional[ArticleTopic]:
        """Get article-topic by composite key."""
        return db.query(ArticleTopic).filter(
            ArticleTopic.rss_item_id == rss_item_id,
            ArticleTopic.topic_id == topic_id
        ).first()
    
    def search(
        self,
        db: Session,
        *,
        rss_item_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        min_relevance_score: Optional[float] = None,
        max_relevance_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ArticleTopic]:
        """Search article-topics with filters."""
        query = db.query(ArticleTopic)
        
        if rss_item_id is not None:
            query = query.filter(ArticleTopic.rss_item_id == rss_item_id)
        
        if topic_id is not None:
            query = query.filter(ArticleTopic.topic_id == topic_id)
        
        if min_relevance_score is not None:
            query = query.filter(ArticleTopic.relevance_score >= min_relevance_score)
        
        if max_relevance_score is not None:
            query = query.filter(ArticleTopic.relevance_score <= max_relevance_score)
        
        return query.order_by(ArticleTopic.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_topics_for_article(
        self, 
        db: Session, 
        *, 
        rss_item_id: int
    ) -> List[ArticleTopic]:
        """Get all topics associated with an article."""
        return db.query(ArticleTopic).filter(
            ArticleTopic.rss_item_id == rss_item_id
        ).all()
    
    def get_articles_for_topic(
        self, 
        db: Session, 
        *, 
        topic_id: int
    ) -> List[ArticleTopic]:
        """Get all articles associated with a topic."""
        return db.query(ArticleTopic).filter(
            ArticleTopic.topic_id == topic_id
        ).all()


class CRUDRSSItemDerivative(CRUDBase[RSSItemDerivative, dict, dict]):
    def get_by_article_id(self, db: Session, *, rss_item_id: int) -> List[RSSItemDerivative]:
        """Get derivatives by article ID."""
        return db.query(RSSItemDerivative).filter(
            RSSItemDerivative.rss_item_id == rss_item_id
        ).all()


# Create instances of CRUD classes
user = CRUDUser(User)
rss_feed = CRUDRSSFeed(RSSFeed)
rss_subscription = CRUDRSSSubscription(RSSSubscription)
rss_fetch_record = CRUDRSSFetchRecord(RSSFetchRecord)
rss_item = CRUDRSSItem(RSSItemMetadata)
rss_item_derivative = CRUDRSSItemDerivative(RSSItemDerivative)
topic = CRUDTopic(Topic)
article_topic = CRUDArticleTopic(ArticleTopic)
event = CRUDEvent(Event)
article_event = CRUDArticleEvent(ArticleEvent)
user_summary = CRUDUserSummary(UserSummary)
system_setting = CRUDSystemSetting(SystemSetting)
