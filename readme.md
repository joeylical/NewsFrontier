# Introduction

This is the root directory of NewsFrontier.

NewsFrontier is an intelligent news aggregation and analysis platform that fetches, analyzes, classifies, and summarizes news articles for personal users. The system provides personalized news insights through advanced clustering and machine learning techniques.

# How It Works

## Overview
NewsFrontier operates through a multi-stage pipeline that transforms raw RSS feeds into organized, summarized news clusters:

1. **Data Collection**: Users can add interested topics and RSS sources through the web interface
2. **RSS Fetching**: The system periodically fetches RSS sources and stores news articles in a PostgreSQL database with full metadata (URL, title, content, timestamps, etc.)
3. **Content Summarization**: A dedicated worker process generates concise summaries of each article using LLM technology
4. **Vector Embeddings**: An embedding service converts article summaries into high-dimensional vectors using modern embedding APIs
5. **Clustering Analysis**: Advanced clustering algorithms group similar articles together to identify trending topics and related stories
6. **API Layer**: A FastAPI-based backend provides RESTful interfaces for the frontend application

The backend application written in Python using FastAPI provides the following interfaces:
### API Endpoints

#### Authentication
* **`POST /api/login`** - User authentication
  ```json
  Request: {"username": "user123", "password": "password123"}
  Response: {"token": "jwt_token", "user_id": 1, "expires": "2024-01-01T12:00:00Z"}
  ```

* **`POST /api/logout`** - User session termination
  ```json  
  Request: {} (requires Authorization header)
  Response: {"message": "Logged out successfully"}
  ```

* **`POST /api/register`** - New user registration
  ```json
  Request: {"username": "newuser", "password": "securepass", "email": "user@example.com"}
  Response: {"user_id": 2, "message": "Registration successful"}
  ```

#### Dashboard & Analytics
* **`GET /api/today`** - Daily news summary and analytics
  ```json
  Response: {
    "date": "2024-01-01",
    "total_articles": 247,
    "clusters_count": 15,
    "top_topics": ["Technology", "Politics", "Sports"],
    "summary": "AI-generated overview of today's major news trends...",
    "trending_keywords": ["AI", "election", "climate"]
  }
  ```

#### Topic Management  
* **`GET /api/topics`** - List all user topics
  ```json
  Response: {
    "topics": [
      {"id": 1, "name": "Technology", "keywords": ["AI", "tech", "software"], "active": true},
      {"id": 2, "name": "Politics", "keywords": ["election", "government"], "active": false}
    ]
  }
  ```

* **`POST /api/topics`** - Create new topic
  ```json
  Request: {"name": "Climate Change", "keywords": ["climate", "environment", "green energy"]}
  Response: {"id": 3, "message": "Topic created successfully"}
  ```

#### Content Discovery
* **`GET /api/topic/{id}`** - Get news clusters for specific topic
  ```json
  Response: {
    "topic": {"id": 1, "name": "Technology"},
    "clusters": [
      {"id": 101, "title": "AI Breakthrough", "article_count": 5, "summary": "Major AI developments..."},
      {"id": 102, "title": "Tech Earnings", "article_count": 8, "summary": "Quarterly results..."}
    ]
  }
  ```

* **`GET /api/cluster/{id}`** - Detailed cluster with articles
  ```json
  Response: {
    "cluster": {
      "id": 101,
      "title": "AI Breakthrough",
      "summary": "Comprehensive cluster summary...",
      "articles": [
        {"id": 1001, "title": "OpenAI Announces...", "source": "TechNews", "timestamp": "2024-01-01T10:00:00Z"},
        {"id": 1002, "title": "Google Responds...", "source": "Reuters", "timestamp": "2024-01-01T11:00:00Z"}
      ]
    }
  }
  ```

# Project Structure

## Directories Overview

### Core Applications
* **`backend/`** - FastAPI-based REST API server
  * Handles user authentication and session management
  * Provides data access layer for news, topics, and clusters
  * Implements business logic for content aggregation and analysis
  * **Administrative Interface**: Dedicated admin authentication endpoints with elevated privileges
  * **System Configuration**: Runtime settings management for AI services and processing parameters
  
