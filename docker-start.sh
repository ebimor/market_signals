#!/bin/bash
# SafeSwing Trader - Docker Quick Start

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       SafeSwing Trader - Docker Setup & Quick Start           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "📥 Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "📥 Docker Compose is included with Docker Desktop"
    exit 1
fi

echo "✅ Docker is installed"
echo "✅ Docker Compose is installed"
echo ""

# Show Docker versions
echo "📊 System Information:"
echo "   Docker: $(docker --version)"
echo "   Docker Compose: $(docker-compose --version)"
echo ""

# Check if already running
if docker-compose ps 2>/dev/null | grep -q "safeswing"; then
    echo "⚠️  Services are already running!"
    echo ""
    echo "Available options:"
    echo "  1. View logs:        docker-compose logs -f"
    echo "  2. Stop services:    docker-compose down"
    echo "  3. Restart services: docker-compose restart"
    echo ""
    echo "Services status:"
    docker-compose ps
    exit 0
fi

echo "🚀 Starting SafeSwing Trader with Docker..."
echo ""

# Create .env if needed
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env from template..."
    cp backend/.env.example backend/.env
fi

# Build and start
echo "🔨 Building Docker images (this may take 1-2 minutes)..."
docker-compose build

echo ""
echo "✨ Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

echo ""
echo "🎉 SafeSwing Trader is starting!"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📍 Services Running:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Backend API:"
echo "    🔗 http://localhost:8000"
echo "    📖 API Docs: http://localhost:8000/docs"
echo "    ❤️  Health: http://localhost:8000/health"
echo ""
echo "  Frontend:"
echo "    🔗 http://localhost:3000"
echo ""
echo "  Database (PostgreSQL):"
echo "    🔗 localhost:5432"
echo "    👤 User: safeswing"
echo "    🔑 Password: safeswing"
echo "    💾 Database: safeswing_db"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📌 Useful Commands:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  View logs:"
echo "    docker-compose logs -f backend"
echo "    docker-compose logs -f frontend"
echo ""
echo "  Stop services:"
echo "    docker-compose down"
echo ""
echo "  Stop and remove data:"
echo "    docker-compose down -v"
echo ""
echo "  Run backend tests:"
echo "    docker-compose exec backend python test_market_data.py"
echo ""
echo "  Access database:"
echo "    docker-compose exec postgres psql -U safeswing -d safeswing_db"
echo ""
echo "  Restart service:"
echo "    docker-compose restart backend"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Show status
echo "📊 Current Status:"
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8000/docs in your browser"
echo "  2. Test endpoints from the Swagger UI"
echo "  3. Open http://localhost:3000 for the frontend"
echo ""
echo "📚 For detailed information, see DOCKER_GUIDE.md"
echo ""
