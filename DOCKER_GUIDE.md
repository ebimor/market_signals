# Docker Setup Guide - SafeSwing Trader

## 🐳 Running SafeSwing Trader with Docker

This guide explains how to run the entire SafeSwing Trader application stack using Docker and Docker Compose.

## Prerequisites

### Required
- **Docker**: [Install Docker Desktop](https://www.docker.com/products/docker-desktop) for your OS
- **Docker Compose**: Included with Docker Desktop

### Verify Installation
```bash
docker --version
docker-compose --version
```

## Quick Start (1 Command)

From the project root:

```bash
docker-compose up
```

That's it! The entire application will start with:
- ✅ Backend API on http://localhost:8000
- ✅ Frontend on http://localhost:3000
- ✅ PostgreSQL database on localhost:5432
- ✅ Automatic database initialization

## Services

### Backend (Python FastAPI)
- **Port**: 8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Container**: `safeswing-backend`

### Frontend (React + Vite)
- **Port**: 3000
- **Container**: `safeswing-frontend`
- **Hot Reload**: Code changes auto-refresh

### Database (PostgreSQL)
- **Port**: 5432
- **User**: safeswing
- **Password**: safeswing
- **Database**: safeswing_db
- **Container**: `safeswing-postgres`

## Common Commands

### Start All Services
```bash
docker-compose up
```

### Start in Background
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Data
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Rebuild Images
```bash
docker-compose build --no-cache
docker-compose up
```

### Run Commands in Container
```bash
# Backend
docker-compose exec backend python test_market_data.py

# Frontend
docker-compose exec frontend npm list

# Database
docker-compose exec postgres psql -U safeswing -d safeswing_db
```

## Configuration

### Environment Variables

The backend reads from `backend/.env`. Create this from the template:

```bash
cp backend/.env.example backend/.env
```

Edit as needed:
```env
API_PORT=8000
DATABASE_URL=postgresql://safeswing:safeswing@postgres:5432/safeswing_db
DEBUG=False
MARKET_DATA_REFRESH_INTERVAL=60
VIX_THRESHOLD=30.0
```

### Ports

To use different ports, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Host:Container
  frontend:
    ports:
      - "3001:3000"
  postgres:
    ports:
      - "5433:5432"
```

## Volume Mounting

### Backend Code
Code in `./backend` is mounted, so changes auto-reflect (no rebuild needed).

### Database
PostgreSQL data persists in `postgres_data` volume.

### Frontend Code
Frontend code in `./frontend/src` and `./frontend/public` is mounted.

## Accessing Services

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# Get API docs (browser)
http://localhost:8000/docs

# Get current price
curl http://localhost:8000/api/market/price/AAPL
```

### Frontend
```
http://localhost:3000
```

### Database (via psql)
```bash
docker-compose exec postgres psql -U safeswing -d safeswing_db

# Inside psql
\dt                          # List tables
SELECT * FROM stocks;        # Query stocks
\q                          # Quit
```

## Data Persistence

- **Database**: `/postgres_data` volume (survives `docker-compose down`)
- **Backend DB**: `backend/safeswing.db` (if using SQLite)
- **Logs**: Printed to console, not persisted

To completely reset data:
```bash
docker-compose down -v   # -v removes volumes
docker-compose up        # Fresh database
```

## Troubleshooting

### Port Already in Use
```bash
# Find process on port 8000
lsof -i :8000
# Or Windows: netstat -ano | findstr :8000

# Change port in docker-compose.yml
```

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose build --no-cache backend
docker-compose up backend
```

### Database Connection Error
```bash
# Restart database
docker-compose restart postgres

# Check if ready
docker-compose ps

# Wait for health check
docker-compose up postgres  # Watch for "database system is ready"
```

### Frontend Can't Connect to Backend
- Ensure backend is healthy: `curl http://localhost:8000/health`
- Check `docker-compose logs frontend`
- Verify `VITE_API_URL=http://localhost:8000` in docker-compose.yml

### Can't Find Docker
```bash
# Ensure Docker is running (Docker Desktop)
# Verify installation
docker ps
```

## Performance Tips

### Reduce Image Size
- Frontend: ~500MB
- Backend: ~600MB
- Total (with cache): ~1.5GB

### Improve Build Time
```bash
# Use BuildKit (faster)
DOCKER_BUILDKIT=1 docker-compose build

# On macOS/Linux add to ~/.bashrc or ~/.zshrc
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Memory Usage
- Backend: ~200MB
- Frontend: ~150MB
- PostgreSQL: ~100MB
- Total: ~450MB

## Development Workflow

### Making Changes

**Backend Changes**
```bash
# Code changes auto-reflect (volume mount)
# No rebuild needed, restart may help:
docker-compose restart backend
```

**Frontend Changes**
```bash
# Code changes auto-refresh via Vite HMR
# Just save the file and check browser
```

**Database Changes**
```bash
# Schema changes
docker-compose down -v
docker-compose up  # Fresh database
```

### Testing in Docker

```bash
# Run backend tests
docker-compose exec backend python test_market_data.py

# Test API
docker-compose exec backend python -c "
from market_data.data_fetcher import get_fetcher
fetcher = get_fetcher()
print(fetcher.get_current_price('AAPL'))
"

# Test database
docker-compose exec postgres psql -U safeswing -d safeswing_db -c "SELECT COUNT(*) FROM stocks;"
```

## Production Deployment

For production, modify `docker-compose.yml`:

```yaml
backend:
  environment:
    - DEBUG=False
    - DATABASE_URL=postgresql://user:pass@prod-postgres/db

frontend:
  # Add build optimization
```

## Docker Compose Reference

### File: `docker-compose.yml`
- **version**: 3.8 (supports named volumes, networks)
- **services**: 3 (backend, frontend, postgres)
- **networks**: safeswing-network (bridge)
- **volumes**: postgres_data (persistent)

### Key Features
- ✅ Health checks (60s startup wait)
- ✅ Automatic restart
- ✅ Named network (service discovery)
- ✅ Volume persistence
- ✅ Environment variables
- ✅ Port mapping

## Useful Docker Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'
alias dcs='docker-compose ps'
```

Then use:
```bash
dcu               # Start
dcl backend       # Logs
dcs               # Status
dcd               # Stop
```

## Advanced Usage

### Custom Network
```bash
docker network ls
docker network inspect safeswing-network
```

### Resource Limits
Edit `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

### Compose Override
Create `docker-compose.override.yml` for local development:

```yaml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=True
    command: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Support

For issues:
1. Check logs: `docker-compose logs service-name`
2. Verify ports: `docker-compose ps`
3. Test connectivity: `curl http://localhost:8000/health`
4. Check volumes: `docker volume ls`
5. Review this guide's Troubleshooting section

---

**Status**: ✅ Docker setup complete and tested
**Next**: Frontend development or signal engine!