* **`frontend/`** - Next.js web application with TypeScript
  * React-based user interface with DaisyUI components
  * Responsive design for desktop and mobile devices
  * Real-time updates and interactive data visualizations
  * **Administrative Dashboard**: System monitoring, user management, and service health status
  * **AI Service Configuration**: Dynamic LLM endpoint management, model selection, and API key settings
  * **RSS Management Interface**: Feed source configuration, fetch scheduling, and processing status monitoring
  * **System Settings Panel**: Configurable processing parameters, retry policies, and performance tuning

### Data Pipeline Components  
* **`scraper/`** - RSS feed collection service
  * Python-based RSS parser with concurrent fetching
  * Configurable scheduling via cron jobs
  * Robust error handling and retry mechanisms
  * PostgreSQL integration for data persistence
  
* **`postprocess/`** - AI-powered content analysis
  * LLM integration for intelligent article summarization
  * Vector embedding generation using modern embedding APIs
  * Batch processing capabilities for high-throughput analysis
  * Quality assurance and content filtering

### Infrastructure & Utilities
* **`lib/`** - Shared Python libraries and utilities
  * Database models and ORM definitions
  * Common data structures and type definitions
  * Shared business logic and helper functions
  
* **`scripts/`** - Development and deployment utilities
  * `init.sql` - PostgreSQL database schema initialization
  * `dev.sh` - Development environment startup script
  * Database migration and maintenance scripts
  
* **`data/`** - PostgreSQL data directory (Docker volume)
  * Persistent storage for the database container
  * Excluded from version control for security and performance


# System Architecture

## Architecture Overview

NewsFrontier follows a microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL    │
│                 │    │                 │    │   + pgvector)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │              ┌────────┴────────┐              │
         │              │                 │              │
         │       ┌─────────────┐   ┌─────────────┐       │
         │       │   Scraper   │   │ PostProcess │       │
         │       │  (RSS Feed) │   │ (AI/ML)     │       │
         └───────┤             │   │             ├───────┘
                 └─────────────┘   └─────────────┘
