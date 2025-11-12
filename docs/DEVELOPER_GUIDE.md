# Unison Manufacturing ERP - Developer Guide

**Complete Technical Documentation for Developers**

*Version 1.0 | Last Updated: 2025-11-11*

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Database Development](#database-development)
6. [Commercial Infrastructure](#commercial-infrastructure)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

**System Requirements**:
```bash
# Operating System
- Linux (Ubuntu 20.04+ recommended)
- macOS 11+
- Windows 10/11 with WSL2

# Software
- PostgreSQL 15+ with extensions (pg_cron, pg_net, TimescaleDB)
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional but recommended)
- Git

# Tools (Recommended)
- VS Code with extensions:
  - Python
  - Pylance
  - ESLint
  - Prettier
  - PostgreSQL (ckolkman.vscode-postgres)
- PostgreSQL GUI (pgAdmin, DBeaver, or TablePlus)
- Postman or Insomnia (API testing)
- Stripe CLI (for webhook testing)
```

### Development Environment Setup

#### 1. Clone Repository

```bash
git clone https://github.com/kunwarVivek/mes.git
cd mes
```

#### 2. Database Setup

```bash
# Create database
createdb unison_dev

# Install PostgreSQL extensions
psql -d unison_dev << EOF
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;
CREATE EXTENSION IF NOT EXISTS timescaledb;
EOF

# Verify extensions
psql -d unison_dev -c "\dx"
```

#### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies (pytest, black, flake8)

# Copy environment template
cp .env.example .env.development

# Edit .env.development with your configuration:
# - DATABASE_URL
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - Stripe keys (use test keys: sk_test_..., pk_test_...)

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server runs at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install  # or: pnpm install, yarn install

# Copy environment template
cp .env.example .env.development

# Edit .env.development:
VITE_API_BASE_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Start development server
npm run dev  # or: pnpm dev

# Server runs at: http://localhost:5173
```

#### 5. Verify Setup

```bash
# Backend health check
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "database": "connected"}

# Frontend: Open browser at http://localhost:5173
# Should see landing page
```

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Pages      │  │   Features   │  │ Design System│          │
│  │  (Routes)    │  │  (Domains)   │  │ (Components) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                 │
│                            │                                     │
│                      TanStack Router                             │
│                            │                                     │
│                       API Client                                 │
│                     (Axios + JWT)                                │
└──────────────────────────────│──────────────────────────────────┘
                               │
                          HTTP/REST
                               │
┌──────────────────────────────│──────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Presentation Layer                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │  API v1      │  │  Webhooks    │  │  Jobs API    │  │    │
│  │  │ (REST)       │  │  (Stripe)    │  │ (Internal)   │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Application Layer                           │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │  Use Cases   │  │   Services   │  │     DTOs     │  │    │
│  │  │  (Business)  │  │  (Analytics) │  │ (Validation) │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Domain Layer                                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │   Entities   │  │ Value Objects│  │ Repositories │  │    │
│  │  │  (Business)  │  │   (Domain)   │  │ (Interfaces) │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Infrastructure Layer                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │  Persistence │  │    Stripe    │  │    Email     │  │    │
│  │  │  (SQLAlch.)  │  │ (Payments)   │  │   (SMTP)     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────│──────────────────────────────────┘
                               │
                          SQLAlchemy
                               │
┌──────────────────────────────│──────────────────────────────────┐
│                    PostgreSQL 15+                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Tables     │  │      RLS     │  │  Extensions  │          │
│  │  (50+ tables)│  │  (Policies)  │  │  (pg_cron)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ TimescaleDB  │  │   pg_cron    │  │    pg_net    │          │
│  │ (Time-series)│  │(Sched. Jobs) │  │ (HTTP Client)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Clean Architecture Layers

**Domain Layer** (Innermost):
- Pure business logic, no dependencies
- Entities: Core business objects (Material, WorkOrder, Subscription)
- Value Objects: Immutable domain concepts (Money, DateRange)
- Repository Interfaces: Contracts for data access

**Application Layer**:
- Use Cases: Business workflows (CreateWorkOrderUseCase)
- DTOs: Data Transfer Objects for API
- Services: Cross-cutting concerns (AnalyticsService, NotificationService)

**Infrastructure Layer**:
- Persistence: Database implementations (SQLAlchemy models, repositories)
- External Services: Stripe, SMTP, S3
- Framework-specific code

**Presentation Layer** (Outermost):
- API Endpoints: FastAPI routes
- Serialization: Request/response models
- Authentication: JWT middleware

**Key Principle**: Dependencies point inward. Domain layer has zero dependencies on outer layers.

### Technology Stack Decisions

#### Why PostgreSQL-Native?

**Problem**: Traditional stack = PostgreSQL + Redis + Celery + RabbitMQ + Elasticsearch = 8-10 containers

**Solution**: PostgreSQL extensions replace all of them

| Component | Traditional | PostgreSQL-Native | Why |
|-----------|-------------|-------------------|-----|
| **Message Queue** | Celery + RabbitMQ | pg_cron + PGMQ | MSME scale: 2-5 jobs/customer << 30K msgs/sec |
| **Cache** | Redis | UNLOGGED tables | 1-2ms latency acceptable for dashboards |
| **Search** | Elasticsearch | pg_search (BM25) | 20x faster at our scale (<1M records) |
| **Time-series** | InfluxDB | TimescaleDB | 75% compression, SQL queries |
| **Scheduled Jobs** | Celery Beat | pg_cron | Native cron syntax, DB-native |

**Benefits**:
- 60% fewer containers to manage
- 40-60% lower infrastructure costs
- Single database to backup/restore
- ACID transactions across all operations
- Simpler deployment (especially on-premise)

**Trade-offs Accepted**:
- Cache latency: 1-2ms (UNLOGGED) vs <1ms (Redis) - acceptable
- Search: BM25 sufficient for MSME scale (not web-scale)
- Job throughput: 30K msgs/sec >> our needs (2-5 jobs/customer)

---

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── config/
│   │   ├── settings.py              # Environment configuration
│   │   ├── database.py              # Database connection & session
│   │   ├── pricing.py               # Subscription tier definitions
│   │   └── stripe_config.py         # Stripe configuration
│   ├── domain/                      # Domain Layer (Pure business logic)
│   │   ├── entities/                # Business entities
│   │   │   ├── material.py
│   │   │   ├── work_order.py
│   │   │   ├── subscription.py
│   │   │   └── ...
│   │   ├── value_objects/           # Immutable domain concepts
│   │   │   ├── money.py
│   │   │   ├── date_range.py
│   │   │   └── ...
│   │   └── repositories/            # Repository interfaces (ABC)
│   │       ├── material_repository.py
│   │       ├── subscription_repository.py
│   │       └── ...
│   ├── application/                 # Application Layer (Use cases)
│   │   ├── dtos/                    # Data Transfer Objects
│   │   │   ├── material_dto.py
│   │   │   ├── subscription_dto.py
│   │   │   └── ...
│   │   ├── use_cases/               # Business workflows
│   │   │   ├── material/
│   │   │   │   ├── create_material.py
│   │   │   │   └── update_material.py
│   │   │   ├── subscription/
│   │   │   │   ├── create_subscription.py
│   │   │   │   ├── upgrade_subscription.py
│   │   │   │   └── handle_stripe_webhook.py
│   │   │   └── ...
│   │   └── services/                # Cross-cutting services
│   │       ├── analytics_service.py
│   │       ├── notification_service.py
│   │       └── usage_service.py
│   ├── infrastructure/              # Infrastructure Layer
│   │   ├── persistence/
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── repositories/        # Repository implementations
│   │   │   │   ├── material_repository_impl.py
│   │   │   │   └── ...
│   │   │   └── mappers/             # Entity <-> Model mappers
│   │   ├── stripe/
│   │   │   └── stripe_client.py     # Stripe API wrapper
│   │   ├── notifications/
│   │   │   └── email_service.py     # SMTP email service
│   │   ├── security/
│   │   │   ├── auth.py              # JWT authentication
│   │   │   ├── feature_gating.py    # @require_tier decorators
│   │   │   └── permissions.py       # Role-based access control
│   │   └── jobs/
│   │       ├── job_runner.py        # Scheduled job executor
│   │       └── usage_tracker.py     # Usage tracking logic
│   └── presentation/                # Presentation Layer (API)
│       └── api/
│           └── v1/
│               ├── __init__.py      # API router registration
│               ├── materials.py     # /api/v1/materials
│               ├── work_orders.py   # /api/v1/work-orders
│               ├── subscriptions.py # /api/v1/subscriptions
│               ├── admin.py         # /api/v1/admin (platform admin)
│               ├── analytics.py     # /api/v1/analytics
│               ├── webhooks.py      # /api/v1/webhooks/stripe
│               └── jobs.py          # /api/v1/jobs (internal)
├── database/
│   ├── migrations/
│   │   ├── env.py                   # Alembic configuration
│   │   └── versions/                # Migration files
│   │       ├── 001_initial_schema.py
│   │       ├── 017_add_subscription_tables.py
│   │       ├── 019_setup_scheduled_jobs.py
│   │       └── ...
│   └── schema/                      # Manual SQL scripts (reference)
├── tests/
│   ├── unit/                        # Unit tests (domain, use cases)
│   ├── integration/                 # Integration tests (DB, API)
│   └── conftest.py                  # Pytest fixtures
├── alembic.ini                      # Alembic migration config
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Dev dependencies
├── Dockerfile                       # Production Docker image
└── .env.example                     # Environment template
```

### Adding a New Feature (Step-by-Step)

Let's add a **"Preventive Maintenance Schedule"** feature using clean architecture.

#### Step 1: Domain Layer (Pure Business Logic)

**Create Entity** (`app/domain/entities/pm_schedule.py`):

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class PMSchedule:
    """Preventive Maintenance Schedule domain entity"""
    id: Optional[int]
    equipment_id: int
    name: str
    frequency: str  # 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    interval: int
    duration_hours: float
    is_active: bool
    last_performed_at: Optional[datetime]
    next_due_at: Optional[datetime]
    created_at: datetime

    def __post_init__(self):
        """Domain validation"""
        if self.frequency not in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
            raise ValueError(f"Invalid frequency: {self.frequency}")
        if self.interval <= 0:
            raise ValueError("Interval must be positive")
        if self.duration_hours <= 0:
            raise ValueError("Duration must be positive")

    def calculate_next_due_date(self) -> datetime:
        """Calculate next due date based on frequency and interval"""
        from dateutil.relativedelta import relativedelta

        base_date = self.last_performed_at or self.created_at

        if self.frequency == 'daily':
            return base_date + timedelta(days=self.interval)
        elif self.frequency == 'weekly':
            return base_date + timedelta(weeks=self.interval)
        elif self.frequency == 'monthly':
            return base_date + relativedelta(months=self.interval)
        elif self.frequency == 'quarterly':
            return base_date + relativedelta(months=3 * self.interval)
        elif self.frequency == 'yearly':
            return base_date + relativedelta(years=self.interval)
```

**Create Repository Interface** (`app/domain/repositories/pm_schedule_repository.py`):

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.pm_schedule import PMSchedule

class IPMScheduleRepository(ABC):
    """Repository interface for PM schedules"""

    @abstractmethod
    def create(self, schedule: PMSchedule) -> PMSchedule:
        """Create new PM schedule"""
        pass

    @abstractmethod
    def get_by_id(self, schedule_id: int) -> Optional[PMSchedule]:
        """Get schedule by ID"""
        pass

    @abstractmethod
    def get_by_equipment(self, equipment_id: int) -> List[PMSchedule]:
        """Get all schedules for equipment"""
        pass

    @abstractmethod
    def get_due_schedules(self) -> List[PMSchedule]:
        """Get schedules that are due now"""
        pass

    @abstractmethod
    def update(self, schedule: PMSchedule) -> PMSchedule:
        """Update existing schedule"""
        pass
```

#### Step 2: Application Layer (Use Cases & DTOs)

**Create DTO** (`app/application/dtos/pm_schedule_dto.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreatePMScheduleDTO(BaseModel):
    """DTO for creating PM schedule"""
    equipment_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    frequency: str = Field(..., pattern='^(daily|weekly|monthly|quarterly|yearly)$')
    interval: int = Field(..., gt=0)
    duration_hours: float = Field(..., gt=0)

class PMScheduleResponseDTO(BaseModel):
    """DTO for PM schedule response"""
    id: int
    equipment_id: int
    name: str
    frequency: str
    interval: int
    duration_hours: float
    is_active: bool
    last_performed_at: Optional[datetime]
    next_due_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
```

**Create Use Case** (`app/application/use_cases/pm_schedule/create_pm_schedule.py`):

```python
from app.domain.entities.pm_schedule import PMSchedule
from app.domain.repositories.pm_schedule_repository import IPMScheduleRepository
from app.application.dtos.pm_schedule_dto import CreatePMScheduleDTO, PMScheduleResponseDTO
from datetime import datetime

class CreatePMScheduleUseCase:
    """Use case for creating PM schedule"""

    def __init__(self, pm_schedule_repository: IPMScheduleRepository):
        self._repository = pm_schedule_repository

    def execute(self, dto: CreatePMScheduleDTO, organization_id: int) -> PMScheduleResponseDTO:
        """Execute use case"""

        # Create domain entity
        schedule = PMSchedule(
            id=None,
            equipment_id=dto.equipment_id,
            name=dto.name,
            frequency=dto.frequency,
            interval=dto.interval,
            duration_hours=dto.duration_hours,
            is_active=True,
            last_performed_at=None,
            next_due_at=None,
            created_at=datetime.utcnow()
        )

        # Calculate next due date
        schedule.next_due_at = schedule.calculate_next_due_date()

        # Persist via repository
        created_schedule = self._repository.create(schedule)

        # Return DTO
        return PMScheduleResponseDTO.from_orm(created_schedule)
```

#### Step 3: Infrastructure Layer (Database)

**Create Database Model** (`app/infrastructure/persistence/models.py`):

```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

class PMScheduleModel(Base):
    """SQLAlchemy model for PM schedules"""
    __tablename__ = "pm_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    name = Column(String(200), nullable=False)
    frequency = Column(String(20), nullable=False)
    interval = Column(Integer, nullable=False)
    duration_hours = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_performed_at = Column(DateTime(timezone=True), nullable=True)
    next_due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Relationships
    equipment = relationship("EquipmentModel", back_populates="pm_schedules")
    organization = relationship("OrganizationModel")

    # Row-Level Security (RLS) - enforced at DB level
    # CREATE POLICY pm_schedules_tenant_isolation ON pm_schedules
    #   USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**Create Migration** (`database/migrations/versions/0XX_add_pm_schedules.py`):

```python
"""Add PM schedules table

Revision ID: 0XX
Revises: 0YY
Create Date: 2025-11-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0XX'
down_revision = '0YY'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create table
    op.create_table(
        'pm_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id']),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_pm_schedules_equipment_id', 'pm_schedules', ['equipment_id'])
    op.create_index('ix_pm_schedules_next_due_at', 'pm_schedules', ['next_due_at'])
    op.create_index('ix_pm_schedules_organization_id', 'pm_schedules', ['organization_id'])

    # Enable RLS
    op.execute("ALTER TABLE pm_schedules ENABLE ROW LEVEL SECURITY;")

    # Create RLS policy
    op.execute("""
    CREATE POLICY pm_schedules_tenant_isolation ON pm_schedules
        USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
    """)

def downgrade() -> None:
    op.drop_table('pm_schedules')
```

**Run Migration**:

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Add PM schedules table"

# Review migration file in database/migrations/versions/

# Apply migration
alembic upgrade head
```

**Create Repository Implementation** (`app/infrastructure/persistence/repositories/pm_schedule_repository_impl.py`):

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.pm_schedule import PMSchedule
from app.domain.repositories.pm_schedule_repository import IPMScheduleRepository
from app.infrastructure.persistence.models import PMScheduleModel
from datetime import datetime

class PMScheduleRepository(IPMScheduleRepository):
    """Repository implementation for PM schedules"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, schedule: PMSchedule) -> PMSchedule:
        """Create new PM schedule"""
        db_schedule = PMScheduleModel(
            equipment_id=schedule.equipment_id,
            name=schedule.name,
            frequency=schedule.frequency,
            interval=schedule.interval,
            duration_hours=schedule.duration_hours,
            is_active=schedule.is_active,
            last_performed_at=schedule.last_performed_at,
            next_due_at=schedule.next_due_at,
            created_at=schedule.created_at
        )
        self._db.add(db_schedule)
        self._db.commit()
        self._db.refresh(db_schedule)

        return self._to_entity(db_schedule)

    def get_by_id(self, schedule_id: int) -> Optional[PMSchedule]:
        """Get schedule by ID"""
        db_schedule = self._db.query(PMScheduleModel).filter(
            PMScheduleModel.id == schedule_id
        ).first()

        return self._to_entity(db_schedule) if db_schedule else None

    def get_by_equipment(self, equipment_id: int) -> List[PMSchedule]:
        """Get all schedules for equipment"""
        db_schedules = self._db.query(PMScheduleModel).filter(
            PMScheduleModel.equipment_id == equipment_id
        ).all()

        return [self._to_entity(s) for s in db_schedules]

    def get_due_schedules(self) -> List[PMSchedule]:
        """Get schedules that are due now"""
        now = datetime.utcnow()
        db_schedules = self._db.query(PMScheduleModel).filter(
            PMScheduleModel.is_active == True,
            PMScheduleModel.next_due_at <= now
        ).all()

        return [self._to_entity(s) for s in db_schedules]

    def update(self, schedule: PMSchedule) -> PMSchedule:
        """Update existing schedule"""
        db_schedule = self._db.query(PMScheduleModel).filter(
            PMScheduleModel.id == schedule.id
        ).first()

        if not db_schedule:
            raise ValueError(f"PM Schedule {schedule.id} not found")

        # Update fields
        db_schedule.name = schedule.name
        db_schedule.frequency = schedule.frequency
        db_schedule.interval = schedule.interval
        db_schedule.duration_hours = schedule.duration_hours
        db_schedule.is_active = schedule.is_active
        db_schedule.last_performed_at = schedule.last_performed_at
        db_schedule.next_due_at = schedule.next_due_at

        self._db.commit()
        self._db.refresh(db_schedule)

        return self._to_entity(db_schedule)

    def _to_entity(self, model: PMScheduleModel) -> PMSchedule:
        """Convert model to entity"""
        return PMSchedule(
            id=model.id,
            equipment_id=model.equipment_id,
            name=model.name,
            frequency=model.frequency,
            interval=model.interval,
            duration_hours=model.duration_hours,
            is_active=model.is_active,
            last_performed_at=model.last_performed_at,
            next_due_at=model.next_due_at,
            created_at=model.created_at
        )
```

#### Step 4: Presentation Layer (API Endpoint)

**Create API Endpoint** (`app/presentation/api/v1/pm_schedules.py`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.application.dtos.pm_schedule_dto import CreatePMScheduleDTO, PMScheduleResponseDTO
from app.application.use_cases.pm_schedule.create_pm_schedule import CreatePMScheduleUseCase
from app.infrastructure.persistence.repositories.pm_schedule_repository_impl import PMScheduleRepository
from app.infrastructure.security.auth import get_current_user, get_current_organization_id
from app.infrastructure.security.feature_gating import require_tier

router = APIRouter(prefix="/pm-schedules", tags=["Preventive Maintenance"])

@router.post(
    "/",
    response_model=PMScheduleResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create PM schedule"
)
@require_tier("professional")  # Feature gating: Professional tier+
async def create_pm_schedule(
    dto: CreatePMScheduleDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id)
):
    """
    Create a new preventive maintenance schedule.

    - **Requires**: Professional or Enterprise tier
    - **Permissions**: maintenance_admin role
    """

    # Create repository
    repository = PMScheduleRepository(db)

    # Execute use case
    use_case = CreatePMScheduleUseCase(repository)
    result = use_case.execute(dto, organization_id)

    return result

@router.get(
    "/",
    response_model=List[PMScheduleResponseDTO],
    summary="List PM schedules"
)
@require_tier("professional")
async def list_pm_schedules(
    equipment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all PM schedules, optionally filtered by equipment"""
    repository = PMScheduleRepository(db)

    if equipment_id:
        schedules = repository.get_by_equipment(equipment_id)
    else:
        schedules = repository.get_all()  # Implement this method

    return [PMScheduleResponseDTO.from_orm(s) for s in schedules]

@router.get(
    "/{schedule_id}",
    response_model=PMScheduleResponseDTO,
    summary="Get PM schedule"
)
@require_tier("professional")
async def get_pm_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get PM schedule by ID"""
    repository = PMScheduleRepository(db)
    schedule = repository.get_by_id(schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PM Schedule {schedule_id} not found"
        )

    return PMScheduleResponseDTO.from_orm(schedule)
```

**Register Router** (`app/presentation/api/v1/__init__.py`):

```python
from fastapi import APIRouter
from app.presentation.api.v1 import (
    materials,
    work_orders,
    subscriptions,
    pm_schedules  # NEW
)

api_router = APIRouter()

# Existing routes
api_router.include_router(materials.router, prefix="/api/v1", tags=["materials"])
api_router.include_router(work_orders.router, prefix="/api/v1", tags=["work_orders"])

# NEW: PM Schedules
api_router.include_router(pm_schedules.router, prefix="/api/v1", tags=["pm_schedules"])
```

#### Step 5: Test

**Unit Test** (`tests/unit/test_pm_schedule.py`):

```python
import pytest
from datetime import datetime, timedelta
from app.domain.entities.pm_schedule import PMSchedule

def test_pm_schedule_creation():
    """Test PM schedule entity creation"""
    schedule = PMSchedule(
        id=None,
        equipment_id=1,
        name="Oil Change",
        frequency="monthly",
        interval=1,
        duration_hours=2.0,
        is_active=True,
        last_performed_at=None,
        next_due_at=None,
        created_at=datetime.utcnow()
    )

    assert schedule.name == "Oil Change"
    assert schedule.frequency == "monthly"

def test_pm_schedule_validation():
    """Test domain validation"""
    with pytest.raises(ValueError, match="Invalid frequency"):
        PMSchedule(
            id=None,
            equipment_id=1,
            name="Test",
            frequency="invalid",  # Invalid frequency
            interval=1,
            duration_hours=2.0,
            is_active=True,
            last_performed_at=None,
            next_due_at=None,
            created_at=datetime.utcnow()
        )

def test_calculate_next_due_date_monthly():
    """Test next due date calculation for monthly schedule"""
    now = datetime.utcnow()
    schedule = PMSchedule(
        id=None,
        equipment_id=1,
        name="Test",
        frequency="monthly",
        interval=1,
        duration_hours=2.0,
        is_active=True,
        last_performed_at=None,
        next_due_at=None,
        created_at=now
    )

    next_due = schedule.calculate_next_due_date()
    expected = now + timedelta(days=30)  # Approximately

    assert abs((next_due - expected).days) <= 2  # Allow 2 days tolerance
```

**Integration Test** (`tests/integration/test_pm_schedule_api.py`):

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_pm_schedule(auth_headers):
    """Test creating PM schedule via API"""
    payload = {
        "equipment_id": 1,
        "name": "Weekly Oil Check",
        "frequency": "weekly",
        "interval": 1,
        "duration_hours": 0.5
    }

    response = client.post(
        "/api/v1/pm-schedules/",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Weekly Oil Check"
    assert data["is_active"] is True
    assert "next_due_at" in data

def test_create_pm_schedule_unauthorized(auth_headers_starter_tier):
    """Test feature gating - Starter tier can't access PM schedules"""
    payload = {
        "equipment_id": 1,
        "name": "Test",
        "frequency": "monthly",
        "interval": 1,
        "duration_hours": 1.0
    }

    response = client.post(
        "/api/v1/pm-schedules/",
        json=payload,
        headers=auth_headers_starter_tier
    )

    # Feature gating should block access
    assert response.status_code == 403
    assert "Professional tier required" in response.json()["detail"]
```

**Run Tests**:

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_pm_schedule.py

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── main.tsx                     # Application entry point
│   ├── App.tsx                      # Root component
│   ├── router.tsx                   # TanStack Router configuration
│   ├── design-system/               # Reusable UI components
│   │   ├── atoms/                   # Basic components (Button, Input)
│   │   ├── molecules/               # Composite components (SearchBar, Card)
│   │   ├── organisms/               # Complex components (DataTable, Form)
│   │   └── templates/               # Layout templates (AppLayout, AuthLayout)
│   ├── features/                    # Domain-specific modules
│   │   ├── auth/                    # Authentication
│   │   │   ├── components/          # Login, Signup components
│   │   │   ├── hooks/               # useAuth, useLogin hooks
│   │   │   └── stores/              # authStore (Zustand)
│   │   ├── materials/               # Material management
│   │   ├── work-orders/             # Work order management
│   │   ├── subscriptions/           # Subscription & billing
│   │   ├── marketing/               # Landing page components
│   │   └── admin/                   # Platform admin
│   ├── pages/                       # Route components
│   │   ├── LandingPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── BillingPage.tsx
│   │   └── admin/
│   │       ├── PlatformDashboardPage.tsx
│   │       ├── OrganizationsPage.tsx
│   │       └── AnalyticsDashboardPage.tsx
│   ├── routes/                      # Route definitions (TanStack Router)
│   │   ├── index.tsx                # Root route
│   │   ├── authenticated.tsx        # Protected route wrapper
│   │   ├── landing.tsx
│   │   ├── billing.tsx
│   │   └── admin-analytics.tsx
│   ├── services/                    # API clients
│   │   ├── material.service.ts
│   │   ├── work-order.service.ts
│   │   ├── subscription.service.ts
│   │   ├── admin.service.ts
│   │   └── analytics.service.ts
│   ├── hooks/                       # Shared React hooks
│   │   ├── useAuth.ts
│   │   ├── useSubscription.ts
│   │   └── useFeatureFlag.ts
│   ├── lib/                         # Utilities
│   │   ├── api-client.ts            # Axios instance with interceptors
│   │   ├── auth.ts                  # JWT helpers
│   │   └── utils.ts                 # General utilities
│   ├── types/                       # TypeScript types
│   │   ├── material.types.ts
│   │   ├── subscription.types.ts
│   │   └── api.types.ts
│   └── styles/                      # Global styles
│       ├── index.css                # Tailwind imports
│       └── globals.css              # Custom global styles
├── public/                          # Static assets
├── index.html                       # HTML template
├── vite.config.ts                   # Vite configuration
├── tailwind.config.js               # Tailwind CSS configuration
├── tsconfig.json                    # TypeScript configuration
├── package.json                     # Dependencies
└── .env.example                     # Environment template
```

### Adding a New Page (Step-by-Step)

Let's add a **"PM Schedules List"** page.

#### Step 1: Create TypeScript Types

**File**: `src/types/pm-schedule.types.ts`

```typescript
export interface PMSchedule {
  id: number
  equipment_id: number
  name: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  interval: number
  duration_hours: number
  is_active: boolean
  last_performed_at: string | null
  next_due_at: string | null
  created_at: string
}

export interface CreatePMScheduleRequest {
  equipment_id: number
  name: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  interval: number
  duration_hours: number
}

export interface PMScheduleListResponse {
  items: PMSchedule[]
  total: number
}
```

#### Step 2: Create API Service

**File**: `src/services/pm-schedule.service.ts`

```typescript
import { apiClient } from '../lib/api-client'
import type {
  PMSchedule,
  CreatePMScheduleRequest,
  PMScheduleListResponse
} from '../types/pm-schedule.types'

export const pmScheduleService = {
  /**
   * Get all PM schedules
   */
  async list(equipmentId?: number): Promise<PMScheduleListResponse> {
    const params = equipmentId ? { equipment_id: equipmentId } : {}
    const response = await apiClient.get<PMSchedule[]>('/api/v1/pm-schedules', { params })
    return {
      items: response.data,
      total: response.data.length
    }
  },

  /**
   * Get single PM schedule
   */
  async getById(id: number): Promise<PMSchedule> {
    const response = await apiClient.get<PMSchedule>(`/api/v1/pm-schedules/${id}`)
    return response.data
  },

  /**
   * Create new PM schedule
   */
  async create(data: CreatePMScheduleRequest): Promise<PMSchedule> {
    const response = await apiClient.post<PMSchedule>('/api/v1/pm-schedules', data)
    return response.data
  },

  /**
   * Update PM schedule
   */
  async update(id: number, data: Partial<CreatePMScheduleRequest>): Promise<PMSchedule> {
    const response = await apiClient.put<PMSchedule>(`/api/v1/pm-schedules/${id}`, data)
    return response.data
  },

  /**
   * Delete PM schedule
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/pm-schedules/${id}`)
  }
}
```

#### Step 3: Create Page Component

**File**: `src/pages/PMSchedulesPage.tsx`

```typescript
import { useState, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { pmScheduleService } from '../services/pm-schedule.service'
import type { PMSchedule } from '../types/pm-schedule.types'
import { Button } from '../design-system/atoms/Button'
import { DataTable } from '../design-system/organisms/DataTable'
import { Badge } from '../design-system/atoms/Badge'

export function PMSchedulesPage() {
  const navigate = useNavigate()
  const [schedules, setSchedules] = useState<PMSchedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSchedules()
  }, [])

  const loadSchedules = async () => {
    try {
      setLoading(true)
      const data = await pmScheduleService.list()
      setSchedules(data.items)
    } catch (err) {
      setError('Failed to load PM schedules')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    navigate({ to: '/maintenance/pm-schedules/new' })
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return

    try {
      await pmScheduleService.delete(id)
      await loadSchedules() // Reload list
    } catch (err) {
      alert('Failed to delete schedule')
    }
  }

  const columns = [
    {
      header: 'Name',
      accessorKey: 'name',
      cell: (row: PMSchedule) => (
        <div>
          <div className="font-medium">{row.name}</div>
          <div className="text-sm text-gray-500">Equipment ID: {row.equipment_id}</div>
        </div>
      )
    },
    {
      header: 'Frequency',
      accessorKey: 'frequency',
      cell: (row: PMSchedule) => (
        <span className="capitalize">
          Every {row.interval} {row.frequency}
        </span>
      )
    },
    {
      header: 'Duration',
      accessorKey: 'duration_hours',
      cell: (row: PMSchedule) => `${row.duration_hours} hours`
    },
    {
      header: 'Status',
      accessorKey: 'is_active',
      cell: (row: PMSchedule) => (
        <Badge variant={row.is_active ? 'success' : 'default'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      )
    },
    {
      header: 'Next Due',
      accessorKey: 'next_due_at',
      cell: (row: PMSchedule) => {
        if (!row.next_due_at) return '-'
        const date = new Date(row.next_due_at)
        const isOverdue = date < new Date()
        return (
          <span className={isOverdue ? 'text-red-600 font-medium' : ''}>
            {date.toLocaleDateString()}
          </span>
        )
      }
    },
    {
      header: 'Actions',
      accessorKey: 'id',
      cell: (row: PMSchedule) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate({ to: `/maintenance/pm-schedules/${row.id}` })}
          >
            View
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => handleDelete(row.id)}
          >
            Delete
          </Button>
        </div>
      )
    }
  ]

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>
  }

  if (error) {
    return <div className="p-8 text-center text-red-600">{error}</div>
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">PM Schedules</h1>
          <p className="text-gray-600 mt-1">
            Manage preventive maintenance schedules for your equipment
          </p>
        </div>
        <Button onClick={handleCreate}>+ New PM Schedule</Button>
      </div>

      {/* Table */}
      <DataTable
        data={schedules}
        columns={columns}
        searchable
        searchPlaceholder="Search schedules..."
        emptyMessage="No PM schedules found. Create one to get started."
      />
    </div>
  )
}
```

#### Step 4: Create Route Definition

**File**: `src/routes/pm-schedules.tsx`

```typescript
import { createRoute } from '@tanstack/react-router'
import { authenticatedRoute } from './authenticated'
import { PMSchedulesPage } from '../pages/PMSchedulesPage'

