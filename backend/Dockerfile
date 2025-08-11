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

# Install dependencies for backend workspace member
RUN uv sync --frozen --package newsfrontier-backend

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]