```

## Data Flow

1. **RSS Ingestion**: The scraper service periodically fetches RSS feeds and stores raw articles
2. **Content Processing**: PostProcess service analyzes articles, generates summaries, and creates embeddings  
3. **Clustering**: Vector similarities are computed to group related articles
4. **API Layer**: Backend exposes processed data through RESTful endpoints
5. **User Interface**: Frontend consumes APIs to present organized news clusters

## Workspace Configuration

The project uses a **uv workspace** structure in the root directory with Git version control.

### Infrastructure Files
* **`docker-compose.yml`** - Container orchestration
  * **Database**: `pgvector/pgvector:pg17` container with vector extension support
    * Initialized with `scripts/init.sql` for schema setup
    * Persistent volume mapping to `./data/` directory
  * **Backend**: Python FastAPI application container
  * **Frontend**: Node.js Next.js application container
  * **Network**: Internal Docker network for service communication

* **`shell.nix`** - Nix development environment definition
  * Provides consistent development tools across different machines
  * Includes Python, Node.js, PostgreSQL client, and other dependencies
  
* **`.vimrc.lua`** - Project-specific Neovim configuration
  * Customized settings for Python and TypeScript development
  * Integrated debugging and testing workflows

# Technical Specifications

## Technology Stack

### Backend Service
* **Language**: Python 3.11+
* **Framework**: FastAPI for high-performance async API development
* **Database**: 
  * **PostgreSQL 17** with pgvector extension for vector operations
  * **psycopg2** for database connectivity
  * **SQLAlchemy ORM** for database modeling (defined in `../lib`)
* **Project Management**: UV workspace member (no VCS within subproject)
* **Code Quality**: Comprehensive type annotations throughout codebase
* **Testing**: Pytest with comprehensive test coverage

#### Key Modules
* **Authentication**: JWT-based user session management
* **API Routes**: RESTful endpoint implementations
* **Data Models**: SQLAlchemy models for news, topics, clusters
* **Business Logic**: Article processing and clustering algorithms

### Frontend Application  
* **Language**: TypeScript for type-safe development
* **Package Management**: pnpm for faster and more modern development
* **Framework**: Next.js 14+ with App Router
* **UI Library**: DaisyUI components with Tailwind CSS
* **State Management**: React Context API / Zustand
* **Testing**: Jest and React Testing Library

#### Key Pages & Components
* **Dashboard**: Personalized news overview
  * Daily news summary and trending topic insights
  * Quick access to most relevant news clusters

* **News Explorer**: Hierarchical news browsing with intelligent clustering
  * **Topics List**: User-defined interest categories with activity indicators
  * **Topic Clusters**: AI-generated article groups within selected topics
    * Visual cluster representation with article count and relevance scores
    * Smart cluster naming based on content analysis
  * **News List**: Detailed article listings within selected clusters
    * Article titles with source attribution and publication timestamps
    * Summary previews and relevance indicators
  * **Article Reader**: Full-content article viewer with enhanced features
    * Original article content with reading time estimates
    * AI-generated summary and key insights extraction
    * Related articles and cross-cluster recommendations

* **Settings & Administration**: Comprehensive system configuration
  * **Topics Management**: Dynamic topic creation and keyword management
    * Custom topic definitions with vector-based matching
    * Topic performance analytics and optimization suggestions
  * **RSS Source Management**: Feed configuration and monitoring dashboard
  * **User Preferences**: Personalization options and notification settings

#### Frontend Project Architecture

```
src/
├── components/                 # Reusable UI Components
│   ├── Modal.tsx              # Modal dialog component for forms and confirmations
│   ├── ListItem.tsx           # Generic list item component for topics and news
│   ├── ListView.tsx           # Container component for paginated lists
│   ├── Timeline.tsx           # Interactive timeline component for cluster visualization
│   ├── LoadingSpinner.tsx     # Loading state indicator
│   └── ErrorBoundary.tsx      # Error handling wrapper component
│
├── lib/                       # Utilities & Configuration
│   ├── auth-context.tsx       # React Context for authentication state management
│   ├── types.ts              # TypeScript type definitions for API responses
│   ├── api-client.ts         # HTTP client with authentication handling
│   ├── utils.ts              # Common utility functions
│   └── constants.ts          # Application constants and configuration
│
├── app/                      # Next.js App Router Pages
│   ├── (auth)/              # Authentication Route Group
│   │   ├── login/
│   │   │   └── page.tsx     # User login form with validation
│   │   ├── register/
│   │   │   └── page.tsx     # User registration with email verification
│   │   └── layout.tsx       # Auth-specific layout (login/register)
│   │
│   ├── dashboard/           # Main Application Routes
│   │   ├── page.tsx        # Display today summary.
│   │   ├── topics/
│   │   │   ├── page.tsx    # Topics list with cluster timeline
│   │   │   └── [id]/
│   │   │       └── page.tsx # Topic detail with clusters view
│   │   ├── clusters/
│   │   │   └── [id]/
│   │   │       └── page.tsx # News list within cluster
│   │   ├── article/
│   │   │   └── [id]/
│   │   │       └── page.tsx # Article reader with AI insights
│   │   └── settings/
│   │       └── page.tsx    # User preferences and topic management
│   │
│   ├── admin/              # Administrative Interface
│   │   ├── page.tsx       # Admin dashboard with system metrics
│   │   ├── users/
│   │   │   └── page.tsx   # User management interface
│   │   ├── rss-feeds/
│   │   │   └── page.tsx   # RSS source configuration
│   │   ├── ai-config/
│   │   │   └── page.tsx   # LLM and embedding service settings
│   │   └── system/
│   │       └── page.tsx   # System-wide configuration
│   │
│   ├── globals.css       # Global styles with DaisyUI
│   ├── layout.tsx        # Root layout with navigation
│   └── page.tsx          # Landing/home page
│
└── middleware.ts         # Next.js middleware for route protection
```

**Key Architecture Decisions:**
- **App Router**: Leverages Next.js 13+ file-based routing with layouts
- **Route Groups**: Organizes authentication and admin routes separately  
- **Component Reusability**: Generic components (ListView, ListItem) support multiple data types
- **Type Safety**: Centralized TypeScript definitions ensure API contract consistency
- **Authentication Flow**: Context-based auth state with middleware protection
- **Progressive Enhancement**: Server-side rendering with client-side interactivity


### Data Processing Services

#### RSS Scraper Service
* **Language**: Python 3.11+
* **Architecture**: UV workspace member
* **Key Features**:
  * Async RSS parsing with concurrent fetching
  * Configurable scheduling and retry mechanisms
  * Data validation and sanitization
  * PostgreSQL persistence layer

#### PostProcess AI Service  
* **Language**: Python 3.11+
* **Architecture**: UV workspace member
* **AI/ML Stack**:
  * **LLM Integration**: OpenAI/Anthropic APIs for summarization
  * **Embeddings**: OpenAI text-embedding-ada-002 or similar
  * **Vector Storage**: pgvector for similarity search
  * **Clustering**: Scikit-learn DBSCAN/K-means algorithms

#### Shared Library (`lib`)
* **Language**: Python 3.11+
* **Architecture**: UV workspace member  
* **Contents**:
  * Database schema definitions
  * Shared data models and types
  * Common utilities and helper functions
  * Configuration management

# Development & Deployment

## Quick Start Scripts

### `scripts/dev.sh` - Development Environment Setup
Automated development environment launcher that orchestrates all services:

```bash
#!/bin/bash
# 1. Start PostgreSQL with pgvector extension
docker run -d --rm --name newsfrontier-db \
  -e POSTGRES_DB=newsfrontier_db \
  -e POSTGRES_USER=newsfrontier \
  -e POSTGRES_PASSWORD=dev_password \
  -p 5432:5432 \
  -v "$(pwd)/data:/var/lib/postgresql/data" \
  -v "$(pwd)/scripts/init.sql:/docker-entrypoint-initdb.d/init.sql" \
  pgvector/pgvector:pg17

