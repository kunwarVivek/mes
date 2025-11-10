# Comprehensive Audit & Technical Debt Implementation Plan

**Generated**: 2025-11-10
**Target Branch**: `claude/audit-and-debt-review-011CUzQmLGCEDJu6vYfGmKd8`
**Execution Strategy**: Bottom-up (Schema → Backend → Frontend)

---

## Executive Summary

Based on comprehensive analysis against PRD/FRD/Architecture documents, the codebase has **solid foundations** but critical gaps:

### Overall Completion Status
- **Database Schema**: 50% complete (RLS: 0%, Extensions: 50%, Hypertables: 0%)
- **Backend APIs**: 60-70% complete (Core CRUD done, integrations & advanced features missing)
- **Frontend**: 45% complete (Basic features done, PWA: 29%, Mobile: 20%, Config UI: 0%)
- **Technical Debt**: Medium-High (Critical: Rate limiting, CI/CD; Medium: N+1 queries, test coverage)

### Critical Blockers for Production
1. ❌ **ZERO Row-Level Security (RLS) policies** - Multi-tenant security vulnerability
2. ❌ **4 of 8 PostgreSQL extensions missing** - Architecture not PostgreSQL-native
3. ❌ **PWA not activated** - Offline mode non-functional
4. ❌ **No barcode scanning** - Core feature missing
5. ❌ **No rate limiting** - API abuse vulnerability
6. ❌ **No CI/CD pipeline** - Deployment risk

---

## Phase 1: Critical Security & Infrastructure 🔴

**Timeline**: Week 1 (5 days)
**Priority**: CRITICAL - Must fix before any other work

### 1.1 Implement Row-Level Security (RLS) Policies
**File**: `backend/database/schema/15_rls_policies.sql`

```sql
-- Enable RLS on all multi-tenant tables
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY; -- No RLS on org table
ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ... (40+ tables)

-- Create tenant isolation policies
CREATE POLICY plants_tenant_isolation ON plants
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

CREATE POLICY departments_tenant_isolation ON departments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- ... (40+ policies)
```

**Backend Integration**: Ensure all database sessions set RLS context
```python
# backend/app/infrastructure/persistence/database.py
def set_rls_context(db: Session, organization_id: int, plant_id: int = None):
    db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))
    if plant_id:
        db.execute(text(f"SET LOCAL app.current_plant_id = {plant_id}"))
```

**Testing**: Create RLS test suite
```python
# backend/tests/integration/test_rls.py
def test_rls_prevents_cross_tenant_access():
    # User from org 1 should not see org 2 data
    ...
```

**Effort**: 2 days
**Risk**: High - Must test thoroughly

---

### 1.2 Enable Missing PostgreSQL Extensions
**File**: `backend/database/schema/00_extensions.sql`

```sql
-- Already enabled
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- NEW: Add missing extensions
CREATE EXTENSION IF NOT EXISTS pgmq;       -- Message queue
CREATE EXTENSION IF NOT EXISTS pg_cron;    -- Scheduler
-- Note: pg_search (ParadeDB) and pg_duckdb require manual installation
```

**Installation Guide**: `docs/postgresql/EXTENSION_INSTALLATION.md`
```bash
# pgmq installation
sudo apt-get install pgmq

# pg_cron installation
sudo apt-get install postgresql-15-cron
```

**Effort**: 1 day (including testing)

---

### 1.3 Configure TimescaleDB Hypertables
**File**: `backend/database/schema/16_timescaledb_hypertables.sql`

```sql
-- Convert time-series tables to hypertables
SELECT create_hypertable('material_transactions', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

SELECT create_hypertable('production_logs', 'logged_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Add compression (75% storage savings)
ALTER TABLE material_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby => 'organization_id, material_id'
);

SELECT add_compression_policy('material_transactions', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('material_transactions', INTERVAL '3 years', if_not_exists => TRUE);

-- Repeat for: production_logs, qr_code_scans, sap_sync_logs,
-- audit_logs, machine_status_history, downtime_events,
-- inspection_logs, inspection_measurements
```

**Effort**: 1 day

---

### 1.4 Add Backend Health Checks
**File**: `backend/app/presentation/api/v1/health.py`

```python
from fastapi import APIRouter, status, HTTPException
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health():
    """Simple health check - always returns 200 OK if service is running"""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness():
    """Readiness probe - checks dependencies (DB, MinIO, etc.)"""
    checks = {}

    # Database connectivity
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=checks)

    # MinIO connectivity (optional)
    try:
        # Test MinIO connection
        checks["storage"] = "healthy"
    except:
        checks["storage"] = "degraded"

    return {"status": "ready", "checks": checks}

@router.get("/live")
async def liveness():
    """Liveness probe - checks if app is alive"""
    return {"status": "alive"}
```

