# COMPREHENSIVE BACKEND ARCHITECTURE ANALYSIS

## Executive Summary

The Unison MES (Manufacturing Execution System) backend is a Python-based FastAPI application implementing **Clean Architecture** principles with clear separation of concerns. It uses PostgreSQL as the database with Row-Level Security (RLS) for multi-tenant data isolation, and includes 240+ Python files organized across 8 architectural layers.

**Tech Stack:**
- FastAPI 0.104.1 (REST API Framework)
- SQLAlchemy 2.0.23 (ORM)
- PostgreSQL with TimescaleDB, PGMQ, and advanced extensions
- JWT-based authentication with organization/plant context
- MinIO for S3-compatible file storage
- Celery for async task processing
- Casbin for RBAC (Role-Based Access Control)

---

## 1. DIRECTORY STRUCTURE

### Root Backend Directory
```
/home/user/mes/backend/
├── app/                          # Main application code (240 Python files)
├── database/                      # Database schemas and migrations
├── migrations/                    # Alembic migration versions
├── scripts/                       # Utility scripts (pg_cron, etc.)
├── tests/                         # Test suite
├── alembic.ini                   # Alembic config
├── requirements.txt              # Python dependencies
└── Dockerfile                    # Container configuration
```

### Core Application Structure (`/app/`)
```
app/
├── main.py                       # FastAPI application entry point
├── __init__.py
├── core/                         # Core configuration & database setup
├── domain/                       # Domain layer (business logic)
├── application/                  # Application layer (use cases & services)
├── infrastructure/               # Infrastructure layer (adapters, persistence)
├── presentation/                 # Presentation layer (API endpoints, middleware)
├── models/                       # SQLAlchemy ORM models (30 model files)
└── schemas/                      # Pydantic schemas
```

---

## 2. SCHEMA & DATABASE CONFIGURATION

### Location: `/home/user/mes/backend/database/schema/`

#### Core Schema Files:
1. **00_extensions.sql** - PostgreSQL extension setup
   - `uuid-ossp`: UUID generation
   - `timescaledb`: Time-series data optimization
   - `pgcrypto`: Encryption functions
   - `pg_trgm`: Fuzzy text search

2. **01_core.sql** - Foundation tables (100+ lines)
   - `organizations` (top-level multi-tenant boundary)
   - `users` (system users with org/plant affiliation)
   - `plants` (manufacturing sites)
   - `departments` (functional units within plants)
   - All tables include indexes and RLS-ready design

3. **init_schema.sql** - Master initialization script
   - Orchestrates schema creation
   - Includes execution steps for all 14 schema modules
   - References to materials, production, quality, machines, projects, RBAC, etc.

### Migrations

**Location:** `/home/user/mes/backend/migrations/versions/`

- **Active Migrations:**
  - `001_initial_schema.py` - Bootstrap schema
  - `env.py` - Alembic environment configuration

- **Archived Migrations** (consolidated into monolithic schema):
  - Multi-tenancy tables (organizations)
  - Projects table
  - RBAC (Role-Based Access Control)
  - Logistics module tables
  - Configuration & workflow engine
  - Quality enhancement
  - Reporting and dashboards
  - Infrastructure (audit, notifications, settings, files, SAP)
  - Traceability (lots, serials)
  - White-label branding

### Database Connection

**File:** `/home/user/mes/backend/app/core/database.py`

```python
# SQLAlchemy Engine Setup
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Session Dependency with RLS Context Management
def get_db(request: Request = None) -> Generator[Session, None, None]:
    # Automatically sets RLS context from JWT claims
    # Sets: app.current_organization_id, app.current_plant_id
```

---

## 3. SQLALCHEMY MODELS (ORM Layer)

**Location:** `/home/user/mes/backend/app/models/`

**30 Model Files (6,312 total lines):**

1. **Core Models:**
   - User, Organization, Plant, Department

2. **Production Models:**
   - Machine, WorkOrder, WorkCenterShift, ProductionLog, Lane

3. **Materials & BOM:**
   - Material, BOM, Costing

4. **Quality Management:**
   - Quality, Inspection, NCR (Non-Conformance Report)

5. **Maintenance & Operations:**
   - Maintenance, Shift

