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

# Install dependencies for scraper workspace member
RUN uv sync --frozen --package newsfrontier-scraper

# Set working directory to scraper
WORKDIR /app/scraper

# Create logs directory
RUN mkdir -p /app/logs

# Health check - check if the process is running
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

# Run the application in daemon mode
CMD ["uv", "run", "python", "main.py", "--daemon"]