export const pmSchedulesRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/maintenance/pm-schedules',
  component: PMSchedulesPage
})
```

#### Step 5: Register Route

**File**: `src/router.tsx`

```typescript
import { createRouter } from '@tanstack/react-router'
import { rootRoute } from './routes/index'
import { authenticatedRoute } from './routes/authenticated'
import { pmSchedulesRoute } from './routes/pm-schedules'  // NEW

// Build route tree
const routeTree = rootRoute.addChildren([
  authenticatedRoute.addChildren([
    dashboardRoute,
    materialsRoute,
    workOrdersRoute,
    pmSchedulesRoute,  // NEW
    // ... other routes
  ])
])

// Create router
const router = createRouter({ routeTree })

export default router
```

#### Step 6: Add Navigation Link

**File**: `src/design-system/templates/AppLayout.tsx`

```typescript
// In Sidebar component
<nav>
  <SidebarLink to="/dashboard" icon={HomeIcon}>
    Dashboard
  </SidebarLink>
  <SidebarLink to="/materials" icon={CubeIcon}>
    Materials
  </SidebarLink>
  <SidebarLink to="/production/work-orders" icon={ClipboardIcon}>
    Work Orders
  </SidebarLink>
  {/* NEW */}
  <SidebarLink to="/maintenance/pm-schedules" icon={WrenchIcon}>
    PM Schedules
  </SidebarLink>