**Register in**: `backend/app/main.py`
```python
from app.presentation.api.v1 import health
app.include_router(health.router, prefix="/api/v1")
```

**Effort**: 0.5 day

---

### 1.5 Implement Rate Limiting Middleware
**File**: `backend/app/infrastructure/middleware/rate_limiter.py`

```python
from fastapi import Request, HTTPException, status
from typing import Callable
import time

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {ip: [timestamps]}

    async def __call__(self, request: Request, call_next: Callable):
        client_ip = request.client.host
        now = time.time()

        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if now - ts < 60
            ]
        else:
            self.requests[client_ip] = []

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Add request
        self.requests[client_ip].append(now)

        response = await call_next(request)
        return response
```

**Register**: `backend/app/main.py`
```python
from app.infrastructure.middleware.rate_limiter import RateLimiter
app.middleware("http")(RateLimiter(requests_per_minute=100))
```

**Effort**: 0.5 day

---

### 1.6 Setup CI/CD Pipeline
**File**: `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop, 'claude/*' ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=html
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit (Python security)
        run: |
          pip install bandit
          bandit -r backend/app -f json -o bandit-report.json || true
      - name: Run npm audit
        run: |
          cd frontend
          npm audit --audit-level=moderate
```

**Effort**: 1 day

---

## Phase 2: Database Schema Fixes 🟡

**Timeline**: Week 2 (5 days)
**Priority**: HIGH - Enables backend features

### 2.1 Create Missing Tables

**File**: `backend/database/schema/17_missing_tables.sql`

```sql
-- Supply Chain & Procurement
CREATE TABLE IF NOT EXISTS suppliers (
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

CREATE TABLE IF NOT EXISTS rfqs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    rfq_number VARCHAR(50) NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    material_id INTEGER REFERENCES materials(id),
    quantity NUMERIC(15,3) NOT NULL,
    required_by_date DATE,
    status VARCHAR(20) DEFAULT 'draft', -- draft, sent, quoted, accepted, rejected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, rfq_number)
);

-- Production Planning
CREATE TABLE IF NOT EXISTS manpower_allocation (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    operation_sequence INTEGER,
    allocated_hours NUMERIC(8,2),
    actual_hours NUMERIC(8,2),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rbs_schedules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    lane_id INTEGER REFERENCES lanes(id),
    operation_sequence INTEGER NOT NULL,
    scheduled_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start_date TIMESTAMP WITH TIME ZONE,
    actual_end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rps_sheets (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    resource_type VARCHAR(50) NOT NULL, -- labor, equipment, material
    resource_id INTEGER, -- References various tables based on type
    planned_hours NUMERIC(10,2),
    actual_hours NUMERIC(10,2),
    planned_cost NUMERIC(15,2),
    actual_cost NUMERIC(15,2),
    week_ending DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_work_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    shift_id INTEGER REFERENCES shifts(id),
    log_date DATE NOT NULL,
    work_center_id INTEGER REFERENCES work_centers(id),
    target_production INTEGER,
    actual_production INTEGER,
    scrap_count INTEGER,
    downtime_minutes INTEGER,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, plant_id, shift_id, log_date, work_center_id)
);

CREATE TABLE IF NOT EXISTS delivery_predictions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    predicted_delivery_date DATE NOT NULL,
    confidence_score NUMERIC(3,2), -- 0.00 to 1.00
    prediction_method VARCHAR(50), -- linear_regression, ml_model, manual
    factors JSONB, -- JSON object with factors affecting prediction
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Infrastructure
CREATE UNLOGGED TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    cache_value JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cache_expires ON cache(expires_at) WHERE expires_at IS NOT NULL;

-- Storage Locations
CREATE TABLE IF NOT EXISTS storage_locations (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plant_id INTEGER NOT NULL REFERENCES plants(id),
    location_code VARCHAR(50) NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50), -- warehouse, production_floor, staging
    parent_location_id INTEGER REFERENCES storage_locations(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, plant_id, location_code)
);

-- Unit of Measure
CREATE TABLE IF NOT EXISTS units_of_measure (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    uom_code VARCHAR(10) NOT NULL,
    uom_name VARCHAR(50) NOT NULL,
    uom_type VARCHAR(20), -- length, weight, volume, count
    base_unit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, uom_code)
);

CREATE TABLE IF NOT EXISTS uom_conversions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    from_uom_id INTEGER NOT NULL REFERENCES units_of_measure(id),
    to_uom_id INTEGER NOT NULL REFERENCES units_of_measure(id),
    conversion_factor NUMERIC(15,6) NOT NULL, -- multiply by this to convert
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, from_uom_id, to_uom_id)
);
```

