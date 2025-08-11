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
5. **Clustering Analysis**: The system attempts to create clusters and categorize articles into clusters
6. **API Layer**: A FastAPI-based backend provides RESTful interfaces for the frontend application

## AI Pipeline

The AI processing pipeline transforms raw RSS articles into structured cluster-driven news insights through intelligent content analysis and contextual awareness:

### 1. Topic Embedding Generation
The system creates vector embeddings for user-defined topics, encoding their semantic meaning into high-dimensional vectors using Google's gemini-embedding-001 model. These 768-dimensional topic embeddings serve as reference points for content classification and relevance scoring throughout the processing pipeline.

### 2. Article Processing and Summarization
Each fetched article undergoes comprehensive two-stage processing:
* **Content Summarization**: Articles are processed through Google Gemini LLM APIs (gemini-2.0-flash-lite) to generate concise, structured summaries that capture key points, context, and maintain anchor link references
* **Vector Generation**: Article summaries are converted into 768-dimensional vector embeddings using gemini-embedding-001 for semantic similarity calculations and clustering operations

### 3. Intelligent Cluster Detection and Classification
When processing each article, the system employs a sophisticated multi-stage clustering approach:

#### Topic Relevance Assessment
* **Initial Filtering**: The system first determines if the article is semantically similar to any user-defined topics using vector similarity calculations
* **Relevance Scoring**: Articles that meet the similarity threshold are scored for relevance to specific topics

#### Cluster Assignment Decision
For each relevant topic, the system processes clusters sequentially:
* **Existing Cluster Matching**: When similar clusters exist within the topic, the article is classified and assigned to the most semantically similar cluster based on embedding distance
* **Similarity Threshold**: Uses configurable similarity thresholds (default: 0.62 for topic, 0.7 for cluster) to ensure high-quality groupings

#### Intelligent New Cluster Creation
When articles don't match existing clusters:
* **LLM-Based Analysis**: The system uses Gemini-2.5-Pro to analyze the article content and determine if it represents a genuinely new cluster or development
* **Context-Aware Creation**: The LLM considers existing cluster titles, descriptions, and the topic hierarchy to make intelligent clustering decisions
* **Dynamic Association**: New clusters are created with AI-generated titles and descriptions, and the article is associated with the new cluster with appropriate relevance scoring

### 4. Cluster Evolution and Relationship Management
* **Cluster Updates**: Existing clusters are dynamically updated as new related articles are added
* **Cross-Cluster Analysis**: The system identifies relationships between different clusters within topics
* **Temporal Tracking**: Cluster evolution is tracked over time to maintain cluster coherence and relevance

### 5. Daily Summary Creation
A personalized daily news summary is generated using contextual information:
* **System-wide Prompts**: Structured prompts defining summary format, tone, and markdown linking conventions
* **User Preferences**: Individual topic interests, subscription priorities, and personalized summary prompts
* **Historical Context**: Previous daily summaries and user interaction patterns
* **Cluster Highlights**: Curated highlights from today's top clusters and developments with internal dashboard links

### 6. Daily Cover Image Generation
Visual content is created through AI-powered image generation using Imagen-3.0-Generate-002:
* **Emotional Tone**: Core sentiments and mood extracted from the daily summary content
* **Visual Scenario**: Concrete settings, situations, and contextual elements from news clusters
* **Key Subjects**: Primary actors, objects, and entities identified in the news without text overlays
* **Narrative Element**: A compelling visual story that encapsulates the day's most significant developments

### AI Models and Applications

The AI pipeline leverages multiple specialized models from Google's AI suite, each optimized for specific tasks:

| Model | Type | Application |
|-------|------|-------------|
| **gemini-2.0-flash-lite** | Instruction-following | Article summary<br/>Image generation prompt generating |
| **gemini-2.5-pro** | Instruction-following | Creating new cluster<br/>Daily summary |
| **imagen-3.0-generate-002** | Image generation | Daily summary cover image |
| **gemini-embedding-001** | Embedding | Article embedding<br/>Topic embedding<br/>Cluster embedding |

This multi-model approach ensures optimal performance for each specific task while maintaining consistency in the overall AI processing pipeline.

# Project Structure

## Directories Overview

### Core Applications
* **`frontend/`** - Next.js web application with TypeScript
  * **Technology Stack**: Next.js 15+ with App Router, TypeScript, TailwindCSS + DaisyUI
  * **Architecture**: React components with server-side rendering and client-side interactivity
  * **Authentication**: JWT-based authentication with middleware protection
  * **Key Features**:
    - Responsive design for desktop and mobile devices
    - Interactive dashboard with daily news summaries
    - Hierarchical news browsing (Topics → Clusters → Articles)
    - Real-time updates and data visualizations
    - Administrative interface for system management
    - RSS feed management and configuration
    - User settings and preferences management
  * **Package Manager**: pnpm for efficient dependency management