# 2. Initialize database schema
psql -h localhost -U newsfrontier -d newsfrontier_db -f scripts/init.sql

# 3. Start all services concurrently
# Backend API server (FastAPI with hot reload)
cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

# Frontend development server (Next.js with hot reload)  
cd frontend && npm run dev &

# RSS Scraper worker (background process)
cd scraper && uv run python main.py --daemon &

# AI PostProcess worker (background process)
cd postprocess && uv run python main.py --daemon &

# TODO: trap Ctrl+C to gracefully kill all processes above

wait # Keep script running until all processes complete
```

### `scripts/init.sql` - Database Schema Initialization
Complete PostgreSQL schema setup with pgvector extension:
* User authentication tables with secure password hashing
* News articles table with full-text search indices
* Topics and RSS sources configuration
* Vector embeddings storage with optimized indexing
* Clustering results and relationships

## Production Deployment

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  database:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: newsfrontier_db
      POSTGRES_USER: newsfrontier
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U newsfrontier -d newsfrontier_db"]
      interval: 10s
      timeout: 5s
      retries: 5
      
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://newsfrontier:${DB_PASSWORD}@database:5432/newsfrontier_db
      JWT_SECRET: ${JWT_SECRET}
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_API_URL: ${LLM_API_URL}
      EMBEDDING_API_URL: ${EMBEDDING_API_URL}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    depends_on:
      database:
        condition: service_healthy
    ports:
      - "8000:8000"
    restart: unless-stopped
      
  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    depends_on:
      - backend
    ports:
      - "3000:3000"
    restart: unless-stopped

  scraper:
    build: ./scraper
    environment:
      DATABASE_URL: postgresql://newsfrontier:${DB_PASSWORD}@database:5432/newsfrontier_db
      DEFAULT_RSS_INTERVAL: ${DEFAULT_RSS_INTERVAL:-60}
      SCRAPER_CONCURRENT_FEEDS: ${SCRAPER_CONCURRENT_FEEDS:-5}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    depends_on:
      database:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs/scraper:/app/logs

  postprocess:
    build: ./postprocess  
    environment:
      DATABASE_URL: postgresql://newsfrontier:${DB_PASSWORD}@database:5432/newsfrontier_db
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_API_URL: ${LLM_API_URL}
      LLM_MODEL_SUMMARY: ${LLM_MODEL_SUMMARY:-gpt-3.5-turbo}
      EMBEDDING_API_URL: ${EMBEDDING_API_URL}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL:-text-embedding-ada-002}
      POSTPROCESS_BATCH_SIZE: ${POSTPROCESS_BATCH_SIZE:-10}
      MAX_PROCESSING_ATTEMPTS: ${MAX_PROCESSING_ATTEMPTS:-3}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    depends_on:
      database:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs/postprocess:/app/logs

networks:
  default:
    name: newsfrontier-network

volumes:
  postgres_data:
    driver: local
```