**SQLAlchemy Models**: Create corresponding models in:
- `backend/app/models/supplier.py`
- `backend/app/models/rfq.py`
- `backend/app/models/manpower_allocation.py`
- `backend/app/models/rbs_schedule.py`
- `backend/app/models/rps_sheet.py`
- `backend/app/models/daily_work_log.py`
- `backend/app/models/delivery_prediction.py`
- `backend/app/models/storage_location.py`
- `backend/app/models/unit_of_measure.py`

**Effort**: 3 days

---

### 2.2 Add Missing Columns to Existing Tables

**File**: `backend/database/schema/18_missing_columns.sql`

```sql
-- Organizations
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS industry VARCHAR(100);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);

-- Users
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_code VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Plants
ALTER TABLE plants ADD COLUMN IF NOT EXISTS plant_type VARCHAR(50); -- fabrication, production, assembly
ALTER TABLE plants ADD COLUMN IF NOT EXISTS manager_user_id INTEGER REFERENCES users(id);
ALTER TABLE plants ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Departments
ALTER TABLE departments ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE departments ADD COLUMN IF NOT EXISTS head_user_id INTEGER REFERENCES users(id);

-- Materials (table name: material)
ALTER TABLE material ADD COLUMN IF NOT EXISTS barcode_data VARCHAR(255);
ALTER TABLE material ADD COLUMN IF NOT EXISTS qr_code_data TEXT;
ALTER TABLE material ADD COLUMN IF NOT EXISTS sap_material_number VARCHAR(100);
ALTER TABLE material ADD COLUMN IF NOT EXISTS minimum_stock_level NUMERIC(15,3);
ALTER TABLE material ADD COLUMN IF NOT EXISTS maximum_stock_level NUMERIC(15,3);
ALTER TABLE material ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Work Orders (table name: work_order)
ALTER TABLE work_order ADD COLUMN IF NOT EXISTS sap_production_order VARCHAR(100);
ALTER TABLE work_order ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE work_order ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);
ALTER TABLE work_order ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(id);

-- Lanes
ALTER TABLE lanes ADD COLUMN IF NOT EXISTS current_work_order_id INTEGER REFERENCES work_orders(id);
ALTER TABLE lanes ADD COLUMN IF NOT EXISTS capacity NUMERIC(10,2); -- units per hour

-- NCRs (table name: ncr)
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS ncr_type VARCHAR(50); -- material, process, final_inspection
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS detected_by INTEGER REFERENCES users(id);
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS assigned_to INTEGER REFERENCES users(id);
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS resolved_by INTEGER REFERENCES users(id);
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS closed_by INTEGER REFERENCES users(id);
ALTER TABLE ncr ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP WITH TIME ZONE;

-- Machines
ALTER TABLE machines ADD COLUMN IF NOT EXISTS capacity_units_per_hour NUMERIC(10,2);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS current_work_order_id INTEGER REFERENCES work_orders(id);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(255);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS model_number VARCHAR(100);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS serial_number VARCHAR(100);
ALTER TABLE machines ADD COLUMN IF NOT EXISTS purchase_cost NUMERIC(15,2);

-- Projects
ALTER TABLE projects ADD COLUMN IF NOT EXISTS sap_sales_order VARCHAR(100);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget NUMERIC(15,2);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS actual_cost NUMERIC(15,2);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- Inventory (if separate from material table)
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS last_counted_at TIMESTAMP WITH TIME ZONE;
```

**Update Models**: Modify SQLAlchemy models to include new columns

**Effort**: 1 day

---

### 2.3 Create Missing Indexes

**File**: `backend/database/schema/19_indexes.sql`

```sql
-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_work_orders_org_plant_status
    ON work_order(organization_id, plant_id, status);

CREATE INDEX IF NOT EXISTS idx_production_logs_wo_date
    ON production_logs(work_order_id, logged_at DESC);

CREATE INDEX IF NOT EXISTS idx_materials_org_active
    ON material(organization_id, is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_inventory_material_location
    ON inventory(material_id, warehouse_location);

CREATE INDEX IF NOT EXISTS idx_ncr_org_status
    ON ncr(organization_id, status);

CREATE INDEX IF NOT EXISTS idx_machines_plant_status
    ON machines(plant_id, status);

-- Foreign key indexes (if missing)
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_plant_id ON user_roles(plant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_id ON workflow_states(workflow_id);

-- Full-text search (pg_trgm for now, pg_search later)
CREATE INDEX IF NOT EXISTS idx_materials_name_trgm ON material USING gin(material_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_materials_desc_trgm ON material USING gin(description gin_trgm_ops);
```

**Effort**: 0.5 day

---

### 2.4 Setup Alembic Migrations

**Initialize Alembic**:
```bash
cd backend
alembic init alembic
```

