# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for package management
RUN pip install uv

# Copy workspace configuration
COPY pyproject.toml uv.lock ./

# Copy all workspace members for dependency resolution
COPY lib/ lib/
COPY backend/ backend/
COPY scraper/ scraper/
COPY postprocess/ postprocess/
COPY scripts/ scripts/

# Install dependencies for postprocess workspace member
RUN uv sync --frozen --package newsfrontier-postprocess

# Set working directory to postprocess
WORKDIR /app/postprocess

# Create logs directory
RUN mkdir -p /app/logs

# Health check - check internal API server
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/api/health', timeout=5)" || exit 1

# Run the application in daemon mode
CMD ["uv", "run", "python", "main.py", "--daemon"]