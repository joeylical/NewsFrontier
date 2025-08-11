"""
NewsFrontier URL Configuration Module

This module centralizes all URL configurations used across the backend, scraper,
and postprocess services. It provides a single source of truth for service URLs,
API endpoints, and external URLs.
"""

import os
from typing import Dict, Optional


class URLConfig:
    """Central URL configuration class"""
    
    def __init__(self):
        # Environment-based configuration
        self.environment = os.getenv("ENVIRONMENT", "development")
        
    # Service URLs
    @property
    def backend_url(self) -> str:
        """Backend API base URL"""
        return os.getenv("BACKEND_URL", "http://localhost:8000")
    
    @property
    def frontend_url(self) -> str:
        """Frontend application URL"""
        return os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    @property
    def database_url(self) -> str:
        """Database connection URL"""
        return os.getenv(
            "DATABASE_URL", 
            "postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db"
        )
    
    # Server binding configuration
    @property
    def server_host(self) -> str:
        """Server host binding"""
        return os.getenv("SERVER_HOST", "0.0.0.0")
    
    @property
    def server_port(self) -> int:
        """Server port"""
        return int(os.getenv("SERVER_PORT", "8000"))
    
    @property
    def frontend_port(self) -> int:
        """Frontend port"""
        return int(os.getenv("FRONTEND_PORT", "3000"))
    
    @property
    def database_port(self) -> int:
        """Database port"""
        return int(os.getenv("DATABASE_PORT", "5432"))
    
    # API Endpoints
    @property
    def api_endpoints(self) -> Dict[str, str]:
        """Internal API endpoints for service-to-service communication"""
        base = self.backend_url
        return {
            # System endpoints
            "health": f"{base}/api/system/health",
            "stats": f"{base}/api/system/stats",
            
            # Feed management endpoints (internal)
            "feeds_pending": f"{base}/api/internal/feeds/pending",
            "feed_status": f"{base}/api/internal/feeds/{{feed_id}}/status",
            
            # Article management endpoints (internal)
            "articles_create": f"{base}/api/internal/articles",
            "articles_pending_processing": f"{base}/api/internal/articles/pending-processing",
            "article_process": f"{base}/api/internal/articles/{{article_id}}/process",
            
            # User-facing API endpoints
            "api_docs": f"{base}/docs",
            "api_redoc": f"{base}/redoc",
        }
    
    # CORS Configuration
    @property
    def cors_origins(self) -> list:
        """Allowed CORS origins"""
        origins = os.getenv("CORS_ORIGINS", self.frontend_url)
        return origins.split(",") if "," in origins else [origins]
    
    # External URLs and Constants
    @property
    def user_agent(self) -> str:
        """User agent string for HTTP requests"""
        domain = os.getenv("APP_DOMAIN", "newsfrontier.example.com")
        return f"NewsFrontier RSS Reader 1.0 (https://{domain})"
    
    @property
    def example_rss_url(self) -> str:
        """Example RSS URL for testing/placeholders"""
        return "https://feeds.bbci.co.uk/news/rss.xml"
    
    @property
    def rss_placeholder(self) -> str:
        """Placeholder for RSS URL inputs"""
        return "https://example.com/rss.xml"
    
    # Development and Testing URLs
    @property
    def test_urls(self) -> Dict[str, str]:
        """URLs used in testing"""
        return {
            "test_api_base": self.backend_url,
            "test_rss_feed": self.example_rss_url,
            "test_article": "https://example.com/test-1",
        }


# Global configuration instance
config = URLConfig()


# Convenience functions for backward compatibility
def get_backend_url() -> str:
    """Get backend URL"""
    return config.backend_url


def get_frontend_url() -> str:
    """Get frontend URL"""
    return config.frontend_url


def get_database_url() -> str:
    """Get database URL"""
    return config.database_url


def get_api_endpoint(endpoint_name: str, **kwargs) -> str:
    """
    Get API endpoint URL with optional parameters
    
    Args:
        endpoint_name: Name of the endpoint
        **kwargs: Parameters to format into the URL
    
    Returns:
        Formatted endpoint URL
    
    Example:
        get_api_endpoint("feed_status", feed_id="123")
        # Returns: "http://localhost:8000/api/internal/feeds/123/status"
    """
    endpoint_url = config.api_endpoints.get(endpoint_name)
    if not endpoint_url:
        raise ValueError(f"Unknown endpoint: {endpoint_name}")
    
    if kwargs:
        return endpoint_url.format(**kwargs)
    return endpoint_url


def get_cors_origins() -> list:
    """Get CORS allowed origins"""
    return config.cors_origins


def get_user_agent() -> str:
    """Get user agent string"""
    return config.user_agent


# Environment-specific configurations
class DevelopmentConfig(URLConfig):
    """Development environment configuration"""
    pass


class ProductionConfig(URLConfig):
    """Production environment configuration"""
    
    @property
    def server_host(self) -> str:
        return os.getenv("SERVER_HOST", "127.0.0.1")


class TestingConfig(URLConfig):
    """Testing environment configuration"""
    
    @property
    def database_url(self) -> str:
        return os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://newsfrontier:test_password@localhost:5432/newsfrontier_test_db"
        )


# Configuration factory
def get_config() -> URLConfig:
    """Get configuration instance based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()


# Export the active configuration
active_config = get_config()