6. **Advanced Features:**
   - Project, ProjectManagement, Role, Workflow
   - Logistics, Branding, CustomField
   - Traceability, QualityEnhancement, Reporting
   - Infrastructure, Currency, OperationConfig

**Example Model Structure:**
```python
class UnitOfMeasure(Base):
    __tablename__ = "unit_of_measure"
    id = Column(Integer, primary_key=True, index=True)
    uom_code = Column(String(10), unique=True, nullable=False, index=True)
    dimension = Column(Enum(DimensionType), nullable=False)
    conversion_factor = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

---

## 4. API ROUTES & ENDPOINTS

**Location:** `/home/user/mes/backend/app/presentation/api/v1/`

### API Router Configuration
**File:** `/home/user/mes/backend/app/presentation/api/v1/__init__.py`

**17+ API Routers Mounted:**

| Router | Prefix | Tags | Endpoint Count |
|--------|--------|------|-----------------|
| auth | /api/v1/auth | authentication | login, refresh token |
| users | /api/v1/users | users | CRUD operations |
| roles | /api/v1/roles | rbac | Role management |
| custom_fields | /api/v1 | configuration | Custom field management |
| workflows | /api/v1 | workflow-engine | Workflow operations |
| logistics | /api/v1 | logistics | Shipment, barcode management |
| reporting | /api/v1 | reporting | Report generation |
| organizations | /api/v1/organizations | organizations | Org management |
| plants | /api/v1/plants | plants | Plant management |
| departments | /api/v1/departments | departments | Department management |
| materials | /api/v1/materials | materials | Material master data |
| machines | /api/v1/machines | machines | Machine catalog |
| quality | /api/v1 | quality | Quality metrics |
| shifts | /api/v1/shifts | shifts | Shift scheduling |
| production_logs | /api/v1/production-logs | production-logs | Production tracking |
| bom | /api/v1/bom | bom | Bill of Materials |
| maintenance | /api/v1 | maintenance | Maintenance tasks |
| branding | /api/v1 | branding | White-label customization |
| infrastructure | /api/v1 | infrastructure | System configuration |
| metrics | /api/v1/metrics | metrics | Dashboard metrics |

### Example Endpoint Implementations

**Authentication (`auth.py`):**
- `POST /api/v1/auth/login` - User login with JWT generation
- `POST /api/v1/auth/refresh` - Refresh access token

**BOM Management (`bom.py`):**
- `POST /api/v1/bom` - Create BOM
- `GET /api/v1/bom` - List BOMs
- `GET /api/v1/bom/{bom_id}` - Get BOM details
- `PUT /api/v1/bom/{bom_id}` - Update BOM
- `POST /api/v1/bom/{bom_id}/lines` - Add BOM line
- `GET /api/v1/bom/{bom_id}/tree` - Get hierarchical BOM structure

**Branding (`branding.py`):**
- `POST /branding/organizations` - Create organization branding
- `GET /branding/organizations/{branding_id}` - Get branding config
- `GET /branding/organizations/by-org/{organization_id}` - Get org branding
- `PATCH /branding/organizations/{branding_id}` - Update branding
- `GET /branding/organizations/{organization_id}/logo` - Get logo URLs
- `GET /branding/organizations/{organization_id}/feature/{feature_name}` - Feature toggle

**Custom Fields (`custom_fields.py`):**
- `POST /` - Create custom field
- `GET /` - List custom fields
- `GET /{field_id}` - Get field details
- `PUT /{field_id}` - Update field
- `DELETE /{field_id}` - Delete field
- `GET /entity/{entity_type}/{entity_id}/values` - Get field values for entity

---

## 5. MIDDLEWARE & AUTHENTICATION

**Location:** `/home/user/mes/backend/app/presentation/middleware/`

### Middleware Stack (Execution Order)

1. **RequestIDMiddleware** (First)
   - Generates unique request IDs
   - Enables request tracking and correlation

2. **AuthMiddleware** (Second)
   - JWT token extraction from Authorization header
   - Token validation via JWTHandler
   - Stores user context in `request.state.user`
   - Public endpoints bypass authentication
   - Sets multi-tenant context (organization_id, plant_id)

3. **RateLimitMiddleware** (Third)
   - Rate limiting enforcement
   - Prevents API abuse

4. **CORSMiddleware** (FastAPI)
   - Configured for localhost:3000, localhost:5173
   - Credentials enabled

### JWT Authentication Implementation

**File:** `/home/user/mes/backend/app/infrastructure/security/jwt_handler.py`

```python
class JWTHandler:
    """JWT Token Handler - Infrastructure service for JWT operations"""
    
    def create_access_token(data: Dict[str, Any]) -> str
        # Claims: sub (user_id), email, organization_id, plant_id
        # Expiration: 30 minutes (configurable)
        # Type: "access"
    
    def create_refresh_token(data: Dict[str, Any]) -> str
        # Type: "refresh"
        # Expiration: 7 days
    
    def decode_token(token: str) -> Dict[str, Any]
        # Validates signature and expiration
        # Returns payload with all claims
    
    def verify_token(token: str) -> bool
