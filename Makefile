# Wiener Linien Live Map - Docker Makefile

.PHONY: help build up down logs clean test status restart

# Default target
help:
	@echo "🐳 Wiener Linien Live Map - Docker Commands"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@echo "  build     - Build the Docker image"
	@echo "  up        - Start the application"
	@echo "  down      - Stop the application"
	@echo "  restart   - Restart the application"
	@echo "  logs      - View application logs"
	@echo "  status    - Check container status"
	@echo "  test      - Run Docker tests"
	@echo "  clean     - Clean up Docker resources"
	@echo "  shell     - Access container shell"
	@echo ""

# Build the Docker image
build:
	@echo "🔨 Building Docker image..."
	docker-compose build

# Start the application
up:
	@echo "🚀 Starting Wiener Linien Live Map..."
	docker-compose up -d
	@echo "✅ Application started at http://localhost:3080"

# Stop the application
down:
	@echo "🛑 Stopping application..."
	docker-compose down
	@echo "✅ Application stopped"

# Restart the application
restart: down up

# View logs
logs:
	@echo "📋 Viewing application logs..."
	docker-compose logs -f

# Check status
status:
	@echo "📊 Container status:"
	docker-compose ps
	@echo ""
	@echo "🔍 Health check:"
	@curl -s http://localhost:3080/api/status || echo "❌ Application not responding"

# Run tests
test:
	@echo "🧪 Running Docker tests..."
	python test_docker.py

# Clean up
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup completed"

# Access container shell
shell:
	@echo "🐚 Accessing container shell..."
	docker-compose exec wiener-linien-app bash

# Development mode (with rebuild)
dev:
	@echo "🔧 Starting in development mode..."
	docker-compose up --build -d
	@echo "✅ Development environment ready at http://localhost:3080"

# Production mode
prod:
	@echo "🏭 Starting in production mode..."
	docker-compose -f docker-compose.yml up -d
	@echo "✅ Production environment ready at http://localhost:3080" 