**Create Baseline Migration**:
```bash
alembic revision --autogenerate -m "baseline_schema"
```

**File**: `backend/alembic/env.py`
```python
from app.core.database import Base
from app.models import *  # Import all models

target_metadata = Base.metadata
```

**Effort**: 1 day

---

## Phase 3: Backend Critical APIs 🟡

**Timeline**: Week 3-4 (10 days)
**Priority**: HIGH - Enables frontend features

### 3.1 SAP Integration Endpoints
**File**: `backend/app/presentation/api/v1/sap_integration.py`

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from app.infrastructure.adapters.sap.sap_client import SAPClient
from app.infrastructure.messaging.pgmq_client import PGMQClient

router = APIRouter(prefix="/sap", tags=["SAP Integration"])

@router.post("/sync/materials")
async def sync_materials(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Trigger material master sync from SAP"""
    job_id = generate_job_id()

    # Enqueue background job
    pgmq_client.send('sap_sync_jobs', {
        'job_id': job_id,
        'sync_type': 'materials',
        'organization_id': current_user['organization_id']
    })

    return {"job_id": job_id, "status": "queued"}

@router.post("/sync/work-orders/{work_order_id}")
async def sync_work_order_to_sap(
    work_order_id: int,
    current_user = Depends(get_current_user)
):
    """Push work order confirmation to SAP"""
    # Implementation
    pass

@router.get("/sync/status/{job_id}")
async def get_sync_status(job_id: str):
    """Check status of sync job"""
    # Query sap_sync_logs table
    pass

@router.get("/sync/logs")
async def get_sync_logs(
    limit: int = 50,
    current_user = Depends(get_current_user)
):
    """Get sync history"""
    pass

@router.post("/connection/test")
async def test_sap_connection(current_user = Depends(get_current_user)):
    """Test SAP connection"""
    try:
        sap_client = SAPClient()
        result = sap_client.test_connection()
        return {"status": "success", "details": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

**PGMQ Worker**: `backend/app/infrastructure/messaging/sap_sync_worker.py`
```python
def process_sap_sync_job(message):
    job_data = message['message']
    sync_type = job_data['sync_type']

    if sync_type == 'materials':
        sap_client = SAPClient()
        materials = sap_client.fetch_materials()
        # Update database

    # Log sync result
    db.add(SAPSyncLog(...))
    db.commit()
```

**Effort**: 3 days

---

### 3.2 Email Notification System
**File**: `backend/app/application/services/notification_service.py`

```python
from app.infrastructure.email.email_service import EmailService
from jinja2 import Template

class NotificationService:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def send_ncr_created_notification(self, ncr_id: int):
        """Send email when NCR is created"""
        ncr = get_ncr(ncr_id)

        template = Template("""
        <h2>NCR #{{ ncr.ncr_number }} Created</h2>
        <p><strong>Description:</strong> {{ ncr.description }}</p>
        <p><strong>Severity:</strong> {{ ncr.severity }}</p>
        <p><strong>Detected by:</strong> {{ ncr.detected_by.full_name }}</p>
        <p><a href="{{ url }}">View NCR</a></p>
        """)

        html_content = template.render(ncr=ncr, url=f"https://app.example.com/quality/ncrs/{ncr_id}")

        await self.email_service.send_email(
            to=ncr.assigned_to.email,
            subject=f"NCR #{ncr.ncr_number} Assigned to You",
            html_content=html_content
        )

    async def send_work_order_assigned_notification(self, work_order_id: int):
        """Send email when work order is assigned"""
        pass

    async def send_low_stock_alert(self, material_id: int):
        """Send email for low stock"""
        pass
```

**Templates**: Create email templates in `backend/app/infrastructure/email/templates/`

**Effort**: 2 days

---

### 3.3 Barcode Generation Service
**File**: `backend/app/application/services/barcode_service.py`

```python
import barcode
from barcode.writer import ImageWriter
import qrcode
from io import BytesIO

class BarcodeService:
    def generate_code128(self, data: str) -> bytes:
        """Generate Code128 barcode"""
        code = barcode.Code128(data, writer=ImageWriter())
        buffer = BytesIO()
        code.write(buffer)
        return buffer.getvalue()

    def generate_qr_code(self, data: str) -> bytes:
        """Generate QR code"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def generate_gs1_barcode(self, gtin: str, lot: str = None, serial: str = None) -> str:
        """Generate GS1-128 barcode for traceability"""
        # GS1 Application Identifiers
        data = f"(01){gtin}"  # GTIN
        if lot:
            data += f"(10){lot}"  # Batch/Lot Number
        if serial:
            data += f"(21){serial}"  # Serial Number
        return data
```

**API Endpoint**: `backend/app/presentation/api/v1/barcodes.py`
```python
@router.post("/materials/{material_id}/barcode")
async def generate_material_barcode(
    material_id: int,
    format: str = "qr",  # qr, code128
    current_user = Depends(get_current_user)
):
    material = material_repo.get(material_id)
    barcode_service = BarcodeService()

    if format == "qr":
        image_bytes = barcode_service.generate_qr_code(material.material_code)
    else:
        image_bytes = barcode_service.generate_code128(material.material_code)

    return Response(content=image_bytes, media_type="image/png")
```

**Effort**: 1 day

---

### 3.4 Storage Location & UOM APIs
**Files**:
- `backend/app/presentation/api/v1/storage_locations.py`
- `backend/app/presentation/api/v1/units_of_measure.py`

**CRUD Operations**: Standard create, read, update, delete for both entities

**Effort**: 2 days

---

### 3.5 Missing Business Logic

**Traceability Service**: Complete forward/backward genealogy
**File**: `backend/app/application/services/traceability_service.py`

```python
class TraceabilityService:
    def get_forward_genealogy(self, lot_number: str):
        """Where was this lot used (forward trace)"""
        # Query lot_genealogy table
        # Recursive query to find all downstream usage
        pass

    def get_backward_genealogy(self, serial_number: str):
        """What materials went into this serial (backward trace)"""
        # Query lot_genealogy table
        # Recursive query to find all upstream materials
        pass

    def generate_traceability_report(self, entity_type: str, entity_id: int):
        """Generate complete traceability report"""
        pass
```

**Effort**: 2 days

---

## Phase 4: Frontend Critical Features 🟡

**Timeline**: Week 5-6 (10 days)
**Priority**: HIGH - MVP blockers

### 4.1 Activate PWA
**File**: `frontend/vite.config.ts`

```typescript
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Unison Manufacturing ERP',
        short_name: 'Unison',
        theme_color: '#3b82f6',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 // 1 hour
              }
            }
          }
        ]
      }
    })
  ]
})
```

**Register Service Worker**: `frontend/src/App.tsx`
```typescript
import { useEffect } from 'react';
import { useRegisterSW } from 'virtual:pwa-register/react';

