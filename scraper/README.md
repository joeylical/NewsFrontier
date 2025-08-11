# NewsFrontier RSS Scraper

RSS feed scraping service for the NewsFrontier news aggregation platform.

## Overview

The RSS Scraper service is responsible for:
- Fetching RSS feeds from configured sources
- Parsing RSS content to extract articles
- Storing raw RSS data and extracted articles in the database
- Providing status updates on fetch operations

## Features

- **Concurrent Feed Processing**: Handles multiple RSS feeds efficiently
- **Error Handling**: Robust error handling with retry mechanisms  
- **Content Deduplication**: Prevents duplicate articles using content hashing
- **Status Tracking**: Tracks feed fetch status and timing
- **Daemon Mode**: Runs continuously in the background
- **One-shot Mode**: Run once for testing or cron jobs

## Usage

### Development Mode
```bash
# Run once for testing
uv run python main.py --once

# Run as daemon
uv run python main.py --daemon

# Run with debug logging
uv run python main.py --daemon --log-level DEBUG
```

### Integration with Backend

The scraper communicates with the backend API:
- `GET /api/internal/feeds/pending` - Get feeds that need fetching
- `POST /api/internal/feeds/{id}/status` - Update feed fetch status
- `POST /api/internal/articles` - Create new articles

## Configuration

The scraper uses the following configuration:
- Backend API URL: `http://localhost:8000` (configurable)
- Fetch interval: Determined by individual feed settings
- Request timeout: 30 seconds
- Retry attempts: Configurable per feed

## Logging

Logs are written to both console and `scraper.log` file:
- INFO: Normal operations and status updates
- WARNING: Non-fatal issues (parsing errors, etc.)
- ERROR: Fetch failures and other errors
- DEBUG: Detailed processing information

## Dependencies

- `requests`: HTTP client for fetching RSS feeds
- `feedparser`: RSS/Atom feed parsing
- `sqlalchemy`: Database ORM (future direct DB access)
- `psycopg2-binary`: PostgreSQL adapter
- `schedule`: Task scheduling utilities
- `python-dateutil`: Date parsing utilities