```

**Token Payload Structure:**
```json
{
  "sub": "user_id",              // Subject (user ID)
  "email": "user@example.com",   // User email
  "organization_id": 1,           // Tenant ID (REQUIRED for RLS)
  "plant_id": 2,                  // Optional plant assignment
  "exp": 1234567890,              // Expiration timestamp
  "iat": 1234567860,              // Issued at timestamp
  "type": "access"                // Token type (access/refresh)
}
```

### Security Dependencies

**File:** `/home/user/mes/backend/app/infrastructure/security/dependencies.py`

```python
# Dependency Injection for Authentication

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT access token
    Extracts tenant context (organization_id, plant_id)
    Sets PostgreSQL session variables for RLS enforcement
    Returns authenticated User entity
    """
    # Sets session variables:
    # - app.current_organization_id (REQUIRED)
    # - app.current_plant_id (OPTIONAL)
    _set_rls_context(db, organization_id, plant_id)
    return user

async def get_current_superuser(current_user: User) -> User:
    """Requires superuser/admin access"""

async def get_current_active_user(current_user: User) -> User:
    """Ensures user account is active"""
```

### Public Endpoints (No Authentication Required)

```python
PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/*/auth/*",  # Login, refresh token endpoints
}
```

---

## 6. CORE CONFIGURATION

**File:** `/home/user/mes/backend/app/core/config.py`

### Settings Class (Pydantic)

```python
class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "Unison API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL Connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "unison"
    POSTGRES_PASSWORD: str = "unison_dev_password"
    POSTGRES_DB: str = "unison_erp"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str  # Auto-constructed from above
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]
    
    # Message Queue (PGMQ)
    PGMQ_QUEUE_PREFIX: str = "unison"
    PGMQ_RETRY_COUNT: int = 3
    PGMQ_VISIBILITY_TIMEOUT: int = 30
    
    # Object Storage (MinIO)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "unison-storage"
    MINIO_SECURE: bool = False
    
    # Email Service
    EMAIL_PROVIDER: Literal["smtp", "sendgrid", "aws_ses"] = "smtp"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # SendGrid Configuration
    SENDGRID_API_KEY: str = ""
    
    # AWS SES Configuration
    AWS_SES_REGION: str = "us-east-1"
    AWS_SES_ACCESS_KEY: str = ""
    AWS_SES_SECRET_KEY: str = ""
    
    # Multi-Currency Support
    DEFAULT_CURRENCY: str = "USD"
    EXCHANGE_RATE_API_KEY: str = ""
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"
    
    # Row-Level Security (RLS)
    RLS_ENABLED: bool = True
    RLS_AUDIT_LOG_ENABLED: bool = True
    
    # JWT Configuration
    SECRET_KEY: str = "dev-secret-key-..."  # Min 32 chars in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Validation
    @field_validator('SECRET_KEY')
    def validate_secret_key(v: str) -> str:
        # Enforces minimum 32-character length for production
        # Prevents default values in non-dev environments
```

### Configuration Loading

- **Priority:** Environment variables > .env file > class defaults
- **Case Sensitive:** True
- **Extra Fields:** Ignored (strict validation)

**Environment File:** `.env` (not in repo, use `.env.example`)

---

## 7. CLEAN ARCHITECTURE LAYERS

### Layer 1: Presentation (API & Middleware)
**Location:** `/app/presentation/`

```
presentation/
├── api/
│   ├── v1/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── materials.py
│   │   ├── machines.py
│   │   ├── quality.py
│   │   ├── shifts.py
│   │   ├── maintenance.py
│   │   ├── organizations.py
│   │   ├── plants.py
│   │   ├── departments.py
│   │   ├── projects.py
│   │   ├── production_logs.py
│   │   ├── lanes.py
│   │   ├── bom.py
│   │   ├── roles.py
│   │   ├── custom_fields.py
│   │   ├── workflows.py
│   │   ├── logistics.py
│   │   ├── reporting.py
│   │   ├── project_management.py
│   │   ├── traceability.py
│   │   ├── branding.py
│   │   ├── infrastructure.py
│   │   └── metrics.py
│   └── __init__.py (Router aggregation)
└── middleware/
    ├── auth_middleware.py         # JWT validation & RLS context
    ├── request_id_middleware.py   # Request correlation IDs
    ├── rate_limit_middleware.py   # API rate limiting
    └── __init__.py
```

**Responsibility:** Convert HTTP requests to application layer calls, return responses

### Layer 2: Application (DTOs, Use Cases, Services)
**Location:** `/app/application/`

```
application/
├── dtos/                          # Data Transfer Objects (24 files)
│   ├── user_dto.py
│   ├── auth_dto.py
│   ├── material_dto.py
│   ├── production_log_dto.py
│   ├── bom_dto.py
│   ├── quality_dto.py
│   ├── maintenance_dto.py
│   ├── workflow_dto.py
│   └── ... (20+ more)
├── use_cases/                     # Business logic orchestration
│   ├── user/
│   │   ├── create_user.py
│   │   ├── get_user.py
│   │   ├── update_user.py
│   │   └── delete_user.py
│   └── auth/
│       ├── login_user.py
│       └── refresh_token.py
└── services/                      # Business services (20+ files)
    ├── email_service.py
    ├── production_scheduling_service.py
    ├── material_search_service.py
    ├── barcode_service.py
    ├── rbac_service.py
    ├── reporting_service.py
    ├── mrp_service.py
    ├── logistics_service.py
    ├── workflow_service.py
    ├── custom_field_service.py
    ├── branding_service.py
    ├── infrastructure_service.py
    └── ... (10+ more)
```

**Responsibility:** Orchestration of use cases, data transformation, business rule enforcement

### Layer 3: Domain (Business Rules & Entities)
**Location:** `/app/domain/`

```
domain/
├── entities/                      # Business entities (25 files)
│   ├── user.py
│   ├── material.py
│   ├── machine.py
│   ├── work_order.py
│   ├── production_log.py
│   ├── project.py
│   ├── shift.py
│   ├── token.py
│   └── ... (17+ more)
├── repositories/                  # Repository interfaces
│   └── user_repository.py
├── services/                      # Domain services (8 files)
│   ├── bom_service.py
│   ├── bom_effectivity_service.py
│   ├── capacity_calculator.py
│   ├── lot_sizing_service.py
│   ├── scheduling_strategy_service.py
│   ├── operation_scheduling_service.py
│   ├── shift_calendar_service.py
│   └── currency/
│       ├── currency_service.py
│       └── exchange_rate_repository.py
├── value_objects/                 # Immutable value objects
│   ├── email.py
│   └── username.py
├── exceptions/                    # Domain exceptions
│   └── domain_exception.py
└── __init__.py
```

**Responsibility:** Pure business logic, validation rules, domain-driven design

### Layer 4: Infrastructure (Adapters, Persistence, External Services)
**Location:** `/app/infrastructure/`

```
infrastructure/
├── database/
│   ├── rls.py                     # Row-Level Security context management
│   └── __init__.py
├── security/
│   ├── jwt_handler.py             # JWT token operations
│   ├── dependencies.py            # Auth dependency injection
│   ├── rbac_dependencies.py       # RBAC enforcement
│   └── casbin_enforcer.py         # Casbin policy enforcement
├── persistence/
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── user_repository_impl.py    # User persistence
│   ├── mappers/
│   │   ├── user_mapper.py         # Entity <-> Model mapping
│   │   └── __init__.py
│   └── __init__.py
├── repositories/                  # Repository implementations (22 files)
│   ├── user_repository.py (should be in persistence)
│   ├── material_repository.py
│   ├── machine_repository.py
│   ├── production_log_repository.py
│   ├── project_repository.py
│   ├── work_order_repository.py
│   ├── shift_repository.py
│   ├── quality_enhancement_repository.py
│   ├── workflow_repository.py
│   ├── custom_field_repository.py
│   ├── branding_repository.py
│   ├── infrastructure_repository.py
│   └── ... (10+ more)
├── adapters/
│   ├── sap/                       # SAP integration adapter
│   │   ├── config.py
│   │   ├── sap_client.py
│   │   ├── material_adapter.py
│   │   ├── inventory_adapter.py
│   │   ├── costing_adapter.py
│   │   ├── models.py
│   │   └── exceptions.py
│   └── __init__.py
├── storage/
│   ├── minio_client.py            # MinIO S3-compatible storage
│   ├── barcode_storage_service.py # Barcode file storage
│   └── __init__.py
├── messaging/
│   ├── pgmq_client.py             # PostgreSQL Message Queue
│   ├── pgmq_tasks.py              # Async task definitions
│   └── __init__.py
├── search/
│   ├── pg_search_service.py       # PostgreSQL full-text search
│   ├── search_config.py
│   └── examples.py
├── email/
│   ├── config.py                  # Email configuration
│   ├── templates/                 # Email templates directory
│   └── README.md
├── tasks/
│   ├── celery_app.py              # Celery task queue setup
│   ├── user_tasks.py              # Example user tasks
│   └── __init__.py
└── utilities/
    └── __init__.py
```

**Responsibility:** External service integration, database access, file storage, messaging

### Layer 5: Core (Configuration & Extensions)
**Location:** `/app/core/`

```
core/
├── config.py                      # Settings & configuration
├── database.py                    # SQLAlchemy setup & session management
├── extensions.py                  # PostgreSQL extension verification
└── __init__.py
```

**Responsibility:** Application-level configuration, database setup, extension management

---

## 8. INFRASTRUCTURE SERVICES

### 8.1 Database Row-Level Security (RLS)

**File:** `/app/infrastructure/database/rls.py`

```python
def set_rls_context(db: Session, organization_id: int, plant_id: int = None):
    """Set PostgreSQL session variables for tenant isolation"""
    db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))
    if plant_id is not None:
        db.execute(text(f"SET LOCAL app.current_plant_id = {plant_id}"))

def clear_rls_context(db: Session):
    """Clear RLS context after transaction"""
    db.execute(text("RESET app.current_organization_id"))
    db.execute(text("RESET app.current_plant_id"))
```

**RLS Scope:** 53+ policies across 28+ tables for multi-tenant data isolation

### 8.2 File Storage (MinIO)

**File:** `/app/infrastructure/storage/minio_client.py`

**Features:**
- S3-compatible object storage
- Automatic bucket creation
- Retry logic for network failures (max 3 attempts)
- Organized folder structure: `{org_id}/{entity_type}/{entity_id}/{filename}`
- Presigned URL generation for secure file access
- Connection pooling via urllib3

**Configuration:** MinIO endpoint, credentials, bucket name from settings

### 8.3 Messaging & Async Tasks

**PostgreSQL Message Queue (PGMQ):**
- File: `/app/infrastructure/messaging/pgmq_client.py`
- 30K messages/second throughput
- Queue prefix: "unison"
- Configurable retry count and visibility timeout
- Replaces external message broker (e.g., RabbitMQ)

**Celery Task Queue:**
- File: `/app/infrastructure/tasks/celery_app.py`
- Redis backend for task state management
- Example user tasks: email notifications, async processing
- Can be transitioned to PGMQ for unified queue architecture

### 8.4 Full-Text Search

**PostgreSQL Search Service:**
- File: `/app/infrastructure/search/pg_search_service.py`
- BM25 full-text search algorithm
- Replaces Elasticsearch for cost efficiency
- Integrates with `pg_search` extension
- Material search indexing example included

**Configuration:** Search config with ranking, filters, pagination

### 8.5 Email Service

**Pluggable Email Providers:**
- File: `/app/infrastructure/email/config.py`
- Supported providers: SMTP, SendGrid, AWS SES
- Abstract interface for provider implementation
- Email templates directory: `/app/infrastructure/email/templates/`

**Configuration:**
- Provider selection via `EMAIL_PROVIDER` setting
- SMTP: Host, port, TLS, authentication
- SendGrid: API key configuration
- AWS SES: Region, access key, secret key

### 8.6 SAP Integration

**SAP Adapter:**
- Location: `/app/infrastructure/adapters/sap/`
- Components:
  - `sap_client.py` - HTTP client for SAP API communication
  - `material_adapter.py` - Material master data sync
  - `inventory_adapter.py` - Inventory management integration
  - `costing_adapter.py` - Cost data integration
  - `config.py` - SAP connection parameters
  - `models.py` - Data structures
  - `exceptions.py` - Error handling

### 8.7 Storage (MinIO)

**Barcode Storage Service:**
- File: `/app/infrastructure/storage/barcode_storage_service.py`
- Stores generated barcodes (images) to MinIO
- Organized by organization and entity type
- Retrievable via presigned URLs for secure download

---

## 9. DEPENDENCY INJECTION

### Key Dependency Patterns

**Repository Dependency:**
```python
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection for UserRepository"""
    return UserRepository(db)
