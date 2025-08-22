# NewsFrontier Backend API

## Overview

The NewsFrontier backend is a FastAPI-based microservice that provides the core API for the news aggregation and analysis platform. It handles user authentication, content management, AI-powered content analysis, and provides REST APIs for the frontend and other services.

## Architecture

### File Structure
```
/home/nixos/NewsFrontier/backend/
├── main.py                 # Main FastAPI application (2,786 lines)
├── text_processor.py      # Text processing utilities (185 lines)
└── pyproject.toml         # Python project configuration
```

### Dependencies
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation and settings management
- **JWT**: Authentication tokens
- **PassLib**: Password hashing
- **NLTK**: Natural language processing
- **Boto3**: AWS S3 integration
- **Google GenerativeAI**: AI processing

### Core Configuration
```python
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_HOURS = 24
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 1536))
```

## Database Models

The application uses SQLAlchemy ORM with PostgreSQL and pgvector extension. All models are defined in `../lib/newsfrontier_lib/models.py`.

### User Management
- **User**: Core user model with authentication, credits, admin flags, and personalization settings
- **RSSSubscription**: User subscriptions to RSS feeds with custom intervals

### Content Management
- **RSSFeed**: RSS feed sources with fetch status and processing intervals
- **RSSFetchRecord**: Raw RSS content with deduplication via content hashes
- **RSSItemMetadata**: Parsed article metadata with processing status tracking
- **RSSItemDerivative**: AI-generated summaries and vector embeddings (768-dimensional)

### AI and Analytics
- **Topic**: User-defined topics with vector embeddings for semantic matching
- **Event**: News events created from article clustering analysis
- **ArticleTopic/ArticleEvent**: Many-to-many relationships with relevance scores
- **UserSummary**: Daily personalized summaries with AI-generated cover images
- **SystemSetting**: Global configuration storage for prompts and settings

## Authentication Functions

### `create_access_token(data: dict) -> str`
Creates JWT access tokens for user authentication.

**Parameters:**
- `data`: Dictionary containing user data (typically username)

**Returns:** Encoded JWT token string

**Functionality:** Adds expiration time and encodes token with SECRET_KEY

### `verify_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials]) -> str`
Validates JWT tokens from Authorization header or cookies.

**Parameters:**
- `request`: FastAPI request object
- `credentials`: Bearer token credentials (optional)

**Returns:** Username string if token is valid

**Raises:** HTTPException(401) if token is invalid or missing

**Functionality:** 
- Tries Authorization header first, then auth_token cookie
- Decodes JWT and validates expiration

### `verify_admin(username: str, db: Session) -> User`
Ensures authenticated user has admin privileges.

**Parameters:**
- `username`: Username from token verification
- `db`: Database session

**Returns:** User object if admin

**Raises:** HTTPException(403) if not admin, HTTPException(404) if user not found

## AI and Embedding Functions

### `generate_topic_embedding(topic_name: str) -> Optional[List[float]]`
Generates vector embeddings for topic names using AI.

**Parameters:**
- `topic_name`: Name of the topic to generate embedding for

**Returns:** List of float values representing the embedding, or None if failed

**Functionality:** 
- Uses shared LLM library for embedding generation
- Logs success/failure with embedding dimensions
- Used for topic similarity calculations

## REST API Endpoints

### Authentication Endpoints

#### `POST /api/login`
Authenticate user and return JWT token.

**Request Body:** `LoginRequest`
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:** `LoginResponse`
```json
{
  "token": "string",
  "user_id": 123,
  "expires": "2024-01-01T00:00:00Z"
}
```

**Functionality:**
- Validates username/password against database
- Creates JWT token with 24-hour expiration  
- Sets HTTP-only cookie for browser clients
- Logs successful/failed login attempts

#### `POST /api/logout`
Logout user by clearing authentication cookie.

**Authentication:** Required (JWT token)

**Response:** Success message

**Functionality:** Deletes auth_token cookie

#### `POST /api/register`
Register new user account.

