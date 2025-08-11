# NewsFrontier AI PostProcess Service

AI-powered post-processing service for the NewsFrontier news aggregation platform.

## Overview

The AI PostProcess service is responsible for:
- Analyzing article content and extracting topics
- Generating embeddings for semantic search and similarity matching
- Creating article summaries and derivatives
- Extracting named entities and keywords
- Clustering related articles based on content similarity
- Performing sentiment analysis and readability scoring

## Features

- **Content Analysis**: Extracts topics, entities, and keywords from articles
- **Embedding Generation**: Creates vector embeddings for semantic search
- **Summarization**: Generates concise summaries of long articles
- **Sentiment Analysis**: Analyzes emotional tone of content
- **Topic Clustering**: Groups related articles together
- **Daemon Mode**: Runs continuously processing new articles
- **One-shot Mode**: Processes pending articles once

## Usage

### Environment Setup

First, configure the required environment variables:

```bash
# Required: Google AI API configuration
export LLM_API_URL="https://generativelanguage.googleapis.com/v1beta/openai/"  # Google Gemini API URL
export LLM_API_KEY="your-api-key-here"  # Your Google API key
export GOOGLE_API_KEY="your-api-key-here"  # Google API key for Gemini models
export LLM_MODEL_SUMMARY="gemini-2.0-flash-lite"  # Fast model for summarization
export LLM_MODEL_ANALYSIS="gemini-2.5-pro"  # Capable model for analysis
export EMBEDDING_MODEL="gemini-embedding-001"  # Model for embeddings
export EMBEDDING_DIMENSION="768"  # Gemini embedding dimensions

# Optional: Backend configuration
export BACKEND_URL="http://localhost:8000"  # NewsFrontier backend URL

# For local development, copy .env.template to .env and configure
```

### Development Mode
```bash
# Test with mock data (great for debugging)
uv run python main.py --test --log-level DEBUG

# Run once for testing
uv run python main.py --once

# Run as daemon
uv run python main.py --daemon

# Run with debug logging
uv run python main.py --daemon --log-level DEBUG

# Override backend URL
uv run python main.py --test --backend-url http://localhost:3000
```

### Integration with Backend

The postprocessor communicates with the backend API:
- `GET /api/internal/articles/pending` - Get articles that need processing
- `POST /api/internal/articles/{id}/process` - Update article with processing results
- Store embeddings, summaries, and analysis metadata

## Processing Pipeline

1. **Content Analysis**
   - Extract topics using NLP techniques
   - Identify named entities (people, places, organizations)
   - Generate keywords and phrases
   - Analyze sentiment and readability

2. **Embedding Generation**
   - Create 768-dimensional vector embeddings
   - Use Google gemini-embedding-001 for high-quality embeddings
   - Store embeddings for similarity search and clustering

3. **Derivative Creation**
   - Generate article summaries
   - Create different content views
   - Extract key quotes and highlights

4. **Clustering & Relations**
   - Find similar articles using embeddings
   - Create topic clusters
   - Identify trending themes

## Configuration

The postprocessor uses the following configuration:
- Backend API URL: `http://localhost:8000` (configurable)
- Processing interval: 2 minutes between cycles
- Embedding dimensions: 768 (Gemini embedding compatible)
- Batch size: Process articles individually with small delays
- AI Models: Gemini-2.0-Flash-Lite for summaries, Gemini-2.5-Pro for analysis
- Image Generation: Imagen-3.0-Generate-002 for cover images

## AI Services Integration

### Google AI (Gemini) Integration
The postprocessor uses Google AI services for advanced content processing:
- **Text Analysis**: AI-powered topic extraction and content analysis using Gemini models
- **Article Summarization**: Intelligent summarization using Gemini-2.0-Flash-Lite for fast processing
- **Advanced Analysis**: Complex clustering and daily summaries using Gemini-2.5-Pro
- **Vector Embeddings**: High-quality embeddings using gemini-embedding-001 (768 dimensions)
- **Event Clustering**: Context-aware clustering decisions with LLM-based logic
- **Daily Summaries**: Personalized daily news summaries with structured markdown output
- **Cover Image Generation**: AI-generated image descriptions using Imagen models

### Compatible Services
- **Google AI**: Official Google Gemini API (gemini-2.0-flash-lite, gemini-2.5-pro, etc.)
- **OpenAI Compatible**: Any service providing OpenAI-compatible endpoints via LLM_API_URL
- **Local Deployments**: Ollama, text-generation-webui, vLLM with OpenAI-compatible APIs
- **Custom Models**: Any service providing chat completion and embedding APIs