* **`backend/`** - FastAPI-based REST API server
  * **Technology Stack**: Python 3.11+, FastAPI, SQLAlchemy ORM, PostgreSQL, JWT authentication
  * **Architecture**: Async-first microservice with dependency injection and middleware pipeline
  * **Core Components**:
    - FastAPI application with automatic OpenAPI documentation generation
    - JWT-based authentication with bcrypt password hashing
    - CORS middleware for cross-origin frontend integration
    - Request/response logging middleware with performance tracking
    - Global exception handling with detailed error logging
    - Integration with shared newsfrontier-lib for database operations
  * **Key Features**:
    - Complete user authentication system (login, register, logout)
    - Daily personalized news summaries with date navigation
    - Topic management with AI-generated vector embeddings
    - Article and cluster content discovery APIs
    - RSS feed subscription management
    - HTML text processing with paragraph anchor insertion
    - Internal service APIs for scraper and postprocess communication
    - Administrative endpoints for system configuration

### Data Pipeline Components  
* **`scraper/`** - RSS feed collection service
  * **Technology Stack**: Python 3.11+, requests, feedparser, SQLAlchemy
  * **Architecture**: Concurrent RSS fetching with configurable scheduling
  * **Key Features**:
    - Async RSS parsing with concurrent fetching capabilities
    - Content deduplication using SHA256 hashing
    - Robust error handling and retry mechanisms
    - Status tracking for feed fetch operations
    - Backend API integration for data persistence
    - Configurable fetch intervals per feed
    - Daemon and one-shot execution modes
  
* **`postprocess/`** - AI-powered content analysis and processing service
  * **Technology Stack**: Python 3.11+, Google AI (Gemini), scikit-learn, pgvector, FastAPI
  * **Architecture**: AI processing pipeline with intelligent clustering and content analysis
  * **Core Responsibilities**:
    - Generating 768-dimensional vector embeddings for semantic search
    - Creating article summaries and derivatives using AI
    - Clustering related articles based on content similarity
  * **AI Integration Features**:
    - Google Gemini models: Gemini-2.0-Flash-Lite for fast summarization
    - Advanced analysis: Gemini-2.5-Pro for complex clustering and daily summaries
    - Vector embeddings: gemini-embedding-001 for high-quality 768-dimensional vectors
    - Clustering: Context-aware clustering decisions with LLM-based logic
    - Daily summaries: Personalized news summaries with structured markdown output
    - Cover image generation: AI-generated image descriptions using Imagen models
  * **Operational Features**:
    - Daemon and one-shot execution modes
    - Comprehensive AI prompt testing framework
    - FastAPI internal server for inter-service communication
    - S3 integration for cover image storage

### Infrastructure & Utilities
* **`lib/`** - Shared Python libraries and utilities
  * **Technology Stack**: Python 3.11+, SQLAlchemy, pgvector, Pydantic
  * **Architecture**: Shared workspace library for common functionality
  * **Key Components**:
    - SQLAlchemy ORM models for all database tables
    - Pydantic schemas for API request/response validation
    - CRUD operations with type-safe database access
    - LLM client integration (Google Generative AI)
    - S3 client for cloud storage operations
    - Vector embedding utilities with pgvector support
  
* **`scripts/`** - Development and deployment utilities
  * **Key Scripts**:
    - `init.sql` - PostgreSQL database schema with pgvector extension
    - `dev.sh` / `stop-dev.sh` - Development environment management
    - `generate-init-sql.py` - Dynamic schema generation with configurable vector dimensions
    - `create-test-users.py` - Test data creation utilities
    - Database dump and restore utilities for debugging
    - System prompt templates for AI services
  
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
* **Framework**: FastAPI for high-performance async API development with automatic OpenAPI documentation
* **Architecture**: Single-file application with modular middleware pipeline
* **Database Integration**: 
  * **PostgreSQL 17** with pgvector extension for vector operations
  * **SQLAlchemy ORM** via shared newsfrontier-lib package
  * **Database session management** with dependency injection
* **Security**: 
  * **JWT authentication** with configurable expiration
  * **bcrypt password hashing** with salt rounds
  * **CORS middleware** for cross-origin requests
* **Project Structure**: UV workspace member with minimal file footprint

#### Key Modules
* **`main.py`** - FastAPI application entry point with complete API implementation
  * Authentication endpoints (login, register, logout, user management)
  * Daily summary APIs with date navigation and calendar integration
  * Topic management with AI vector embedding generation
  * Content discovery APIs (topics, clusters, articles)
  * RSS feed subscription management
  * Internal service APIs for scraper and postprocess communication
  * Administrative endpoints for system configuration
  * Comprehensive middleware pipeline (CORS, logging, exception handling)