</nav>
```

#### Step 7: Test

```bash
cd frontend

# Start dev server
npm run dev

# Navigate to: http://localhost:5173/maintenance/pm-schedules

# Should see:
# - List of PM schedules (or empty state if none)
# - "New PM Schedule" button
# - Search bar
# - Table with columns: Name, Frequency, Duration, Status, Next Due, Actions
```

---

## Database Development

### Row-Level Security (RLS) Policies

**Multi-tenant isolation is enforced at the database level using RLS.**

#### How RLS Works

**1. Application sets session context** (on every request):

```python
# In middleware (backend/app/infrastructure/security/auth.py)
from sqlalchemy import text

def set_organization_context(db: Session, organization_id: int):
    """Set organization context for RLS"""
    db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))
```

**2. Database policies filter queries automatically**:

```sql
-- Example: materials table RLS policy
CREATE POLICY materials_tenant_isolation ON materials
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- All queries now auto-filter by organization_id:
SELECT * FROM materials;
-- Becomes: SELECT * FROM materials WHERE organization_id = 123;
```

#### Creating RLS Policies

**Template for new tables**:

```sql
-- 1. Enable RLS
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;

-- 2. Create policy
CREATE POLICY your_table_tenant_isolation ON your_table
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- 3. Create index for performance
CREATE INDEX ix_your_table_organization_id ON your_table(organization_id);
```

**In migrations**:

```python
def upgrade() -> None:
    # Create table
    op.create_table('your_table', ...)

    # Enable RLS
    op.execute("ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;")

    # Create policy
    op.execute("""
    CREATE POLICY your_table_tenant_isolation ON your_table
        USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
    """)

    # Create index
    op.create_index('ix_your_table_organization_id', 'your_table', ['organization_id'])
