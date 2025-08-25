#!/usr/bin/env bash

# NewsFrontier Development Environment Startup Script
# This script sets up and runs all services needed for development

set -e  # Exit on any error

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
elif [ -f ".env.template" ]; then
    echo "Warning: .env file not found. Please copy .env.template to .env and configure your settings."
    echo "Using default values from template for development..."
    export $(grep -v '^#' .env.template | grep -v '^$' | xargs)
else
    echo "Warning: No .env or .env.template file found. Using hardcoded defaults."
fi

# Set default values if environment variables are not set
export DATABASE_URL=${DATABASE_URL:-"postgresql://newsfrontier:dev_password@localhost:5432/newsfrontier_db"}
export DB_PASSWORD=${DB_PASSWORD:-"dev_password"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}
export EMBEDDING_DIMENSION=${EMBEDDING_DIMENSION:-1536}

echo "🚀 Starting NewsFrontier Development Environment..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    print_step "Cleaning up background processes..."
    
    # Kill any existing services
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "python.*main.py.*daemon" 2>/dev/null || true
    pkill -f "newsfrontier-db" 2>/dev/null || true
    
    # Stop Docker container but don't remove it (for reuse)
    docker stop newsfrontier-db 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Function to restore debug data
restore_debug_data() {
    print_step "Restoring debug data..."
    
    # Check if debug restore file exists
    if [ -f "scripts/latest_debug_restore.sql" ]; then
        print_step "Found debug restore file, importing data..."
        
        # Extract database credentials from environment
        DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p' || echo "newsfrontier_db")
        DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p' || echo "newsfrontier")
        
        # Wait a bit more for database to be fully ready
        sleep 2
        
        # Import debug data
        if docker exec -i newsfrontier-db psql -U "$DB_USER" -d "$DB_NAME" < "scripts/latest_debug_restore.sql"; then
            print_status "Debug data imported successfully"
            
            # Show import statistics
            echo ""
            echo "📊 Debug Data Import Statistics:"
            echo "================================="
            
            # Count records in each table
            for table in rss_feeds rss_subscriptions rss_fetch_records rss_items_metadata; do
                count=$(docker exec newsfrontier-db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $table;" | tr -d ' ')
                echo "  • $table: $count records"
            done
            
            # Show processing status distribution
            echo ""
            echo "📋 Processing Status Distribution:"
            docker exec newsfrontier-db psql -U "$DB_USER" -d "$DB_NAME" -t -c "
                SELECT '  • ' || processing_status || ': ' || COUNT(*) 
                FROM rss_items_metadata 
                GROUP BY processing_status 
                ORDER BY processing_status;
            " | grep -v "^$"
            echo ""
            
        else
            print_error "Failed to import debug data"
            print_warning "Continuing with fresh database initialization"
        fi
    else
        print_warning "No debug restore file found at scripts/latest_debug_restore.sql"
        print_warning "Run 'python scripts/db_dump_debug.py' first to create debug dump"
        print_warning "Continuing with fresh database initialization"
    fi
}

# Function to completely cleanup including removing containers
full_cleanup() {
    local restore_debug="${1:-}"
    
    print_step "Performing full cleanup (removing containers)..."
    
    # Kill any existing services
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "python.*main.py.*daemon" 2>/dev/null || true
    pkill -f "newsfrontier-db" 2>/dev/null || true
    
    # Stop and remove Docker containers
    docker stop newsfrontier-db 2>/dev/null || true
    docker rm newsfrontier-db 2>/dev/null || true

    sudo rm -rf data
    mkdir data
    
    print_status "Full cleanup completed"
    
    # Check if --restore-debug flag is provided
    if [[ "$restore_debug" == "--restore-debug" ]]; then
        print_step "Starting database for debug data restore..."
        start_database_for_restore
        restore_debug_data
        print_status "Database with debug data is ready"
        echo ""
        echo "🔧 Debug Mode Active:"
        echo "  • Database contains restored debug data"
        echo "  • rss_items_metadata processing_status reset to 'pending'"
        echo "  • Ready for debugging postprocess pipeline"
        echo ""
    fi
}

# Function to create test users
create_test_users() {
    print_step "Creating test users..."
    
    # Check if Python script exists
    if [ ! -f "scripts/create-test-users.py" ]; then
        print_error "create-test-users.py not found"
        return 1
    fi
    
    # Check if backend directory exists (needed for user creation)
    if [ ! -d "backend" ]; then
        print_warning "Backend directory not found, skipping user creation"
        return 1
    fi
    
    # Run user creation script with retries using backend's environment
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if uv run --project scripts python scripts/create-test-users.py; then
            print_status "Test users created successfully"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_warning "Failed to create test users after $max_attempts attempts"
            print_warning "You may need to create users manually"
            return 1
        fi
        
        print_warning "Attempt $attempt failed, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
}

# Function to start database for restore (simplified version without user creation)
start_database_for_restore() {
    print_step "Starting PostgreSQL database for debug data restore..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed. Please install Docker first."
        exit 1
    fi
    
    # Extract database credentials from environment
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p' || echo "newsfrontier_db")
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p' || echo "newsfrontier")
    
    print_step "Creating new PostgreSQL container with pgvector extension"
    
    # Generate init.sql with correct embedding dimension
    print_step "Generating init.sql with embedding dimension: ${EMBEDDING_DIMENSION:-1536}"
    uv run --project scripts python scripts/generate-init-sql.py
    
    # Create new PostgreSQL container
    docker run -d --name newsfrontier-db \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -p 5432:5432 \
        -v "$(pwd)/data:/var/lib/postgresql/data" \
        -v "$(pwd)/scripts/init.sql:/docker-entrypoint-initdb.d/init.sql" \
        pgvector/pgvector:pg17

    # extra waiting time
    sleep 8
    
    print_status "PostgreSQL container created and started"
    
    # Wait for database to be ready
    print_step "Waiting for database to be ready..."
    
    # Test database connection
    max_attempts=30
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker exec newsfrontier-db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            print_status "Database is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Database failed to start after $max_attempts attempts"
            exit 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo ""
}

# Function to start PostgreSQL with pgvector
start_database() {
    print_step "Starting PostgreSQL database with pgvector extension..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed. Please install Docker first."
        exit 1
    fi
    
    # Extract database credentials from environment
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p' || echo "newsfrontier_db")
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p' || echo "newsfrontier")
    
    # Check if container already exists
    if docker ps -a --format "{{.Names}}" | grep -q "^newsfrontier-db$"; then
        print_step "Found existing container 'newsfrontier-db'"
        
        # Check if it's running
        if docker ps --format "{{.Names}}" | grep -q "^newsfrontier-db$"; then
            print_status "Container 'newsfrontier-db' is already running"
        else
            print_step "Starting existing container 'newsfrontier-db'"
            docker start newsfrontier-db
            print_status "Existing PostgreSQL container started"
        fi
    else
        print_step "Creating new PostgreSQL container with pgvector extension"
        
        # Generate init.sql with correct embedding dimension
        print_step "Generating init.sql with embedding dimension: ${EMBEDDING_DIMENSION:-1536}"
        uv run --project scripts python scripts/generate-init-sql.py
        
        # Create new PostgreSQL container
        docker run -d --name newsfrontier-db \
            -e POSTGRES_DB="$DB_NAME" \
            -e POSTGRES_USER="$DB_USER" \
            -e POSTGRES_PASSWORD="$DB_PASSWORD" \
            -p 5432:5432 \
            -v "$(pwd)/data:/var/lib/postgresql/data" \
            -v "$(pwd)/scripts/init.sql:/docker-entrypoint-initdb.d/init.sql" \
            pgvector/pgvector:pg17

        # extra waiting time
        sleep 5
        
        print_status "New PostgreSQL container created and started"
    fi
    
    # Wait for database to be ready
    print_step "Waiting for database to be ready..."
    sleep 1
    
    # Test database connection
    max_attempts=30
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if docker exec newsfrontier-db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            print_status "Database is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Database failed to start after $max_attempts attempts"
            exit 1
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo ""
    
    # Create test users
    create_test_users
}

# Function to start backend API server
start_backend() {
    print_step "Starting Backend API server (FastAPI)..."
    
    cd backend
    
    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        print_step "Installing backend dependencies..."
        uv sync
    else
        print_step "Updating backend dependencies (including lib)..."
        uv sync --reinstall-package newsfrontier-lib
    fi
    
    # Export environment variables for backend
    export DATABASE_URL="$DATABASE_URL"
    export JWT_SECRET="${JWT_SECRET:-your-dev-jwt-secret}"
    export LLM_API_KEY="${LLM_API_KEY:-your-llm-api-key}"
    export LLM_API_URL="${LLM_API_URL:-https://api.openai.com/v1}"
    export EMBEDDING_API_URL="${EMBEDDING_API_URL:-https://api.openai.com/v1}"
    
    # Start backend server in background with logging
    print_status "Starting FastAPI server on http://localhost:8000"
    LOG_LEVEL_LOWER=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')
    uv run --project . uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level "${LOG_LEVEL_LOWER:-debug}" --access-log 2>&1 | tee server.log &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait a moment for server to start
    sleep 3
    
    # Test backend health
    if curl -f http://localhost:8000/api/system/health >/dev/null 2>&1; then
        print_status "Backend API server is running"
    else
        print_warning "Backend server might not be fully ready yet"
    fi
}

# Function to start frontend development server
start_frontend() {
    print_step "Starting Frontend development server (Next.js)..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_step "Installing frontend dependencies..."
        pnpm install
    fi
    
    # Export environment variables for frontend
    export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
    export NEXTJS_HOST="${NEXTJS_HOST:-localhost}"
    export NEXTJS_PORT="${NEXTJS_PORT:-3000}"
    
    # Start frontend server in background
    print_status "Starting Next.js server on http://$NEXTJS_HOST:$NEXTJS_PORT"
    pnpm run dev -H $NEXTJS_HOST -p $NEXTJS_PORT &
    FRONTEND_PID=$!
    
    cd ..
    
    sleep 3
    print_status "Frontend development server is running"
}

# Function to start scraper service
start_scraper() {
    print_step "Starting RSS Scraper service..."
    
    cd scraper
    
    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        print_step "Installing scraper dependencies..."
        uv sync
    fi
    
    # Export environment variables for scraper
    export DATABASE_URL="$DATABASE_URL"
    export DEFAULT_RSS_INTERVAL="${DEFAULT_RSS_INTERVAL:-60}"
    export SCRAPER_CONCURRENT_FEEDS="${SCRAPER_CONCURRENT_FEEDS:-5}"
    export LOG_LEVEL="$LOG_LEVEL"
    
    # Start scraper in daemon mode with logging
    print_status "Starting RSS scraper (daemon mode)"
    uv run python main.py --daemon 2>&1 | tee scraper.log &
    SCRAPER_PID=$!
    
    cd ..
    
    sleep 2
    print_status "RSS Scraper service is running"
}

# Function to start postprocess service
start_postprocess() {
    print_step "Starting AI PostProcess service..."
    
    cd postprocess
    
    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        print_step "Installing postprocess dependencies..."
        uv sync
    else
        print_step "Updating backend dependencies (including lib)..."
        uv sync --reinstall-package newsfrontier-lib
    fi
    
    # Export environment variables for postprocess
    export DATABASE_URL="$DATABASE_URL"
    export LLM_API_KEY="${LLM_API_KEY:-your-llm-api-key}"
    export LLM_API_URL="${LLM_API_URL:-https://api.openai.com/v1}"
    export LLM_MODEL_SUMMARY="${LLM_MODEL_SUMMARY:-gpt-3.5-turbo}"
    export EMBEDDING_API_URL="${EMBEDDING_API_URL:-https://api.openai.com/v1}"
    export EMBEDDING_MODEL="${EMBEDDING_MODEL:-text-embedding-ada-002}"
    export POSTPROCESS_BATCH_SIZE="${POSTPROCESS_BATCH_SIZE:-10}"
    export MAX_PROCESSING_ATTEMPTS="${MAX_PROCESSING_ATTEMPTS:-3}"
    export LOG_LEVEL="$LOG_LEVEL"
    
    # Start postprocess in daemon mode with logging
    print_status "Starting AI postprocess service (daemon mode)"
    uv run main.py --daemon 2>&1 | tee postprocess.log &
    POSTPROCESS_PID=$!
    
    cd ..
    
    sleep 2
    print_status "AI PostProcess service is running"
}

# Function to display service status
show_status() {
    echo ""
    echo "🎉 NewsFrontier Development Environment is Ready!"
    echo "================================================="
    echo ""
    echo "📊 Service Status:"
    echo "  • Database (PostgreSQL): http://localhost:5432"
    echo "  • Backend API:           http://localhost:8000"
    echo "  • Frontend Web App:      http://$NEXTJS_HOST:NEXTJS_PORT"
    echo "  • API Documentation:     http://localhost:8000/docs"
    echo "  • RSS Scraper:           Running in background"
    echo "  • AI PostProcess:        Running in background"
    echo ""
    echo "🔧 Development URLs:"
    echo "  • API Health Check:      curl http://localhost:8000/api/system/health"
    echo "  • API Stats:             curl http://localhost:8000/api/system/stats"
    echo "  • Swagger UI:            http://localhost:8000/docs"
    echo "  • ReDoc:                 http://localhost:8000/redoc"
    echo ""
    echo "👥 Test Users:"
    echo "  • admin/admin            Administrator account"
    echo "  • test/test              Regular user account"
    echo ""
    echo "📝 Logs:"
    echo "  • Backend logs:          tail -f backend/server.log"
    echo "  • Frontend logs:         Check terminal output"
    echo "  • Scraper logs:          tail -f scraper/scraper.log"
    echo "  • PostProcess logs:      tail -f postprocess/postprocess.log"
    echo ""
    echo "⚡ To stop all services: Press Ctrl+C or run: scripts/dev.sh --cleanup"
    echo "🗑️  To completely remove containers: scripts/dev.sh --full-cleanup"
    echo ""
}

# Function to wait for user interrupt
wait_for_interrupt() {
    print_status "All services are running. Press Ctrl+C to stop..."
    
    # Trap Ctrl+C
    trap 'echo ""; print_step "Shutting down all services..."; cleanup; sleep 1; exit 0' INT
    
    # Keep script running
    while true; do
        sleep 5
        
        # Optional: Check if services are still running and restart if needed
        if ! pgrep -f "uvicorn main:app" > /dev/null; then
            print_warning "Backend server appears to have stopped"
        fi
        
        if ! pgrep -f "pnpm run dev" > /dev/null; then
            print_warning "Frontend server appears to have stopped"
        fi
    done
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            echo "NewsFrontier Development Environment Setup"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --help, -h               Show this help message"
            echo "  --no-db                  Skip database setup (use existing)"
            echo "  --backend-only           Start only backend services"
            echo "  --cleanup                Stop all services (keeps containers for reuse)"
            echo "  --full-cleanup           Stop all services and remove containers"
            echo "  --full-cleanup --restore-debug  Full cleanup then restore debug data"
            echo ""
            echo "Debug data management:"
            echo "  1. Export current data:   python scripts/db_dump_debug.py"
            echo "  2. Clean and restore:     ./scripts/dev.sh --full-cleanup --restore-debug"
            echo "  3. Or restore manually:   psql -d newsfrontier_db -f scripts/debug_dump/latest_debug_restore.sql"
            echo ""
            exit 0
            ;;
        --cleanup)
            cleanup
            exit 0
            ;;
        --full-cleanup)
            # Check if --restore-debug is the second argument
            if [[ "${2:-}" == "--restore-debug" ]]; then
                full_cleanup "--restore-debug"
            else
                full_cleanup
            fi
            exit 0
            ;;
    esac
    
    # Cleanup any existing processes first
    cleanup
    
    # Start services in order
    if [[ "${1:-}" != "--no-db" ]]; then
        start_database
    fi
    
    start_backend
    
    if [[ "${1:-}" != "--backend-only" ]]; then
        start_frontend
        start_scraper
        start_postprocess
    fi
    
    # Show status
    show_status
    
    # Wait for user to stop
    wait_for_interrupt
}

# Run main function with all arguments
main "$@"