```

**Authentication Dependency:**
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Validates JWT and returns authenticated user"""
```

**Database Session Dependency:**
```python
def get_db(request: Request = None) -> Generator[Session, None, None]:
    """Session with automatic RLS context management"""
```

---

## 10. ERROR HANDLING & EXCEPTIONS

**Domain Exceptions:**
- Location: `/app/domain/exceptions/`
- Custom exception hierarchy for validation, business rules, not found errors
- Examples: `DomainValidationException`, `EntityNotFoundException`, `DuplicateEntityException`

**HTTP Exception Mapping:**
- Domain exceptions mapped to HTTP status codes (400, 404, 409, 500)
- Consistent error response format with detail messages

---

## 11. DATA MODELS OVERVIEW

### Total Models: 30 SQLAlchemy ORM Models

**Production Domain:**
- Machines, Work Orders, Work Center Shifts, Production Logs, Lanes

**Materials & Planning:**
- Materials, BOMs, Costing, MRP Planning, Lot Sizing

**Quality:**
- Quality Records, Inspections, NCRs (Non-Conformance Reports)

**Organization:**
- Organization, Plant, Department, Users, Roles

**Advanced Modules:**
- Projects, Maintenance, Shifts, Workflows, Custom Fields
- Logistics (Shipments, Barcodes), Reporting, Traceability
- Branding (White-label), Infrastructure (Audit, Notifications, Settings)
- Currency Management