```

### TimescaleDB Hypertables

**For time-series data (production logs, downtime events, metrics):**

```sql
-- Create regular table first
CREATE TABLE production_logs (
    id SERIAL,
    time TIMESTAMPTZ NOT NULL,
    work_order_id INTEGER,
    quantity_produced INTEGER,
    operator_id INTEGER,
    organization_id INTEGER,
    PRIMARY KEY (id, time)  -- Composite key including time
);

-- Convert to hypertable
SELECT create_hypertable('production_logs', 'time');

-- Set up compression (75% space savings)
ALTER TABLE production_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id,work_order_id'
);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy('production_logs', INTERVAL '7 days');
```

### pg_cron Scheduled Jobs

**For automated tasks (usage tracking, trial expiration, email notifications):**

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Schedule usage tracking (every 6 hours)
SELECT cron.schedule(
    'track-usage',
    '0 */6 * * *',  -- Cron syntax: At minute 0 past every 6th hour
    $$SELECT net.http_post(
        url := 'https://api.yourdomain.com/api/v1/jobs/track-usage',
        headers := '{"X-API-Key": "your-internal-api-key"}'::jsonb
    );$$
);

-- Schedule trial expiration check (daily at 2 AM UTC)
SELECT cron.schedule(
    'check-trial-expirations',
    '0 2 * * *',  -- At 02:00 every day
    $$SELECT net.http_post(
        url := 'https://api.yourdomain.com/api/v1/jobs/check-trial-expirations',
        headers := '{"X-API-Key": "your-internal-api-key"}'::jsonb
    );$$
);

-- View scheduled jobs
SELECT * FROM cron.job;

-- View job run history
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;

-- Unschedule a job
SELECT cron.unschedule('track-usage');
```

