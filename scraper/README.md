# NewsFrontier RSS Scraper

## Overview

The NewsFrontier RSS Scraper is a Python service that continuously monitors RSS feeds, fetches new content, parses articles, and forwards them to the backend API for processing. It handles content deduplication, error recovery, and provides reliable RSS feed monitoring for the news aggregation platform.

## Architecture

### File Structure
```
/home/nixos/NewsFrontier/scraper/
├── main.py                 # Main scraper service
├── pyproject.toml         # Python project configuration  
└── scraper.log           # Service logs (generated)
```

### Dependencies
- **requests (≥2.31.0)**: HTTP client for RSS fetching
- **feedparser (≥6.0.10)**: RSS/Atom feed parsing
- **sqlalchemy (≥2.0.0)**: Database ORM
- **psycopg2-binary (≥2.9.7)**: PostgreSQL adapter
- **pydantic (≥2.5.0)**: Data validation

## Core Service Class

### `RSSScraperService`

Main service class that handles RSS feed monitoring and processing.

#### `__init__(self)`
Initialize the scraper service.

**Functionality:**
- Sets up running state and backend URL configuration
- Configures signal handlers for graceful shutdown (SIGINT, SIGTERM)
- Backend URL from environment variable `BACKEND_URL` (default: "http://localhost:8000")

#### `_signal_handler(self, signum, frame)`
Handle shutdown signals gracefully.

**Parameters:**
- `signum`: Signal number received
- `frame`: Current stack frame

**Functionality:** Sets running flag to False for graceful shutdown

## RSS Feed Processing Functions

### `get_pending_feeds(self) -> List[Dict[str, Any]]`
Retrieve feeds requiring processing via backend API.

**Returns:** List of feed dictionaries with metadata

**API Endpoint:** `GET /api/internal/feeds/pending`

**Functionality:**
- Fetches feeds that need processing based on their intervals
- Returns empty list on API failure with error logging

### `fetch_rss_feed(self, feed_url: str, feed_id: int) -> Optional[Dict[str, Any]]`
Fetch and parse RSS feeds from URLs.

**Parameters:**
- `feed_url`: RSS feed URL to fetch
- `feed_id`: Database ID of the RSS feed

**Returns:** Dictionary containing parsed data or None on failure

**Functionality:**
- Uses browser-mimicking headers with custom User-Agent
- 30-second timeout for HTTP requests
- Content hash calculation using SHA256 for deduplication
- RSS parsing using `feedparser` library
- Error handling for malformed feeds (bozo detection)
- Extracts feed metadata (title, description, language)

### `extract_articles(self, feed_data: Dict[str, Any]) -> List[Dict[str, Any]]`
Extract individual articles from parsed RSS feed.

**Parameters:**
- `feed_data`: Parsed RSS feed data from feedparser

**Returns:** List of article dictionaries with extracted metadata

**Article Data Extracted:**
- GUID (unique identifier)
- Title
- Content (via `_extract_content()`)
- URL
- Author
- Published date (via `_parse_published_date()`)
- Category (via `_extract_category()`)

**Functionality:**
- Processes RSS entries into standardized article format
- Handles missing fields gracefully
- Validates required fields (GUID, title)

### `_extract_content(self, entry) -> Optional[str]`
Extract article content from RSS entry.

**Parameters:**
- `entry`: Individual RSS entry from feedparser

**Returns:** Article content as string or None if not available

**Content Fields Priority:**
1. `content` (list or string format)
2. `summary` 
3. `description`

**Functionality:**
- Handles both list and string content formats
- Returns first available content source
- HTML content preserved as-is

### `_parse_published_date(self, entry) -> Optional[str]`
Parse and format article publication date.

**Parameters:**
- `entry`: RSS entry containing date information

**Returns:** ISO format datetime string or None

**Date Fields Priority:**
1. `published_parsed`
2. `updated_parsed`

**Functionality:**
- Converts time.struct_time to ISO format
- Handles missing or invalid date fields
- Returns None for unparseable dates

### `_extract_category(self, entry) -> Optional[str]`
Extract article category from RSS entry.

**Parameters:**
- `entry`: RSS entry containing category information

**Returns:** Category string or None

**Category Sources:**
1. Tags (first term if available)
2. Direct category field

**Functionality:**
- Prioritizes tag-based categorization
- Falls back to category field
- Returns None if no category information available

## Database Integration Functions

### `create_fetch_record(self, feed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]`
Create or update RSS fetch record in database.

**Parameters:**
- `feed_data`: Complete feed data including content and metadata

**Returns:** Fetch record data or None on failure

**API Endpoint:** `POST /api/internal/fetch-records`

**Functionality:**
- Stores raw RSS content with metadata
- Automatic duplicate detection via content hashing
- Updates timestamp if duplicate content found
- Creates new record for fresh content

### `create_articles(self, articles: List[Dict[str, Any]], fetch_record_id: int) -> bool`
Create articles in database via backend API.

**Parameters:**
- `articles`: List of article dictionaries to create
- `fetch_record_id`: ID of associated fetch record

**Returns:** True if successful, False otherwise

**API Endpoint:** `POST /api/internal/articles`

**Functionality:**
- Bulk article creation for efficiency
- Links articles to fetch record
- Handles API errors gracefully
- Returns creation statistics