---

## 12. KEY FEATURES IMPLEMENTED

### Authentication & Authorization
- JWT-based stateless authentication
- Multi-tenant context embedding in tokens
- Row-Level Security (RLS) for data isolation
- RBAC via Casbin policy enforcement
- Superuser and active user verification

### Multi-Tenancy
- Organization-level isolation
- Plant-level optional segmentation
- RLS policies enforce tenant boundaries
- JWT claims carry org/plant context

### Data Integrity
- Cascading deletes at foreign key boundaries
- Unique constraints (email, username, org-specific codes)
- Timestamp tracking (created_at, updated_at)
- Soft deletes via is_active flags (where applicable)

### Extensibility
- Custom fields framework for entity attribute extension
- Pluggable email providers (SMTP, SendGrid, AWS SES)
- Adapter pattern for external system integration (SAP)
- Abstract interfaces for storage, messaging, search

### Performance Optimizations
- Database connection pooling
- Indexed queries on common filter columns
- Pagination support in list endpoints
- TimescaleDB for time-series data compression
- Full-text search with BM25 ranking
- PGMQ for high-throughput messaging (30K msgs/sec)

---

## 13. PROJECT STRUCTURE SUMMARY TABLE

| Component | Location | Purpose | Count |
|-----------|----------|---------|-------|
| API Routes | `/presentation/api/v1/` | REST endpoints | 17+ routers |
| Middleware | `/presentation/middleware/` | Request processing | 3 middleware |
| DTOs | `/application/dtos/` | Data transfer | 24 files |
| Use Cases | `/application/use_cases/` | Orchestration | 6+ files |
| Services | `/application/services/` | Business logic | 20+ files |
| Domain Entities | `/domain/entities/` | Business objects | 25 files |
| Domain Services | `/domain/services/` | Domain logic | 8 files |
| Value Objects | `/domain/value_objects/` | Immutable values | 2 files |
| ORM Models | `/models/` | Database mapping | 30 files |
| Repositories | `/infrastructure/repositories/` | Data access | 22+ files |
| Security | `/infrastructure/security/` | Auth & RBAC | 4 files |
| Adapters | `/infrastructure/adapters/sap/` | External systems | 8 files |
| Storage | `/infrastructure/storage/` | File management | 3 files |
| Messaging | `/infrastructure/messaging/` | Async processing | 2 files |
| Search | `/infrastructure/search/` | Full-text search | 3 files |
| Email | `/infrastructure/email/` | Email service | 2 files |
| **Total Python Files** | `/app/` | Full backend | **240+** |