* **`text_processor.py`** - HTML content processing utilities
  * Paragraph anchor ID generation (P-xxxxx format)
  * HTML anchor insertion for multi-paragraph content
  * Paragraph extraction with anchor metadata
  * Anchor ID validation and text processing analysis
  * Support for both SEN-xxxxx and P-xxxxx anchor formats

* **Shared Dependencies** (via newsfrontier-lib):
  * SQLAlchemy ORM models for all database entities
  * Pydantic schemas for request/response validation
  * CRUD operations with type-safe database access
  * AI client integration for topic embedding generation

#### APIs

The backend provides a comprehensive RESTful API built with FastAPI, featuring automatic OpenAPI documentation and async request handling.

**Base URL**: `/api`

##### Authentication Endpoints
* **`POST /api/login`** - User authentication and session creation
  * Request: `{username: string, password: string}`
  * Response: `{token: string, user_id: number, expires: string, user: UserResponse}`
  * Sets HTTP-only authentication cookie for session management
  
* **`POST /api/register`** - New user registration with validation
  * Request: `{username: string, password: string, email: string}`
  * Response: `{user_id: number, message: string}`
  * Validates unique username and email, creates secure password hash
  
* **`POST /api/logout`** - User session termination
  * Headers: `Authorization: Bearer <token>`
  * Response: `{message: string}`
  * Clears authentication cookie and invalidates session

##### User Management
* **`GET /api/user/me`** - Get current user profile information
  * Headers: `Authorization: Bearer <token>`
  * Response: `UserResponse` with user details, credits, and settings
  
* **`PUT /api/user/settings`** - Update user preferences and configuration
  * Headers: `Authorization: Bearer <token>`
  * Request: `{daily_summary_prompt?: string, ...}`
  * Response: `{message: string}`

##### Dashboard & Analytics
* **`GET /api/today`** - Daily personalized news summary and statistics
  * Headers: `Authorization: Bearer <token>`
  * Query: `?date=YYYY-MM-DD` (optional, defaults to today)
  * Response: `TodayResponse` with daily summary, article counts, top topics, and trending keywords
  
* **`GET /api/available-dates`** - Get available summary dates for calendar navigation
  * Headers: `Authorization: Bearer <token>`
  * Query: `?year=2024&month=1`
  * Response: `{month: string, available_dates: string[]}`

##### Topic Management
* **`GET /api/topics`** - List all user topics with activity metrics
  * Headers: `Authorization: Bearer <token>`
  * Response: `TopicResponse[]` with topic details and statistics
  
* **`POST /api/topics`** - Create new topic with automatic vector generation
  * Headers: `Authorization: Bearer <token>`
  * Request: `TopicCreate` with name and optional keywords
  * Response: `TopicResponse` with generated topic vector
  
* **`GET /api/topics/{id}`** - Get specific topic details and related clusters
  * Headers: `Authorization: Bearer <token>`
  * Response: `TopicResponse` with associated clusters and articles
  
* **`PUT /api/topics/{id}`** - Update topic configuration and settings
  * Headers: `Authorization: Bearer <token>`
  * Request: `TopicUpdate` with name, keywords, or active status
  * Response: `TopicResponse` with updated information
  
* **`DELETE /api/topics/{id}`** - Delete topic and associated data
  * Headers: `Authorization: Bearer <token>`
  * Response: `{message: string}`

##### Content Discovery
* **`GET /api/topic/{id}`** - Get AI-generated clusters for specific topic
  * Headers: `Authorization: Bearer <token>`
  * Query: `?limit=20&offset=0&since=YYYY-MM-DD`
  * Response: `{topic: TopicResponse, events: EventResponse[]}`
  
* **`GET /api/cluster/{id}`** - Detailed cluster information with associated articles
  * Headers: `Authorization: Bearer <token>`
  * Response: `EventDetailResponse` with cluster details and article list
  
* **`GET /api/article/{id}`** - Individual article with AI-generated insights
  * Headers: `Authorization: Bearer <token>`
  * Response: `RSSItemDetailResponse` with content, summary, and metadata
  
* **`GET /api/articles`** - List articles with filtering and pagination
  * Headers: `Authorization: Bearer <token>`
  * Query: `?limit=50&offset=0&status=completed&topic_id=1`
  * Response: `PaginatedResponse<RSSItemResponse[]>`

##### RSS Feed Management
* **`GET /api/feeds`** - List user's RSS subscriptions and feed status
  * Headers: `Authorization: Bearer <token>`
  * Response: `RSSSubscriptionResponse[]` with feed details and fetch status
  
* **`POST /api/feeds`** - Add new RSS feed subscription
  * Headers: `Authorization: Bearer <token>`
  * Request: `RSSSubscriptionCreate` with feed URL and optional alias
  * Response: `RSSSubscriptionResponse` with subscription details
  