function App() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  useEffect(() => {
    if (needRefresh) {
      // Show update prompt
      if (confirm('New version available. Update now?')) {
        updateServiceWorker(true);
      }
    }
  }, [needRefresh]);

  return <RouterProvider router={router} />;
}
```

**Offline Indicator**: `frontend/src/components/OfflineIndicator.tsx`
```typescript
export function OfflineIndicator() {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded">
      📡 Offline - Changes will sync when connection is restored
    </div>
  );
}
```

**Effort**: 1 day

---

### 4.2 Barcode Scanner Component
**File**: `frontend/src/components/BarcodeScanner.tsx`

```typescript
import { Html5QrcodeScanner } from 'html5-qrcode';
import { useEffect, useRef } from 'react';

interface BarcodeScannerProps {
  onScan: (code: string) => void;
  onError?: (error: string) => void;
}

export function BarcodeScanner({ onScan, onError }: BarcodeScannerProps) {
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    const scanner = new Html5QrcodeScanner(
      'qr-reader',
      { fps: 10, qrbox: { width: 250, height: 250 } },
      false
    );

    scanner.render(
      (decodedText) => {
        onScan(decodedText);
        scanner.clear();
      },
      (error) => {
        if (onError) onError(error);
      }
    );

    scannerRef.current = scanner;

    return () => {
      scanner.clear();
    };
  }, []);

  return <div id="qr-reader" />;
}
```

**Usage Example**: Material receiving with barcode
```typescript
function MaterialReceivingPage() {
  const [scanning, setScanning] = useState(false);

  const handleScan = (materialCode: string) => {
    // Look up material by code
    const material = lookupMaterial(materialCode);
    // Pre-fill form
    setFormData({ material_id: material.id, ... });
    setScanning(false);
  };

  return (
    <>
      <Button onClick={() => setScanning(true)}>
        📷 Scan Barcode
      </Button>
      {scanning && (
        <Modal>
          <BarcodeScanner onScan={handleScan} />
        </Modal>
      )}
    </>
  );
}
```

**Effort**: 1 day

---

### 4.3 Camera Capture for NCRs
**File**: `frontend/src/components/CameraCapture.tsx`

```typescript
export function CameraCapture({ onCapture }: { onCapture: (file: File) => void }) {
  return (
    <input
      type="file"
      accept="image/*"
      capture="environment"  // Use rear camera
      onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) onCapture(file);
      }}
    />
  );
}
```

**Integrate in NCR Form**: `frontend/src/features/quality/components/NCRForm.tsx`
```typescript
function NCRForm() {
  const [photos, setPhotos] = useState<File[]>([]);

  const handlePhotoCapture = (file: File) => {
    setPhotos([...photos, file]);
  };

  return (
    <form>
      {/* ... other fields ... */}

      <div>
        <label>Defect Photos</label>
        <CameraCapture onCapture={handlePhotoCapture} />

        <div className="grid grid-cols-3 gap-2 mt-2">
          {photos.map((photo, idx) => (
            <img
              key={idx}
              src={URL.createObjectURL(photo)}
              alt={`Photo ${idx + 1}`}
              className="w-full h-32 object-cover rounded"
            />
          ))}
        </div>
      </div>
    </form>
  );
}
```

**Effort**: 0.5 day

---

### 4.4 Organization/Plant Switcher
**File**: `frontend/src/components/OrganizationSwitcher.tsx`

```typescript
import { useAuthStore } from '@/stores/auth.store';

