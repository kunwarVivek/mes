# Unison Tech Stack

## Backend Technologies

### Core Framework
- **FastAPI** (0.104.1) - Modern async Python web framework
- **Pydantic v2** (2.5.0) - Data validation and settings
- **Uvicorn** (0.24.0) - ASGI server

### Database & ORM
- **PostgreSQL 15** - Relational database
- **SQLAlchemy** (2.0.23) - ORM
- **Alembic** (1.12.1) - Database migrations

### Authentication & Authorization
- **PyJWT** (2.8.0) - JWT token generation/validation
- **PyCasbin** (1.36.2) - RBAC authorization
- **python-jose** (3.3.0) - Additional JWT support
- **passlib[bcrypt]** (1.7.4) - Password hashing

### Async Tasks
- **Celery** (5.3.4) - Distributed task queue
- **Redis** (5.0.1) - Message broker for Celery

### Testing
- **pytest** (7.4.3)
- **pytest-asyncio** (0.21.1)
- **httpx** (0.25.1) - HTTP client for testing

## Frontend Technologies

### Core
- **React** (18.2.0) - UI library
- **TypeScript** (5.2.2) - Type safety
- **Vite** (5.0.0) - Build tool

### UI & Styling
- **Tailwind CSS** (3.3.6) - Utility-first CSS
- **ShadCN UI** - Component library (Radix UI based)
- **Lucide React** (0.294.0) - Icons
- **class-variance-authority** (0.7.0) - Component variants

### State Management
- **Zustand** (4.4.7) - Global state
- **TanStack Query** (5.8.4) - Server state & caching
- **TanStack Router** (1.8.0) - Routing

### Validation & Forms
- **Zod** (3.22.4) - Schema validation
- **React Hook Form** (recommended, not yet added)

### HTTP Client
- **Axios** (1.6.2) - HTTP requests with interceptors

## Infrastructure

### Containerization
- **Docker** - Container runtime
- **Docker Compose** - Multi-container orchestration

### Services Running
1. PostgreSQL (5432)
2. Redis (6379)
3. Backend API (8000)
4. Celery Worker (background)
5. Frontend (5173)
6. pgAdmin (5050)

## Development Tools
- **ESLint** - JavaScript/TypeScript linting
- **PostCSS** - CSS processing
- **Autoprefixer** - CSS vendor prefixes