## Database Design

### Core Design Principles
* **Data Reliability Separation**: Raw RSS data and AI-processed data are stored separately to maintain data integrity and enable reprocessing
* **Error Recovery Support**: All processing tables include status tracking for reliable restart and recovery
* **Scalable Architecture**: Vector embeddings and clustering designed for high-volume news processing

### Tables

#### `users`
* `id` - SERIAL PRIMARY KEY
* `username` - VARCHAR(50) UNIQUE NOT NULL
* `password_hash` - VARCHAR(255) NOT NULL (salted bcrypt hash)
* `email` - VARCHAR(255) UNIQUE
* `is_admin` - BOOLEAN DEFAULT FALSE
* `daily_summary_prompt` - TEXT
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

#### `rss_feeds` (RSS Feed Sources)
* `id` - SERIAL PRIMARY KEY
* `uuid` - UUID UNIQUE NOT NULL DEFAULT gen_random_uuid()
* `url` - TEXT NOT NULL
* `title` - VARCHAR(255)
* `description` - TEXT
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()
* `last_fetch_at` - TIMESTAMP
* `last_fetch_status` - VARCHAR(50) DEFAULT 'pending'
* `fetch_interval_minutes` - INTEGER DEFAULT 60

Note: `uuid` serves as stable identifier when URLs change

#### `rss_subscriptions` (User RSS Subscriptions)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `rss_uuid` - UUID REFERENCES rss_feeds(uuid) ON DELETE CASCADE
* `alias` - VARCHAR(255) (user-defined feed name)
* `is_active` - BOOLEAN DEFAULT TRUE
* `created_at` - TIMESTAMP DEFAULT NOW()
* PRIMARY KEY (user_id, rss_uuid)

#### `rss_fetch_records` (Raw RSS Content - Immutable)
* `id` - SERIAL PRIMARY KEY
* `rss_feed_id` - INTEGER REFERENCES rss_feeds(id) ON DELETE CASCADE
* `raw_content` - TEXT NOT NULL (original RSS XML/JSON)
* `content_hash` - VARCHAR(64) NOT NULL (SHA256 for deduplication)
* `fetch_timestamp` - TIMESTAMP DEFAULT NOW()
* `http_status` - INTEGER
* `content_encoding` - VARCHAR(50)

#### `rss_items_metadata` (AI-Extracted Article Data)
* `id` - SERIAL PRIMARY KEY
* `rss_fetch_record_id` - INTEGER REFERENCES rss_fetch_records(id) ON DELETE CASCADE
* `guid` - TEXT (RSS item GUID)
* `title` - TEXT NOT NULL
* `content` - TEXT
* `url` - TEXT
* `published_at` - TIMESTAMP
* `author` - VARCHAR(255)
* `category` - VARCHAR(255)
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `processing_started_at` - TIMESTAMP
* `processing_completed_at` - TIMESTAMP
* `processing_attempts` - INTEGER DEFAULT 0
* `last_error_message` - TEXT
* `created_at` - TIMESTAMP DEFAULT NOW()

#### `rss_item_derivatives` (AI-Generated Content)
* `id` - SERIAL PRIMARY KEY
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `summary` - TEXT
* `title_embedding` - VECTOR(1536) (pgvector for similarity search)
* `summary_embedding` - VECTOR(1536)
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `summary_generated_at` - TIMESTAMP
* `embeddings_generated_at` - TIMESTAMP
* `processing_attempts` - INTEGER DEFAULT 0
* `last_error_message` - TEXT
* `llm_model_version` - VARCHAR(100)
* `embedding_model_version` - VARCHAR(100)
* `created_at` - TIMESTAMP DEFAULT NOW()

#### `topics`
* `id` - SERIAL PRIMARY KEY
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `name` - VARCHAR(255) NOT NULL
* `keywords` - TEXT[] (PostgreSQL array of keywords)
* `topic_vector` - VECTOR(1536)
* `is_active` - BOOLEAN DEFAULT TRUE
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

#### `article_topics` (Many-to-Many: Articles ↔ Topics)
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `relevance_score` - FLOAT (0.0 to 1.0)
* `created_at` - TIMESTAMP DEFAULT NOW()
* PRIMARY KEY (rss_item_id, topic_id)

