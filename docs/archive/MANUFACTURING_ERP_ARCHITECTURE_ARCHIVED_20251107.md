# Manufacturing ERP System - Architecture Design

**Version**: 1.0  
**Date**: 2025-11-06  
**System**: Unison Manufacturing ERP  
**Type**: B2B Enterprise SaaS for Manufacturing Management

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Layers](#architecture-layers)
4. [Database Schema](#database-schema)
5. [Domain Model](#domain-model)
6. [API Design](#api-design)
7. [Frontend Architecture](#frontend-architecture)
8. [Infrastructure](#infrastructure)
9. [Security & Multi-Tenancy](#security--multi-tenancy)
10. [Implementation Phases](#implementation-phases)

---

## System Overview

### Technical Architecture
Multi-tenant B2B SaaS platform built with FastAPI (backend) and React (frontend), deployed on containerized infrastructure with PostgreSQL-native stack (using extensions: pgmq, pg_cron, pg_search, pg_duckdb, timescaledb) for persistence, queuing, caching, search, and analytics, plus MinIO for object storage.

```mermaid
C4Context
    title System Context - Unison Manufacturing ERP

    Person(user, "Plant User", "Operator, Supervisor, Manager")
    Person(admin, "Admin", "Configure workflows, manage users")

    System(unison, "Unison ERP", "Manufacturing management platform")

    System_Ext(sap, "SAP ERP", "Enterprise resource planning")
    System_Ext(email, "Email Service", "Notifications")
    System_Ext(stripe, "Stripe", "Subscription billing")

    Rel(user, unison, "Uses", "HTTPS/PWA")
    Rel(admin, unison, "Configures", "HTTPS")
    Rel(unison, sap, "Syncs data", "REST API")
    Rel(unison, email, "Sends notifications", "SMTP")
    Rel(unison, stripe, "Processes payments", "API")
```

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        A[React PWA]
        B[Mobile Browser]
    end

    subgraph "API Layer"
        C[FastAPI Backend]
        D[JWT Auth Middleware]
        E[RBAC PyCasbin]
    end

    subgraph "Application Layer"
        F[Use Cases]
        G[Domain Services]
    end

    subgraph "Infrastructure Layer"
        H[PostgreSQL + RLS]
        I[Redis Cache/Queue]
        J[MinIO Storage]
        K[Celery Workers]
    end

    subgraph "External Systems"
        L[SAP ERP]
        M[Email/SMS]
    end

    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    G --> J
    C --> K
    K --> L
    K --> M

    style H fill:#e1f5e1
    style I fill:#fff4e1
    style J fill:#e1e5f5
```

### Implementation Phases (Technical Breakdown)

**Phase 1: Foundation (Weeks 1-8)**
```python
# Core domain entities (15 tables)
Organization, Plant, Department
User, Role, Permission
Material, MaterialCategory, MaterialInventory
Project, BOM, Document

# Infrastructure services
MinIOService, BarcodeService, JWTHandler
CasbinEnforcer, RLSPolicy

# API endpoints: ~25 endpoints
# Key deliverables: Multi-tenancy working, JWT+RBAC, basic CRUD
```

**Phase 2: Production Core (Weeks 9-16)**
```python
# Work order domain (12 tables)
WorkOrder, WorkOrderOperation
Lane, LaneAssignment
ProductionLog, MaterialTransaction

# Infrastructure services
SchedulingService, CostingService
CeleryTasks (SAP sync, barcode generation)

# PWA implementation
ServiceWorker, OfflineQueue, CameraAPI

# API endpoints: +30 endpoints
# Key deliverables: Work orders, scheduling, mobile production logging
```

**Phase 3: Quality & Analytics (Weeks 17-24)**
```python
# Quality domain (8 tables)
NCRReport, NCRDisposition, NCRWorkflow
QualityInspection, InspectionCheckpoint

# Analytics domain (5 tables)
KPICalculation, Dashboard, Report

# Services
OEEService, ReportingEngine
WorkflowEngine

# API endpoints: +20 endpoints
# Key deliverables: NCR workflows, KPI dashboards, reporting
```

**Phase 4: Polish & Production (Weeks 25-32)**
```python
# Performance optimization
RedisCache implementation (10-minute TTLs)
Database indexes (20+ indexes)
Query optimization (eager loading, pagination)

# Security hardening
SOC 2 compliance audit
Penetration testing
Rate limiting, DDoS protection

# Deployment
Docker Compose production configs
Nginx reverse proxy
Health checks, monitoring, logging

# Key deliverables: Production-ready, SOC 2 certified, documented
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+
- **Architecture**: Domain-Driven Design (DDD)
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.12.1
- **Validation**: Pydantic v2
- **Authentication**: PyJWT 2.8.0
- **Authorization**: PyCasbin 1.25.0
- **Task Queue**: PGMQ (PostgreSQL extension - 30K msgs/sec)
- **Scheduled Tasks**: pg_cron (PostgreSQL extension)
- **Cache**: PostgreSQL UNLOGGED tables (1-2ms latency)
- **Object Storage**: MinIO (S3-compatible)
- **Barcode**: python-barcode, qrcode, Pillow

### Frontend
- **Framework**: React 18
- **Language**: TypeScript 5.2.2
- **Build Tool**: Vite 5.0.8
- **Styling**: Tailwind CSS 3.3.6
- **UI Components**: ShadCN UI (Radix primitives)
- **State Management**: Zustand 4.4.7
- **Server State**: TanStack Query 5.8.4
- **Validation**: Zod 3.22.4
- **Forms**: React Hook Form 7.48.2
- **HTTP Client**: Axios 1.6.2
- **Charts**: Recharts 2.10.3
- **PWA**: Vite PWA Plugin

### Database
- **DBMS**: PostgreSQL 15
- **Row-Level Security**: Enabled for multi-tenancy
- **Extensions**:
  - **pgmq**: Message queue (30K msgs/sec, replaces Celery + Redis)
  - **pg_cron**: Scheduled task automation (replaces Celery Beat)
  - **pg_search (ParadeDB)**: Full-text search with BM25 ranking (20x faster than tsvector)
  - **pg_duckdb**: Analytics engine (10-1500x faster OLAP queries)
  - **timescaledb**: Time-series optimization (75% storage compression)
- **Native Features**:
  - **UNLOGGED tables**: High-speed cache (2x faster writes, 1-2ms latency)
  - **LISTEN/NOTIFY**: Pub/sub messaging for real-time updates
  - **SKIP LOCKED**: Concurrent job queue processing
- **Audit**: Trigger-based audit tables

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (for production)
- **Services**: PostgreSQL (with extensions), MinIO, Backend API, Frontend
- **Deployment**: 3-4 containers (vs 8-10 with traditional stack) - 60% fewer containers

---

## Architecture Layers

### DDD Layers (Backend)

```
app/
├── domain/                 # Pure business logic (no framework dependencies)
│   ├── entities/          # Business entities
│   ├── value_objects/     # Immutable value objects
│   ├── repositories/      # Repository interfaces (abstractions)
│   ├── services/          # Domain services
│   └── exceptions/        # Domain-specific exceptions
│
├── application/           # Use cases & orchestration
│   ├── use_cases/        # Business operations
│   ├── dtos/             # Data Transfer Objects
│   └── services/         # Application services
│
├── infrastructure/        # External concerns
│   ├── persistence/      # Database, repositories impl
│   ├── security/         # JWT, RBAC, RLS
│   ├── storage/          # MinIO client
│   ├── tasks/            # Celery tasks
│   ├── sap/              # SAP adapter
│   └── barcode/          # Barcode generation
│
└── presentation/          # API layer
    └── api/
        └── v1/           # Versioned endpoints
```

### Atomic Design (Frontend)

### Data Flow (Request → Response Path)

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Nginx as Nginx Proxy
    participant API as Presentation Layer<br/>(FastAPI Router)
    participant AUTH as Security Middleware<br/>(JWT + RLS)
    participant USE as Application Layer<br/>(Use Case)
    participant DOM as Domain Layer<br/>(Business Logic)
    participant REPO as Repository Interface<br/>(Abstract)
    participant INFRA as Infrastructure Layer<br/>(Postgres Impl)
    participant DB as PostgreSQL<br/>(with RLS)
    
    Client->>Nginx: POST /api/v1/production-logs<br/>Authorization: Bearer JWT
    Nginx->>API: Forward request
    API->>AUTH: Extract & validate JWT
    AUTH->>AUTH: Decode JWT → org_id, user_id, plant_id
    AUTH->>AUTH: Set RLS context vars
    AUTH->>USE: Call CreateProductionLogUseCase(dto)
    USE->>USE: Validate business rules (qty > 0, WO active)
    USE->>DOM: Create ProductionLog entity
    DOM->>DOM: Calculate material cost (FIFO/LIFO)
    DOM->>DOM: Calculate labor cost (hours × rate)
    DOM->>REPO: productionLogRepo.save(log)
    REPO->>INFRA: PostgreSQL implementation
    INFRA->>DB: INSERT INTO production_logs<br/>WHERE organization_id = {org_id}
    DB->>DB: RLS policy enforces organization_id
    DB-->>INFRA: Return saved record
    INFRA-->>REPO: ProductionLog entity
    REPO-->>DOM: Success
    DOM->>REPO: workOrderRepo.updateQuantity(wo_id)
    REPO->>INFRA: Update work order
    INFRA->>DB: UPDATE work_orders SET qty_completed<br/>WHERE id = {wo_id} AND org_id = {org_id}
    DB-->>INFRA: Updated
    INFRA-->>REPO: Success
    REPO-->>USE: Transaction committed
    USE->>USE: Map entity → DTO
    USE-->>API: ProductionLogResponseDTO
    API->>API: Serialize to JSON
    API-->>Nginx: 201 Created + JSON body
    Nginx-->>Client: HTTP Response
```

**Key Flow Characteristics**:

1. **Authentication**: JWT validated at middleware layer before reaching use case
2. **Multi-Tenancy**: RLS context variables set from JWT claims (organization_id, plant_id)
3. **Layer Separation**: Each layer has single responsibility:
   - Presentation: HTTP concerns, validation, serialization
   - Application: Use case orchestration, DTO mapping
   - Domain: Pure business logic, no framework dependencies
   - Infrastructure: External services, database, I/O
4. **Database Security**: RLS policies automatically filter queries by organization_id
5. **Transaction Management**: Use cases manage transaction boundaries
6. **Dependency Direction**: Outer layers depend on inner (Infrastructure → Domain, not reverse)

**Example: Production Logging Flow**:
```
Client → Nginx → API Router → JWT Middleware → Use Case → Domain Service → 
Repository (Interface) → Infrastructure (Postgres) → Database (RLS enforced) → 
Response (reverse path)
```

### Atomic Design (Frontend)

```
src/
├── design-system/
│   ├── atoms/           # Button, Input, Label
│   ├── molecules/       # FormField, SearchBar, StatusBadge
│   ├── organisms/       # ProjectForm, MaterialTable, LaneCard
│   └── templates/       # PageLayout, DashboardLayout
│
├── components/
│   └── ui/              # ShadCN UI components
│
├── pages/               # Full pages (Projects, Materials, Production)
├── stores/              # Zustand stores
├── hooks/               # Custom React hooks
├── services/            # API clients
└── schemas/             # Zod validation schemas
```

---

## Database Schema

### Full Normalized Schema (47 Tables)

#### 1. Multi-Tenancy & Identity (7 tables)

**organizations**
```sql
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    industry VARCHAR(100),
    address TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

**plants**
```sql
CREATE TABLE plants (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    plant_type VARCHAR(50) NOT NULL, -- 'fabrication', 'production', 'assembly'
    address TEXT,
    manager_user_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, code)
);

-- Enable RLS
ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
CREATE POLICY plants_tenant_isolation ON plants
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**departments**
```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    head_user_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(plant_id, code)
);

ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
CREATE POLICY departments_tenant_isolation ON departments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    employee_code VARCHAR(50),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_tenant_isolation ON users
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**roles**
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, code)
);

ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY roles_tenant_isolation ON roles
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**user_roles**
```sql
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    plant_id INTEGER REFERENCES plants(id), -- Optional: role at plant level
    department_id INTEGER REFERENCES departments(id), -- Optional: role at dept level
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, role_id, plant_id, department_id)
);

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_roles_tenant_isolation ON user_roles
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**user_plant_access**
```sql
CREATE TABLE user_plant_access (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, plant_id)
);

ALTER TABLE user_plant_access ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_plant_access_tenant_isolation ON user_plant_access
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 2. Material Management (6 tables)

**material_categories**
```sql
CREATE TABLE material_categories (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    parent_category_id INTEGER REFERENCES material_categories(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, code)
);

ALTER TABLE material_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_categories_tenant_isolation ON material_categories
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**materials**
```sql
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    material_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES material_categories(id),
    unit_of_measure VARCHAR(50) NOT NULL, -- 'kg', 'pcs', 'meter', etc.
    standard_cost DECIMAL(15, 2),
    sap_material_number VARCHAR(100),
    barcode_data VARCHAR(255),
    qr_code_data TEXT,
    minimum_stock_level INTEGER,
    maximum_stock_level INTEGER,
    reorder_point INTEGER,
    lead_time_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY materials_tenant_isolation ON materials
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_materials_barcode ON materials(barcode_data);
CREATE INDEX idx_materials_qr ON materials(qr_code_data);
CREATE INDEX idx_materials_sap ON materials(sap_material_number);
```

**material_inventory**
```sql
CREATE TABLE material_inventory (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    warehouse_location VARCHAR(100),
    quantity_on_hand DECIMAL(15, 3) NOT NULL DEFAULT 0,
    quantity_reserved DECIMAL(15, 3) NOT NULL DEFAULT 0,
    quantity_available DECIMAL(15, 3) GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    last_counted_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(material_id, plant_id, warehouse_location)
);

ALTER TABLE material_inventory ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_inventory_tenant_isolation ON material_inventory
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**material_transactions**
```sql
CREATE TABLE material_transactions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    transaction_type VARCHAR(50) NOT NULL, -- 'receipt', 'issue', 'transfer', 'adjustment'
    quantity DECIMAL(15, 3) NOT NULL,
    unit_cost DECIMAL(15, 2),
    reference_type VARCHAR(50), -- 'work_order', 'purchase_order', 'adjustment'
    reference_id INTEGER,
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE material_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_transactions_tenant_isolation ON material_transactions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_material_transactions_material ON material_transactions(material_id);
CREATE INDEX idx_material_transactions_created ON material_transactions(created_at DESC);
```

**suppliers**
```sql
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    payment_terms VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, code)
);

ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
CREATE POLICY suppliers_tenant_isolation ON suppliers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**rfqs** (Request for Quotations)
```sql
CREATE TABLE rfqs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    rfq_number VARCHAR(100) UNIQUE NOT NULL,
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'sent', 'received', 'approved', 'rejected'
    requested_by INTEGER NOT NULL REFERENCES users(id),
    required_by_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE rfqs ENABLE ROW LEVEL SECURITY;
CREATE POLICY rfqs_tenant_isolation ON rfqs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 3. Project Management (5 tables)

**projects**
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_number VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    customer_name VARCHAR(255),
    customer_code VARCHAR(100),
    sap_sales_order VARCHAR(100),
    project_manager_id INTEGER REFERENCES users(id),
    primary_plant_id INTEGER REFERENCES plants(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'on_hold', 'completed', 'cancelled'
    priority VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    start_date DATE,
    planned_end_date DATE,
    actual_end_date DATE,
    budget DECIMAL(15, 2),
    actual_cost DECIMAL(15, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY projects_tenant_isolation ON projects
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_sap_so ON projects(sap_sales_order);
```

**project_bom** (Bill of Materials)
```sql
CREATE TABLE project_bom (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    material_id INTEGER NOT NULL REFERENCES materials(id),
    quantity_required DECIMAL(15, 3) NOT NULL,
    quantity_issued DECIMAL(15, 3) DEFAULT 0,
    quantity_consumed DECIMAL(15, 3) DEFAULT 0,
    unit_cost DECIMAL(15, 2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE project_bom ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_bom_tenant_isolation ON project_bom
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**project_documents**
```sql
CREATE TABLE project_documents (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    document_type VARCHAR(50) NOT NULL, -- 'drawing', 'specification', 'contract', 'other'
    document_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path
    file_size BIGINT,
    mime_type VARCHAR(100),
    version INTEGER DEFAULT 1,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_documents_tenant_isolation ON project_documents
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**rda_drawings** (RDA Drawing Monitoring)
```sql
CREATE TABLE rda_drawings (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    drawing_number VARCHAR(100) NOT NULL,
    drawing_name VARCHAR(255) NOT NULL,
    revision VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'in_review'
    submitted_by INTEGER REFERENCES users(id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    document_id INTEGER REFERENCES project_documents(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, project_id, drawing_number, revision)
);

ALTER TABLE rda_drawings ENABLE ROW LEVEL SECURITY;
CREATE POLICY rda_drawings_tenant_isolation ON rda_drawings
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**project_milestones**
```sql
CREATE TABLE project_milestones (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    planned_date DATE NOT NULL,
    actual_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'delayed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_milestones_tenant_isolation ON project_milestones
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 4. Production Management (10 tables)

**work_orders**
```sql
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_number VARCHAR(100) UNIQUE NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    department_id INTEGER REFERENCES departments(id),
    operation_type VARCHAR(100) NOT NULL, -- 'fabrication', 'machining', 'assembly', 'testing'
    description TEXT,
    quantity_ordered INTEGER NOT NULL,
    quantity_completed INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'planned', -- 'planned', 'released', 'in_progress', 'completed', 'cancelled'
    priority VARCHAR(50) DEFAULT 'medium',
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    sap_production_order VARCHAR(100),
    assigned_to INTEGER REFERENCES users(id),
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY work_orders_tenant_isolation ON work_orders
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_work_orders_plant ON work_orders(plant_id);
```

**work_order_operations**
```sql
CREATE TABLE work_order_operations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    operation_number INTEGER NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    description TEXT,
    planned_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2),
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    assigned_to INTEGER REFERENCES users(id),
    completed_by INTEGER REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(work_order_id, operation_number)
);

ALTER TABLE work_order_operations ENABLE ROW LEVEL SECURITY;
CREATE POLICY work_order_operations_tenant_isolation ON work_order_operations
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**lanes**
```sql
CREATE TABLE lanes (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    lane_number VARCHAR(50) NOT NULL,
    lane_name VARCHAR(255),
    lane_type VARCHAR(50), -- 'fabrication', 'assembly', 'testing'
    capacity INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'available', -- 'available', 'occupied', 'maintenance', 'inactive'
    current_work_order_id INTEGER REFERENCES work_orders(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, plant_id, lane_number)
);

ALTER TABLE lanes ENABLE ROW LEVEL SECURITY;
CREATE POLICY lanes_tenant_isolation ON lanes
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**lane_assignments**
```sql
CREATE TABLE lane_assignments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    lane_id INTEGER NOT NULL REFERENCES lanes(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    released_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    assigned_by INTEGER NOT NULL REFERENCES users(id)
);

ALTER TABLE lane_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY lane_assignments_tenant_isolation ON lane_assignments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**production_logs**
```sql
CREATE TABLE production_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    operation_id INTEGER REFERENCES work_order_operations(id),
    lane_id INTEGER REFERENCES lanes(id),
    log_type VARCHAR(50) NOT NULL, -- 'start', 'pause', 'resume', 'complete', 'issue'
    quantity_completed INTEGER,
    notes TEXT,
    logged_by INTEGER NOT NULL REFERENCES users(id),
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE production_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY production_logs_tenant_isolation ON production_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_production_logs_work_order ON production_logs(work_order_id);
CREATE INDEX idx_production_logs_logged_at ON production_logs(logged_at DESC);
```

**manpower_allocation**
```sql
CREATE TABLE manpower_allocation (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role VARCHAR(100), -- 'operator', 'supervisor', 'qc_inspector'
    allocated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    released_at TIMESTAMP WITH TIME ZONE,
    hours_worked DECIMAL(10, 2),
    allocated_by INTEGER NOT NULL REFERENCES users(id)
);

ALTER TABLE manpower_allocation ENABLE ROW LEVEL SECURITY;
CREATE POLICY manpower_allocation_tenant_isolation ON manpower_allocation
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**rbs_schedules** (Resource-Based Scheduling)
```sql
CREATE TABLE rbs_schedules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    schedule_date DATE NOT NULL,
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    lane_id INTEGER REFERENCES lanes(id),
    planned_start_time TIME,
    planned_end_time TIME,
    actual_start_time TIME,
    actual_end_time TIME,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE rbs_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY rbs_schedules_tenant_isolation ON rbs_schedules
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_rbs_schedules_date ON rbs_schedules(schedule_date);
CREATE INDEX idx_rbs_schedules_plant ON rbs_schedules(plant_id);
```

**rps_sheets** (Resource Planning Sheet)
```sql
CREATE TABLE rps_sheets (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    sheet_number VARCHAR(100) NOT NULL,
    planning_period_start DATE NOT NULL,
    planning_period_end DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'approved', 'archived'
    created_by INTEGER NOT NULL REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, sheet_number)
);

ALTER TABLE rps_sheets ENABLE ROW LEVEL SECURITY;
CREATE POLICY rps_sheets_tenant_isolation ON rps_sheets
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**daily_work_logs**
```sql
CREATE TABLE daily_work_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    work_date DATE NOT NULL,
    shift VARCHAR(50), -- 'morning', 'afternoon', 'night'
    work_order_id INTEGER REFERENCES work_orders(id),
    lane_id INTEGER REFERENCES lanes(id),
    workers_present INTEGER,
    hours_worked DECIMAL(10, 2),
    quantity_produced INTEGER,
    notes TEXT,
    logged_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE daily_work_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY daily_work_logs_tenant_isolation ON daily_work_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_daily_work_logs_date ON daily_work_logs(work_date DESC);
CREATE INDEX idx_daily_work_logs_plant ON daily_work_logs(plant_id);
```

**delivery_predictions**
```sql
CREATE TABLE delivery_predictions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    predicted_date DATE NOT NULL,
    confidence_level VARCHAR(50), -- 'low', 'medium', 'high'
    factors TEXT, -- JSON array of factors affecting prediction
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    calculated_by VARCHAR(100) DEFAULT 'system'
);

ALTER TABLE delivery_predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY delivery_predictions_tenant_isolation ON delivery_predictions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 5. Quality Management (4 tables)

**ncr_reports** (Non-Conformance Reports)
```sql
CREATE TABLE ncr_reports (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    ncr_number VARCHAR(100) UNIQUE NOT NULL,
    work_order_id INTEGER REFERENCES work_orders(id),
    project_id INTEGER REFERENCES projects(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    ncr_type VARCHAR(50) NOT NULL, -- 'material', 'process', 'final_inspection'
    severity VARCHAR(50) NOT NULL, -- 'minor', 'major', 'critical'
    description TEXT NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    preventive_action TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'open', -- 'open', 'in_review', 'resolved', 'closed'
    detected_by INTEGER NOT NULL REFERENCES users(id),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_to INTEGER REFERENCES users(id),
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    closed_by INTEGER REFERENCES users(id),
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE ncr_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY ncr_reports_tenant_isolation ON ncr_reports
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_ncr_reports_status ON ncr_reports(status);
CREATE INDEX idx_ncr_reports_project ON ncr_reports(project_id);
```

**ncr_photos**
```sql
CREATE TABLE ncr_photos (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    ncr_id INTEGER NOT NULL REFERENCES ncr_reports(id),
    photo_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path
    file_size BIGINT,
    mime_type VARCHAR(100),
    caption TEXT,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE ncr_photos ENABLE ROW LEVEL SECURITY;
CREATE POLICY ncr_photos_tenant_isolation ON ncr_photos
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**quality_inspections**
```sql
CREATE TABLE quality_inspections (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    inspection_type VARCHAR(50) NOT NULL, -- 'in_process', 'final', 'incoming'
    inspection_date DATE NOT NULL,
    inspector_id INTEGER NOT NULL REFERENCES users(id),
    result VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'conditional'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE quality_inspections ENABLE ROW LEVEL SECURITY;
CREATE POLICY quality_inspections_tenant_isolation ON quality_inspections
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**quality_checkpoints**
```sql
CREATE TABLE quality_checkpoints (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    inspection_id INTEGER NOT NULL REFERENCES quality_inspections(id),
    checkpoint_name VARCHAR(255) NOT NULL,
    expected_value VARCHAR(255),
    actual_value VARCHAR(255),
    result VARCHAR(50) NOT NULL, -- 'passed', 'failed'
    notes TEXT
);

ALTER TABLE quality_checkpoints ENABLE ROW LEVEL SECURITY;
CREATE POLICY quality_checkpoints_tenant_isolation ON quality_checkpoints
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 6. Logistics & Tracking (4 tables)

**shipments**
```sql
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    shipment_number VARCHAR(100) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    from_plant_id INTEGER REFERENCES plants(id),
    to_location VARCHAR(255),
    shipment_type VARCHAR(50), -- 'internal_transfer', 'customer_delivery', 'supplier_return'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'in_transit', 'delivered', 'cancelled'
    carrier VARCHAR(255),
    tracking_number VARCHAR(255),
    planned_shipment_date DATE,
    actual_shipment_date DATE,
    planned_delivery_date DATE,
    actual_delivery_date DATE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
CREATE POLICY shipments_tenant_isolation ON shipments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**shipment_items**
```sql
CREATE TABLE shipment_items (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    shipment_id INTEGER NOT NULL REFERENCES shipments(id),
    material_id INTEGER REFERENCES materials(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    quantity DECIMAL(15, 3) NOT NULL,
    packaging VARCHAR(255),
    notes TEXT
);

ALTER TABLE shipment_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY shipment_items_tenant_isolation ON shipment_items
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**qr_code_scans**
```sql
CREATE TABLE qr_code_scans (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    qr_code_data TEXT NOT NULL,
    scan_type VARCHAR(50) NOT NULL, -- 'material_receipt', 'work_order_start', 'shipment', etc.
    reference_type VARCHAR(50), -- 'material', 'work_order', 'shipment'
    reference_id INTEGER,
    plant_id INTEGER REFERENCES plants(id),
    scanned_by INTEGER NOT NULL REFERENCES users(id),
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    location VARCHAR(255),
    notes TEXT
);

ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY qr_code_scans_tenant_isolation ON qr_code_scans
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_qr_code_scans_data ON qr_code_scans(qr_code_data);
CREATE INDEX idx_qr_code_scans_scanned_at ON qr_code_scans(scanned_at DESC);
```

**barcode_labels**
```sql
CREATE TABLE barcode_labels (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    label_type VARCHAR(50) NOT NULL, -- 'material', 'work_order', 'shipment'
    reference_type VARCHAR(50) NOT NULL,
    reference_id INTEGER NOT NULL,
    barcode_format VARCHAR(50), -- 'code128', 'qr', 'datamatrix'
    barcode_data VARCHAR(255) NOT NULL,
    file_path VARCHAR(500), -- MinIO path to generated image
    generated_by INTEGER NOT NULL REFERENCES users(id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE barcode_labels ENABLE ROW LEVEL SECURITY;
CREATE POLICY barcode_labels_tenant_isolation ON barcode_labels
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_barcode_labels_data ON barcode_labels(barcode_data);
```

#### 7. SAP Integration (3 tables)

**sap_sync_logs**
```sql
CREATE TABLE sap_sync_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    sync_type VARCHAR(50) NOT NULL, -- 'sales_order', 'production_order', 'material_master', 'invoice'
    sync_direction VARCHAR(50) NOT NULL, -- 'inbound', 'outbound'
    entity_type VARCHAR(50),
    entity_id INTEGER,
    sap_reference VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'pending', 'success', 'error', 'retry'
    request_payload TEXT,
    response_payload TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE sap_sync_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sap_sync_logs_tenant_isolation ON sap_sync_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_sap_sync_logs_status ON sap_sync_logs(status);
CREATE INDEX idx_sap_sync_logs_synced_at ON sap_sync_logs(synced_at DESC);
```

**sap_mappings**
```sql
CREATE TABLE sap_mappings (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    entity_type VARCHAR(50) NOT NULL, -- 'project', 'material', 'plant'
    entity_id INTEGER NOT NULL,
    sap_reference VARCHAR(255) NOT NULL,
    mapping_type VARCHAR(50), -- 'sales_order', 'production_order', 'material_number'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, entity_type, entity_id, mapping_type)
);

ALTER TABLE sap_mappings ENABLE ROW LEVEL SECURITY;
CREATE POLICY sap_mappings_tenant_isolation ON sap_mappings
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**sap_queue**
```sql
CREATE TABLE sap_queue (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    sync_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    payload TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

ALTER TABLE sap_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY sap_queue_tenant_isolation ON sap_queue
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_sap_queue_status ON sap_queue(status, priority);
```

#### 8. Reporting & Analytics (3 tables)

**reports**
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    report_code VARCHAR(50) NOT NULL, -- 'production_summary', 'otd_tracking', 'ncr_analysis'
    report_name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50), -- 'operational', 'management', 'compliance'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, report_code)
);

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY reports_tenant_isolation ON reports
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**report_executions**
```sql
CREATE TABLE report_executions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    report_id INTEGER NOT NULL REFERENCES reports(id),
    parameters TEXT, -- JSON parameters for filtering
    file_path VARCHAR(500), -- MinIO path to generated report (PDF/CSV)
    file_format VARCHAR(50), -- 'pdf', 'csv', 'xlsx'
    executed_by INTEGER NOT NULL REFERENCES users(id),
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE report_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY report_executions_tenant_isolation ON report_executions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**dashboards**
```sql
CREATE TABLE dashboards (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    dashboard_code VARCHAR(50) NOT NULL,
    dashboard_name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_config TEXT, -- JSON configuration for widgets
    is_default BOOLEAN DEFAULT FALSE,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, dashboard_code)
);

ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;
CREATE POLICY dashboards_tenant_isolation ON dashboards
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 9. Audit & System (5 tables)

**audit_logs**
```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    changed_fields TEXT[], -- Array of changed field names
    performed_by INTEGER NOT NULL REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_performed_at ON audit_logs(performed_at DESC);
```

**notifications**
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    notification_type VARCHAR(50) NOT NULL, -- 'ncr_created', 'work_order_delayed', 'material_low_stock'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY notifications_tenant_isolation ON notifications
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
```

**system_settings**
```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id), -- NULL for global settings
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT NOT NULL,
    data_type VARCHAR(50), -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, setting_key)
);
```

**file_uploads**
```sql
CREATE TABLE file_uploads (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path
    file_size BIGINT,
    mime_type VARCHAR(100),
    bucket_name VARCHAR(100),
    entity_type VARCHAR(50), -- 'ncr_photo', 'project_document', 'report'
    entity_id INTEGER,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
CREATE POLICY file_uploads_tenant_isolation ON file_uploads
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**celery_task_results**
```sql
CREATE TABLE celery_task_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'
    result TEXT,
    traceback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_celery_task_results_status ON celery_task_results(status);
```



#### 10. MES Modules (15 tables)

**machines**
```sql
CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    machine_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    machine_type VARCHAR(100), -- 'CNC', 'Lathe', 'Press', 'Welder', etc.
    capacity_units_per_hour DECIMAL(10,2), -- Rated capacity
    status VARCHAR(50) DEFAULT 'available', -- 'available', 'running', 'idle', 'down', 'setup', 'maintenance', 'decommissioned'
    current_work_order_id INTEGER REFERENCES work_orders(id),
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    installation_date DATE,
    manufacturer VARCHAR(255),
    model_number VARCHAR(100),
    serial_number VARCHAR(100),
    purchase_cost DECIMAL(12,2),
    location VARCHAR(255), -- Physical location in plant
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, machine_code)
);

ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
CREATE POLICY machines_tenant_isolation ON machines
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_machines_plant ON machines(plant_id);
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_next_maintenance ON machines(next_maintenance_due) WHERE is_active = TRUE;
```

**machine_status_history**
```sql
CREATE TABLE machine_status_history (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    work_order_id INTEGER REFERENCES work_orders(id),
    reason_code VARCHAR(100), -- For 'down' status transitions
    notes TEXT,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_minutes INTEGER -- Calculated when status changes again
);

ALTER TABLE machine_status_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY machine_status_history_tenant_isolation ON machine_status_history
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_machine_status_history_machine ON machine_status_history(machine_id, changed_at DESC);
CREATE INDEX idx_machine_status_history_status ON machine_status_history(new_status);
```

**shifts**
```sql
CREATE TABLE shifts (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    name VARCHAR(100) NOT NULL, -- 'Day Shift', 'Night Shift', 'A Shift'
    start_time TIME NOT NULL, -- e.g., '06:00'
    end_time TIME NOT NULL, -- e.g., '14:00'
    break_duration_minutes INTEGER DEFAULT 30,
    active_days VARCHAR(50)[], -- ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    production_target_units INTEGER, -- Target units per shift
    oee_target_percent DECIMAL(5,2), -- Target OEE percentage
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, plant_id, name)
);

ALTER TABLE shifts ENABLE ROW LEVEL SECURITY;
CREATE POLICY shifts_tenant_isolation ON shifts
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_shifts_plant ON shifts(plant_id);
```

**shift_handovers**
```sql
CREATE TABLE shift_handovers (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    shift_id INTEGER NOT NULL REFERENCES shifts(id),
    date DATE NOT NULL,
    handover_notes TEXT NOT NULL,
    wip_summary TEXT, -- JSON array of work-in-progress work orders
    issues_reported TEXT, -- JSON array of issues/problems
    logged_by INTEGER NOT NULL REFERENCES users(id),
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, shift_id, date)
);

ALTER TABLE shift_handovers ENABLE ROW LEVEL SECURITY;
CREATE POLICY shift_handovers_tenant_isolation ON shift_handovers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_shift_handovers_shift_date ON shift_handovers(shift_id, date DESC);
```

**shift_performance**
```sql
CREATE TABLE shift_performance (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    shift_id INTEGER NOT NULL REFERENCES shifts(id),
    date DATE NOT NULL,
    target_units INTEGER,
    actual_units INTEGER,
    target_attainment_percent DECIMAL(5,2), -- (actual / target) * 100
    oee_percent DECIMAL(5,2),
    downtime_minutes INTEGER,
    quality_fpy_percent DECIMAL(5,2),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, shift_id, date)
);

ALTER TABLE shift_performance ENABLE ROW LEVEL SECURITY;
CREATE POLICY shift_performance_tenant_isolation ON shift_performance
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_shift_performance_shift_date ON shift_performance(shift_id, date DESC);
```

**pm_schedules**
```sql
CREATE TABLE pm_schedules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    pm_type VARCHAR(50) NOT NULL, -- 'inspection', 'lubrication', 'calibration', 'parts_replacement'
    frequency_type VARCHAR(50) NOT NULL, -- 'calendar' or 'meter'
    frequency_value INTEGER NOT NULL, -- Number of days or hours
    frequency_unit VARCHAR(50) NOT NULL, -- 'days', 'weeks', 'months' OR 'hours', 'cycles'
    lead_time_days INTEGER DEFAULT 7, -- Generate WO this many days before due
    estimated_duration_hours DECIMAL(5,2),
    task_checklist TEXT, -- JSON array of tasks
    assigned_technician_id INTEGER REFERENCES users(id),
    last_pm_date DATE,
    next_due_date DATE,
    last_meter_value INTEGER, -- For meter-based schedules
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE pm_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY pm_schedules_tenant_isolation ON pm_schedules
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_pm_schedules_machine ON pm_schedules(machine_id);
CREATE INDEX idx_pm_schedules_next_due ON pm_schedules(next_due_date) WHERE is_active = TRUE;
```

**pm_work_orders**
```sql
CREATE TABLE pm_work_orders (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_number VARCHAR(50) UNIQUE NOT NULL, -- 'PM-2025-001'
    pm_schedule_id INTEGER NOT NULL REFERENCES pm_schedules(id),
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    pm_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'planned', -- 'planned', 'in_progress', 'completed', 'cancelled'
    scheduled_date DATE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    checklist_completion TEXT, -- JSON with completed tasks
    completion_notes TEXT,
    assigned_technician_id INTEGER REFERENCES users(id),
    performed_by INTEGER REFERENCES users(id),
    priority VARCHAR(50) DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'
    is_overdue BOOLEAN GENERATED ALWAYS AS (
        CASE WHEN status IN ('planned', 'in_progress') AND scheduled_date < CURRENT_DATE 
        THEN TRUE ELSE FALSE END
    ) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE pm_work_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY pm_work_orders_tenant_isolation ON pm_work_orders
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_pm_work_orders_machine ON pm_work_orders(machine_id);
CREATE INDEX idx_pm_work_orders_status ON pm_work_orders(status);
CREATE INDEX idx_pm_work_orders_scheduled ON pm_work_orders(scheduled_date);
```

**downtime_events**
```sql
CREATE TABLE downtime_events (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    machine_id INTEGER NOT NULL REFERENCES machines(id),
    work_order_id INTEGER REFERENCES work_orders(id),
    downtime_reason_code VARCHAR(100) NOT NULL, -- 'mechanical_failure', 'material_shortage', 'operator_issue', etc.
    downtime_category VARCHAR(50), -- 'equipment', 'material', 'quality', 'setup', 'process'
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER, -- Calculated when ended_at is set
    notes TEXT,
    resolution_notes TEXT,
    reported_by INTEGER REFERENCES users(id),
    resolved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY downtime_events_tenant_isolation ON downtime_events
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_downtime_events_machine ON downtime_events(machine_id, started_at DESC);
CREATE INDEX idx_downtime_events_reason ON downtime_events(downtime_reason_code);
CREATE INDEX idx_downtime_events_category ON downtime_events(downtime_category);
```

**inspection_plans**
```sql
CREATE TABLE inspection_plans (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    product_id INTEGER REFERENCES products(id), -- Which product this applies to
    plan_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, product_id, plan_name)
);

ALTER TABLE inspection_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_plans_tenant_isolation ON inspection_plans
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_inspection_plans_product ON inspection_plans(product_id);
```

**inspection_points**
```sql
CREATE TABLE inspection_points (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    inspection_plan_id INTEGER NOT NULL REFERENCES inspection_plans(id),
    point_name VARCHAR(255) NOT NULL, -- 'First Piece', 'In-Process', 'Final'
    frequency_type VARCHAR(50) NOT NULL, -- 'first_piece', 'periodic', 'sampling', 'final'
    frequency_value INTEGER, -- For 'periodic': every N units
    sampling_plan TEXT, -- JSON with AQL, sample size, accept/reject numbers
    sequence_order INTEGER, -- Display order
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE inspection_points ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_points_tenant_isolation ON inspection_points
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_inspection_points_plan ON inspection_points(inspection_plan_id);
```

**inspection_characteristics**
```sql
CREATE TABLE inspection_characteristics (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    inspection_point_id INTEGER NOT NULL REFERENCES inspection_points(id),
    characteristic_name VARCHAR(255) NOT NULL, -- 'Shaft Diameter', 'Weight', 'Surface Finish'
    characteristic_type VARCHAR(50) NOT NULL, -- 'dimensional', 'weight', 'visual', 'functional'
    specification VARCHAR(255), -- Target value: '25mm', '500g', 'Pass/Fail'
    usl DECIMAL(12,4), -- Upper Spec Limit
    lsl DECIMAL(12,4), -- Lower Spec Limit
    tolerance VARCHAR(50), -- '±0.1mm'
    measurement_method VARCHAR(255), -- 'Micrometer', 'Scale', 'Visual comparison'
    measurement_unit VARCHAR(50), -- 'mm', 'g', 'kg'
    control_chart_enabled BOOLEAN DEFAULT FALSE, -- Enable SPC control charts
    sequence_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE inspection_characteristics ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_characteristics_tenant_isolation ON inspection_characteristics
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_inspection_characteristics_point ON inspection_characteristics(inspection_point_id);
```

**inspection_logs**
```sql
CREATE TABLE inspection_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    inspection_point_id INTEGER NOT NULL REFERENCES inspection_points(id),
    overall_result VARCHAR(50) NOT NULL, -- 'pass', 'fail'
    inspected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    inspector_id INTEGER NOT NULL REFERENCES users(id),
    notes TEXT,
    ncr_report_id INTEGER REFERENCES ncr_reports(id), -- Created if failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE inspection_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_logs_tenant_isolation ON inspection_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_inspection_logs_work_order ON inspection_logs(work_order_id);
CREATE INDEX idx_inspection_logs_result ON inspection_logs(overall_result);
CREATE INDEX idx_inspection_logs_inspected_at ON inspection_logs(inspected_at DESC);
```

**inspection_measurements**
```sql
CREATE TABLE inspection_measurements (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    inspection_log_id INTEGER NOT NULL REFERENCES inspection_logs(id),
    characteristic_id INTEGER NOT NULL REFERENCES inspection_characteristics(id),
    measured_value DECIMAL(12,4),
    measured_text VARCHAR(255), -- For non-numeric values like 'Pass', 'Fail', 'Good'
    within_tolerance BOOLEAN, -- TRUE if measured_value is within USL/LSL
    result VARCHAR(50), -- 'pass', 'fail'
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE inspection_measurements ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_measurements_tenant_isolation ON inspection_measurements
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_inspection_measurements_log ON inspection_measurements(inspection_log_id);
CREATE INDEX idx_inspection_measurements_characteristic ON inspection_measurements(characteristic_id, measured_at DESC);
```

**lot_numbers**
```sql
CREATE TABLE lot_numbers (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    lot_number VARCHAR(100) UNIQUE NOT NULL, -- 'STL001-20251106-001'
    material_id INTEGER NOT NULL REFERENCES materials(id),
    quantity DECIMAL(12,3) NOT NULL,
    receipt_date DATE NOT NULL,
    expiry_date DATE,
    supplier_id INTEGER REFERENCES suppliers(id),
    supplier_lot_number VARCHAR(100), -- Supplier's lot number
    certificate_file_id INTEGER REFERENCES file_uploads(id), -- Material certificate
    remaining_quantity DECIMAL(12,3), -- Quantity not yet issued
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE lot_numbers ENABLE ROW LEVEL SECURITY;
CREATE POLICY lot_numbers_tenant_isolation ON lot_numbers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_lot_numbers_material ON lot_numbers(material_id);
CREATE INDEX idx_lot_numbers_expiry ON lot_numbers(expiry_date) WHERE is_active = TRUE;
CREATE INDEX idx_lot_numbers_remaining ON lot_numbers(material_id, remaining_quantity) WHERE remaining_quantity > 0;
```

**serial_numbers**
```sql
CREATE TABLE serial_numbers (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    serial_number VARCHAR(100) UNIQUE NOT NULL, -- 'PUMP-2511-00001'
    product_id INTEGER REFERENCES products(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    production_date DATE NOT NULL,
    shipment_id INTEGER REFERENCES shipments(id), -- If shipped
    shipped_date DATE,
    customer_id INTEGER REFERENCES customers(id),
    status VARCHAR(50) DEFAULT 'in_stock', -- 'in_stock', 'shipped', 'returned', 'scrapped'
    location VARCHAR(255), -- Current physical location
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

ALTER TABLE serial_numbers ENABLE ROW LEVEL SECURITY;
CREATE POLICY serial_numbers_tenant_isolation ON serial_numbers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_serial_numbers_product ON serial_numbers(product_id);
CREATE INDEX idx_serial_numbers_work_order ON serial_numbers(work_order_id);
CREATE INDEX idx_serial_numbers_status ON serial_numbers(status);
CREATE INDEX idx_serial_numbers_shipment ON serial_numbers(shipment_id) WHERE shipment_id IS NOT NULL;
```

**genealogy_records**
```sql
CREATE TABLE genealogy_records (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    parent_type VARCHAR(50) NOT NULL, -- 'lot_number', 'serial_number'
    parent_id INTEGER NOT NULL, -- ID in lot_numbers or serial_numbers table
    child_type VARCHAR(50) NOT NULL, -- 'lot_number', 'serial_number', 'work_order'
    child_id INTEGER NOT NULL,
    relationship_type VARCHAR(50), -- 'consumed', 'produced', 'assembled_into'
    quantity_used DECIMAL(12,3), -- For lot-to-product relationships
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE genealogy_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY genealogy_records_tenant_isolation ON genealogy_records
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE INDEX idx_genealogy_records_parent ON genealogy_records(parent_type, parent_id);
CREATE INDEX idx_genealogy_records_child ON genealogy_records(child_type, child_id);
```

---

## Domain Model

### Core Entities Structure (DDD)

Each domain entity follows the same pattern established in `User` entity:

**Common Structure**:
```python
class EntityName:
    def __init__(self, id, organization_id, ...other_fields):
        self._id = id
        self._organization_id = organization_id
        # Value objects
        # Other attributes
    
    @property
    def id(self) -> int:
        return self._id
    
    # Business logic methods
    def perform_business_action(self) -> None:
        # Business rules validation
        # State mutation
        self._update_timestamp()
    
    def _update_timestamp(self) -> None:
        self._updated_at = datetime.utcnow()
```

### Key Domain Entities by Module

#### Multi-Tenancy Module
- `Organization` - Tenant root entity
- `Plant` - Manufacturing site within organization
- `Department` - Organizational unit within plant
- `User` - System user with plant access

#### Material Management Module
- `Material` - Material master with barcode
- `MaterialInventory` - Stock levels per plant
- `MaterialTransaction` - Inventory movement
- `Supplier` - Vendor master
- `RFQ` - Request for quotation

#### Project Management Module
- `Project` - Manufacturing project
- `ProjectBOM` - Bill of materials for project
- `RDADrawing` - Drawing approval workflow
- `ProjectMilestone` - Project timeline tracking

#### Production Management Module
- `WorkOrder` - Production order
- `WorkOrderOperation` - Operation within work order
- `Lane` - Production line/station
- `ProductionLog` - Real-time production tracking
- `RBSSchedule` - Resource-based schedule
- `RPSSheet` - Resource planning sheet

#### Quality Management Module
- `NCRReport` - Non-conformance report
- `QualityInspection` - Inspection record
- `QualityCheckpoint` - Inspection checkpoint result

#### Logistics Module
- `Shipment` - Outbound/inbound shipment
- `QRCodeScan` - Tracking scan event

#### SAP Integration Module
- `SAPSyncLog` - Integration log
- `SAPMapping` - Entity-to-SAP mapping

### Value Objects

**Existing**:
- `Email` - Email validation
- `Username` - Username validation

**New Value Objects**:
```python
# Material Module
class MaterialCode:
    def __init__(self, value: str):
        # Validation logic
        self._value = value.upper().strip()

class UnitOfMeasure:
    VALID_UNITS = ['kg', 'pcs', 'meter', 'liter', ...]
    def __init__(self, value: str):
        # Validation
        
# Project Module
class ProjectNumber:
    def __init__(self, value: str):
        # Format: PRJ-YYYY-NNNN
        
class OrderStatus:
    VALID_STATUSES = ['draft', 'active', 'completed', ...]
    def __init__(self, value: str):
        # Validation

# Production Module
class WorkOrderNumber:
    def __init__(self, value: str):
        # Format: WO-PLANT-YYYY-NNNN

class LaneNumber:
    def __init__(self, value: str):
        # Validation
```

---

## API Design

### API Structure (RESTful)

**Base URL**: `/api/v1`

### Authentication & Multi-Tenancy Endpoints

```
POST   /api/v1/auth/login               # Login with email/password
POST   /api/v1/auth/refresh             # Refresh access token
POST   /api/v1/auth/logout              # Logout
GET    /api/v1/auth/me                  # Current user info
```

### Organization Management

```
GET    /api/v1/organizations            # List organizations (superadmin only)
POST   /api/v1/organizations            # Create organization
GET    /api/v1/organizations/{id}       # Get organization details
PUT    /api/v1/organizations/{id}       # Update organization
DELETE /api/v1/organizations/{id}       # Deactivate organization
```

### Plant Management

```
GET    /api/v1/plants                   # List plants (filtered by org context)
POST   /api/v1/plants                   # Create plant
GET    /api/v1/plants/{id}              # Get plant details
PUT    /api/v1/plants/{id}              # Update plant
DELETE /api/v1/plants/{id}              # Deactivate plant
```

### User Management

```
GET    /api/v1/users                    # List users
POST   /api/v1/users                    # Create user
GET    /api/v1/users/{id}               # Get user
PUT    /api/v1/users/{id}               # Update user
DELETE /api/v1/users/{id}               # Deactivate user
POST   /api/v1/users/{id}/assign-plant  # Assign user to plant
POST   /api/v1/users/{id}/assign-role   # Assign role to user
```

### Material Management

```
GET    /api/v1/materials                # List materials (with filters)
POST   /api/v1/materials                # Create material
GET    /api/v1/materials/{id}           # Get material
PUT    /api/v1/materials/{id}           # Update material
DELETE /api/v1/materials/{id}           # Deactivate material
GET    /api/v1/materials/{id}/barcode   # Generate barcode image
GET    /api/v1/materials/{id}/qrcode    # Generate QR code image
GET    /api/v1/materials/{id}/inventory # Get inventory by plant

POST   /api/v1/inventory/transactions   # Record material transaction
GET    /api/v1/inventory/summary        # Inventory summary by plant
```

### Project Management

```
GET    /api/v1/projects                 # List projects
POST   /api/v1/projects                 # Create project
GET    /api/v1/projects/{id}            # Get project
PUT    /api/v1/projects/{id}            # Update project
DELETE /api/v1/projects/{id}            # Cancel project
GET    /api/v1/projects/{id}/bom        # Get project BOM
POST   /api/v1/projects/{id}/bom        # Add BOM item
GET    /api/v1/projects/{id}/documents  # List documents
POST   /api/v1/projects/{id}/documents  # Upload document
GET    /api/v1/projects/{id}/milestones # List milestones
POST   /api/v1/projects/{id}/milestones # Create milestone
```

### RDA Drawing Management

```
GET    /api/v1/rda-drawings             # List drawings
POST   /api/v1/rda-drawings             # Submit drawing
GET    /api/v1/rda-drawings/{id}        # Get drawing
PUT    /api/v1/rda-drawings/{id}        # Update drawing
POST   /api/v1/rda-drawings/{id}/approve   # Approve drawing
POST   /api/v1/rda-drawings/{id}/reject    # Reject drawing
```

### Work Order Management

```
GET    /api/v1/work-orders              # List work orders
POST   /api/v1/work-orders              # Create work order
GET    /api/v1/work-orders/{id}         # Get work order
PUT    /api/v1/work-orders/{id}         # Update work order
DELETE /api/v1/work-orders/{id}         # Cancel work order
POST   /api/v1/work-orders/{id}/start   # Start work order
POST   /api/v1/work-orders/{id}/complete # Complete work order
GET    /api/v1/work-orders/{id}/operations # List operations
POST   /api/v1/work-orders/{id}/operations # Add operation
POST   /api/v1/work-orders/{id}/assign-manpower # Assign workers
```

### Lane Management

```
GET    /api/v1/lanes                    # List lanes by plant
POST   /api/v1/lanes                    # Create lane
GET    /api/v1/lanes/{id}               # Get lane
PUT    /api/v1/lanes/{id}               # Update lane
DELETE /api/v1/lanes/{id}               # Deactivate lane
POST   /api/v1/lanes/{id}/assign        # Assign work order to lane
POST   /api/v1/lanes/{id}/release       # Release lane
GET    /api/v1/lanes/{id}/history       # Lane assignment history
```

### Production Logging

```
POST   /api/v1/production-logs          # Create production log
GET    /api/v1/production-logs          # List logs (by work order, date)
GET    /api/v1/daily-work-logs          # Daily work summary
POST   /api/v1/daily-work-logs          # Create daily log
```

### Scheduling (RBS/RPS)

```
GET    /api/v1/rbs-schedules            # List schedules
POST   /api/v1/rbs-schedules            # Create schedule
GET    /api/v1/rbs-schedules/{id}       # Get schedule
PUT    /api/v1/rbs-schedules/{id}       # Update schedule
GET    /api/v1/rbs-schedules/calendar   # Calendar view

GET    /api/v1/rps-sheets               # List RPS sheets
POST   /api/v1/rps-sheets               # Create RPS sheet
GET    /api/v1/rps-sheets/{id}          # Get sheet
POST   /api/v1/rps-sheets/{id}/approve  # Approve sheet
```

### Quality Management

```
GET    /api/v1/ncr-reports              # List NCR reports
POST   /api/v1/ncr-reports              # Create NCR
GET    /api/v1/ncr-reports/{id}         # Get NCR
PUT    /api/v1/ncr-reports/{id}         # Update NCR
POST   /api/v1/ncr-reports/{id}/photos  # Upload NCR photo
POST   /api/v1/ncr-reports/{id}/assign  # Assign NCR
POST   /api/v1/ncr-reports/{id}/resolve # Resolve NCR
POST   /api/v1/ncr-reports/{id}/close   # Close NCR

GET    /api/v1/quality-inspections      # List inspections
POST   /api/v1/quality-inspections      # Create inspection
GET    /api/v1/quality-inspections/{id} # Get inspection
```

### Logistics & Tracking

```
GET    /api/v1/shipments                # List shipments
POST   /api/v1/shipments                # Create shipment
GET    /api/v1/shipments/{id}           # Get shipment
PUT    /api/v1/shipments/{id}           # Update shipment
POST   /api/v1/shipments/{id}/dispatch  # Dispatch shipment
POST   /api/v1/shipments/{id}/deliver   # Mark as delivered

POST   /api/v1/qr-scans                 # Record QR scan
GET    /api/v1/qr-scans/history         # Scan history
GET    /api/v1/qr-scans/lookup/{code}   # Lookup by QR code
```

### Barcode Generation

```
GET    /api/v1/barcodes/{type}/{id}     # Generate barcode image
                                         # type: material, work_order, shipment
                                         # Returns PNG image
```

### Reporting & Analytics

```
GET    /api/v1/reports                  # List available reports
POST   /api/v1/reports/{code}/execute   # Execute report (returns CSV/PDF)
GET    /api/v1/reports/executions       # Report execution history

GET    /api/v1/dashboards               # List dashboards
GET    /api/v1/dashboards/{code}        # Get dashboard config
GET    /api/v1/dashboards/{code}/data   # Get dashboard data

# Pre-defined report endpoints
GET    /api/v1/reports/production-summary      # Production summary
GET    /api/v1/reports/otd-tracking            # On-time delivery
GET    /api/v1/reports/ncr-analysis            # NCR analysis
GET    /api/v1/reports/material-consumption    # Material usage
GET    /api/v1/reports/manpower-utilization    # Manpower report
```

### SAP Integration

```
GET    /api/v1/sap/sync-logs            # List sync logs
POST   /api/v1/sap/sync/sales-orders    # Trigger SO sync
POST   /api/v1/sap/sync/production-orders # Trigger PO sync
POST   /api/v1/sap/sync/materials       # Trigger material sync
GET    /api/v1/sap/mappings             # List entity mappings
POST   /api/v1/sap/mappings             # Create mapping
```

### Notifications

```
GET    /api/v1/notifications            # List user notifications
PUT    /api/v1/notifications/{id}/read  # Mark as read
PUT    /api/v1/notifications/read-all   # Mark all as read
```



### Equipment/Machine Management

```
GET    /api/v1/machines                 # List machines
POST   /api/v1/machines                 # Create machine
GET    /api/v1/machines/{id}            # Get machine details
PUT    /api/v1/machines/{id}            # Update machine
DELETE /api/v1/machines/{id}            # Deactivate machine
PUT    /api/v1/machines/{id}/status     # Update machine status
GET    /api/v1/machines/{id}/utilization # Get utilization metrics
GET    /api/v1/machines/{id}/history    # Get status history
```

### Shift Management

```
GET    /api/v1/shifts                   # List shift patterns
POST   /api/v1/shifts                   # Create shift
GET    /api/v1/shifts/{id}              # Get shift details
PUT    /api/v1/shifts/{id}              # Update shift
DELETE /api/v1/shifts/{id}              # Deactivate shift
POST   /api/v1/shift-handovers          # Log shift handover
GET    /api/v1/shift-handovers          # List handovers
GET    /api/v1/shift-performance        # Get shift performance metrics
```

### Maintenance Management

```
GET    /api/v1/pm-schedules             # List PM schedules
POST   /api/v1/pm-schedules             # Create PM schedule
GET    /api/v1/pm-schedules/{id}        # Get PM schedule
PUT    /api/v1/pm-schedules/{id}        # Update PM schedule
DELETE /api/v1/pm-schedules/{id}        # Deactivate PM schedule
GET    /api/v1/pm-work-orders           # List PM work orders
POST   /api/v1/pm-work-orders           # Create PM work order
GET    /api/v1/pm-work-orders/{id}      # Get PM work order
PUT    /api/v1/pm-work-orders/{id}      # Update PM work order
POST   /api/v1/pm-work-orders/{id}/start  # Start PM work
POST   /api/v1/pm-work-orders/{id}/complete # Complete PM work
POST   /api/v1/downtime-events          # Log downtime event
GET    /api/v1/downtime-events          # List downtime events
GET    /api/v1/maintenance-metrics      # Get MTBF, MTTR, PM compliance
```

### Visual Production Scheduling

```
GET    /api/v1/schedule/gantt           # Get Gantt chart data
PUT    /api/v1/work-orders/{id}/reschedule # Reschedule work order
PUT    /api/v1/work-orders/{id}/reassign-lane # Reassign to different lane
POST   /api/v1/schedule/validate        # Validate schedule conflicts
POST   /api/v1/schedule/auto-schedule   # Auto-generate optimal schedule
```

### Inspection & Quality

```
GET    /api/v1/inspection-plans         # List inspection plans
POST   /api/v1/inspection-plans         # Create inspection plan
GET    /api/v1/inspection-plans/{id}    # Get inspection plan
PUT    /api/v1/inspection-plans/{id}    # Update inspection plan
POST   /api/v1/inspection-logs          # Log inspection results
GET    /api/v1/inspection-logs          # List inspection logs
GET    /api/v1/inspection-logs/{id}     # Get inspection log details
GET    /api/v1/spc-charts               # Get SPC control chart data
GET    /api/v1/spc-charts/{characteristic_id}/capability # Get Cp/Cpk
```

### Traceability

```
POST   /api/v1/lot-numbers              # Generate lot number
GET    /api/v1/lot-numbers              # List lot numbers
GET    /api/v1/lot-numbers/{lot_number} # Get lot details
POST   /api/v1/serial-numbers/generate  # Generate serial numbers
GET    /api/v1/serial-numbers           # List serial numbers
GET    /api/v1/serial-numbers/{serial_number} # Get serial details
GET    /api/v1/traceability/forward     # Forward trace (lot → customers)
GET    /api/v1/traceability/backward    # Backward trace (customer → lots)
POST   /api/v1/recall-reports           # Generate recall report
GET    /api/v1/recall-reports/{id}      # Get recall report
```

---

## Frontend Architecture

### Module Structure

```
src/
├── design-system/           # Atomic Design components
│   ├── atoms/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Badge.tsx
│   │   ├── Avatar.tsx
│   │   └── ...
│   ├── molecules/
│   │   ├── FormField.tsx
│   │   ├── SearchBar.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── LaneCard.tsx
│   │   ├── ProjectCard.tsx
│   │   └── ...
│   ├── organisms/
│   │   ├── ProjectForm.tsx
│   │   ├── MaterialTable.tsx
│   │   ├── WorkOrderForm.tsx
│   │   ├── NCRForm.tsx
│   │   ├── ProductionLogForm.tsx
│   │   └── ...
│   └── templates/
│       ├── PageLayout.tsx
│       ├── DashboardLayout.tsx
│       └── FormLayout.tsx
│
├── components/
│   └── ui/                 # ShadCN UI components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── table.tsx
│       ├── dialog.tsx
│       ├── tabs.tsx
│       └── ...
│
├── pages/                  # Feature pages
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   └── LogoutPage.tsx
│   ├── projects/
│   │   ├── ProjectsListPage.tsx
│   │   ├── ProjectDetailPage.tsx
│   │   └── CreateProjectPage.tsx
│   ├── materials/
│   │   ├── MaterialsListPage.tsx
│   │   ├── MaterialDetailPage.tsx
│   │   └── InventoryPage.tsx
│   ├── production/
│   │   ├── WorkOrdersPage.tsx
│   │   ├── WorkOrderDetailPage.tsx
│   │   ├── LanesPage.tsx
│   │   ├── ProductionDashboardPage.tsx
│   │   └── DailyWorkLogPage.tsx
│   ├── quality/
│   │   ├── NCRListPage.tsx
│   │   ├── NCRDetailPage.tsx
│   │   └── InspectionsPage.tsx
│   ├── scheduling/
│   │   ├── RBSSchedulePage.tsx
│   │   └── RPSSheetPage.tsx
│   ├── logistics/
│   │   ├── ShipmentsPage.tsx
│   │   └── QRScannerPage.tsx
│   ├── reports/
│   │   ├── ReportsListPage.tsx
│   │   └── DashboardPage.tsx
│   └── settings/
│       ├── PlantsPage.tsx
│       ├── UsersPage.tsx
│       └── RolesPage.tsx
│
├── stores/                 # Zustand stores
│   ├── auth.store.ts       # Auth state (existing)
│   ├── ui.store.ts         # UI state (existing)
│   ├── plant.store.ts      # Current plant context
│   ├── notification.store.ts # Notifications
│   └── offline.store.ts    # PWA offline queue
│
├── hooks/                  # React hooks
│   ├── useUsers.ts         # User queries (existing)
│   ├── useProjects.ts      # Project queries
│   ├── useMaterials.ts     # Material queries
│   ├── useWorkOrders.ts    # Work order queries
│   ├── useNCRs.ts          # NCR queries
│   ├── usePolling.ts       # Smart polling hook
│   └── useOffline.ts       # PWA offline detection
│
├── services/               # API clients
│   ├── user.service.ts     # User API (existing)
│   ├── auth.service.ts     # Auth API
│   ├── project.service.ts  # Project API
│   ├── material.service.ts # Material API
│   ├── workorder.service.ts # Work order API
│   ├── ncr.service.ts      # NCR API
│   ├── barcode.service.ts  # Barcode generation API
│   ├── report.service.ts   # Reporting API
│   └── sap.service.ts      # SAP integration API
│
├── schemas/                # Zod validation
│   ├── user.schema.ts      # User schemas (existing)
│   ├── project.schema.ts   # Project schemas
│   ├── material.schema.ts  # Material schemas
│   ├── workorder.schema.ts # Work order schemas
│   ├── ncr.schema.ts       # NCR schemas
│   └── common.schema.ts    # Common types
│
├── lib/
│   ├── api-client.ts       # Axios instance with interceptors
│   ├── utils.ts            # Utility functions
│   ├── date.ts             # Date formatting
│   └── barcode.ts          # Barcode scanning (PWA)
│
├── public/
│   ├── manifest.json       # PWA manifest
│   ├── service-worker.js   # PWA service worker
│   └── icons/              # PWA icons
│
└── App.tsx                 # Main app with routing
```

### PWA Configuration

**vite.config.ts** - Add PWA plugin:
```typescript
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'Unison Manufacturing ERP',
        short_name: 'Unison',
        description: 'Manufacturing Management System',
        theme_color: '#0ea5e9',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: { maxEntries: 50, maxAgeSeconds: 300 }
            }
          }
        ]
      }
    })
  ]
})
```

### Smart Polling Pattern (TanStack Query)

```typescript
// hooks/usePolling.ts
export const usePolling = (intervalMs = 30000) => {
  const [isVisible, setIsVisible] = useState(true)
  
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(!document.hidden)
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])
  
  return { refetchInterval: isVisible ? intervalMs : false }
}

// Usage in hooks/useWorkOrders.ts
export const useWorkOrders = (plantId: number) => {
  const { refetchInterval } = usePolling(30000) // 30 seconds
  
  return useQuery({
    queryKey: ['work-orders', plantId],
    queryFn: () => workOrderService.getWorkOrders({ plant_id: plantId }),
    refetchInterval, // Auto-polls when tab is visible
  })
}
```

---

## Infrastructure

### Deployment Topology

```mermaid
graph TB
    subgraph "Client Layer"
        CLIENT[Web Browser<br/>React PWA]
    end
    
    subgraph "Reverse Proxy Layer"
        NGINX[Nginx<br/>Port 80/443]
    end
    
    subgraph "Application Layer"
        FRONTEND[Frontend Container<br/>React + Vite<br/>Port 5173]
        BACKEND[Backend Container<br/>FastAPI + Uvicorn<br/>Port 8000]
        CELERY_WORKER[Celery Worker<br/>Background Tasks]
        CELERY_BEAT[Celery Beat<br/>Scheduler]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL 15<br/>Port 5432)]
        REDIS[(Redis 7<br/>Cache + Queue<br/>Port 6379)]
        MINIO[MinIO<br/>Object Storage<br/>Port 9000/9001]
    end
    
    subgraph "Admin Tools"
        PGADMIN[pgAdmin<br/>DB Management<br/>Port 5050]
    end
    
    CLIENT -->|HTTPS| NGINX
    NGINX -->|/| FRONTEND
    NGINX -->|/api| BACKEND
    FRONTEND -.->|API Calls| BACKEND
    
    BACKEND -->|SQL Queries| POSTGRES
    BACKEND -->|Cache| REDIS
    BACKEND -->|File Storage| MINIO
    CELERY_WORKER -->|Task Queue| REDIS
    CELERY_WORKER -->|DB Access| POSTGRES
    CELERY_WORKER -->|Barcode Gen| MINIO
    CELERY_BEAT -->|Schedule| REDIS
    
    PGADMIN -.->|Admin| POSTGRES
    
    style CLIENT fill:#E3F2FD
    style NGINX fill:#FFF3E0
    style FRONTEND fill:#E8F5E9
    style BACKEND fill:#E8F5E9
    style POSTGRES fill:#FCE4EC
    style REDIS fill:#FCE4EC
    style MINIO fill:#FCE4EC
```

**Service Responsibilities**:
- **Nginx**: SSL termination, reverse proxy, load balancing, static file serving
- **Frontend**: React SPA, PWA service workers, offline capabilities
- **Backend**: REST API, business logic, authentication, authorization
- **Celery Worker**: Async tasks (barcode generation, SAP sync, reports, emails)
- **Celery Beat**: Scheduled tasks (daily KPI calculation, inventory alerts)
- **PostgreSQL**: Primary data store, RLS enforcement, JSONB for custom fields
- **Redis**: Session cache, Celery message broker, rate limiting
- **MinIO**: S3-compatible object storage (barcodes, NCR photos, drawings, reports)

**Health Check Endpoints**:
- Backend: `GET /api/health` → `{"status": "healthy", "db": "connected", "redis": "connected"}`
- MinIO: `GET /minio/health/live` → `200 OK`
- PostgreSQL: `SELECT 1` → Connection test
- Redis: `PING` → `PONG`

**Port Mapping** (Dev Environment):
- 80/443: Nginx (Production)
- 5173: Frontend (Development)
- 8000: Backend API (Development & Production)
- 5432: PostgreSQL
- 6379: Redis
- 9000: MinIO API
- 9001: MinIO Console
- 5050: pgAdmin

### Docker Compose (Updated)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: unison_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: unison_erp
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - unison_network

  redis:
    image: redis:7-alpine
    container_name: unison_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - unison_network

  minio:
    image: minio/minio:latest
    container_name: unison_minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    networks:
      - unison_network

  minio_setup:
    image: minio/mc:latest
    container_name: unison_minio_setup
    depends_on:
      - minio
    entrypoint: >
      /bin/sh -c "
      sleep 5;
      /usr/bin/mc alias set myminio http://minio:9000 minioadmin minioadmin;
      /usr/bin/mc mb myminio/barcodes --ignore-existing;
      /usr/bin/mc mb myminio/ncr-photos --ignore-existing;
      /usr/bin/mc mb myminio/rda-drawings --ignore-existing;
      /usr/bin/mc mb myminio/reports --ignore-existing;
      /usr/bin/mc mb myminio/documents --ignore-existing;
      exit 0;
      "
    networks:
      - unison_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: unison_backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/unison_erp
      REDIS_HOST: redis
      REDIS_PORT: 6379
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      MINIO_SECURE: "false"
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - unison_network

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: unison_celery_worker
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/unison_erp
      REDIS_HOST: redis
      REDIS_PORT: 6379
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    depends_on:
      - postgres
      - redis
      - minio
    volumes:
      - ./backend:/app
    command: celery -A app.infrastructure.tasks.celery_app worker --loglevel=info
    networks:
      - unison_network

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: unison_celery_beat
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/unison_erp
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: celery -A app.infrastructure.tasks.celery_app beat --loglevel=info
    networks:
      - unison_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: unison_frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000
    command: npm run dev -- --host
    networks:
      - unison_network

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: unison_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@unison.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - unison_network

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  unison_network:
    driver: bridge
```

---

## Security & Multi-Tenancy

### Row-Level Security Implementation

**1. Enable RLS Function**

Create PostgreSQL function to get current organization:

```sql
-- Function to set organization context
CREATE OR REPLACE FUNCTION set_organization_context(org_id INTEGER)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', org_id::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to get current organization
CREATE OR REPLACE FUNCTION current_organization_id()
RETURNS INTEGER AS $$
BEGIN
    RETURN current_setting('app.current_organization_id', TRUE)::INTEGER;
END;
$$ LANGUAGE plpgsql;
```

**2. Backend Middleware**

```python
# app/infrastructure/security/rls_context.py
from sqlalchemy import event
from app.infrastructure.persistence.database import engine

def set_rls_context(connection, organization_id: int):
    """Set RLS context for database connection"""
    connection.execute(
        text(f"SELECT set_organization_context({organization_id})")
    )

# app/presentation/api/dependencies.py
from fastapi import Depends, Request
from app.domain.entities.user import User
from app.infrastructure.security.dependencies import get_current_user
from app.infrastructure.security.rls_context import set_rls_context

async def get_db_with_rls(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Session:
    """Get database session with RLS context set"""
    set_rls_context(db.connection(), current_user.organization_id)
    return db
```

**3. Usage in Endpoints**

```python
@router.get("/projects/", response_model=List[ProjectResponseDTO])
def list_projects(
    db: Session = Depends(get_db_with_rls),  # RLS automatically filters by org
    current_user: User = Depends(get_current_user)
):
    # Query automatically filtered by organization_id via RLS
    projects = db.query(ProjectModel).all()
    return projects
```

### RBAC with Casbin

**Permissions Structure**:

```
Subject (User Role)  |  Object (Resource)  |  Action
---------------------|---------------------|----------
admin                |  projects           |  read
admin                |  projects           |  write
admin                |  projects           |  delete
plant_manager        |  work_orders        |  read
plant_manager        |  work_orders        |  write
shop_floor_worker    |  work_orders        |  read
shop_floor_worker    |  production_logs    |  write
quality_inspector    |  ncr_reports        |  write
```

**casbin_model.conf**:
```
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

**Week 1: Multi-Tenancy Foundation**
- [ ] Create Organization, Plant, Department entities
- [ ] Implement RLS for all tables
- [ ] Update User entity with organization_id
- [ ] Add plant access control
- [ ] Create migration scripts
- [ ] Add RLS middleware

**Week 2: Material Management**
- [ ] Material entities (Material, Category, Inventory)
- [ ] Material CRUD APIs
- [ ] Barcode/QR generation service (MinIO integration)
- [ ] Material transaction logging
- [ ] Frontend: Material pages

**Week 3: Project Management**
- [ ] Project entity + BOM
- [ ] Project CRUD APIs
- [ ] RDA Drawing workflow
- [ ] Document upload (MinIO)
- [ ] Frontend: Project pages

**Week 4: MinIO & Barcode System**
- [ ] MinIO client setup
- [ ] Barcode generation (Code128, QR)
- [ ] File upload service
- [ ] Document metadata management
- [ ] Frontend: Camera integration (PWA)

### Phase 2: Production Core (Weeks 5-8)

**Week 5: Work Orders**
- [ ] WorkOrder entity + operations
- [ ] Work order CRUD APIs
- [ ] Work order status transitions
- [ ] Frontend: Work order pages

**Week 6: Lane Management**
- [ ] Lane entity
- [ ] Lane assignment logic
- [ ] Lane status tracking
- [ ] Frontend: Lane management pages

**Week 7: Production Logging**
- [ ] Production log entity
- [ ] Real-time logging API
- [ ] Manpower allocation
- [ ] Frontend: Production log forms

**Week 8: RBS/RPS Scheduling**
- [ ] RBS schedule entity
- [ ] RPS sheet entity
- [ ] Scheduling algorithms
- [ ] Frontend: Schedule calendar views

### Phase 3: Quality & Logistics (Weeks 9-12)

**Week 9: Quality Management**
- [ ] NCR entity + workflow
- [ ] NCR photo uploads
- [ ] Quality inspection entity
- [ ] Frontend: NCR pages

**Week 10: Logistics**
- [ ] Shipment entity
- [ ] QR code scanning
- [ ] Shipment tracking
- [ ] Frontend: Logistics pages

**Week 11: SAP Integration**
- [ ] SAP adapter interface
- [ ] Mock SAP adapter
- [ ] Celery tasks for sync
- [ ] SAP queue + retry logic
- [ ] Frontend: SAP sync status

**Week 12: Reporting & Dashboard**
- [ ] Report entities
- [ ] Pre-defined reports (production, OTD, NCR)
- [ ] Chart components (Recharts)
- [ ] CSV export
- [ ] Frontend: Dashboard pages

### Phase 4: Polish & PWA (Weeks 13-14)

**Week 13: PWA Implementation**
- [ ] Service worker setup
- [ ] Offline queue (Zustand)
- [ ] Camera API for NCR photos
- [ ] Barcode scanner (WebRTC)
- [ ] Push notifications

**Week 14: Testing & Deployment**
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Production Docker setup
- [ ] Deployment guide
- [ ] User documentation

---

---

## Implementation Details

### Backend Domain Services

#### Material Costing Service

```python
# app/domain/services/material_costing_service.py
from typing import List, Tuple
from decimal import Decimal
from datetime import datetime
from app.domain.entities.material import Material
from app.domain.entities.material_transaction import MaterialTransaction

class MaterialCostingService:
    """Domain service for material costing calculations"""

    def calculate_fifo_cost(
        self,
        transactions: List[MaterialTransaction],
        quantity_to_issue: Decimal
    ) -> Tuple[Decimal, List[Tuple[int, Decimal, Decimal]]]:
        """
        Calculate FIFO cost for material issue

        Returns:
            - Total cost
            - List of (transaction_id, quantity_used, unit_cost)
        """
        remaining_qty = quantity_to_issue
        total_cost = Decimal('0')
        breakdown = []

        # Sort by created_at (oldest first)
        sorted_txns = sorted(
            [t for t in transactions if t.transaction_type == 'receipt'],
            key=lambda x: x.created_at
        )

        for txn in sorted_txns:
            if remaining_qty <= 0:
                break

            available = txn.quantity - txn.quantity_consumed
            if available <= 0:
                continue

            qty_from_this = min(remaining_qty, available)
            cost_from_this = qty_from_this * txn.unit_cost

            breakdown.append((txn.id, qty_from_this, txn.unit_cost))
            total_cost += cost_from_this
            remaining_qty -= qty_from_this

        if remaining_qty > 0:
            raise ValueError(f"Insufficient inventory: {remaining_qty} units short")

        return total_cost, breakdown

    def calculate_weighted_average_cost(
        self,
        transactions: List[MaterialTransaction]
    ) -> Decimal:
        """Calculate weighted average unit cost"""
        receipts = [t for t in transactions if t.transaction_type == 'receipt']

        if not receipts:
            return Decimal('0')

        total_cost = sum(t.quantity * t.unit_cost for t in receipts)
        total_quantity = sum(t.quantity for t in receipts)

        return total_cost / total_quantity if total_quantity > 0 else Decimal('0')
```

#### Work Order Scheduling Service

```python
# app/domain/services/scheduling_service.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.domain.entities.work_order import WorkOrder
from app.domain.entities.lane import Lane
from app.domain.exceptions import SchedulingConflictException

class SchedulingService:
    """Domain service for RBS scheduling logic"""

    def find_available_lanes(
        self,
        plant_id: int,
        lanes: List[Lane],
        required_from: datetime,
        required_to: datetime
    ) -> List[Lane]:
        """Find lanes available for given time window"""
        available = []

        for lane in lanes:
            if not lane.is_active:
                continue

            if lane.status == 'maintenance':
                continue

            # Check for conflicts with existing assignments
            if not self._has_conflict(lane, required_from, required_to):
                available.append(lane)

        return available

    def calculate_completion_date(
        self,
        work_order: WorkOrder,
        start_date: datetime
    ) -> datetime:
        """Calculate predicted completion date based on operations"""
        total_hours = sum(
            op.planned_hours or 0
            for op in work_order.operations
        )

        # Assume 8-hour workdays
        working_days = total_hours / 8

        # Add buffer (20%)
        buffer_days = working_days * 0.2

        completion_date = start_date + timedelta(days=working_days + buffer_days)
        return completion_date

    def _has_conflict(
        self,
        lane: Lane,
        required_from: datetime,
        required_to: datetime
    ) -> bool:
        """Check if lane has scheduling conflicts"""
        # Implementation checks lane_assignments table
        # This would query repository in application layer
        return False
```

#### OEE Calculation Service

```python
# app/domain/services/oee_service.py
from decimal import Decimal
from typing import Dict
from datetime import datetime, timedelta

class OEEService:
    """Domain service for OEE (Overall Equipment Effectiveness) calculation"""

    def calculate_oee(
        self,
        planned_hours: Decimal,
        actual_hours: Decimal,
        quantity_planned: int,
        quantity_produced: int,
        quantity_good: int
    ) -> Dict[str, Decimal]:
        """
        Calculate OEE = Availability × Performance × Quality

        Returns dict with availability, performance, quality, oee
        """
        # Availability = (Actual Operating Time / Planned Operating Time)
        availability = (actual_hours / planned_hours) if planned_hours > 0 else Decimal('0')

        # Performance = (Actual Output / Planned Output)
        performance = (Decimal(quantity_produced) / Decimal(quantity_planned)) if quantity_planned > 0 else Decimal('0')

        # Quality = (Good Units / Total Units Produced)
        quality = (Decimal(quantity_good) / Decimal(quantity_produced)) if quantity_produced > 0 else Decimal('0')

        # OEE
        oee = availability * performance * quality

        return {
            'availability': round(availability * 100, 2),
            'performance': round(performance * 100, 2),
            'quality': round(quality * 100, 2),
            'oee': round(oee * 100, 2)
        }
```



#### Machine Utilization Service

```python
# app/domain/services/machine_utilization_service.py
from decimal import Decimal
from typing import Dict, List
from datetime import datetime, timedelta

class MachineUtilizationService:
    """Domain service for calculating machine utilization metrics"""
    
    def calculate_utilization(
        self,
        available_time_minutes: int,
        productive_time_minutes: int
    ) -> Decimal:
        """
        Calculate machine utilization percentage
        Utilization = (Productive Time / Available Time) × 100
        """
        if available_time_minutes == 0:
            return Decimal('0.00')
        
        utilization = (Decimal(productive_time_minutes) / Decimal(available_time_minutes)) * 100
        return round(utilization, 2)
    
    def calculate_mtbf(
        self,
        total_operating_hours: Decimal,
        number_of_failures: int
    ) -> Decimal:
        """
        Calculate Mean Time Between Failures (MTBF)
        MTBF = Total Operating Time / Number of Failures
        """
        if number_of_failures == 0:
            return Decimal('0.00')
        
        mtbf = total_operating_hours / number_of_failures
        return round(mtbf, 2)
    
    def calculate_mttr(
        self,
        total_repair_time_hours: Decimal,
        number_of_repairs: int
    ) -> Decimal:
        """
        Calculate Mean Time To Repair (MTTR)
        MTTR = Total Repair Time / Number of Repairs
        """
        if number_of_repairs == 0:
            return Decimal('0.00')
        
        mttr = total_repair_time_hours / number_of_repairs
        return round(mttr, 2)
```

#### Shift Performance Service

```python
# app/domain/services/shift_performance_service.py
from decimal import Decimal
from typing import Dict

class ShiftPerformanceService:
    """Domain service for calculating shift performance metrics"""
    
    def calculate_target_attainment(
        self,
        actual_units: int,
        target_units: int
    ) -> Decimal:
        """
        Calculate shift target attainment percentage
        Target Attainment = (Actual / Target) × 100
        """
        if target_units == 0:
            return Decimal('0.00')
        
        attainment = (Decimal(actual_units) / Decimal(target_units)) * 100
        return round(attainment, 2)
    
    def compare_shifts(
        self,
        current_shift_performance: Dict,
        historical_avg_performance: Dict
    ) -> Dict[str, str]:
        """
        Compare current shift performance vs historical average
        Returns dict with percentage differences
        """
        comparisons = {}
        
        for metric in ['target_attainment', 'oee', 'fpy']:
            current = Decimal(str(current_shift_performance.get(metric, 0)))
            historical = Decimal(str(historical_avg_performance.get(metric, 0)))
            
            if historical == 0:
                comparisons[f'vs_{metric}_avg'] = 'N/A'
            else:
                diff = ((current - historical) / historical) * 100
                sign = '+' if diff > 0 else ''
                comparisons[f'vs_{metric}_avg'] = f"{sign}{round(diff, 1)}%"
        
        return comparisons
```

#### Preventive Maintenance Scheduling Service

```python
# app/domain/services/pm_scheduling_service.py
from datetime import date, timedelta
from typing import Optional

class PMSchedulingService:
    """Domain service for PM schedule calculations"""
    
    def calculate_next_due_date(
        self,
        last_pm_date: date,
        frequency_value: int,
        frequency_unit: str
    ) -> date:
        """
        Calculate next PM due date based on frequency
        
        Args:
            last_pm_date: Date of last PM
            frequency_value: Number of units (e.g., 30, 90)
            frequency_unit: 'days', 'weeks', or 'months'
        
        Returns:
            Next due date
        """
        if frequency_unit == 'days':
            return last_pm_date + timedelta(days=frequency_value)
        elif frequency_unit == 'weeks':
            return last_pm_date + timedelta(weeks=frequency_value)
        elif frequency_unit == 'months':
            # Approximate month as 30 days
            return last_pm_date + timedelta(days=frequency_value * 30)
        else:
            raise ValueError(f"Invalid frequency_unit: {frequency_unit}")
    
    def should_generate_pm_wo(
        self,
        next_due_date: date,
        lead_time_days: int,
        today: Optional[date] = None
    ) -> bool:
        """
        Determine if PM work order should be generated
        
        Args:
            next_due_date: When PM is due
            lead_time_days: Days before due to generate WO
            today: Current date (defaults to date.today())
        
        Returns:
            True if WO should be generated
        """
        if today is None:
            today = date.today()
        
        trigger_date = next_due_date - timedelta(days=lead_time_days)
        return today >= trigger_date
    
    def calculate_pm_compliance(
        self,
        completed_pm_count: int,
        total_pm_due_count: int
    ) -> Decimal:
        """
        Calculate PM compliance rate
        PM Compliance = (Completed PMs / Total PMs Due) × 100
        
        Target: ≥ 90%
        """
        if total_pm_due_count == 0:
            return Decimal('100.00')
        
        compliance = (Decimal(completed_pm_count) / Decimal(total_pm_due_count)) * 100
        return round(compliance, 2)
```

#### Inspection SPC Service

```python
# app/domain/services/inspection_spc_service.py
from decimal import Decimal
from typing import List, Dict, Optional
import statistics

class InspectionSPCService:
    """Domain service for Statistical Process Control calculations"""
    
    def calculate_control_limits(
        self,
        measurements: List[Decimal],
        usl: Decimal,
        lsl: Decimal
    ) -> Dict[str, Decimal]:
        """
        Calculate control limits for SPC chart
        
        Returns:
            Dict with ucl, lcl, center_line
        """
        if not measurements:
            return {
                'ucl': usl,
                'lcl': lsl,
                'center_line': (usl + lsl) / 2
            }
        
        mean = Decimal(str(statistics.mean(measurements)))
        std_dev = Decimal(str(statistics.stdev(measurements))) if len(measurements) > 1 else Decimal('0')
        
        # Control limits at ±3σ from mean
        ucl = mean + (3 * std_dev)
        lcl = mean - (3 * std_dev)
        
        return {
            'ucl': round(ucl, 4),
            'lcl': round(lcl, 4),
            'center_line': round(mean, 4)
        }
    
    def calculate_cpk(
        self,
        measurements: List[Decimal],
        usl: Decimal,
        lsl: Decimal
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculate Process Capability indices Cp and Cpk
        
        Cp = (USL - LSL) / (6 × σ)
        Cpk = min[(USL - μ) / (3 × σ), (μ - LSL) / (3 × σ)]
        
        Interpretation:
            Cpk ≥ 1.67: Excellent (5σ capable)
            Cpk ≥ 1.33: Good (4σ capable)
            Cpk ≥ 1.00: Marginal (3σ capable)
            Cpk < 1.00: Poor
        """
        if len(measurements) < 2:
            return {'cp': None, 'cpk': None, 'interpretation': 'Insufficient data'}
        
        mean = Decimal(str(statistics.mean(measurements)))
        std_dev = Decimal(str(statistics.stdev(measurements)))
        
        if std_dev == 0:
            return {'cp': None, 'cpk': None, 'interpretation': 'No variation'}
        
        # Calculate Cp
        cp = (usl - lsl) / (6 * std_dev)
        
        # Calculate Cpk
        cpu = (usl - mean) / (3 * std_dev)
        cpl = (mean - lsl) / (3 * std_dev)
        cpk = min(cpu, cpl)
        
        # Interpretation
        if cpk >= Decimal('1.67'):
            interpretation = 'Excellent (5σ capable)'
        elif cpk >= Decimal('1.33'):
            interpretation = 'Good (4σ capable)'
        elif cpk >= Decimal('1.00'):
            interpretation = 'Marginal (3σ capable)'
        else:
            interpretation = 'Poor (process improvement required)'
        
        return {
            'cp': round(cp, 2),
            'cpk': round(cpk, 2),
            'interpretation': interpretation
        }
    
    def detect_control_rule_violations(
        self,
        measurements: List[Decimal],
        ucl: Decimal,
        lcl: Decimal,
        center_line: Decimal
    ) -> List[Dict[str, str]]:
        """
        Detect Western Electric / Nelson control chart rules violations
        
        Returns list of alerts:
        - Point outside control limits (±3σ)
        - 7+ consecutive points above/below center line
        - 2 out of 3 points > 2σ from center
        """
        alerts = []
        
        # Rule 1: Point outside control limits
        for i, value in enumerate(measurements):
            if value > ucl or value < lcl:
                alerts.append({
                    'type': 'out_of_control',
                    'message': f'Point {i+1} outside control limits',
                    'severity': 'critical'
                })
        
        # Rule 2: 7+ consecutive points above/below center line
        if len(measurements) >= 7:
            above_count = 0
            below_count = 0
            for value in measurements[-7:]:
                if value > center_line:
                    above_count += 1
                    below_count = 0
                elif value < center_line:
                    below_count += 1
                    above_count = 0
            
            if above_count >= 7:
                alerts.append({
                    'type': 'trend',
                    'message': '7 consecutive points above center line',
                    'severity': 'warning'
                })
            elif below_count >= 7:
                alerts.append({
                    'type': 'trend',
                    'message': '7 consecutive points below center line',
                    'severity': 'warning'
                })
        
        return alerts
```

#### Traceability Service

```python
# app/domain/services/traceability_service.py
from typing import List, Dict, Optional

class TraceabilityService:
    """Domain service for lot and serial number traceability"""
    
    def generate_lot_number(
        self,
        material_code: str,
        receipt_date: date,
        sequence: int
    ) -> str:
        """
        Generate lot number: {MaterialCode}-{YYYYMMDD}-{Sequence}
        Example: STL001-20251106-001
        """
        date_str = receipt_date.strftime('%Y%m%d')
        sequence_str = str(sequence).zfill(3)
        return f"{material_code}-{date_str}-{sequence_str}"
    
    def generate_serial_number(
        self,
        product_code: str,
        production_year_month: str,
        sequence: int
    ) -> str:
        """
        Generate serial number: {ProductCode}-{YYMM}-{Sequence}
        Example: PUMP-2511-00001
        """
        sequence_str = str(sequence).zfill(5)
        return f"{product_code}-{production_year_month}-{sequence_str}"
    
    def validate_lot_availability(
        self,
        lot_remaining_quantity: Decimal,
        requested_quantity: Decimal
    ) -> bool:
        """
        Validate if sufficient quantity available in lot
        """
        return lot_remaining_quantity >= requested_quantity
```

### Application Layer Use Cases

#### Create Work Order Use Case

```python
# app/application/use_cases/production/create_work_order.py
from typing import Optional
from app.domain.entities.work_order import WorkOrder
from app.domain.repositories.work_order_repository import WorkOrderRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.services.scheduling_service import SchedulingService
from app.application.dtos.work_order_dto import CreateWorkOrderDTO, WorkOrderResponseDTO
from app.domain.exceptions import ProjectNotFoundException

class CreateWorkOrderUseCase:
    """Use case for creating work orders"""

    def __init__(
        self,
        work_order_repo: WorkOrderRepository,
        project_repo: ProjectRepository,
        scheduling_service: SchedulingService
    ):
        self._work_order_repo = work_order_repo
        self._project_repo = project_repo
        self._scheduling_service = scheduling_service

    async def execute(
        self,
        dto: CreateWorkOrderDTO,
        organization_id: int,
        created_by_user_id: int
    ) -> WorkOrderResponseDTO:
        """Create work order with scheduling"""

        # Validate project exists
        project = await self._project_repo.get_by_id(dto.project_id)
        if not project:
            raise ProjectNotFoundException(dto.project_id)

        # Generate work order number
        wo_number = await self._generate_work_order_number(
            organization_id,
            dto.plant_id
        )

        # Create work order entity
        work_order = WorkOrder(
            id=None,
            organization_id=organization_id,
            work_order_number=wo_number,
            project_id=dto.project_id,
            plant_id=dto.plant_id,
            department_id=dto.department_id,
            operation_type=dto.operation_type,
            description=dto.description,
            quantity_ordered=dto.quantity_ordered,
            status='planned',
            created_by=created_by_user_id
        )

        # Calculate completion date
        if dto.planned_start_date:
            completion_date = self._scheduling_service.calculate_completion_date(
                work_order,
                dto.planned_start_date
            )
            work_order.set_planned_dates(dto.planned_start_date, completion_date)

        # Save
        saved_work_order = await self._work_order_repo.save(work_order)

        # Trigger SAP sync (async via Celery)
        from app.infrastructure.tasks.sap_tasks import sync_production_order
        sync_production_order.delay(saved_work_order.id)

        return WorkOrderResponseDTO.from_entity(saved_work_order)

    async def _generate_work_order_number(
        self,
        organization_id: int,
        plant_id: int
    ) -> str:
        """Generate sequential work order number"""
        # Format: WO-{PLANT}-{YEAR}-{SEQUENCE}
        year = datetime.now().year
        count = await self._work_order_repo.count_for_year(organization_id, plant_id, year)
        return f"WO-{plant_id}-{year}-{count + 1:04d}"
```

#### Record Production Log Use Case

```python
# app/application/use_cases/production/record_production_log.py
from app.domain.entities.production_log import ProductionLog
from app.domain.entities.work_order import WorkOrder
from app.domain.repositories.production_log_repository import ProductionLogRepository
from app.domain.repositories.work_order_repository import WorkOrderRepository
from app.application.dtos.production_log_dto import CreateProductionLogDTO

class RecordProductionLogUseCase:
    """Use case for recording production events"""

    def __init__(
        self,
        production_log_repo: ProductionLogRepository,
        work_order_repo: WorkOrderRepository
    ):
        self._production_log_repo = production_log_repo
        self._work_order_repo = work_order_repo

    async def execute(
        self,
        dto: CreateProductionLogDTO,
        organization_id: int,
        logged_by_user_id: int
    ) -> None:
        """Record production log and update work order progress"""

        # Get work order
        work_order = await self._work_order_repo.get_by_id(dto.work_order_id)

        # Create log entity
        log = ProductionLog(
            id=None,
            organization_id=organization_id,
            work_order_id=dto.work_order_id,
            operation_id=dto.operation_id,
            lane_id=dto.lane_id,
            log_type=dto.log_type,
            quantity_completed=dto.quantity_completed,
            notes=dto.notes,
            logged_by=logged_by_user_id
        )

        # Save log
        await self._production_log_repo.save(log)

        # Update work order progress
        if dto.log_type == 'complete' and dto.quantity_completed:
            work_order.add_completed_quantity(dto.quantity_completed)
            await self._work_order_repo.save(work_order)

            # Check if work order is fully completed
            if work_order.is_completed():
                work_order.mark_as_completed()
                await self._work_order_repo.save(work_order)

                # Trigger notifications
                from app.infrastructure.tasks.notification_tasks import notify_work_order_completed
                notify_work_order_completed.delay(work_order.id)
```

### Infrastructure Layer Implementation

#### MinIO Service

```python
# app/infrastructure/storage/minio_service.py
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
from datetime import timedelta
import os

class MinIOService:
    """MinIO object storage service"""

    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        """Create buckets if they don't exist"""
        buckets = ['barcodes', 'ncr-photos', 'rda-drawings', 'reports', 'documents']
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: str = 'application/octet-stream'
    ) -> str:
        """Upload file to MinIO"""
        try:
            file_data.seek(0, os.SEEK_END)
            file_size = file_data.tell()
            file_data.seek(0)

            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type
            )

            return f"{bucket}/{object_name}"
        except S3Error as e:
            raise Exception(f"MinIO upload failed: {str(e)}")

    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate presigned URL for temporary access"""
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete file from MinIO"""
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error as e:
            raise Exception(f"MinIO delete failed: {str(e)}")
