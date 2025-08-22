# NewsFrontier PostProcess Service - Modular Architecture

## Overview

The NewsFrontier PostProcess Service is an AI-powered microservice that analyzes articles, generates summaries, performs topic matching, creates event clusters, and generates personalized daily summaries. It features a **modular architecture** with specialized services for each function, making it highly maintainable and extensible.

## Refactored Modular Architecture

### File Structure
```
/home/nixos/NewsFrontier/postprocess/
├── main.py                         # Main service coordinator (refactored)
├── main_original.py               # Original monolithic version (backup)
├── summary_generator.py           # Article summarization module
├── embedding_generator.py         # Vector embedding generation module  
├── image_generator.py             # Cover image generation module
├── clustering_service.py          # Event clustering module
├── daily_summary_service.py       # Daily summary generation module
├── pyproject.toml                 # Python project configuration
├── postprocess.log               # Service logs (generated)
└── test_prompts/                 # AI testing framework
    ├── run_prompt_tests.sh       # Test execution script
    ├── test_summary_creation.py
    ├── test_cluster_detection.py
    ├── test_daily_summary.py
    └── test_cover_image_generation.py
```

### Dependencies
- **FastAPI**: Web framework for API endpoints
- **Google GenerativeAI**: AI processing (Gemini models)
- **SQLAlchemy**: Database ORM
- **scikit-learn**: Vector similarity calculations
- **numpy**: Numerical computing for embeddings
- **requests**: HTTP client for backend communication
- **uvicorn**: ASGI server for FastAPI

## Modular Service Components

### 1. Summary Generator (`summary_generator.py`)

#### `SummaryGenerator`
Handles AI-powered article summarization using configurable prompts.

**Key Methods:**
- `create_article_summary(article: Dict[str, Any]) -> Optional[str]`
  - Creates HTML-formatted bullet-point summaries
  - Uses database prompts (NO DEFAULT FALLBACKS)
  - Includes internal anchor links for navigation
  - Preserves factual accuracy and key information

- `validate_summary_content(summary: str) -> bool`
  - Validates generated summary quality
  - Checks HTML structure and content length
  - Ensures meaningful content

- `get_summary_stats(summary: str) -> Dict[str, Any]`
  - Returns statistics about summary content
  - Character count, word count, bullet points, anchor links

#### `PromptManager`
Manages AI prompts retrieved from database with caching.

**Key Methods:**
- `set_prompts(prompts_dict: Dict[str, str])`
- `get_prompt(prompt_type: str) -> Optional[str]`
- `clear_cache()`

### 2. Embedding Generator (`embedding_generator.py`)

#### `EmbeddingGenerator`
Handles vector embedding generation for text content using Google Gemini models.

**Key Methods:**
- `generate_title_embedding(article: Dict[str, Any]) -> Optional[List[float]]`
  - Generates 768-dimensional embeddings for article titles
  - Optimized for semantic title matching

- `generate_summary_embedding(summary: str) -> Optional[List[float]]`
  - Generates embeddings for AI-generated summaries
  - Enables dual embedding comparison

- `generate_topic_embedding(topic_name: str) -> Optional[List[float]]`
  - Creates embeddings for user-defined topics
  - Used for semantic topic matching

- `generate_event_embedding(event_description: str) -> Optional[List[float]]`
  - Generates embeddings for event clusters
  - Supports clustering algorithm requirements

- `validate_embedding(embedding: List[float]) -> bool`
  - Validates embedding format and dimensions
  - Ensures 768-dimensional vectors with finite values

#### `SimilarityCalculator`
Handles similarity calculations between embedding vectors.

**Key Methods:**
- `calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float`
  - Calculates cosine similarity between two embeddings
  - Returns similarity score (0.0 to 1.0)

- `find_similar_topics(article_title_embedding, article_summary_embedding, topics, threshold) -> List[Dict]`
  - **Dual embedding strategy**: Compares both title and summary embeddings
  - **Maximum similarity**: Uses higher of title/summary similarity scores
  - **Threshold filtering**: Configurable similarity threshold
  - **Sorted results**: Returns topics ordered by relevance

- `find_similar_events(article_title_embedding, article_summary_embedding, events, threshold) -> Optional[Dict]`
  - Finds most similar event cluster using embedding comparison
  - Used in two-stage clustering algorithm

### 3. Image Generator (`image_generator.py`)

#### `ImageGenerator`
Handles AI-powered cover image generation and S3 upload.

**Key Methods:**
- `generate_cover_image_prompt(summary_content: str) -> Optional[str]`
  - Generates AI image descriptions for daily summary covers
  - Uses database prompts (NO DEFAULT FALLBACKS)
  - Formats prompt with summary content (limited to 2000 chars)

- `generate_and_upload_cover_image(cover_prompt: str, summary_date: date) -> Optional[str]`
  - Uses Google Imagen model for image generation
  - Configurable aspect ratio and person generation settings
  - Uploads to S3 with date-based naming
  - Returns S3 key for uploaded image