* **`PUT /api/feeds/{uuid}`** - Update RSS subscription settings
  * Headers: `Authorization: Bearer <token>`
  * Request: `RSSSubscriptionUpdate` with alias or active status
  * Response: `RSSSubscriptionResponse` with updated settings
  
* **`DELETE /api/feeds/{uuid}`** - Remove RSS feed subscription
  * Headers: `Authorization: Bearer <token>`
  * Response: `{message: string}`

##### Internal Service APIs (Inter-service Communication)
* **`GET /api/internal/articles/pending`** - Get articles awaiting AI processing
  * Used by postprocess service to fetch unprocessed articles
  * Response: `RSSItemResponse[]` with processing status and metadata
  
* **`POST /api/internal/articles/{id}/process`** - Update article processing results
  * Used by postprocess service to store AI-generated content
  * Request: Processing results with summaries, embeddings, and analysis
  
* **`GET /api/internal/feeds/pending`** - Get RSS feeds due for fetching
  * Used by scraper service to determine which feeds to process
  * Response: `RSSFeedResponse[]` with fetch schedules and intervals
  
* **`POST /api/internal/feeds/{id}/status`** - Update feed fetch status
  * Used by scraper service to report fetch results and errors
  * Request: Fetch status, timing, and error information

##### System Administration (Admin Only)
* **`GET /api/admin/users`** - List all users with comprehensive statistics
  * Headers: `Authorization: Bearer <admin_token>`
  * Response: `UserResponse[]` with user details, activity metrics, and admin flags
  
* **`GET /api/admin/system-stats`** - System-wide performance and health metrics
  * Headers: `Authorization: Bearer <admin_token>`
  * Response: System statistics including processing queues, active feeds, and performance data
  
* **`POST /api/admin/system-settings`** - Update global system configuration
  * Headers: `Authorization: Bearer <admin_token>`
  * Request: `SystemSettingCreate` with configuration key-value pairs
  * Response: `SystemSettingResponse` with updated settings
  
* **`GET /api/admin/system-settings`** - Retrieve system configuration settings
  * Headers: `Authorization: Bearer <admin_token>`
  * Response: `SystemSettingResponse[]` with all system settings and metadata

##### Error Responses
All endpoints return standardized error responses:
```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": "Additional context (optional)"
}
```

**Common HTTP Status Codes:**
* `200` - Success
* `201` - Created
* `400` - Bad Request (validation errors)
* `401` - Unauthorized (invalid/missing token)
* `403` - Forbidden (insufficient permissions)
* `404` - Not Found
* `422` - Unprocessable Entity (invalid data format)
* `500` - Internal Server Error

#### Backend Project Architecture

The backend follows a streamlined FastAPI architecture with a minimal file footprint, optimized for maintainability and direct integration:

```
backend/
├── main.py                    # Complete FastAPI application with all endpoints
├── text_processor.py          # HTML text processing utilities
├── pyproject.toml            # Python dependencies and project metadata
├── server.log                # Application log file
└── uv.lock                   # Dependency lock file

# Shared Dependencies (../lib/newsfrontier-lib)
../lib/newsfrontier-lib
├── models.py                 # SQLAlchemy database models
├── database.py               # Database connection and session management  
├── crud.py                   # Database operations (Create, Read, Update, Delete)
├── schemas.py                # Pydantic request/response schemas
├── llm_client.py             # AI/LLM integration utilities
├── s3_client.py              # S3 storage client
└── __init__.py              # Package initialization with utility exports
```

**Core Architecture Components:**

##### `main.py` - Monolithic Application Design
* **Complete API Implementation**: All endpoints in single file for simplified deployment
* **FastAPI App Configuration**: CORS middleware, request logging, and global exception handling
* **Authentication System**: JWT token generation, validation, and user session management
* **Database Integration**: Direct integration with newsfrontier-lib for all data operations
* **Middleware Pipeline**: Request/response logging with performance timing and error tracking
* **API Categories**: Authentication, user management, dashboard analytics, content discovery, RSS management, and admin endpoints

##### `text_processor.py` - Content Processing Utilities
* **HTML Anchor Processing**: Automatic insertion of paragraph anchors for article content
* **Content Analysis**: Text processing strategy determination based on HTML structure
* **Anchor Management**: Generation, validation, and extraction of both P-xxxxx and SEN-xxxxx format anchors
* **Error Handling**: Graceful fallback to original content when processing fails

##### Database Layer (`../lib/`)
* **`models.py`** - SQLAlchemy ORM Models
  * User authentication and authorization models
  * RSS feeds and subscription relationships
  * Article metadata with vector embeddings
  * Topic and cluster classification schemas
  * Processing status tracking for AI workflows

* **`database.py`** - Connection Management
  * Async PostgreSQL connection with pgvector extension
  * Connection pooling for high-concurrency handling
  * Database migration support and health checks
  * Transaction management for data consistency

