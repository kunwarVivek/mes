# Quick Reference Guide

## Project Structure

```
unison/
├── backend/              # FastAPI + DDD
│   ├── app/
│   │   ├── domain/      # Business logic
│   │   ├── application/ # Use cases
│   │   ├── infrastructure/  # Tech implementations
│   │   └── presentation/    # API endpoints
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/            # React + Tailwind + ShadCN
│   ├── src/
│   │   ├── components/ui/  # ShadCN components
│   │   ├── stores/        # Zustand stores
│   │   ├── schemas/       # Zod validation
│   │   ├── services/      # API clients
│   │   ├── hooks/         # TanStack Query
│   │   └── pages/         # Views
│   ├── package.json
│   └── Dockerfile
│
├── database/            # Migrations & seeds
├── docker-compose.yml   # All services
└── *.md                 # Documentation
```

## Key Files

### Backend
- `app/main.py` - FastAPI app entry point
- `app/core/config.py` - Settings (DB, Redis, JWT)
- `app/core/database.py` - SQLAlchemy setup
- `app/infrastructure/security/jwt_handler.py` - JWT operations
- `app/infrastructure/security/casbin_enforcer.py` - RBAC
- `app/infrastructure/tasks/celery_app.py` - Celery config

### Frontend
- `src/main.tsx` - React entry point
- `src/lib/api-client.ts` - Axios with interceptors
- `src/stores/auth.store.ts` - Auth state
- `tailwind.config.js` - Tailwind configuration
- `src/index.css` - Global styles + Tailwind

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token

### Users (Protected)
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user (requires admin)

### Health
- `GET /health` - Health check

## Environment Variables

### Backend (.env)
```bash
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=unison
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | Database |
| redis | 6379 | Celery broker |
| backend | 8000 | FastAPI API |
| celery_worker | - | Background tasks |
| frontend | 5173 | React app |
| pgadmin | 5050 | DB management |

## Common Commands

### Development
```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# Stop everything
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback
docker-compose exec backend alembic downgrade -1

# Access database
docker-compose exec postgres psql -U postgres -d unison
```

### Backend
```bash
# Run tests
docker-compose exec backend pytest

# Access Python shell
docker-compose exec backend python

# Install new package
docker-compose exec backend pip install package-name
# Then add to requirements.txt
```

### Frontend
```bash
# Install dependencies
cd frontend && npm install

# Start dev server (outside Docker)
npm run dev

# Build production
npm run build

# Lint code
npm run lint

# Add new package
npm install package-name
```

### Celery
```bash
# View active tasks
docker-compose exec celery_worker celery -A app.infrastructure.tasks.celery_app inspect active

# View registered tasks
docker-compose exec celery_worker celery -A app.infrastructure.tasks.celery_app inspect registered

# Purge all tasks
docker-compose exec celery_worker celery -A app.infrastructure.tasks.celery_app purge
```

## Testing Locally

### Create Test User
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!",
    "is_active": true
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'
```

### Use Token
```bash
TOKEN="your-access-token-here"

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users/
```

## Troubleshooting

### Database Connection Error
```bash
# Check if Postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Redis Connection Error
```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Celery Not Processing Tasks
```bash
# Check worker status
docker-compose ps celery_worker

# View worker logs
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker
```

### Frontend Not Loading
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check frontend logs
docker-compose logs frontend

# Rebuild node_modules
cd frontend && rm -rf node_modules && npm install
```

## Key Documentation

- `ARCHITECTURE.md` - Detailed architecture guide
- `DEVELOPER_GUIDE.md` - How to add features
- `IMPLEMENTATION_COMPLETE.md` - Full tech stack integration
- `REFACTORING_SUMMARY.md` - Original refactoring details
- `README.md` - Project overview