### Features
- **Intelligent Processing**: Real AI analysis when API keys are provided
- **Graceful Degradation**: Fallback to keyword-based analysis when AI is unavailable
- **Token Management**: Automatic text truncation to respect API token limits
- **Error Recovery**: Robust error handling with automatic fallbacks
- **Debug Support**: Detailed logging and test mode for development

## Logging

Logs are written to both console and `postprocess.log` file:
- INFO: Normal processing operations and statistics
- WARNING: Non-fatal issues (missing content, API errors)
- ERROR: Processing failures and system errors
- DEBUG: Detailed analysis and embedding information

## Dependencies

- `requests`: HTTP client for backend API communication
- `numpy`: Numerical operations for embeddings and clustering
- `scikit-learn`: Machine learning utilities for clustering analysis
- `google-generativeai`: Google AI API client for Gemini models
- `fastapi`: Internal API server for service communication
- `uvicorn`: ASGI server for FastAPI application
- `boto3`: AWS S3 client for cover image storage
- `newsfrontier-lib`: Shared library for database operations and AI utilities
- `sqlalchemy`: Database ORM for direct database access
- `psycopg2-binary`: PostgreSQL adapter with pgvector support
- `pgvector`: Vector similarity operations

## Performance

- Processes articles individually to avoid memory issues
- Uses batching for embedding generation when possible
- Implements caching for repeated content analysis
- Monitors processing times and success rates

## Development Notes

### Current Implementation (✓ Complete)
- **Real AI Integration**: Uses OpenAI library for actual AI processing
- **Environment Configuration**: Configurable via environment variables
- **Fallback Methods**: Graceful degradation when AI services are unavailable
- **Test Mode**: Built-in test mode with mock data for debugging
- **Token Management**: Intelligent text truncation for API limits
- **Error Recovery**: Robust error handling and retry mechanisms
- **Debug Support**: Comprehensive logging and configuration display

### Key Features
- **Dual-Mode Operation**: Uses AI when available, falls back to basic methods otherwise
- **Production Ready**: Real OpenAI integration with proper error handling
- **Developer Friendly**: Test mode, debug logging, and environment validation
- **Flexible Configuration**: Support for OpenAI, local deployments, and custom APIs

### Testing and Debugging
```bash
# Test with mock data to verify AI integration
uv run python main.py --test --log-level DEBUG

# Check environment configuration
uv run python main.py --test | head -20

# Test without API keys (fallback mode)
unset LLM_API_KEY && uv run python main.py --test
```

## AI Prompt Testing

### Prompt Testing Suite

The postprocess service includes a comprehensive testing framework for AI prompts located in the `test_prompts/` directory:

#### Available Test Scripts

1. **`test_summary_creation.py`** - Test article summarization prompt effectiveness
2. **`test_cluster_detection.py`** - Test event clustering decision prompt logic  
3. **`test_daily_summary.py`** - Test daily summary generation prompt quality
4. **`test_cover_image_generation.py`** - Test cover image description generation prompt

#### Unified Testing Interface

**`run_prompt_tests.sh`** - Convenient shell wrapper for all prompt tests:

```bash
# View usage help
./test_prompts/run_prompt_tests.sh --help

# Test all prompts with sample data
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh all --sample

# Test specific prompts
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh summary --sample
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh cluster --article-id 123
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh daily --user-id 1
GOOGLE_API_KEY=your_key ./test_prompts/run_prompt_tests.sh cover --summary-id 456
```

#### Individual Test Usage

```bash
# Test article summarization
uv run test_prompts/test_summary_creation.py --sample
uv run test_prompts/test_summary_creation.py --article-id 123

# Test clustering detection  
uv run test_prompts/test_cluster_detection.py --sample --user-id 1
uv run test_prompts/test_cluster_detection.py --article-id 456 --user-id 2

# Test daily summary generation
uv run test_prompts/test_daily_summary.py --sample
uv run test_prompts/test_daily_summary.py --user-id 1 --date 2024-01-15

# Test cover image description
uv run test_prompts/test_cover_image_generation.py --sample
uv run test_prompts/test_cover_image_generation.py --summary-id 789
```

### Testing Features

The prompt testing framework provides:
- **Built-in Sample Data**: Test without database connectivity using realistic examples
- **Real Data Integration**: Fetch actual articles, users, and summaries from database
- **Multiple Test Scenarios**: Different test cases for each prompt type
- **Detailed Output**: Comprehensive results showing input, processing, and output
- **Performance Monitoring**: Execution time and resource usage tracking
- **Error Analysis**: Clear error reporting and debugging information
- **Prompt Transparency**: Display actual prompts sent to AI services

### Environment Setup

Set required environment variables:
```bash
export GOOGLE_API_KEY=your_google_api_key_here
export LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export EMBEDDING_MODEL=gemini-embedding-001
export EMBEDDING_DIMENSION=768
```