---

## 14. ENTRY POINT

**File:** `/home/user/mes/backend/app/main.py`

```python
from fastapi import FastAPI
from app.core.config import settings
from app.presentation.api import api_router
from app.presentation.middleware import (
    AuthMiddleware,
    RequestIDMiddleware,
    RateLimitMiddleware,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Middleware added in reverse execution order
app.add_middleware(CORSMiddleware, ...)      # Executes last
app.add_middleware(RateLimitMiddleware)      # 3rd
app.add_middleware(AuthMiddleware)           # 2nd
app.add_middleware(RequestIDMiddleware)      # Executes first

# Mount all API routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Runtime
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 15. RUNTIME & DEPLOYMENT

**Python Version:** 3.10+ (inferred from async/await syntax)

**Key Dependencies (requirements.txt):**
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- sqlalchemy==2.0.23
- psycopg2-binary==2.9.9 (PostgreSQL driver)
- alembic==1.12.1 (Database migrations)
- PyJWT==2.8.0 (JWT operations)
- passlib[bcrypt]==1.7.4 (Password hashing)
- casbin==1.36.2 (RBAC)
- celery[redis]==5.3.4 (Task queue)
- tembo-pgmq-python==0.10.0 (Message queue)
- minio==7.2.0 (Object storage)
- sendgrid==6.11.0 (Email service)
- boto3==1.34.0 (AWS services)
- python-barcode==0.15.1 (Barcode generation)
- qrcode[pil]==7.4.2 (QR code generation)

**Docker:**
- Dockerfile: `/home/user/mes/backend/Dockerfile`
- Exposed port: 8000 (default FastAPI)
- Environment: Development/Production via .env

---

## 16. CONFIGURATION FILES & DOCUMENTATION

### Quick Reference Guides:
- `/backend/BOM_API_QUICK_REFERENCE.md` - BOM operations guide
- `/backend/LANE_SCHEDULING_QUICK_REFERENCE.md` - Lane scheduling
- `/backend/MAINTENANCE_QUICK_REFERENCE.md` - Maintenance operations
- `/backend/JWT_TENANT_CONTEXT_USAGE_GUIDE.md` - JWT and tenant context
- `/backend/app/core/EXTENSIONS_QUICKREF.md` - PostgreSQL extensions reference
- `/backend/app/domain/entities/SHIFT_MODULE_README.md` - Shift management

### Infrastructure Documentation:
- `/backend/app/infrastructure/email/README.md` - Email service
- `/backend/app/infrastructure/messaging/README.md` - Message queue
- `/backend/app/infrastructure/search/README.md` - Full-text search
- `/backend/database/schema/README.md` - Schema documentation

---

## CONCLUSION

The Unison MES backend is a **production-ready, enterprise-grade manufacturing execution system** built with:

✓ Clean architecture for maintainability and testability  
✓ Multi-tenant data isolation via Row-Level Security  
✓ JWT-based stateless authentication  
✓ Comprehensive API covering all manufacturing domains  
✓ Integration with SAP for enterprise data sync  
✓ PostgreSQL-native message queue and search (no external dependencies)  
✓ Extensible design for custom fields and white-label branding  
✓ Async task processing for long-running operations  
✓ S3-compatible file storage for barcode/document management  

Total code volume: **240+ Python files** with 6,312+ lines in models alone, structured across 5 architectural layers with full RBAC, audit logging, and multi-currency support.