**Request Body:** `RegisterRequest`
```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

**Response:** `RegisterResponse`
```json
{
  "user_id": 123,
  "message": "User created successfully"
}
```

**Functionality:**
- Validates username and email uniqueness
- Hashes password using bcrypt
- Creates new user with is_admin=False

### User Management Endpoints

#### `GET /api/user/me`
Get current user profile information.

**Authentication:** Required (JWT token)

**Response:** User details including credits and settings

#### `PUT /api/user/settings`
Update user settings like daily summary prompt.

**Authentication:** Required (JWT token)

**Request Body:** Dictionary with settings to update

**Functionality:** Updates user preferences and personalization settings

### Dashboard and Summary Endpoints

#### `GET /api/today`
Get dashboard data for today or specified date.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `date_param` (optional): Date in YYYY-MM-DD format

**Response:** `TodayResponse`

**Functionality:**
- Calculates statistics: total articles, clusters count, top topics
- Retrieves user's daily summary if available
- Gets trending keywords from article categories

#### `GET /api/available-dates`
Get dates in a month that have daily summaries.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `year`: Year (2000-3000)
- `month`: Month (1-12)

**Response:** `AvailableDatesResponse`

**Functionality:** Queries database for dates where user has summaries

#### `GET /api/cover-image`
Get presigned URL for daily summary cover image.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `date_param` (optional): Date in YYYY-MM-DD format

**Response:** Cover image URL and S3 key

**Functionality:** Generates presigned S3 URL for cover image access

### Topic Management Endpoints

#### `GET /api/topics`
Get all topics for authenticated user.

**Authentication:** Required (JWT token)

**Response:** `TopicsResponse` with list of user's topics

#### `POST /api/topics`
Create new topic for user.

**Authentication:** Required (JWT token)

**Request Body:** `TopicRequest`
```json
{
  "name": "string"
}
```

**Response:** `TopicCreateResponse`

**Functionality:**
- Validates topic name uniqueness for user
- Generates vector embedding for topic
- Triggers background processing for existing articles
- Uses threading for non-blocking topic processing

#### `PUT /api/topics/{topic_id}`
Update existing topic.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `topic_id`: ID of topic to update

**Request Body:** `TopicRequest`

**Functionality:**
- Validates ownership and name conflicts
- Regenerates embedding if name changed
- Updates topic properties

#### `DELETE /api/topics/{topic_id}`
Delete topic and all related data.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `topic_id`: ID of topic to delete

**Response:** Details about deleted relationships

**Functionality:**
- Validates topic ownership
- Uses CASCADE DELETE for related events, article-topics, user-topics
- Logs deletion statistics

#### `GET /api/topic/{topic_id}`
Get topic details with associated clusters.

**Authentication:** Required (JWT token)

**Response:** `TopicDetailResponse`

**Functionality:** Returns topic info and up to 50 related events (clusters)

### Article Management Endpoints

#### `GET /api/articles`
Get paginated list of articles.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Articles per page  
- `status` (default: "completed"): Processing status filter

**Response:** `ArticlesResponse` with pagination info

**Functionality:** Returns articles with pagination metadata

#### `GET /api/article/{article_id}`
Get detailed article information including AI summary.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `article_id`: ID of article to retrieve

**Response:** `Article` with derivatives data

**Functionality:** Includes AI-generated summary and processing status

#### `POST /api/article/{article_id}/reprocess-anchors`
Reprocess article content to add paragraph anchors.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `article_id`: ID of article to reprocess

**Response:** Processing results with anchor information

**Functionality:** 
- Uses text_processor module to add HTML anchors
- Updates article content in database
- Returns statistics about anchors added

#### `GET /api/article/{article_id}/sentences`
Get paragraph breakdown with anchor information.

**Authentication:** Required (JWT token)

**Response:** List of paragraphs with anchor IDs and positions

#### `GET /api/article/{article_id}/processing-info`
Get information about how article would be processed.

**Authentication:** Required (JWT token)

**Response:** Processing strategy and content analysis

### RSS Feed Management Endpoints

#### `GET /api/feeds`
Get user's RSS feed subscriptions.

**Authentication:** Required (JWT token)

**Response:** List of subscribed feeds with metadata

**Functionality:** Returns feed details joined with subscription information

#### `POST /api/feeds`
Add new RSS feed subscription.

**Authentication:** Required (JWT token)

**Request Body:** Feed configuration with URL, title, description

**Functionality:**
- Checks for existing feed by URL
- Creates new feed or reuses existing
- Creates user subscription relationship

#### `PUT /api/feeds/{feed_uuid}`
Update RSS feed subscription settings.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `feed_uuid`: UUID of feed to update

**Functionality:** Updates user's subscription preferences (alias, active status)

#### `DELETE /api/feeds/{feed_uuid}`
Remove RSS feed subscription.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `feed_uuid`: UUID of feed to unsubscribe from

**Functionality:** Removes user subscription (doesn't delete feed itself)

## Internal API Endpoints (Microservice Communication)

### Article Processing APIs

#### `GET /api/internal/articles/pending-processing`
Get articles that need AI processing (for postprocess service).

**Query Parameters:**
- `limit` (default: 50): Maximum articles to return

**Response:** List of articles with processing status "pending"

#### `POST /api/internal/articles/{article_id}/process`
Update article processing status and store AI analysis (from postprocess).

**Path Parameters:**
- `article_id`: ID of processed article

**Request Body:** `ArticleProcessingUpdate` with AI-generated content

**Functionality:**
- Stores embeddings and summaries in derivatives table
- Updates article processing status
- Handles both new and existing derivative records

### Topic and Similarity APIs

#### `GET /api/internal/topics`
Get all topics with embeddings (for postprocess service).

**Query Parameters:**
- `user_id` (optional): Filter by specific user

**Response:** Topics with vector embeddings

**Functionality:** Returns topic data needed for similarity calculations

#### `POST /api/internal/topics/similar`
Find topics similar to given embedding.

**Request Body:** Embedding vector and similarity threshold

**Response:** List of similar topics with similarity scores

**Functionality:**
- Calculates cosine similarity between embeddings
- Returns topics above threshold, sorted by similarity

### Event and Clustering APIs

#### `GET /api/internal/events`
Get event clusters with filtering.

**Query Parameters:**
- `user_id`: Filter by user
- `topic_id`: Filter by topic  
- `created_date`: Filter by creation date

**Response:** List of events with embeddings

#### `POST /api/internal/events`
Create new event cluster (from postprocess).

**Request Body:** `EventData` with event information

**Functionality:**
- Validates user and topic existence
- Generates embedding for event description
- Creates Event record

#### `POST /api/internal/article-events`
Link articles to event clusters.

**Request Body:** `ArticleEventData` with relevance score

**Functionality:** Creates ArticleEvent relationship records

### Daily Summary APIs

#### `GET /api/internal/users`
Get all users for summary generation.

**Response:** List of users with daily summary prompts

**Functionality:** Used by postprocess service for daily summary generation

#### `POST /api/internal/user-summaries`
Create new daily summary.

**Request Body:** `DailySummaryCreateRequest`

**Functionality:** Creates UserSummary record with cover image metadata

#### `GET /api/internal/prompts`
Get AI processing prompts for postprocess service.

**Response:** Dictionary of prompt keys and values

**Functionality:** Returns prompts for summary creation, clustering, daily summaries, cover images

## Admin API Endpoints

#### `GET /api/admin/system-settings`
Get all system settings (Admin only).

**Authentication:** Admin JWT token required

**Response:** List of `SystemSettingResponse`

**Functionality:** Returns all system configuration settings

#### `PUT /api/admin/system-settings`
Update multiple system settings (Admin only).

**Authentication:** Admin JWT token required

**Request Body:** List of `SystemSettingUpdate`

**Response:** Update statistics and any failures

**Functionality:**
- Validates setting types (string, integer, boolean, json, float)
- Type-specific validation for values
- Updates existing settings or creates new ones
- Returns detailed success/failure reporting

## Text Processing Module (text_processor.py)

### `generate_paragraph_anchor_id() -> str`
Generate random paragraph anchor IDs.

**Returns:** String in format "P-xxxxx" where xxxxx is random 5-digit number

**Functionality:** Used to create unique anchors for paragraph navigation

### `process_text_with_anchors(text: Optional[str]) -> Optional[str]`
Add HTML anchors before paragraph tags for navigation.

**Parameters:**
- `text`: Input HTML text to process

**Returns:** Processed text with anchor tags, or original if processing fails

**Functionality:**
- Only processes content with multiple `<p>` tags
- Inserts `<a id="P-xxxxx"></a>` before each `<p>` tag
- Handles offset calculations for multiple insertions
- Error handling returns original text

### `extract_paragraphs_with_anchors(text: Optional[str]) -> List[dict]`
Extract paragraph content with anchor information.

**Parameters:**
- `text`: HTML text to analyze

**Returns:** List of dictionaries with anchor_id, text, and position

**Functionality:**
- Finds all `<p>` tag content using regex
- Only processes content with multiple paragraphs
- Returns structured data for frontend navigation

### `extract_anchor_ids_from_text(text: Optional[str]) -> List[str]`
Find all existing anchor IDs in text.

**Parameters:**
- `text`: Text containing anchor tags

**Returns:** List of anchor IDs (both SEN-xxxxx and P-xxxxx formats)

**Functionality:** Uses regex to find existing anchor tags

### `validate_anchor_format(anchor_id: str) -> bool`
Validate anchor ID format.

**Parameters:**
- `anchor_id`: Anchor ID to validate

**Returns:** True if format is valid (SEN-xxxxx or P-xxxxx)

**Functionality:** Regex validation for proper anchor format

### `get_text_processing_info(text: Optional[str]) -> dict`
Analyze how text would be processed.

**Parameters:**
- `text`: Text to analyze

**Returns:** Dictionary with strategy, length, p_tag_count, and reason

**Functionality:**
- Determines if text would be processed (multiple `<p>` tags required)
- Returns metadata about processing decision
- Used for debugging and frontend information

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `POSTPROCESS_API_URL` - PostProcess service URL
- `JWT_SECRET` - Authentication secret key
- `LLM_API_URL` - Google AI API endpoint
- `LLM_API_KEY` - Google AI API key
- `GOOGLE_API_KEY` - Google services API key
- `LLM_MODEL_SUMMARY` - AI model for summarization
- `LLM_MODEL_ANALYSIS` - AI model for analysis tasks
- `EMBEDDING_MODEL` - Text embedding model
- `S3API_*` - S3 storage configuration

## Key Features

1. **Vector Similarity Search**: Uses pgvector for semantic content matching
2. **Real-time Processing Pipeline**: Coordinates with scraper and postprocess services
3. **Personalized Content**: User-specific topics and daily summaries
4. **AI-Powered Analysis**: Automated content summarization and clustering
5. **Scalable Architecture**: Microservices design with clear separation of concerns
6. **Secure Authentication**: JWT tokens with HTTP-only cookies
7. **Admin Interface**: System settings and user management capabilities

## Development

### Running the Backend
```bash
# From project root
docker-compose up backend

# Or standalone
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation
FastAPI automatically generates OpenAPI documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`