### `update_feed_status(self, feed_id: int, status: str, fetch_time: datetime) -> bool`
Update feed processing status and timestamp.

**Parameters:**
- `feed_id`: Database ID of the RSS feed
- `status`: Status string ('success', 'failed', 'timeout')
- `fetch_time`: Timestamp of fetch attempt

**Returns:** True if update successful, False otherwise

**API Endpoint:** `POST /api/internal/feeds/{feed_id}/status`

**Functionality:**
- Updates last fetch status and timestamp
- Used for tracking feed health and scheduling
- Error logging for failed updates

## Processing Workflow Functions

### `process_feed(self, feed: Dict[str, Any]) -> bool`
Complete processing pipeline for a single RSS feed.

**Parameters:**
- `feed`: Feed dictionary with URL and metadata

**Returns:** True if processing successful, False otherwise

**Processing Workflow:**
1. Fetch RSS data from URL
2. Create/update fetch record with content hash
3. Check for duplicate content (skip if duplicate)
4. Extract articles from RSS entries
5. Create articles via backend API
6. Update feed status (success/failed)

**Error Handling:**
- Network errors logged and feed marked as failed
- Parse errors logged but not fatal
- API errors logged and feed marked as failed
- Processing continues with next feed

### `run_scraper_cycle(self)`
Execute single iteration of the scraper process.

**Functionality:**
- Gets pending feeds from backend API
- Processes each feed sequentially
- Tracks success/failure statistics
- Implements inter-feed delays (1 second)
- Logs cycle completion statistics

### `run_daemon(self)`
Run scraper in continuous daemon mode.

**Functionality:**
- 5-minute cycles (300 seconds between cycles)
- Graceful shutdown on signal reception
- Error recovery with 1-minute wait on critical errors
- Continuous operation until stopped

### `run_once(self)`
Execute scraper once and exit.

**Returns:** True if successful, False otherwise

**Functionality:**
- Single execution mode for testing/cron jobs
- Runs one complete scraper cycle
- Useful for debugging and manual testing

## Command Line Interface

### Main Entry Point: `main()`
Parses command line arguments and launches scraper service.

**Command Line Arguments:**
- `--daemon`: Run as daemon service (continuous operation)
- `--once`: Run once and exit (single execution)
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)

**Default Behavior:** If no mode specified, defaults to daemon mode

**Example Usage:**
```bash
# Run as daemon
python main.py --daemon

# Run once for testing  
python main.py --once

# Run with debug logging
python main.py --daemon --log-level DEBUG
```

## Environment Configuration

### Environment Variables
- **`BACKEND_URL`**: Backend API URL (default: "http://localhost:8000")
- **Database access**: Via backend API (no direct database connection)

### Logging Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),  # File logging
        logging.StreamHandler()              # Console logging
    ]
)
```

## Database Models Integration

The scraper integrates with shared database models from `../lib/newsfrontier_lib/models.py`:

### RSS Feed Management
- **RSSFeed**: Feed metadata and status tracking
- **RSSSubscription**: User subscriptions to feeds
- **RSSFetchRecord**: Raw content storage with deduplication
- **RSSItemMetadata**: Individual article metadata

### Processing Pipeline
1. **Fetch**: RSS content retrieval and parsing
2. **Deduplicate**: Content hash comparison
3. **Extract**: Article metadata extraction  
4. **Store**: Database persistence via API
5. **Queue**: Articles queued for AI processing

## Error Handling and Recovery

### Error Categories
1. **Network Errors**: Request timeouts, connection failures
2. **Parsing Errors**: Malformed RSS content (non-fatal)
3. **API Errors**: Backend communication failures
4. **Content Errors**: Missing required fields (non-fatal)

### Recovery Strategies
- **Feed-level**: Individual feed failures don't stop processing
- **Cycle-level**: Errors logged, next cycle continues after delay
- **Daemon-level**: 1-minute wait on critical errors before retry
- **Graceful Shutdown**: Signal handling for clean service stops

### Monitoring and Logging
- **File Logging**: All events logged to `scraper.log`
- **Console Output**: Real-time logging for daemon monitoring
- **Statistics**: Success/failure counts logged per cycle
- **Health Tracking**: Feed status updates for monitoring

## Integration with NewsFrontier Platform

### Service Dependencies
1. **Database**: PostgreSQL with shared models
2. **Backend API**: All data operations via REST API
3. **PostProcess Service**: Articles queued for AI processing

### Deployment
- **Docker Container**: Runs as containerized service
- **Health Checks**: Process monitoring and restart capability
- **Volume Mounts**: Log persistence and configuration
- **Service Ordering**: Database → Backend → Scraper

### Development and Testing
```bash
# From project root
docker-compose up scraper

# Or standalone testing
cd scraper  
python main.py --once --log-level DEBUG
```

## Key Features

1. **Content Deduplication**: SHA256 hashing prevents duplicate processing
2. **Error Recovery**: Robust error handling with graceful degradation
3. **Scalable Processing**: Sequential feed processing with configurable delays
4. **Health Monitoring**: Feed status tracking and failure reporting
5. **Flexible Deployment**: Daemon or one-shot execution modes
6. **API Integration**: RESTful communication with backend services
7. **Standards Compliance**: Proper RSS/Atom feed parsing
8. **Resource Efficient**: Memory-conscious processing with cleanup