---

## Commercial Infrastructure

### Subscription System

The platform includes complete subscription management:

#### Pricing Tiers

**Configuration** (`backend/app/config/pricing.py`):

```python
from enum import Enum

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"

PRICING_TIERS = {
    SubscriptionTier.STARTER: {
        "monthly_price": 4900,  # $49 in cents
        "annual_price": 52920,  # 10% discount
        "max_users": 3,
        "max_plants": 1,
        "storage_limit_gb": 10,
        "features": [
            "basic_production",
            "material_management",
            "bom_management",
            "inventory_tracking",
            "work_orders",
            "basic_quality"
        ]
    },
    SubscriptionTier.PROFESSIONAL: {
        "monthly_price": 19900,  # $199
        "annual_price": 214920,  # 10% discount
        "max_users": 25,
        "max_plants": 5,
        "storage_limit_gb": 100,
        "features": [
            # All Starter features +
            "visual_scheduling",
            "quality_analytics",
            "spc_charts",
            "maintenance_management",
            "pm_scheduling",
            "multi_plant"
        ]
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly_price": 99900,  # $999
        "annual_price": 1019150,  # 15% discount
        "max_users": -1,  # Unlimited
        "max_plants": -1,  # Unlimited
        "storage_limit_gb": 1024,  # 1 TB
        "features": [
            # All Professional features +
            "advanced_analytics",
            "bi_dashboards",
            "api_access",
            "custom_integrations",
            "priority_support"
        ]
    }
}
```