* **`crud.py`** - Data Access Layer
  * Type-safe database operations using SQLAlchemy async sessions
  * Complex queries for vector similarity search using pgvector
  * Bulk operations for AI processing workflows
  * Optimized queries for dashboard analytics and reporting

* **`schemas.py`** - API Contracts
  * Pydantic models for request validation and serialization
  * Response schemas with computed fields for frontend consumption
  * Type-safe data transformation between database models and API responses
  * Validation rules for user input and system constraints

**Key Design Patterns:**

##### Async-First Architecture
* All database operations use async/await patterns for non-blocking I/O
* FastAPI's async request handling minimizes resource consumption
* Background task queuing for AI processing workflows
* Concurrent RSS feed processing and content analysis

##### Dependency Injection
* FastAPI's dependency system for database sessions, authentication, and configuration
* Modular service layers for AI integration (LLM, embedding, clustering)
* Environment-based configuration injection for different deployment contexts
* Testing-friendly architecture with mockable dependencies

##### Error Handling & Logging
* Structured logging with contextual information for debugging
* Graceful error recovery with retry mechanisms for AI services
* User-friendly error messages with technical details for debugging
* Performance monitoring and health check endpoints

##### Security Implementation
* JWT-based authentication with configurable expiration
* Password hashing using bcrypt with salted rounds
* Role-based access control (user/admin permissions)
* Input validation and SQL injection prevention
* Rate limiting and request throttling capabilities

### Frontend Application  
* **Language**: TypeScript for type-safe development
* **Package Management**: pnpm for faster and more modern development
* **Framework**: Next.js 14+ with App Router
* **UI Library**: DaisyUI components with Tailwind CSS
* **State Management**: React Context API / Zustand
* **Testing**: Jest and React Testing Library

#### Key Pages & Components
* **Dashboard**: Personalized news overview
  * Daily news summary
  * The daily news includes reference links to articles or clusters.

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
* **Architecture**: UV workspace member with AI processing pipeline
* **AI/ML Stack**:
  * **LLM Integration**: Google AI (Gemini) for content analysis and summarization
  * **Models**: Gemini-2.0-Flash-Lite (fast), Gemini-2.5-Pro (advanced analysis)
  * **Embeddings**: gemini-embedding-001 with 768-dimensional vectors
  * **Vector Storage**: pgvector for similarity search and clustering
  * **Image Generation**: Imagen-3.0-Generate-002 for cover images
  * **Clustering**: Scikit-learn with LLM-based decision making
* **Key Capabilities**:
  * Content analysis with topic extraction and entity recognition
  * Intelligent clustering with context-aware decisions
  * Personalized daily summaries with structured markdown output
  * AI prompt testing framework for development and debugging
  * S3 integration for cover image storage
  * FastAPI internal server for inter-service communication

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

### `scripts/init.sql` - Database Schema Initialization
Complete PostgreSQL schema setup with pgvector extension:
* User authentication tables with secure password hashing
* News articles table with full-text search indices
* Topics and RSS sources configuration
* Vector embeddings storage with optimized indexing
* Clustering results and relationships

## Production Deployment

### Docker Compose Configuration

The project includes a complete `docker-compose.yml` configuration that orchestrates all NewsFrontier services in a containerized environment. The setup follows the architecture and environment variables defined in the development script (`scripts/dev.sh`).

#### Service Architecture:

**Database Service (`newsfrontier-db`):**
- Uses `pgvector/pgvector:pg17` image with vector extension support
- Configures PostgreSQL with environment-based credentials
- Mounts persistent data volume and initialization script
- Includes health checks for service dependency management
- Exposes port 5432 for external database access

**Backend Service (`newsfrontier-backend`):**
- Builds from `./backend` directory with Dockerfile
- Configures complete AI/ML environment (LLM APIs, embedding services)
- Includes all security settings (JWT, bcrypt) and processing parameters
- Depends on healthy database service before starting
- Exposes FastAPI server on port 8000 with log volume mounting

**Frontend Service (`newsfrontier-frontend`):**
- Builds Next.js application from `./frontend` directory
- Configures API endpoint for backend communication
- Exposes web application on port 3000
- Depends on backend service availability

**Scraper Service (`newsfrontier-scraper`):**
- Builds RSS scraping service from `./scraper` directory
- Configures RSS fetching parameters and database connection
- Runs in daemon mode with log file persistence
- Depends on healthy database service

**Postprocess Service (`newsfrontier-postprocess`):**
- Builds AI processing service from `./postprocess` directory
- Configures complete AI pipeline (LLM, embeddings, image generation)
- Includes S3 storage configuration for cover images
- Runs in daemon mode with comprehensive logging

#### Deployment Features:

- **Environment Variable Integration**: All services use `.env` file variables with sensible defaults
- **Service Dependencies**: Proper startup order with health check dependencies
- **Persistent Storage**: Database data persistence and log file mounting
- **Network Isolation**: Services communicate through internal Docker network
- **Restart Policies**: Automatic service restart on failure
- **Resource Management**: Container naming and volume management