#### `clusters`
* `id` - SERIAL PRIMARY KEY
* `friendly_name` - VARCHAR(255)
* `description` - TEXT
* `centroid_vector` - VECTOR(1536)
* `cluster_radius` - FLOAT
* `article_count` - INTEGER DEFAULT 0
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

#### `article_clusters` (Many-to-Many: Articles ↔ Clusters)
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `cluster_id` - INTEGER REFERENCES clusters(id) ON DELETE CASCADE
* `distance_to_centroid` - FLOAT
* `created_at` - TIMESTAMP DEFAULT NOW()
* PRIMARY KEY (rss_item_id, cluster_id)

#### `user_topics` (Many-to-Many: Users ↔ Topics)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `priority` - INTEGER DEFAULT 1
* `created_at` - TIMESTAMP DEFAULT NOW()
* PRIMARY KEY (user_id, topic_id)

#### `user_summaries`
* `id` - SERIAL PRIMARY KEY
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `summary` - TEXT
* `date` - TIMESTAMP
* `created_at` - TIMESTAMP DEFAULT NOW()

#### `system_settings`
* `id` - SERIAL PRIMARY KEY
* `setting_key` - VARCHAR(100) UNIQUE NOT NULL
* `setting_value` - TEXT
* `description` - TEXT
* `updated_at` - TIMESTAMP DEFAULT NOW()
* `updated_by` - INTEGER REFERENCES users(id)

**Common System Settings:**
* `llm_api_url` - Primary LLM service endpoint
* `llm_api_key_hash` - Encrypted API key storage
* `embedding_api_url` - Vector embedding service endpoint  
* `transcript_api_url` - Speech-to-text service endpoint
* `tts_api_url` - Text-to-speech service endpoint
* `default_rss_fetch_interval` - Default RSS polling interval (minutes)
* `max_processing_attempts` - Maximum retry attempts for failed processing 


### Environment Variables

#### Required Configuration
**Database & Core Services:**
* `DATABASE_URL` - PostgreSQL connection string (postgresql://user:pass@host:port/dbname)
* `DB_PASSWORD` - PostgreSQL database password
* `REDIS_URL` - Redis connection string for caching and session storage (optional)

**Security & Authentication:**
* `JWT_SECRET` - Secret key for JWT token signing (use strong random string)
* `JWT_EXPIRE_HOURS` - JWT token expiration time in hours (default: 24)
* `PASSWORD_SALT_ROUNDS` - Bcrypt salt rounds for password hashing (default: 12)

**AI/ML Services:**
* `LLM_API_URL` - Primary LLM service endpoint (e.g., OpenAI, Anthropic, or local)
* `LLM_API_KEY` - API key for LLM services
* `LLM_MODEL_SUMMARY` - Model for article summarization (e.g., gpt-3.5-turbo)
* `LLM_MODEL_ANALYSIS` - Model for content analysis (e.g., gpt-4)
* `LLM_MODEL_CLUSTERING` - Model for clustering tasks (e.g., gpt-3.5-turbo)
* `EMBEDDING_API_URL` - Vector embedding service endpoint
* `EMBEDDING_MODEL` - Embedding model name (e.g., text-embedding-ada-002)
* `EMBEDDING_DIMENSION` - Vector dimension size (default: 1536)

**Optional AI Services:**
* `TRANSCRIPT_API_URL` - Speech-to-text service endpoint
* `TTS_API_URL` - Text-to-speech service endpoint
* `TTS_API_KEY` - API key for audio services

**Application Settings:**
* `LOG_LEVEL` - Application logging level (DEBUG, INFO, WARNING, ERROR)
* `MAX_PROCESSING_ATTEMPTS` - Maximum retry attempts for failed AI processing (default: 3)
* `DEFAULT_RSS_INTERVAL` - Default RSS fetch interval in minutes (default: 60)
* `SCRAPER_CONCURRENT_FEEDS` - Number of concurrent RSS feeds to process (default: 5)
* `POSTPROCESS_BATCH_SIZE` - Batch size for AI processing (default: 10)

**Development Settings:**
* `ENVIRONMENT` - Runtime environment (development, staging, production)
* `DEBUG` - Enable debug mode (true/false)
* `API_RATE_LIMIT` - API rate limiting (requests per minute)
* `CORS_ORIGINS` - Allowed CORS origins for frontend access