#### Feature Gating

**Decorator-based enforcement** (`backend/app/infrastructure/security/feature_gating.py`):

```python
from functools import wraps
from fastapi import HTTPException, status
from app.config.pricing import SubscriptionTier, PRICING_TIERS

def require_tier(required_tier: str):
    """Decorator to enforce tier-based access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current subscription from context
            subscription = get_current_subscription()  # Implement this

            # Check tier hierarchy
            tier_hierarchy = {
                SubscriptionTier.STARTER: 1,
                SubscriptionTier.PROFESSIONAL: 2,
                SubscriptionTier.ENTERPRISE: 3
            }

            current_level = tier_hierarchy[subscription.tier]
            required_level = tier_hierarchy[required_tier]

            if current_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature requires {required_tier} tier or higher"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature_name: str):
    """Decorator to enforce feature-based access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            subscription = get_current_subscription()
            tier_features = PRICING_TIERS[subscription.tier]["features"]

            if feature_name not in tier_features:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature_name}' not available in your plan"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Usage in API endpoints**:

```python
@router.get("/visual-schedule")
@require_tier("professional")  # Professional tier or higher
async def get_visual_schedule():
    # Only accessible to Professional and Enterprise customers
    pass

@router.post("/pm-schedules")
@require_feature("pm_scheduling")  # Specific feature check
async def create_pm_schedule():
    # Only accessible if subscription includes PM scheduling
    pass
