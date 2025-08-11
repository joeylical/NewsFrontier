"""
NewsFrontier Shared Library

This package contains shared database models and utilities
for the NewsFrontier news aggregation platform.
"""

from .models import *
from .database import get_database_url, create_engine, get_session, Base
from .schemas import *
from . import crud
from .urls import (
    config as url_config,
    get_backend_url,
    get_frontend_url, 
    get_database_url as get_url_database_url,
    get_api_endpoint,
    get_cors_origins,
    get_user_agent,
    active_config
)
from .llm_client import (
    LLMClient,
    get_llm_client,
    generate_topic_embedding,
    generate_content_embedding,
    create_summary
)

__version__ = "0.1.0"