```

#### Barcode Generation Service

```python
# app/infrastructure/barcode/barcode_service.py
import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO
from PIL import Image
from typing import Tuple

class BarcodeService:
    """Service for generating barcodes and QR codes"""

    def generate_code128(self, data: str) -> BytesIO:
        """Generate Code128 barcode"""
        code128 = barcode.get('code128', data, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        buffer.seek(0)
        return buffer

    def generate_qr_code(self, data: str, size: int = 300) -> BytesIO:
        """Generate QR code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    def generate_material_barcode(
        self,
        material_code: str,
        material_name: str
    ) -> Tuple[BytesIO, str]:
        """Generate barcode for material with metadata"""
        # Data format: MAT|{code}|{name}
        barcode_data = f"MAT|{material_code}|{material_name}"
        barcode_image = self.generate_code128(material_code)
        return barcode_image, barcode_data

    def generate_work_order_qr(
        self,
        work_order_number: str,
        project_number: str,
        plant_id: int
    ) -> Tuple[BytesIO, str]:
        """Generate QR code for work order"""
        # Data format: WO|{wo_number}|{project}|{plant}
        qr_data = f"WO|{work_order_number}|{project_number}|{plant_id}"
        qr_image = self.generate_qr_code(qr_data)
        return qr_image, qr_data
```

#### SAP Adapter (Mock Implementation)

```python
# app/infrastructure/sap/sap_adapter.py
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class SAPAdapter:
    """Mock SAP adapter for integration"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "http://mock-sap-server"
        self.enabled = False  # Set to True when real SAP is available

    async def sync_sales_order(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync project to SAP as Sales Order"""
        if not self.enabled:
            logger.info(f"[MOCK] Would sync Sales Order: {project_data}")
            # Simulate API delay
            await asyncio.sleep(0.5)
            return {
                'success': True,
                'sap_sales_order': f"SO-{project_data['project_number']}",
                'synced_at': datetime.utcnow().isoformat()
            }

        # Real SAP integration would go here
        # response = requests.post(f"{self.base_url}/sales-orders", json=project_data)
        # return response.json()

    async def sync_production_order(self, work_order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync work order to SAP as Production Order"""
        if not self.enabled:
            logger.info(f"[MOCK] Would sync Production Order: {work_order_data}")
            await asyncio.sleep(0.5)
            return {
                'success': True,
                'sap_production_order': f"PO-{work_order_data['work_order_number']}",
                'synced_at': datetime.utcnow().isoformat()
            }

    async def sync_material_master(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync material to SAP Material Master"""
        if not self.enabled:
            logger.info(f"[MOCK] Would sync Material Master: {material_data}")
            await asyncio.sleep(0.5)
            return {
                'success': True,
                'sap_material_number': f"MAT-{material_data['material_code']}",
                'synced_at': datetime.utcnow().isoformat()
            }

    async def get_sales_order_status(self, sap_sales_order: str) -> Dict[str, Any]:
        """Query SAP for sales order status"""
        if not self.enabled:
            return {
                'sap_sales_order': sap_sales_order,
                'status': 'IN_PROGRESS',
                'delivery_date': '2024-12-31'
            }
```

#### Celery Task Definitions

```python
# app/infrastructure/tasks/sap_tasks.py
from celery import shared_task
from app.infrastructure.sap.sap_adapter import SAPAdapter
from app.infrastructure.persistence.database import get_db
from sqlalchemy.orm import Session

@shared_task(bind=True, max_retries=3)
def sync_production_order(self, work_order_id: int):
    """Async task to sync work order to SAP"""
    db: Session = next(get_db())

    try:
        # Get work order data
        work_order = db.query(WorkOrderModel).filter_by(id=work_order_id).first()

        if not work_order:
            return {'error': 'Work order not found'}

        # Prepare data
        wo_data = {
            'work_order_number': work_order.work_order_number,
            'project_id': work_order.project_id,
            'quantity_ordered': work_order.quantity_ordered,
            'planned_start_date': work_order.planned_start_date.isoformat() if work_order.planned_start_date else None
        }

        # Sync to SAP
        adapter = SAPAdapter()
        result = asyncio.run(adapter.sync_production_order(wo_data))

        # Log sync
        log = SAPSyncLogModel(
            organization_id=work_order.organization_id,
            sync_type='production_order',
            sync_direction='outbound',
            entity_type='work_order',
            entity_id=work_order_id,
            sap_reference=result.get('sap_production_order'),
            status='success' if result.get('success') else 'error',
            response_payload=str(result)
        )
        db.add(log)

        # Update work order with SAP reference
        if result.get('success'):
            work_order.sap_production_order = result.get('sap_production_order')

        db.commit()

        return result

    except Exception as e:
        db.rollback()
        # Log error
        log = SAPSyncLogModel(
            organization_id=work_order.organization_id if work_order else None,
            sync_type='production_order',
            sync_direction='outbound',
            entity_type='work_order',
            entity_id=work_order_id,
            status='error',
            error_message=str(e)
        )
        db.add(log)
        db.commit()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()

@shared_task
def generate_barcode_batch(material_ids: list):
    """Async task to generate barcodes for multiple materials"""
    from app.infrastructure.barcode.barcode_service import BarcodeService
    from app.infrastructure.storage.minio_service import MinIOService

    barcode_service = BarcodeService()
    minio_service = MinIOService()
    db: Session = next(get_db())

    try:
        for material_id in material_ids:
            material = db.query(MaterialModel).filter_by(id=material_id).first()

            if not material:
                continue

            # Generate barcode
            barcode_img, barcode_data = barcode_service.generate_material_barcode(
                material.material_code,
                material.name
            )

            # Upload to MinIO
            object_name = f"materials/{material.material_code}.png"
            file_path = minio_service.upload_file(
                bucket='barcodes',
                object_name=object_name,
                file_data=barcode_img,
                content_type='image/png'
            )

            # Update material
            material.barcode_data = barcode_data

            # Save to barcode_labels table
            label = BarcodeLabelModel(
                organization_id=material.organization_id,
                label_type='material',
                reference_type='material',
                reference_id=material_id,
                barcode_format='code128',
                barcode_data=barcode_data,
                file_path=file_path,
                generated_by=1  # System user
            )
            db.add(label)

        db.commit()
        return {'success': True, 'count': len(material_ids)}

    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}

    finally:
        db.close()
```

### Frontend Implementation Details

#### Zustand Store for Plant Context

```typescript
// src/stores/plant.store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Plant {
  id: number
  name: string
  code: string
  plant_type: 'fabrication' | 'production' | 'assembly'
}

interface PlantState {
  currentPlant: Plant | null
  availablePlants: Plant[]

  // Actions
  setCurrentPlant: (plant: Plant) => void
  setAvailablePlants: (plants: Plant[]) => void
  clearPlantContext: () => void
}

export const usePlantStore = create<PlantState>()(
  persist(
    (set) => ({
      currentPlant: null,
      availablePlants: [],

      setCurrentPlant: (plant) => set({ currentPlant: plant }),

      setAvailablePlants: (plants) => set({ availablePlants: plants }),

      clearPlantContext: () => set({
        currentPlant: null,
        availablePlants: []
      }),
    }),
    {
      name: 'plant-context',
    }
  )
)
```

#### TanStack Query Hook with Polling

```typescript
// src/hooks/useWorkOrders.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workOrderService } from '@/services/workorder.service'
import { usePlantStore } from '@/stores/plant.store'
import { usePolling } from './usePolling'

export const useWorkOrders = (status?: string) => {
  const currentPlant = usePlantStore((state) => state.currentPlant)
  const { refetchInterval } = usePolling(30000) // 30 seconds

  return useQuery({
    queryKey: ['work-orders', currentPlant?.id, status],
    queryFn: () => workOrderService.getWorkOrders({
      plant_id: currentPlant?.id,
      status
    }),
    enabled: !!currentPlant,
    refetchInterval, // Smart polling - pauses when tab hidden
    staleTime: 20000, // Consider data fresh for 20s
  })
}

export const useCreateWorkOrder = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: workOrderService.createWorkOrder,
    onSuccess: () => {
      // Invalidate and refetch work orders
      queryClient.invalidateQueries({ queryKey: ['work-orders'] })
    },
  })
}

export const useWorkOrderDetail = (workOrderId: number) => {
  const { refetchInterval } = usePolling(60000) // 60 seconds for detail page

  return useQuery({
    queryKey: ['work-order', workOrderId],
    queryFn: () => workOrderService.getWorkOrderById(workOrderId),
    enabled: !!workOrderId,
    refetchInterval,
  })
}
```

#### Offline Queue Store (PWA)

```typescript
// src/stores/offline.store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface QueuedRequest {
  id: string
  endpoint: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data: any
  timestamp: number
  retryCount: number
}

interface OfflineState {
  isOnline: boolean
  queue: QueuedRequest[]

  // Actions
  setOnlineStatus: (status: boolean) => void
  addToQueue: (request: Omit<QueuedRequest, 'id' | 'timestamp' | 'retryCount'>) => void
  removeFromQueue: (id: string) => void
  processQueue: () => Promise<void>
}

export const useOfflineStore = create<OfflineState>()(
  persist(
    (set, get) => ({
      isOnline: navigator.onLine,
      queue: [],

      setOnlineStatus: (status) => {
        set({ isOnline: status })

        // Process queue when coming back online
        if (status) {
          get().processQueue()
        }
      },

      addToQueue: (request) => {
        const queuedRequest: QueuedRequest = {
          ...request,
          id: `${Date.now()}-${Math.random()}`,
          timestamp: Date.now(),
          retryCount: 0
        }

        set((state) => ({
          queue: [...state.queue, queuedRequest]
        }))
      },

      removeFromQueue: (id) => {
        set((state) => ({
          queue: state.queue.filter(req => req.id !== id)
        }))
      },

      processQueue: async () => {
        const { queue, isOnline, removeFromQueue } = get()

        if (!isOnline || queue.length === 0) return

        for (const request of queue) {
          try {
            // Attempt to send queued request
            const response = await fetch(request.endpoint, {
              method: request.method,
              headers: { 'Content-Type': 'application/json' },
              body: request.data ? JSON.stringify(request.data) : undefined
            })

            if (response.ok) {
              removeFromQueue(request.id)
            }
          } catch (error) {
            console.error('Failed to process queued request:', error)
            // Will retry next time
          }
        }
      },
    }),
    {
      name: 'offline-queue',
    }
  )
)

// Setup online/offline event listeners
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    useOfflineStore.getState().setOnlineStatus(true)
  })

  window.addEventListener('offline', () => {
    useOfflineStore.getState().setOnlineStatus(false)
  })
}
```

#### React Component Example (Work Order Form)

```typescript
// src/design-system/organisms/WorkOrderForm.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { workOrderSchema, type WorkOrderFormData } from '@/schemas/workorder.schema'
import { useCreateWorkOrder } from '@/hooks/useWorkOrders'
import { useProjects } from '@/hooks/useProjects'
import { usePlantStore } from '@/stores/plant.store'

export const WorkOrderForm = () => {
  const currentPlant = usePlantStore((state) => state.currentPlant)
  const { data: projects } = useProjects()
  const createWorkOrder = useCreateWorkOrder()

  const { register, handleSubmit, formState: { errors } } = useForm<WorkOrderFormData>({
    resolver: zodResolver(workOrderSchema)
  })

  const onSubmit = async (data: WorkOrderFormData) => {
    try {
      await createWorkOrder.mutateAsync({
        ...data,
        plant_id: currentPlant?.id
      })
      // Show success toast
      // Navigate to work orders list
    } catch (error) {
      // Show error toast
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="project_id">Project</Label>
        <Select {...register('project_id')}>
          <SelectTrigger>
            <SelectValue placeholder="Select project" />
          </SelectTrigger>
          <SelectContent>
            {projects?.map((project) => (
              <SelectItem key={project.id} value={project.id.toString()}>
                {project.project_number} - {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.project_id && (
          <p className="text-sm text-red-500">{errors.project_id.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="operation_type">Operation Type</Label>
        <Select {...register('operation_type')}>
          <SelectTrigger>
            <SelectValue placeholder="Select operation" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fabrication">Fabrication</SelectItem>
            <SelectItem value="machining">Machining</SelectItem>
            <SelectItem value="assembly">Assembly</SelectItem>
            <SelectItem value="testing">Testing</SelectItem>
          </SelectContent>
        </Select>
        {errors.operation_type && (
          <p className="text-sm text-red-500">{errors.operation_type.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="quantity_ordered">Quantity</Label>
        <Input
          id="quantity_ordered"
          type="number"
          {...register('quantity_ordered', { valueAsNumber: true })}
        />
        {errors.quantity_ordered && (
          <p className="text-sm text-red-500">{errors.quantity_ordered.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input
          id="description"
          {...register('description')}
          placeholder="Work order description"
        />
        {errors.description && (
          <p className="text-sm text-red-500">{errors.description.message}</p>
        )}
      </div>

      <Button
        type="submit"
        className="w-full"
        disabled={createWorkOrder.isPending}
      >
        {createWorkOrder.isPending ? 'Creating...' : 'Create Work Order'}
      </Button>
    </form>
  )
}
```

---

## Performance Optimization

### Database Optimization

#### Indexes Strategy

```sql
-- High-frequency query indexes
CREATE INDEX CONCURRENTLY idx_work_orders_plant_status
ON work_orders(plant_id, status)
WHERE status NOT IN ('completed', 'cancelled');

CREATE INDEX CONCURRENTLY idx_material_inventory_plant_material
ON material_inventory(plant_id, material_id);

CREATE INDEX CONCURRENTLY idx_production_logs_work_order_date
ON production_logs(work_order_id, logged_at DESC);

CREATE INDEX CONCURRENTLY idx_ncr_reports_plant_status
ON ncr_reports(plant_id, status)
WHERE status IN ('open', 'in_review');

-- Full-text search indexes
CREATE INDEX idx_materials_search
ON materials USING gin(to_tsvector('english', name || ' ' || description));

CREATE INDEX idx_projects_search
ON projects USING gin(to_tsvector('english', name || ' ' || description));

-- Composite indexes for common filters
CREATE INDEX idx_work_orders_project_plant_status
ON work_orders(project_id, plant_id, status);

CREATE INDEX idx_material_transactions_material_created
ON material_transactions(material_id, created_at DESC);
```

#### Query Optimization Examples

```python
# app/infrastructure/persistence/repositories/work_order_repository.py

class WorkOrderRepository:
    """Optimized work order repository"""

    def get_active_work_orders_with_operations(
        self,
        plant_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> List[WorkOrder]:
        """Optimized query with eager loading"""
        query = (
            self.db.query(WorkOrderModel)
            .filter(
                WorkOrderModel.plant_id == plant_id,
                WorkOrderModel.status.in_(['planned', 'released', 'in_progress'])
            )
            .options(
                joinedload(WorkOrderModel.operations),  # Eager load operations
                joinedload(WorkOrderModel.project),     # Eager load project
                selectinload(WorkOrderModel.assigned_user)  # Eager load user
            )
            .order_by(WorkOrderModel.created_at.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )

        return query.all()
```

### Caching Strategy

#### Redis Caching

```python
# app/infrastructure/cache/redis_cache.py
import redis
import json
from typing import Any, Optional
from datetime import timedelta

class RedisCache:
    """Redis caching service"""

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.client.get(key)
        return json.loads(value) if value else None

    def set(
        self,
        key: str,
        value: Any,
        ttl: timedelta = timedelta(minutes=5)
    ) -> None:
        """Set value in cache with TTL"""
        self.client.setex(
            key,
            int(ttl.total_seconds()),
            json.dumps(value)
        )

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        self.client.delete(key)

    def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern"""
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

# Usage in repository
class MaterialRepository:
    def __init__(self, db: Session, cache: RedisCache):
        self.db = db
        self.cache = cache

    def get_by_id(self, material_id: int) -> Optional[Material]:
        """Get material with caching"""
        cache_key = f"material:{material_id}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return Material(**cached)

        # Query database
        model = self.db.query(MaterialModel).filter_by(id=material_id).first()
        if not model:
            return None

        entity = Material.from_model(model)

        # Cache for 10 minutes
        self.cache.set(cache_key, entity.to_dict(), ttl=timedelta(minutes=10))

        return entity

    def save(self, material: Material) -> Material:
        """Save and invalidate cache"""
        # Save to database
        saved = super().save(material)

        # Invalidate cache
        self.cache.delete(f"material:{saved.id}")
        self.cache.invalidate_pattern(f"materials:list:*")

        return saved
```

### API Response Optimization

```python
# app/application/dtos/work_order_dto.py
from typing import List, Optional
from pydantic import BaseModel, Field

class WorkOrderListItemDTO(BaseModel):
    """Lightweight DTO for list views"""
    id: int
    work_order_number: str
    project_number: str = Field(alias='project.project_number')
    operation_type: str
    status: str
    quantity_ordered: int
    quantity_completed: int
    progress_percentage: int

    class Config:
        orm_mode = True

class WorkOrderDetailDTO(BaseModel):
    """Full DTO for detail views"""
    id: int
    work_order_number: str
    project: ProjectSummaryDTO
    plant: PlantSummaryDTO
    operation_type: str
    description: Optional[str]
    quantity_ordered: int
    quantity_completed: int
    status: str
    operations: List[WorkOrderOperationDTO]
    assigned_user: Optional[UserSummaryDTO]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# Use appropriate DTO in endpoints
@router.get("/work-orders/", response_model=List[WorkOrderListItemDTO])
def list_work_orders(...):
    """Returns lightweight DTOs for list view"""
    pass

@router.get("/work-orders/{id}", response_model=WorkOrderDetailDTO)
def get_work_order_detail(...):
    """Returns full DTO for detail view"""
    pass
```

---

## Testing Strategy

### Backend Unit Tests

```python
# tests/domain/services/test_material_costing_service.py
import pytest
from decimal import Decimal
from datetime import datetime
from app.domain.services.material_costing_service import MaterialCostingService
from app.domain.entities.material_transaction import MaterialTransaction

class TestMaterialCostingService:
    """Test material costing calculations"""

    def test_fifo_cost_calculation(self):
        """Test FIFO costing with multiple receipts"""
        service = MaterialCostingService()

        # Create transactions
        transactions = [
            MaterialTransaction(
                id=1,
                material_id=1,
                transaction_type='receipt',
                quantity=Decimal('100'),
                unit_cost=Decimal('10.00'),
                created_at=datetime(2024, 1, 1)
            ),
            MaterialTransaction(
                id=2,
                material_id=1,
                transaction_type='receipt',
                quantity=Decimal('50'),
                unit_cost=Decimal('12.00'),
                created_at=datetime(2024, 1, 15)
            ),
        ]

        # Issue 120 units
        total_cost, breakdown = service.calculate_fifo_cost(
            transactions,
            Decimal('120')
        )

        # Assert: First 100 @ $10, next 20 @ $12
        assert total_cost == Decimal('1240.00')
        assert len(breakdown) == 2
        assert breakdown[0] == (1, Decimal('100'), Decimal('10.00'))
        assert breakdown[1] == (2, Decimal('20'), Decimal('12.00'))

    def test_fifo_insufficient_inventory(self):
        """Test FIFO raises error when insufficient inventory"""
        service = MaterialCostingService()

        transactions = [
            MaterialTransaction(
                id=1,
                material_id=1,
                transaction_type='receipt',
                quantity=Decimal('50'),
                unit_cost=Decimal('10.00'),
                created_at=datetime(2024, 1, 1)
            ),
        ]

        # Try to issue more than available
        with pytest.raises(ValueError, match="Insufficient inventory"):
            service.calculate_fifo_cost(transactions, Decimal('100'))
```

### Integration Tests

```python
# tests/api/test_work_orders.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestWorkOrderAPI:
    """Integration tests for work order endpoints"""

    def test_create_work_order(self, auth_headers, test_project):
        """Test work order creation"""
        response = client.post(
            "/api/v1/work-orders/",
            headers=auth_headers,
            json={
                "project_id": test_project.id,
                "plant_id": 1,
                "operation_type": "fabrication",
                "description": "Test work order",
                "quantity_ordered": 10
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["work_order_number"].startswith("WO-")
        assert data["status"] == "planned"

    def test_list_work_orders_filtered_by_plant(self, auth_headers):
        """Test work order list with plant filter"""
        response = client.get(
            "/api/v1/work-orders/?plant_id=1",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned work orders should be from plant 1
        assert all(wo["plant_id"] == 1 for wo in data)
```

### Frontend Tests

```typescript
// src/hooks/__tests__/useWorkOrders.test.tsx
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWorkOrders } from '../useWorkOrders'
import { workOrderService } from '@/services/workorder.service'

jest.mock('@/services/workorder.service')

describe('useWorkOrders', () => {
  const queryClient = new QueryClient()
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  it('fetches work orders successfully', async () => {
    const mockWorkOrders = [
      { id: 1, work_order_number: 'WO-001', status: 'planned' },
      { id: 2, work_order_number: 'WO-002', status: 'in_progress' }
    ]

    workOrderService.getWorkOrders.mockResolvedValue(mockWorkOrders)

    const { result } = renderHook(() => useWorkOrders(), { wrapper })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockWorkOrders)
  })
})
```

---

## Deployment Configuration

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: unison_postgres_prod
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    networks:
      - unison_network_prod
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: unison_redis_prod
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data_prod:/data
    networks:
      - unison_network_prod
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    container_name: unison_minio_prod
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data_prod:/data
    command: server /data --console-address ":9001"
    networks:
      - unison_network_prod
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: unison_backend_prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      - postgres
      - redis
      - minio
    networks:
      - unison_network_prod
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: unison_celery_worker_prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    command: celery -A app.infrastructure.tasks.celery_app worker --loglevel=info --concurrency=4
    depends_on:
      - postgres
      - redis
    networks:
      - unison_network_prod
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: unison_nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_build:/usr/share/nginx/html
    depends_on:
      - backend
    networks:
      - unison_network_prod
    restart: unless-stopped

volumes:
  postgres_data_prod:
  redis_data_prod:
  minio_data_prod:
  frontend_build:

networks:
  unison_network_prod:
    driver: bridge
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    client_max_body_size 50M;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://backend;
        access_log off;
    }

    # MinIO static files (optional direct access)
    location /files/ {
        proxy_pass http://minio:9000/;
        proxy_set_header Host $host;
    }
}
```

---

## Monitoring & Observability

### Logging Configuration

```python
# app/core/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # JSON formatter for production
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Usage in main.py
from app.core.logging import setup_logging

logger = setup_logging()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_id": getattr(request.state, 'user_id', None)
        }
    )

    return response
```

### Health Check Endpoint

```python
# app/presentation/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.persistence.database import get_db
from app.infrastructure.cache.redis_cache import RedisCache

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    health = {
        "status": "healthy",
        "checks": {}
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = f"unhealthy: {str(e)}"

    # Redis check
    try:
        cache = RedisCache()
        cache.client.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["redis"] = f"unhealthy: {str(e)}"

    # MinIO check (optional)
    try:
        from app.infrastructure.storage.minio_service import MinIOService
        minio = MinIOService()
        minio.client.bucket_exists('barcodes')
        health["checks"]["minio"] = "healthy"
    except Exception as e:
        health["checks"]["minio"] = f"degraded: {str(e)}"

    return health
```

---

## Summary

This architecture provides:

✅ **Complete 3-phase implementation** (all PDF features)
✅ **Hierarchical multi-tenancy** with RLS isolation
✅ **Full normalized schema** (47 tables)
✅ **DDD + Atomic Design** maintaining existing patterns
✅ **MinIO integration** for barcodes, documents, photos
✅ **Mock SAP adapter** with async Celery sync
✅ **PWA with offline support** (camera, barcode scanning)
✅ **Smart polling** (TanStack Query 30-60s intervals)
✅ **Basic reporting** (Recharts + CSV export)
✅ **Enterprise security** (JWT + RBAC + RLS)
✅ **Performance optimization** (caching, indexes, query optimization)
✅ **Comprehensive testing** (unit, integration, E2E)
✅ **Production deployment** (Docker, Nginx, monitoring)
✅ **Complete implementation code examples** (backend services, frontend components)

**Architecture Philosophy**:
- **Separation of Concerns**: Clean DDD layers, no mixing of responsibilities
- **Metadata-Driven**: Configuration stored in DB, not hardcoded
- **Event-Driven**: Loose coupling via async Celery tasks
- **Multi-Tenant by Design**: RLS enforced at database level
- **Offline-First PWA**: Smart polling + offline queue for reliability
- **Performance-Oriented**: Caching, indexing, query optimization
- **Production-Ready**: Monitoring, logging, health checks, deployment configs

**Next Step**: Begin Phase 1 implementation (Weeks 1-4: Foundation)!