- `validate_image_prompt(prompt: str) -> bool`
  - Validates image generation prompt quality
  - Checks length bounds and descriptive content

#### `ImagePromptFormatter`
Utility class for enhancing image generation prompts.

**Key Methods:**
- `enhance_prompt_with_style(base_prompt: str, style_preferences: Dict) -> str`
  - Adds professional news imagery style guidelines
  - Modern, clean design aesthetics

- `filter_inappropriate_content(prompt: str) -> str`
  - Filters potentially inappropriate content
  - Ensures news-appropriate imagery

### 4. Clustering Service (`clustering_service.py`)

#### `ClusteringService`
Handles intelligent event clustering using a two-stage approach.

**Key Methods:**
- `detect_or_create_cluster(user_id, topic_id, topic_name, article_title, article_summary, title_embedding, summary_embedding) -> Optional[Dict]`
  - **Two-Stage Process:**
    1. **Embedding Distance Check**: Direct cosine similarity with existing events
    2. **LLM Analysis**: AI-powered contextual clustering decisions
  - Uses configurable cluster threshold (default 0.7)
  - Creates new event clusters when no match found

- `create_article_event_association(article_id: int, event_id: int, relevance_score: float) -> bool`
  - Links articles to event clusters with relevance scoring

- `update_cluster_threshold(new_threshold: float)`
  - Updates clustering similarity threshold dynamically

#### `BackendClient`
Handles backend API communication for clustering operations.

**Key Methods:**
- `get_events_for_topic(user_id: int, topic_id: int) -> List[Dict]`
- `create_event_cluster(user_id, topic_id, title, description, event_description) -> Optional[Dict]`
- `create_article_event_association(article_id, event_id, relevance_score) -> bool`

### 5. Daily Summary Service (`daily_summary_service.py`)

#### `DailySummaryService`
Handles personalized daily summary generation for users.

**Key Methods:**
- `generate_user_daily_summary(user_id: int, username: str, summary_date: Optional[date]) -> bool`
  - **Complete Process:**
    1. Check for existing summary (avoid duplicates)
    2. Gather user context (topics, articles, events)
    3. Generate summary content using LLM
    4. Generate cover image prompt (optional)
    5. Save summary with metadata

- `generate_summaries_for_all_users() -> Dict[str, int]`
  - Processes all users individually
  - Returns detailed generation statistics
  - Comprehensive error handling per user

- `_get_user_daily_context(user_id: int, summary_date: date) -> Optional[Dict]`
  - **Context Includes:**
    - User profile and custom prompt
    - User-defined topics
    - Relevant articles published today
    - New events created today
    - Recent daily summaries (last 5 for context)

- `_create_daily_summary_content(user_context: Dict) -> Optional[str]`
  - Uses daily summary system prompt from database (NO DEFAULT)
  - Combines system prompt with user's custom prompt
  - Formats articles, events, and historical context
  - Generates personalized content using analysis model

**Content Formatting Methods:**
- `_format_articles_for_summary(articles: List[Dict]) -> str`
  - Creates local dashboard links (`/dashboard/article/{id}`)
  - Includes AI-generated summaries when available

- `_format_events_for_summary(events: List[Dict]) -> str`
  - Groups events by topic with local dashboard links
  - Includes event descriptions and context

- `_format_recent_summaries(summaries: List[Dict]) -> str`
  - Provides continuity and context for new summaries

### 6. Main Service Coordinator (`main.py`)

#### `AIPostProcessService` (Refactored)
Main service class that coordinates all modular services.

**Key Methods:**
- `_initialize_services()`
  - Initializes all modular services with proper dependencies
  - Sets up service communication channels

- `process_article(article: Dict[str, Any]) -> bool`
  - **Processing Pipeline using modular services:**
    1. Generate title embedding (`embedding_generator`)
    2. Create AI summary (`summary_generator`)
    3. Generate summary embedding (`embedding_generator`)
    4. Update article with results
    5. Topic matching and clustering (`similarity_calculator`, `clustering_service`)

- `run_processing_cycle()`
  - Coordinates article processing using all services
  - Handles prompt reloading and error recovery

- `run_daily_summary_generation()`
  - Delegates to `daily_summary_service`
  - Manages scheduling and statistics

#### `BackendAPIClient` (Extended)
Extended backend client with additional methods for main service.

**Key Methods:**
- `get_all_users() -> List[Dict[str, Any]]`
- `check_summary_exists(user_id: int, summary_date) -> bool`
- `get_user_data(user_id: int) -> Optional[Dict[str, Any]]`
- `get_user_topics(user_id: int) -> List[Dict[str, Any]]`
- `get_topic_articles(topic_id: int, date) -> List[Dict[str, Any]]`
- `get_topic_events(topic_id: int, date) -> List[Dict[str, Any]]`
- `save_daily_summary(user_id, date, summary, cover_prompt, cover_s3key) -> bool`

## HTTP API Endpoints

The service provides REST endpoints for external integration:

### `POST /api/process-new-topic`
Process new topic against existing articles.