export function OrganizationSwitcher() {
  const { organizations, currentOrg, currentPlant, setCurrentOrg, setCurrentPlant } = useAuthStore();

  return (
    <div className="flex gap-2">
      <Select
        value={currentOrg?.id}
        onChange={(orgId) => setCurrentOrg(orgId)}
      >
        {organizations.map(org => (
          <option key={org.id} value={org.id}>{org.name}</option>
        ))}
      </Select>

      {currentOrg && (
        <Select
          value={currentPlant?.id}
          onChange={(plantId) => setCurrentPlant(plantId)}
        >
          {currentOrg.plants.map(plant => (
            <option key={plant.id} value={plant.id}>{plant.name}</option>
          ))}
        </Select>
      )}
    </div>
  );
}
```

**Add to Navigation**: `frontend/src/components/layouts/Navigation.tsx`

**Effort**: 0.5 day

---

### 4.5 Dashboard KPIs (OEE, OTD, FPY)
**File**: `frontend/src/pages/DashboardPage.tsx`

```typescript
export function DashboardPage() {
  const { data: oee } = useQuery(['oee'], () => api.getOEE());
  const { data: otd } = useQuery(['otd'], () => api.getOTD());
  const { data: fpy } = useQuery(['fpy'], () => api.getFPY());

  return (
    <div className="grid grid-cols-3 gap-4">
      <OEEGauge value={oee?.oee || 0} />
      <OTDWidget value={otd?.percentage || 0} />
      <FPYWidget value={fpy?.percentage || 0} />
    </div>
  );
}
```

**Backend Endpoints**: Add to `backend/app/presentation/api/v1/metrics.py`
```python
@router.get("/oee")
async def get_oee(
    plant_id: int,
    start_date: date,
    end_date: date
):
    # Calculate OEE
    pass

@router.get("/otd")
async def get_otd(plant_id: int, start_date: date, end_date: date):
    # Calculate On-Time Delivery
    delivered_on_time = db.query(WorkOrder).filter(
        WorkOrder.plant_id == plant_id,
        WorkOrder.actual_end_date <= WorkOrder.due_date
    ).count()

    total = db.query(WorkOrder).filter(
        WorkOrder.plant_id == plant_id
    ).count()

    percentage = (delivered_on_time / total * 100) if total > 0 else 0
    return {"percentage": percentage, "delivered_on_time": delivered_on_time, "total": total}

@router.get("/fpy")
async def get_fpy(plant_id: int, start_date: date, end_date: date):
    # Calculate First Pass Yield
    pass
```

**Effort**: 2 days

---

### 4.6 Gantt Chart Scheduling
**File**: `frontend/src/features/scheduling/components/GanttChart.tsx`

**Option 1: Use react-gantt-chart library**
```typescript
import { Gantt, Task } from 'react-gantt-chart';

export function GanttChart({ workOrders }: { workOrders: WorkOrder[] }) {
  const tasks: Task[] = workOrders.map(wo => ({
    id: wo.id.toString(),
    name: wo.work_order_number,
    start: new Date(wo.scheduled_start_date),
    end: new Date(wo.scheduled_end_date),
    progress: wo.quantity_completed / wo.quantity_ordered * 100,
    dependencies: wo.dependencies?.map(d => d.toString()) || [],
  }));

  return (
    <Gantt
      tasks={tasks}
      viewMode="Day"
      onDoubleClick={(task) => {
        // Open work order detail modal
      }}
      onDateChange={(task, start, end) => {
        // Update work order schedule via API
        updateWorkOrderSchedule(task.id, start, end);
      }}
    />
  );
}
```

**Option 2: Use DHTMLX Gantt (more powerful but license required)**

**Integration**: `frontend/src/routes/scheduling.tsx`
```typescript
export const Route = createFileRoute('/scheduling')({
  component: SchedulingPage,
})