```

#### Stripe Integration

**Webhook Handler** (`backend/app/presentation/api/v1/webhooks.py`):

```python
from fastapi import APIRouter, Request, HTTPException
import stripe
from app.config.stripe_config import get_stripe_webhook_secret
from app.application.use_cases.subscription.handle_stripe_webhook import HandleStripeWebhookUseCase

router = APIRouter()

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""

    # Get payload and signature
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, get_stripe_webhook_secret()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    use_case = HandleStripeWebhookUseCase()  # Inject dependencies
    await use_case.execute(event)

    return {"status": "success"}
```

**Supported Events**:
- `checkout.session.completed`: New subscription created
- `invoice.payment_succeeded`: Payment successful
- `invoice.payment_failed`: Payment failed (retry or suspend)
- `customer.subscription.updated`: Subscription changed (upgrade/downgrade)
- `customer.subscription.deleted`: Subscription cancelled

### Admin Dashboard

**Platform-wide metrics** for SaaS operators:

**Analytics Service** (`backend/app/application/services/analytics_service.py`):

```python
class AnalyticsService:
    def get_mrr_breakdown(self) -> Dict[str, Any]:
        """Calculate Monthly Recurring Revenue breakdown"""
        # Query subscriptions, calculate MRR by tier and billing cycle
        return {
            "total_mrr": 12450,  # $124.50
            "mrr_by_tier": {
                "starter": 2940,
                "professional": 7960,
                "enterprise": 1550
            },
            "mrr_by_cycle": {
                "monthly": 8500,
                "annual": 3950
            },
            "customer_count": 42,
            "arpu": 296  # Average Revenue Per User
        }

    def get_churn_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Calculate churn rate"""
        # Calculate customer churn and MRR churn
        return {
            "customer_churn_rate": 2.5,  # 2.5% monthly churn
            "mrr_churn_rate": 3.1,
            "churned_customers": 3,
            "churned_mrr": 385
        }
```

---

## Testing

### Backend Testing

**Structure**:
```
tests/
├── unit/                           # Fast, isolated tests
│   ├── domain/
│   │   ├── test_material_entity.py
│   │   └── test_subscription_entity.py
│   └── use_cases/
│       └── test_create_material_use_case.py
├── integration/                    # Tests with DB/API
│   ├── test_material_api.py
│   ├── test_subscription_api.py
│   └── test_stripe_webhook.py
└── conftest.py                     # Pytest fixtures
```

**Running Tests**:

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_material_entity.py

# Run tests matching pattern
pytest -k "test_create"

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/

# Run and stop at first failure
pytest -x
```

**Example Test** (`tests/integration/test_subscription_api.py`):

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers(test_user):
    """Fixture providing authentication headers"""
    response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_subscription(auth_headers, test_organization):
    """Test creating subscription"""
    payload = {
        "organization_id": test_organization.id,
        "tier": "professional",
        "billing_cycle": "monthly"
    }

    response = client.post(
        "/api/v1/subscriptions/",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tier"] == "professional"
    assert data["status"] == "trial"  # New subscriptions start as trial

def test_upgrade_subscription(auth_headers, test_subscription):
    """Test upgrading subscription"""
    payload = {
        "new_tier": "enterprise",
        "billing_cycle": "annual"
    }

    response = client.put(
        f"/api/v1/subscriptions/{test_subscription.id}/upgrade",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "enterprise"
    assert data["billing_cycle"] == "annual"
```

### Frontend Testing

**Testing Stack**:
- **Unit/Component**: Vitest + React Testing Library
- **E2E**: Playwright

**Running Tests**:

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests in headed mode (see browser)
npm run test:e2e:headed
```

**Example Component Test** (`src/components/TrialBanner.test.tsx`):

```typescript
import { render, screen } from '@testing-library/react'
import { TrialBanner } from './TrialBanner'
import { useAuthStore } from '../features/auth/stores/authStore'

describe('TrialBanner', () => {
  it('shows blue banner with 10 days remaining', () => {
    // Mock subscription data
    useAuthStore.setState({
      subscription: {
        status: 'trial',
        trial_ends_at: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString()
      }
    })

    render(<TrialBanner />)

    expect(screen.getByText(/10 days left/i)).toBeInTheDocument()
    expect(screen.getByRole('banner')).toHaveClass('bg-blue-50')  // Blue background
  })

  it('shows red banner with 2 days remaining', () => {
    useAuthStore.setState({
      subscription: {
        status: 'trial',
        trial_ends_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString()
      }
    })

    render(<TrialBanner />)

    expect(screen.getByText(/2 days left/i)).toBeInTheDocument()
    expect(screen.getByRole('banner')).toHaveClass('bg-red-50')  // Red background (urgent)
  })
})
```

---

## Deployment

### Docker Deployment

**Backend Dockerfile** (`backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend Dockerfile** (`frontend/Dockerfile`):

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build production bundle
COPY . .
RUN npm run build

# Production image with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose** (`docker-compose.yml`):

```yaml
version: '3.8'

services:
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: unison
      POSTGRES_USER: unison
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://unison:${DB_PASSWORD}@db:5432/unison
      SECRET_KEY: ${SECRET_KEY}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
    depends_on:
      - db
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Deploy**:

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Best Practices

### Code Style

**Backend (Python)**:
- Use **Black** for formatting (88 char line length)
- Use **isort** for import sorting
- Use **flake8** for linting
- Use **type hints** everywhere

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/
```

**Frontend (TypeScript)**:
- Use **Prettier** for formatting
- Use **ESLint** for linting
- Use **explicit types** (avoid `any`)

```bash
# Format code
npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

### Git Workflow

**Branching Strategy**:
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `fix/*`: Bug fixes
- `hotfix/*`: Production hotfixes

**Commit Messages**:

Use **Conventional Commits**:
```
feat: Add PM schedule management
fix: Correct MRR calculation in analytics
docs: Update deployment guide
refactor: Extract subscription service
test: Add integration tests for webhooks
chore: Update dependencies
```

### Security Best Practices

1. **Never commit secrets** (`.env` files in `.gitignore`)
2. **Use environment variables** for all secrets
3. **Validate all inputs** (Pydantic DTOs)
4. **Use parameterized queries** (SQLAlchemy prevents SQL injection)
5. **Verify webhook signatures** (Stripe)
6. **Rate limit API endpoints**
7. **Enable CORS** only for known domains
8. **Use HTTPS** in production
9. **Rotate JWT secrets** periodically
10. **Audit admin actions** (logging)

---

## Troubleshooting

### Common Development Issues

#### 1. Database Connection Errors

**Error**: `connection refused` or `database does not exist`

**Solutions**:
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Create database if missing
createdb unison_dev

# Check connection string in .env
DATABASE_URL=postgresql://user:password@localhost:5432/unison_dev
```

#### 2. Migration Conflicts

**Error**: `alembic.util.exc.CommandError: Multiple head revisions are present`

**Solutions**:
```bash
# View migration history
alembic history

# Merge heads
alembic merge heads -m "Merge migration branches"

# Apply merged migration
alembic upgrade head
```

#### 3. Import Errors (Python)

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Add PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

#### 4. Frontend Build Errors

**Error**: `Module not found` or `Cannot find module`

**Solutions**:
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Restart dev server
npm run dev
```

---

## Additional Resources

### Documentation
- [PRD - Product Requirements](01-requirements/PRD.md)
- [FRD - Functional Requirements](01-requirements/FRD_INDEX.md)
- [Architecture Overview](02-architecture/OVERVIEW.md)
- [Database Schema](02-architecture/DATABASE_SCHEMA.md)
- [API Design](02-architecture/API_DESIGN.md)
- [PostgreSQL Extensions](03-postgresql/README.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [TanStack Router Documentation](https://tanstack.com/router)
- [PostgreSQL RLS Guide](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Stripe API Reference](https://stripe.com/docs/api)

---

**Happy Coding! 🚀**

*Last Updated: 2025-11-11 | Version 1.0*
