#!/bin/bash

# XVPN Docker Image Optimization Script
# Version: 1.0
# Author: XVPN Team
# Description: Script to optimize Docker images for XVPN with uv

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
XVPN_DIR="/opt/xvpn"
DOCKERFILE_DIR="$XVPN_DIR/docker"
BUILDER_CACHE_DIR="$XVPN_DIR/.docker-cache"
REGISTRY="${REGISTRY:-localhost:5000}"
IMAGE_PREFIX="${IMAGE_PREFIX:-xvpn}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11-slim}"
ALPINE_VERSION="${ALPINE_VERSION:-3.19}"

# Logging function
log() {
    echo -e "$1"
}

# Error handling
error_exit() {
    log "${RED}❌ Error: $1${NC}"
    exit 1
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error_exit "Docker is not installed"
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    error_exit "Docker daemon is not running"
fi

# Create cache directory
mkdir -p "$BUILDER_CACHE_DIR"

log "${BLUE}🚀 Starting XVPN Docker image optimization...${NC}"

# Function to build optimized Docker image
build_optimized_image() {
    local service_name=$1
    local dockerfile=$2
    local context=$3
    
    log "${BLUE}📦 Building optimized image for $service_name...${NC}"
    
    # Build argument optimization
    local build_args=(
        "--build-arg" "PYTHON_VERSION=$PYTHON_VERSION"
        "--build-arg" "ALPINE_VERSION=$ALPINE_VERSION"
        "--build-arg" "UV_CACHE_DIR=/tmp/uv-cache"
    )
    
    # Cache optimization
    local cache_from=()
    if [ -f "$BUILDER_CACHE_DIR/$service_name-cache.tar" ]; then
        cache_from=("--cache-from" "type=local,src=$BUILDER_CACHE_DIR/$service_name-cache.tar")
        log "${YELLOW}📂 Using cache for $service_name${NC}"
    fi
    
    # Build with multi-stage optimization
    docker buildx build \
        --file "$dockerfile" \
        --tag "$REGISTRY/$IMAGE_PREFIX-$service_name:latest" \
        --tag "$REGISTRY/$IMAGE_PREFIX-$service_name:$(date +%Y%m%d)" \
        --platform linux/amd64,linux/arm64 \
        --target runtime \
        --progress=plain \
        "${build_args[@]}" \
        "${cache_from[@]}" \
        --output "type=docker,push=false" \
        "$context"
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Successfully built $service_name image${NC}"
        
        # Save cache for next build
        docker save "$REGISTRY/$IMAGE_PREFIX-$service_name:latest" | \
            gzip > "$BUILDER_CACHE_DIR/$service_name-cache.tar"
        log "${GREEN}💾 Cache saved for $service_name${NC}"
    else
        error_exit "Failed to build $service_name image"
    fi
}

# Function to optimize base image
optimize_base_image() {
    log "${BLUE}🏗️ Optimizing base image...${NC}"
    
    # Create optimized base Dockerfile
    cat > "$DOCKERFILE_DIR/Dockerfile.base" << EOF
# Multi-stage build for optimal image size
FROM python:$PYTHON_VERSION-alpine$ALPINE_VERSION as base

# Install minimal dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -S xvpn && adduser -S xvpn -G xvpn

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:\$PATH"

# Install Python dependencies with uv
COPY pyproject.toml /app/
WORKDIR /app

# Install dependencies
RUN uv pip install --system --no-cache-dir -e .

# Copy application code
COPY --from=builder /app /app

# Switch to non-root user
USER xvpn

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8443/health || exit 1

# Expose port
EXPOSE 8443

# Run with uvx
CMD ["uvx", "run", "--app", "server.api.main:app"]
EOF

    log "${GREEN}✅ Base image optimized${NC}"
}

# Function to create multi-arch build
build_multi_arch() {
    local service_name=$1
    
    log "${BLUE}🏗️ Building multi-arch image for $service_name...${NC}"
    
    # Create buildx builder if not exists
    if ! docker buildx inspect xvpn-builder &> /dev/null; then
        docker buildx create --name xvpn-builder --use
    fi
    
    # Build for multiple architectures
    docker buildx build \
        --file "$DOCKERFILE_DIR/Dockerfile.$service_name" \
        --tag "$REGISTRY/$IMAGE_PREFIX-$service_name:latest" \
        --tag "$REGISTRY/$IMAGE_PREFIX-$service_name:$(date +%Y%m%d)" \
        --platform linux/amd64,linux/arm64 \
        --progress=plain \
        --push \
        "$DOCKERFILE_DIR/../"
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Successfully built multi-arch $service_name image${NC}"
    else
        error_exit "Failed to build multi-arch $service_name image"
    fi
}

# Function to optimize Docker layer caching
optimize_layer_caching() {
    log "${BLUE}🗂️ Optimizing Docker layer caching...${NC}"
    
    # Create .dockerignore file
    cat > "$XVPN_DIR/.dockerignore" << EOF
.git
.gitignore
README.md
*.md
*.log
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*,cover
*.cover
.git
.mypy_cache
.pytest_cache
.hypothesis
.venv
.env
.DS_Store
.vscode
.idea
*.swp
*.swo
*~
EOF

    log "${GREEN}✅ Docker layer caching optimized${NC}"
}

# Function to optimize Docker Compose
optimize_docker_compose() {
    log "${BLUE}⚡ Optimizing docker-compose.yml...${NC}"
    
    # Create optimized docker-compose.yml
    cat > "$XVPN_DIR/docker-compose.optimized.yml" << EOF
# XVPN Docker Compose Optimized Configuration
version: '3.8'

services:
  # === XVPN API Service ===
  xvpn-api:
    image: $REGISTRY/$IMAGE_PREFIX-api:latest
    container_name: xvpn-api-optimized
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=false
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=sqlite:////data/xvpn.db
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - xvpn-data:/data:ro
      - xvpn-config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    depends_on:
      - redis
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # === XVPN Agent Service ===
  xvpn-agent:
    image: $REGISTRY/$IMAGE_PREFIX-agent:latest
    container_name: xvpn-agent-optimized
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - DATABASE_URL=sqlite:////data/agent.db
      - MANIFEST_URL=http://xvpn-api:8443/transports/manifest.json
      - HEALTH_URL=http://xvpn-api:8443/mcp/v1/vpn.health
    volumes:
      - xvpn-data:/data:ro
      - xvpn-config:/config:ro
      - uv-cache:/tmp/uv-cache
      - agent-knowledge:/app/server/agent/knowledge:ro
    networks:
      - xvpn-network
    depends_on:
      - xvpn-api
      - redis
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 128M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/mcp/v1/vpn.health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # === XVPN Bot Service ===
  xvpn-bot:
    image: $REGISTRY/$IMAGE_PREFIX-bot:latest
    container_name: xvpn-bot-optimized
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - BOT_CONFIG_FILE=/config/bot.json
      - API_BASE_URL=http://xvpn-api:8443
    volumes:
      - xvpn-config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    depends_on:
      - xvpn-api
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.25'
        reservations:
          memory: 64M
          cpus: '0.1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/mcp/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # === XVPN Worker Service ===
  xvpn-worker:
    image: $REGISTRY/$IMAGE_PREFIX-worker:latest
    container_name: xvpn-worker-optimized
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
      - WORKER_COUNT=2
    volumes:
      - xvpn-data:/data:ro
      - xvpn-config:/config:ro
      - uv-cache:/tmp/uv-cache
    networks:
      - xvpn-network
    depends_on:
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/mcp/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # === Redis Cache ===
  redis:
    image: redis:7-alpine
    container_name: xvpn-redis-optimized
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
      - ./config/redis.conf:/etc/redis/redis.conf:ro
    networks:
      - xvpn-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'

volumes:
  xvpn-data:
    driver: local
  xvpn-config:
    driver: local
  redis-data:
    driver: local
  uv-cache:
    driver: local
  agent-knowledge:
    driver: local

networks:
  xvpn-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

    log "${GREEN}✅ Docker Compose optimized${NC}"
}

# Function to analyze image sizes
analyze_image_sizes() {
    log "${BLUE}📊 Analyzing image sizes...${NC}"
    
    # Get image sizes
    echo "📦 Image Size Analysis:"
    echo "================================="
    
    # List all xvpn images
    docker images | grep "$IMAGE_PREFIX" | while read -r line; do
        local image_name=$(echo $line | awk '{print $1}')
        local image_tag=$(echo $line | awk '{print $2}')
        local image_size=$(echo $line | awk '{print $7}')
        local image_size_raw=$(echo $line | awk '{print $5}')
        
        echo "📋 $image_name:$image_tag"
        echo "   Size: $image_size ($image_size_raw)"
        echo ""
    done
}

# Function to cleanup old images
cleanup_old_images() {
    log "${BLUE}🧹 Cleaning up old images...${NC}"
    
    # Keep only last 5 versions
    docker images | grep "$IMAGE_PREFIX" | awk '{print $1":"$2}' | sort -u | tail -n +6 | xargs -r docker rmi
    
    # Remove dangling images
    docker image prune -f
    
    log "${GREEN}✅ Cleanup completed${NC}"
}

# Main script logic
case "${1:-help}" in
    optimize-base)
        optimize_base_image
        ;;
    build-api)
        build_optimized_image "api" "$DOCKERFILE_DIR/Dockerfile.api" "$DOCKERFILE_DIR/../"
        ;;
    build-agent)
        build_optimized_image "agent" "$DOCKERFILE_DIR/Dockerfile.agent" "$DOCKERFILE_DIR/../"
        ;;
    build-bot)
        build_optimized_image "bot" "$DOCKERFILE_DIR/Dockerfile.bot" "$DOCKERFILE_DIR/../"
        ;;
    build-worker)
        build_optimized_image "worker" "$DOCKERFILE_DIR/Dockerfile.worker" "$DOCKERFILE_DIR/../"
        ;;
    build-all)
        build_optimized_image "api" "$DOCKERFILE_DIR/Dockerfile.api" "$DOCKERFILE_DIR/../"
        build_optimized_image "agent" "$DOCKERFILE_DIR/Dockerfile.agent" "$DOCKERFILE_DIR/../"
        build_optimized_image "bot" "$DOCKERFILE_DIR/Dockerfile.bot" "$DOCKERFILE_DIR/../"
        build_optimized_image "worker" "$DOCKERFILE_DIR/Dockerfile.worker" "$DOCKERFILE_DIR/../"
        ;;
    multi-arch)
        build_multi_arch "api"
        build_multi_arch "agent"
        build_multi_arch "bot"
        build_multi_arch "worker"
        ;;
    cache)
        optimize_layer_caching
        ;;
    compose)
        optimize_docker_compose
        ;;
    analyze)
        analyze_image_sizes
        ;;
    cleanup)
        cleanup_old_images
        ;;
    full)
        log "${BLUE}🚀 Starting full optimization...${NC}"
        optimize_base_image
        optimize_layer_caching
        optimize_docker_compose
        build_all
        analyze_image_sizes
        cleanup_old_images
        ;;
    help|*)
        echo "XVPN Docker Optimization Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  optimize-base      - Optimize base image"
        echo "  build-api          - Build API service image"
        echo "  build-agent        - Build Agent service image"
        echo "  build-bot          - Build Bot service image"
        echo "  build-worker       - Build Worker service image"
        echo "  build-all          - Build all service images"
        echo "  multi-arch         - Build multi-arch images"
        echo "  cache              - Optimize layer caching"
        echo "  compose            - Optimize docker-compose.yml"
        echo "  analyze            - Analyze image sizes"
        echo "  cleanup            - Cleanup old images"
        echo "  full               - Run full optimization"
        echo "  help               - Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  REGISTRY           - Docker registry (default: localhost:5000)"
        echo "  IMAGE_PREFIX       - Image prefix (default: xvpn)"
        echo "  PYTHON_VERSION     - Python version (default: 3.11-slim)"
        echo "  ALPINE_VERSION     - Alpine version (default: 3.19)"
        ;;
esac

log "${GREEN}🎉 Docker optimization completed!${NC}"