#### Usage:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down
```

## Database Design

### Core Design Principles
* **Data Reliability Separation**: Raw RSS data and AI-processed data are stored separately to maintain data integrity and enable reprocessing
* **Error Recovery Support**: All processing tables include status tracking for reliable restart and recovery
* **Scalable Architecture**: Vector embeddings and clustering designed for high-volume news processing

### Database Schema

#### Core User Management

##### `users` - User authentication and profile information
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `username` - VARCHAR(50) UNIQUE NOT NULL
* `password_hash` - VARCHAR(255) NOT NULL (bcrypt salted hash)
* `email` - VARCHAR(255) UNIQUE NOT NULL (email validation)
* `is_admin` - BOOLEAN DEFAULT FALSE (role-based access control)
* `credits` - INTEGER DEFAULT 0 CHECK (credits >= 0) (user credit system)
* `credits_accrual` - INTEGER DEFAULT 0 CHECK (credits_accrual >= 0) (earned credits)
* `daily_summary_prompt` - TEXT (personalized AI prompt)
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW() (auto-update trigger)

**Relationships:**
- One-to-many with topics, clusters, summaries, RSS subscriptions

#### RSS Feed Management

##### `rss_feeds` - RSS feed source configuration
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `uuid` - UUID UNIQUE NOT NULL DEFAULT gen_random_uuid() (stable external identifier)
* `url` - TEXT NOT NULL UNIQUE (RSS feed URL)
* `title` - VARCHAR(255) (extracted from feed metadata)
* `description` - TEXT (feed description)
* `last_fetch_at` - TIMESTAMP (most recent fetch time)
* `last_fetch_status` - VARCHAR(50) DEFAULT 'pending' CHECK (last_fetch_status IN ('pending', 'success', 'failed', 'timeout'))
* `fetch_interval_minutes` - INTEGER DEFAULT 60 (configurable fetch frequency)
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

**Design Note:** UUID serves as stable identifier when URLs change

##### `rss_subscriptions` - User RSS feed subscriptions (many-to-many)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `rss_uuid` - UUID REFERENCES rss_feeds(uuid) ON DELETE CASCADE
* `alias` - VARCHAR(255) (user-defined feed name)
* `is_active` - BOOLEAN DEFAULT TRUE (subscription toggle)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (user_id, rss_uuid)

##### `rss_fetch_records` - Raw RSS content with deduplication
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `rss_feed_id` - INTEGER REFERENCES rss_feeds(id) ON DELETE CASCADE
* `raw_content` - TEXT NOT NULL (original RSS XML/JSON content)
* `content_hash` - VARCHAR(64) NOT NULL (SHA256 for deduplication)
* `first_fetch_timestamp` - TIMESTAMP DEFAULT NOW() (initial discovery)
* `last_fetch_timestamp` - TIMESTAMP DEFAULT NOW() (most recent fetch)
* `http_status` - INTEGER (HTTP response code)
* `content_encoding` - VARCHAR(50) (content encoding type)

**Design Pattern:** Separates raw RSS data from processed articles for data integrity

#### Article Processing Pipeline

##### `rss_items_metadata` - AI-extracted article data
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `rss_fetch_record_id` - INTEGER REFERENCES rss_fetch_records(id) ON DELETE CASCADE
* `guid` - TEXT (RSS item GUID for deduplication)
* `title` - TEXT NOT NULL (article title)
* `content` - TEXT (full article content)
* `url` - TEXT (article URL)
* `published_at` - TIMESTAMP (article publication time)
* `author` - VARCHAR(255) (article author)
* `category` - VARCHAR(255) (article category/topic)
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `processing_started_at` - TIMESTAMP (AI processing start time)
* `processing_completed_at` - TIMESTAMP (AI processing completion time)
* `processing_attempts` - INTEGER DEFAULT 0 CHECK (processing_attempts >= 0 AND processing_attempts <= 10)
* `last_error_message` - TEXT (error tracking for debugging)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT:** (rss_fetch_record_id, guid) - prevents duplicate articles per feed

##### `rss_item_derivatives` - AI-generated content and embeddings
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `rss_item_id` - INTEGER UNIQUE REFERENCES rss_items_metadata(id) ON DELETE CASCADE (one-to-one relationship)
* `summary` - TEXT (AI-generated article summary)
* `title_embedding` - VECTOR(dynamic_dimension) (pgvector title embeddings)
* `summary_embedding` - VECTOR(dynamic_dimension) (pgvector summary embeddings)
* `processing_status` - VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
* `summary_generated_at` - TIMESTAMP (LLM processing timestamp)
* `embeddings_generated_at` - TIMESTAMP (embedding generation timestamp)
* `processing_attempts` - INTEGER DEFAULT 0 (retry counter)
* `last_error_message` - TEXT (AI processing error details)
* `llm_model_version` - VARCHAR(100) (AI model version tracking)
* `embedding_model_version` - VARCHAR(100) (embedding model version)
* `created_at` - TIMESTAMP DEFAULT NOW()

**Vector Dimensions:** Configurable via environment variable (default: 1536 for OpenAI compatibility)

#### Topic and Cluster Management

##### `topics` - User-defined news categorization
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `name` - VARCHAR(255) NOT NULL (topic name)
* `topic_vector` - VECTOR(dynamic_dimension) (AI-generated topic embedding)
* `is_active` - BOOLEAN DEFAULT TRUE (topic status toggle)
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT:** (user_id, name) - prevents duplicate topic names per user

##### `events` - News event clusters extracted from article analysis
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `title` - VARCHAR(500) NOT NULL (cluster title)
* `description` - TEXT (cluster description)
* `event_description` - TEXT (detailed event analysis)
* `event_embedding` - VECTOR(dynamic_dimension) (event vector representation)
* `last_updated_at` - TIMESTAMP DEFAULT NOW() (event evolution tracking)
* `created_at` - TIMESTAMP DEFAULT NOW()
* `updated_at` - TIMESTAMP DEFAULT NOW()

#### Relationship Tables (Many-to-Many)

##### `article_topics` - Article-topic associations with relevance scoring
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `relevance_score` - FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0) (AI-computed relevance)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (rss_item_id, topic_id)

##### `article_events` - Article-event cluster associations
* `rss_item_id` - INTEGER REFERENCES rss_items_metadata(id) ON DELETE CASCADE
* `event_id` - INTEGER REFERENCES events(id) ON DELETE CASCADE
* `relevance_score` - FLOAT CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0) (clustering confidence)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (rss_item_id, event_id)

##### `user_topics` - User topic preferences and prioritization
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `topic_id` - INTEGER REFERENCES topics(id) ON DELETE CASCADE
* `priority` - INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 10) (user preference ranking)
* `notification_enabled` - BOOLEAN DEFAULT TRUE (notification settings)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **PRIMARY KEY** (user_id, topic_id)

#### Daily Summaries and System Configuration

##### `user_summaries` - Daily personalized news summaries
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `user_id` - INTEGER REFERENCES users(id) ON DELETE CASCADE
* `summary` - TEXT (AI-generated daily summary)
* `cover_arguments` - TEXT (cover image generation parameters)
* `cover_prompt` - TEXT (AI image generation prompt)
* `cover_seed` - INTEGER (image generation seed for reproducibility)
* `cover_s3key` - TEXT (S3 storage key for generated cover image)
* `date` - DATE NOT NULL (summary date)
* `created_at` - TIMESTAMP DEFAULT NOW()
* **UNIQUE CONSTRAINT:** (user_id, date) - one summary per user per day

##### `system_settings` - Global system configuration
* `id` - INTEGER PRIMARY KEY (auto-increment)
* `setting_key` - VARCHAR(100) UNIQUE NOT NULL (configuration key)
* `setting_value` - TEXT (configuration value)
* `setting_type` - VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json', 'float'))
* `description` - TEXT (setting documentation)
* `is_public` - BOOLEAN DEFAULT FALSE (public/private setting flag)
* `updated_at` - TIMESTAMP DEFAULT NOW()
* `updated_by` - INTEGER REFERENCES users(id) ON DELETE SET NULL (audit trail)
* `created_at` - TIMESTAMP DEFAULT NOW()

**Common System Settings:**

**Processing Configuration:**
* `default_rss_fetch_interval` - Default RSS polling interval in minutes (default: 60)
* `max_processing_attempts` - Maximum retry attempts for failed processing (default: 3)
* `embedding_dimension` - Vector dimension size (default: 768)
* `max_articles_per_event` - Maximum articles to associate with a single event (default: 50)

**AI Clustering Thresholds:**
* `similarity_threshold` - Minimum similarity score for clustering articles (default: 0.62)
* `cluster_threshold` - Minimum embedding similarity score for direct event assignment (default: 0.7)

**AI System Prompts (Private Settings):**
* `prompt_summary_creation` - Template prompt for generating article summaries with bullet points and anchor links
* `prompt_cluster_detection` - Template prompt for creating new event clusters
* `prompt_daily_summary_system` - System prompt for creating personalized daily news summaries with markdown links
* `prompt_cover_image_generation` - Template prompt for generating cover image descriptions for daily summaries

**Prompt Features:**
- Article summarization with anchor link preservation (`<a id="P-67890">` → `[text](#P-67890)`)
- Event clustering with topic hierarchy enforcement (one level below user topics)
- Daily summary generation with structured markdown links to dashboard pages
- Cover image prompt generation with professional editorial illustration guidelines

### Database Performance Optimizations

#### Vector Search Performance
* **pgvector Extensions**: All vector columns use IVFFlat indexes for fast similarity search
* **Index Tuning**: Vector indexes configured with `lists = 100` for optimal performance
* **Embedding Dimensions**: Consistent 1536-dimensional vectors across all tables

#### Query Performance Enhancements
* **Composite Indexes**: Multi-column indexes for common query patterns
* **Partial Indexes**: Status-based filtering optimized with dedicated indexes  
* **Time-Series Optimization**: DESC indexes on timestamp columns for recent data queries

#### Data Integrity Safeguards
* **Constraint Validation**: CHECK constraints prevent invalid data states
* **Referential Integrity**: Proper CASCADE/SET NULL behaviors for foreign keys
* **Unique Constraints**: Business logic constraints prevent duplicate data
* **Processing Limits**: Bounded retry attempts prevent infinite processing loops

#### Maintenance Recommendations
* **Regular VACUUM**: Vector indexes benefit from periodic maintenance
* **Index Monitoring**: Monitor query performance and adjust `lists` parameter as data grows
* **Partition Strategy**: Consider partitioning large tables by date for improved performance
* **Archive Strategy**: Implement data retention policies for historical records


### Environment Variables

#### Required Configuration
Copy `.env.template` to `.env` and configure the following variables:

**Database & Core Services:**
* `DATABASE_URL` - PostgreSQL connection string 
  * Format: `postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db`
* `DB_PASSWORD` - PostgreSQL database password
* `S3API_REGION` - S3-compatible storage region
* `S3API_ENDPOINT` - S3-compatible storage endpoint URL
* `S3API_BUCKET` - S3 bucket name for cover image storage
* `S3API_KEY_ID` - S3 access key ID
* `S3API_KEY` - S3 secret access key

**Security & Authentication:**
* `JWT_SECRET` - Secret key for JWT token signing (use strong random string in production)
  * Default: `your-super-secret-jwt-key-change-this-in-production`
* `JWT_EXPIRE_HOURS` - JWT token expiration time in hours (default: 24)
* `PASSWORD_SALT_ROUNDS` - Bcrypt salt rounds for password hashing (default: 12)

**AI/ML Services:**
* `LLM_API_URL` - Primary LLM service endpoint
  * Default: `https://generativelanguage.googleapis.com/v1beta/openai/`
* `LLM_API_KEY` - API key for LLM services
* `GOOGLE_API_KEY` - Google AI API key (for Gemini models)

**LLM Model Configuration:**
* `LLM_MODEL_SUMMARY` - Fast model for article summarization
  * Default: `gemini-2.0-flash-lite`
* `LLM_MODEL_ANALYSIS` - Capable model for cluster detection and daily summaries
  * Default: `gemini-2.5-pro`

**Vector Embedding Services:**
* `EMBEDDING_API_URL` - Vector embedding service endpoint
  * Default: `https://api.openai.com/v1`
* `EMBEDDING_MODEL` - Embedding model name
  * Default: `gemini-embedding-001`
* `EMBEDDING_DIMENSION` - Vector dimension size (default: 768)

**Image Generation Services:**
* `IMAGEGEN_MODEL` - AI image generation model
  * Default: `imagen-3.0-generate-002`
* `IMAGEGEN_ASPECT_RATIO` - Generated image aspect ratio (default: 16:9)
* `IMAGEGEN_PERSON_GENERATE` - Person generation policy (default: dont_allow)

**Optional AI Services:**
* `TRANSCRIPT_API_URL` - Speech-to-text service endpoint (optional)
* `TTS_API_URL` - Text-to-speech service endpoint (optional)
* `TTS_API_KEY` - API key for audio services (optional)

**Application Settings:**
* `LOG_LEVEL` - Application logging level (DEBUG, INFO, WARNING, ERROR)
  * Default: `INFO`
* `ENVIRONMENT` - Runtime environment (development, staging, production)
  * Default: `development`
* `DEBUG` - Enable debug mode (true/false)
  * Default: `true`

**Processing Configuration:**
* `MAX_PROCESSING_ATTEMPTS` - Maximum retry attempts for failed AI processing (default: 3)
* `DEFAULT_RSS_INTERVAL` - Default RSS fetch interval in minutes (default: 60)
* `SCRAPER_CONCURRENT_FEEDS` - Number of concurrent RSS feeds to process (default: 5)
* `POSTPROCESS_BATCH_SIZE` - Batch size for AI processing (default: 10)

**API Configuration:**
* `API_RATE_LIMIT` - API rate limiting (requests per minute, default: 100)
* `CORS_ORIGINS` - Allowed CORS origins for frontend access
  * Default: `http://localhost:3000,http://localhost:8000`

**Development Settings:**
* `NEXT_PUBLIC_API_URL` - Frontend API endpoint configuration
  * Default: `http://localhost:8000`

