#!/usr/bin/env bash

# NewsFrontier Development Environment Stop Script

echo "🛑 Stopping NewsFrontier Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

# Stop all processes
print_step "Stopping backend server..."
pkill -f "uvicorn main:app" 2>/dev/null || true

print_step "Stopping frontend server..."
pkill -f "npm run dev\|pnpm.*dev" 2>/dev/null || true

print_step "Stopping scraper service..."
pkill -f "python.*main.py.*daemon" 2>/dev/null || true

print_step "Stopping postprocess service..."
pkill -f "python.*main.py.*daemon" 2>/dev/null || true

print_step "Stopping database..."
docker stop newsfrontier-db 2>/dev/null || true
docker rm newsfrontier-db 2>/dev/null || true

print_status "All services stopped successfully!"