function SchedulingPage() {
  const { data: workOrders } = useQuery(['work-orders'], fetchWorkOrders);

  return (
    <div>
      <h1>Visual Production Scheduling</h1>
      <GanttChart workOrders={workOrders} />
    </div>
  );
}
```

**Effort**: 3 days

---

### 4.7 Custom Fields Configuration UI
**File**: `frontend/src/features/settings/pages/CustomFieldsPage.tsx`

```typescript
export function CustomFieldsPage() {
  const [fields, setFields] = useState<CustomField[]>([]);

  return (
    <div>
      <h1>Custom Fields Configuration</h1>

      <Button onClick={() => setShowCreateModal(true)}>
        + Add Custom Field
      </Button>

      <Table>
        <thead>
          <tr>
            <th>Field Name</th>
            <th>Entity</th>
            <th>Type</th>
            <th>Required</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {fields.map(field => (
            <tr key={field.id}>
              <td>{field.field_name}</td>
              <td>{field.entity_type}</td>
              <td>{field.field_type}</td>
              <td>{field.is_required ? 'Yes' : 'No'}</td>
              <td>
                <Button onClick={() => editField(field)}>Edit</Button>
                <Button onClick={() => deleteField(field.id)}>Delete</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {showCreateModal && (
        <CustomFieldFormModal
          onClose={() => setShowCreateModal(false)}
          onSave={(field) => {
            createCustomField(field);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}
```

**Form Modal**: `frontend/src/features/settings/components/CustomFieldFormModal.tsx`
```typescript
function CustomFieldFormModal({ onSave, onClose }) {
  const { register, handleSubmit } = useForm();

  return (
    <Modal onClose={onClose}>
      <form onSubmit={handleSubmit(onSave)}>
        <Input {...register('field_name')} label="Field Name" />

        <Select {...register('entity_type')} label="Apply To">
          <option value="material">Materials</option>
          <option value="work_order">Work Orders</option>
          <option value="ncr">NCRs</option>
          <option value="project">Projects</option>
        </Select>

        <Select {...register('field_type')} label="Field Type">
          <option value="text">Text</option>
          <option value="number">Number</option>
          <option value="date">Date</option>
          <option value="boolean">Checkbox</option>
          <option value="select">Dropdown</option>
        </Select>

        <Checkbox {...register('is_required')} label="Required" />

        <Button type="submit">Save</Button>
      </form>
    </Modal>
  );
}
```

**Routes**: Add `/settings/custom-fields` route

**Effort**: 2 days

---

### 4.8 Global Error Handling
**File**: `frontend/src/components/ErrorBoundary.tsx`

```typescript
import React from 'react';

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
    // Send to error tracking service (e.g., Sentry)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600">Something went wrong</h1>
            <p className="mt-2 text-gray-600">{this.state.error?.message}</p>
            <Button
              onClick={() => this.setState({ hasError: false })}
              className="mt-4"
            >
              Try Again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Toast Notification Store**: `frontend/src/stores/notifications.store.ts`
```typescript
import { create } from 'zustand';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
}

interface NotificationStore {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  addNotification: (notification) => {
    const id = Math.random().toString(36);
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id }],
    }));
    // Auto-remove after 5 seconds
    setTimeout(() => {
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      }));
    }, 5000);
  },
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
```

**Toast Component**: `frontend/src/components/Toast.tsx`
```typescript
export function ToastContainer() {
  const { notifications, removeNotification } = useNotificationStore();

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`px-4 py-3 rounded shadow-lg ${
            notification.type === 'error' ? 'bg-red-500' :
            notification.type === 'success' ? 'bg-green-500' :
            notification.type === 'warning' ? 'bg-yellow-500' :
            'bg-blue-500'
          } text-white`}
        >
          {notification.message}
          <button
            onClick={() => removeNotification(notification.id)}
            className="ml-4 font-bold"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
```

**Usage**: Replace all `console.error` with `addNotification`
```typescript
// Before
catch (error) {
  console.error('Failed to create material', error);
}

// After
import { useNotificationStore } from '@/stores/notifications.store';

const { addNotification } = useNotificationStore();
catch (error) {
  addNotification({ type: 'error', message: 'Failed to create material' });
}
```

**Effort**: 1 day

---

## Phase 5: Business Logic & Advanced Features 🟢

**Timeline**: Week 7-10 (4 weeks)
**Priority**: MEDIUM - Nice to have for MVP

### 5.1 Complete MRP Service
### 5.2 Workflow Designer UI
### 5.3 White-Label Branding UI
### 5.4 Inspection Plans UI
### 5.5 Serial/Lot Traceability UI
### 5.6 Logistics/Shipment Tracking
### 5.7 Export/Import Functionality
### 5.8 PDF Report Generation
### 5.9 Advanced Scheduling (APS)
### 5.10 Increase Test Coverage to 70%+

*(Detailed implementation plans for Phase 5 available upon request)*

---

## Testing Strategy

### Unit Tests
- Backend: pytest with >70% coverage target
- Frontend: Vitest with >60% coverage target

### Integration Tests
- API endpoint tests with test database
- Database migration tests
- PGMQ job processing tests

### E2E Tests
- Critical user journeys (Playwright):
  1. Login → Create Work Order → Production Logging
  2. Material Receipt → Inventory Check → Material Issue
  3. NCR Creation → Approval Workflow → Closure
  4. Barcode Scan → Work Order Assignment

### Security Tests
- RLS isolation tests (prevent cross-tenant access)
- RBAC permission tests
- Input validation tests (XSS, SQL injection)
- Rate limiting tests

---

## Deployment Checklist

### Before Production
- [ ] All RLS policies tested and verified
- [ ] PostgreSQL extensions installed (pgmq, pg_cron)
- [ ] Environment variables validated (no default secrets)
- [ ] Health check endpoints responding
- [ ] Rate limiting enabled
- [ ] CI/CD pipeline passing
- [ ] Security audit completed
- [ ] Backup strategy configured
- [ ] Monitoring/alerting setup (Sentry, Datadog)
- [ ] Load testing completed

### Post-Deployment
- [ ] Smoke tests passing
- [ ] Health checks green
- [ ] Monitor error rates
- [ ] Check RLS performance impact
- [ ] Verify PWA installation works

---

## Monitoring & Observability

### Metrics to Track
- API response times (p50, p95, p99)
- Error rates by endpoint
- Database query performance
- RLS policy overhead
- PGMQ queue depth
- Cache hit rates
- PWA installation rate
- Offline sync success rate

### Alerting
- API error rate >5%
- Database connection pool exhausted
- PGMQ queue depth >1000
- Disk space <20%
- Memory usage >80%
- RLS policy failures

---

## Effort Summary

| Phase | Timeline | Engineer-Days | Priority |
|-------|----------|---------------|----------|
| Phase 1: Critical Security & Infrastructure | Week 1 | 5 days | 🔴 CRITICAL |
| Phase 2: Database Schema Fixes | Week 2 | 5 days | 🟡 HIGH |
| Phase 3: Backend Critical APIs | Week 3-4 | 10 days | 🟡 HIGH |
| Phase 4: Frontend Critical Features | Week 5-6 | 10 days | 🟡 HIGH |
| Phase 5: Advanced Features | Week 7-10 | 20 days | 🟢 MEDIUM |
| **Total** | **10 weeks** | **50 days** | |

**With 2-3 engineers**: ~3-4 months to production-ready state

---

## Success Criteria

### Phase 1 Success
- ✅ RLS policies block cross-tenant access (integration tests passing)
- ✅ PostgreSQL extensions installed and operational
- ✅ Health checks returning 200 OK
- ✅ Rate limiting preventing abuse (429 errors for >100 req/min)
- ✅ CI/CD pipeline green

### MVP Success
- ✅ All Phase 1-4 features deployed
- ✅ PWA installable and offline mode working
- ✅ Barcode scanning functional on mobile
- ✅ Dashboard showing OEE, OTD, FPY
- ✅ Email notifications sending
- ✅ SAP sync operational (at least mock mode)
- ✅ 70%+ test coverage on critical paths
- ✅ Zero known security vulnerabilities

### Production Ready
- ✅ All MVP criteria met
- ✅ Load testing passed (100 concurrent users)
- ✅ Security audit completed
- ✅ Backup/restore tested
- ✅ Monitoring and alerting configured
- ✅ Deployment runbook documented

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLS performance degradation | Medium | High | Benchmark queries, add indexes, cache where appropriate |
| PostgreSQL extension install failures | Low | High | Document manual installation, provide Docker images with extensions |
| PWA not working on iOS Safari | Medium | Medium | Test on iOS devices, provide fallback for unsupported features |
| Gantt chart library incompatibility | Low | Medium | Evaluate 2-3 libraries, have backup plan |
| Migration breaking existing data | Medium | High | Test migrations on staging database, backup before migration |

---

## Next Steps

1. **Review and approve plan** with stakeholders
2. **Setup development branch** (`claude/audit-and-debt-review-011CUzQmLGCEDJu6vYfGmKd8`)
3. **Start Phase 1** with RLS implementation
4. **Daily standups** to track progress
5. **Weekly demos** of completed features

---

**Document Owner**: Claude Code Agent
**Last Updated**: 2025-11-10
**Status**: READY FOR IMPLEMENTATION