**Request Body:**
```json
{
  "topic_id": 123,
  "topic_name": "example topic",
  "topic_embedding": [0.1, 0.2, ...],
  "user_id": 456
}
```

### `GET /api/health`
Health check endpoint for monitoring.

### `POST /api/generate-user-summary/{user_id}`
Trigger daily summary generation for specific user.

### `POST /api/process`
Trigger manual article processing cycle.

## Environment Configuration

### Environment Variables
- **`BACKEND_URL`**: Backend API URL (default: "http://localhost:8000")
- **`LLM_API_URL`**: Google AI API endpoint
- **`LLM_API_KEY`**: Google AI API key
- **`GOOGLE_API_KEY`**: Google services API key
- **`LLM_MODEL_SUMMARY`**: AI model for summarization (default: gemini-2.0-flash-lite)
- **`LLM_MODEL_ANALYSIS`**: AI model for analysis (default: gemini-2.5-pro)
- **`EMBEDDING_MODEL`**: Text embedding model (default: gemini-embedding-001)
- **`IMAGEGEN_MODEL`**: Image generation model (default: imagen-3.0-generate-002)
- **`IMAGEGEN_ASPECT_RATIO`**: Image aspect ratio (default: 16:9)
- **`IMAGEGEN_PERSON_GENERATE`**: Person generation control (default: dont_allow)
- **`S3API_*`**: S3 storage configuration for cover images

### Key Configuration
- **Processing Intervals**: 2 minutes between cycles
- **Similarity Threshold**: 0.3 (configurable via database)
- **Cluster Threshold**: 0.7 (configurable via database)
- **Embedding Dimensions**: 768 (Google Gemini standard)
- **Daily Summary Time**: 00:00-00:30 (configurable)

## Key Features of Modular Architecture

### 1. **Separation of Concerns**
- Each module handles a specific functionality
- Clear interfaces between components
- Independent error handling and logging

### 2. **Enhanced Maintainability**
- Easy to modify individual components
- Isolated testing for each module
- Clear dependency management

### 3. **Improved Debugging**
- Issues can be traced to specific modules
- Module-level logging and statistics
- Independent validation methods

### 4. **Extensibility**
- New features can be added as separate modules
- Existing modules can be enhanced independently
- Plugin-like architecture for new AI models

### 5. **No Default Prompts Policy**
- All modules enforce database-driven prompt configuration
- Prevents prompt drift and ensures consistency
- Explicit error handling when prompts unavailable

### 6. **Dual Embedding Strategy**
- Both title and summary embeddings for improved accuracy
- Maximum similarity scoring for better topic matching
- Enhanced clustering decisions

### 7. **Two-Stage Clustering**
- Fast embedding-based similarity for direct matches
- LLM-based contextual analysis for complex decisions
- Configurable thresholds for flexibility

## Testing Framework

### Comprehensive Test Suite (`test_prompts/`)

The PostProcess service includes isolated testing framework for AI components:

#### Test Scripts:
- **`test_summary_creation.py`** - Test article summarization prompts
- **`test_cluster_detection.py`** - Test event clustering decision logic
- **`test_daily_summary.py`** - Test daily summary generation
- **`test_cover_image_generation.py`** - Test cover image descriptions

#### Test Features:
- **Sample Data Mode**: Built-in realistic test data (`--sample` flag)
- **Real Data Mode**: Connect to backend for actual data testing
- **Prompt Transparency**: Display actual prompts sent to AI services
- **Performance Monitoring**: Execution time and resource tracking
- **Unified Execution**: `run_prompt_tests.sh` script for convenient testing

#### Example Usage:
```bash
# Test with sample data
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh summary --sample

# Test with real data
GOOGLE_API_KEY=your_key uv run test_prompts/test_daily_summary.py

# Test all components
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh all --sample
```

## Development

### Running the PostProcess Service
```bash
# From project root
docker-compose up postprocess

# Or standalone daemon mode
cd postprocess
python main.py --daemon

# Single execution for testing
python main.py --once --log-level DEBUG
```

### Testing Individual Modules
```bash
# Test specific component
cd postprocess
GOOGLE_API_KEY=your_key python test_prompts/test_summary_creation.py --sample

# Test all components
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh all --sample
```

### Module Development
Each module can be developed and tested independently:

```python
# Example: Testing summary generator independently
from summary_generator import SummaryGenerator, PromptManager

prompt_manager = PromptManager()
prompt_manager.set_prompts({'summary_creation': 'Your prompt here'})

generator = SummaryGenerator(prompt_manager)
result = generator.create_article_summary({'title': 'Test', 'content': 'Test content'})
```

## Migration Notes

- **Original Code**: Backed up as `main_original.py`
- **Compatibility**: All existing APIs and functionality preserved
- **Configuration**: Same environment variables and settings
- **Database**: No schema changes required
- **Deployment**: Drop-in replacement for existing service

The modular architecture maintains full backward compatibility while providing a much cleaner, more maintainable codebase for future development.