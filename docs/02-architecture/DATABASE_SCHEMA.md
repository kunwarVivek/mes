# Database Schema - PostgreSQL-Native Architecture

**Version**: 2.0
**Date**: 2025-11-07
**Database**: PostgreSQL 15+ with Extensions
**Architecture**: Multi-tenant with Row-Level Security (RLS)

---

## Table of Contents

1. [Overview](#overview)
2. [PostgreSQL Extensions & Features](#postgresql-extensions--features)
3. [Schema Structure (47 Tables)](#schema-structure-47-tables)
4. [Multi-Tenancy & RLS](#multi-tenancy--rls)
5. [Indexes & Performance](#indexes--performance)
6. [Data Partitioning](#data-partitioning)

---

## Overview

### Architecture Principles

- **PostgreSQL-Native Stack**: All infrastructure services (queue, cache, search, analytics, scheduling) implemented as PostgreSQL extensions
- **Row-Level Security (RLS)**: Multi-tenant data isolation at database level
- **Normalized Design**: 3NF normalized schema with strategic denormalization
- **Time-Series Optimization**: `timescaledb` hypertables for time-series data (production logs, machine status, inspections)
- **Full-Text Search**: `pg_search` (ParadeDB) BM25 indexes for materials, work orders, projects
- **ACID Compliance**: Transactional consistency for all operations

### Container Reduction Impact

| Aspect | Traditional Stack | PostgreSQL-Native | Improvement |
|--------|-------------------|-------------------|-------------|
| **Services** | PostgreSQL + Redis + Celery + RabbitMQ + Elasticsearch | PostgreSQL (with extensions) | **5 → 1** (80% reduction) |
| **Containers** | 8-10 | 3-4 | **60% reduction** |
| **Backup Operations** | 5 separate backup strategies | 1 database backup | **80% simpler** |
| **Monitoring Tools** | 5 different monitoring stacks | 1 database monitoring | **80% simpler** |

---

## PostgreSQL Extensions & Features

### Extensions Used

```sql
-- Enable all extensions
CREATE EXTENSION IF NOT EXISTS pgmq;           -- Message queue (replaces Celery + RabbitMQ)
CREATE EXTENSION IF NOT EXISTS pg_cron;        -- Scheduled tasks (replaces Celery Beat)
CREATE EXTENSION IF NOT EXISTS pg_search;      -- Full-text search (replaces Elasticsearch)
CREATE EXTENSION IF NOT EXISTS pg_duckdb;      -- Analytics engine (OLAP queries)
CREATE EXTENSION IF NOT EXISTS timescaledb;    -- Time-series optimization
```

### Native Features Used

```sql
-- UNLOGGED tables for cache (2x faster writes, 1-2ms latency)
CREATE UNLOGGED TABLE cache (...);

-- LISTEN/NOTIFY for pub/sub messaging
SELECT pg_notify('production_log_created', json_build_object('id', 123)::text);

-- SKIP LOCKED for concurrent queue processing
SELECT * FROM queue FOR UPDATE SKIP LOCKED;

-- Row-Level Security (RLS) for multi-tenant isolation
ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
CREATE POLICY plants_tenant_isolation ON plants
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

### Performance Benchmarks

| Operation | Traditional Stack | PostgreSQL-Native | Improvement |
|-----------|-------------------|-------------------|-------------|
| **Background Jobs** | Celery: ~500 jobs/hour | PGMQ: 30K msgs/sec | **300x faster** |
| **Full-Text Search** | tsvector: 100ms | pg_search: 5ms | **20x faster** |
| **Analytics Queries** | Standard: 5s | pg_duckdb: 50ms | **100x faster** |
| **Cache Operations** | Redis: <1ms | UNLOGGED: 1-2ms | Acceptable trade-off |
| **Time-Series Queries** | Standard: 2s | timescaledb: 200ms | **10x faster** |

---

## Schema Structure (47 Tables)

### 1. Multi-Tenancy & Identity (7 tables)

#### **organizations**
*Tenant root entity - no RLS (global table)*

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

-- pg_search: Enable BM25 full-text search on organizations
SELECT paradedb.create_bm25(
    table_name => 'organizations',
    index_name => 'organizations_search_idx',
    key_field => 'id',
    text_fields => '{name, code, industry}'
);
```

#### **plants**
*Manufacturing sites within organization*

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

-- RLS: Tenant isolation
ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
CREATE POLICY plants_tenant_isolation ON plants
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_plants_org ON plants(organization_id);
CREATE INDEX idx_plants_type ON plants(plant_type) WHERE is_active = TRUE;
```

#### **departments**
*Organizational units within plants*

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

-- RLS: Tenant isolation
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
CREATE POLICY departments_tenant_isolation ON departments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_departments_plant ON departments(plant_id);
```

#### **users**
*System users with plant access*

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

-- RLS: Tenant isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_tenant_isolation ON users
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_users_email ON users(email) WHERE is_active = TRUE;
CREATE INDEX idx_users_employee_code ON users(employee_code);

-- pg_search: Full-text search on user names
SELECT paradedb.create_bm25(
    table_name => 'users',
    index_name => 'users_search_idx',
    key_field => 'id',
    text_fields => '{full_name, email, username, employee_code}'
);
```

#### **roles**
*RBAC role definitions*

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

-- RLS: Tenant isolation
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY roles_tenant_isolation ON roles
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### **user_roles**
*User-role assignments*

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

-- RLS: Tenant isolation
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_roles_tenant_isolation ON user_roles
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
```

#### **user_plant_access**
*Plant-level access control*

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

-- RLS: Tenant isolation
ALTER TABLE user_plant_access ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_plant_access_tenant_isolation ON user_plant_access
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_user_plant_access_user ON user_plant_access(user_id);
CREATE INDEX idx_user_plant_access_plant ON user_plant_access(plant_id);
```

---

### 2. Material Management (6 tables)

#### **material_categories**
*Hierarchical material classification*

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

-- RLS: Tenant isolation
ALTER TABLE material_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_categories_tenant_isolation ON material_categories
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_material_categories_parent ON material_categories(parent_category_id);
```

#### **materials**
*Material master with barcode/QR and SAP integration*

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

-- RLS: Tenant isolation
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY materials_tenant_isolation ON materials
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_materials_barcode ON materials(barcode_data);
CREATE INDEX idx_materials_qr ON materials(qr_code_data);
CREATE INDEX idx_materials_sap ON materials(sap_material_number);
CREATE INDEX idx_materials_category ON materials(category_id) WHERE is_active = TRUE;

-- pg_search: BM25 full-text search on materials (20x faster than tsvector)
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, material_code, barcode_data, sap_material_number}',
    numeric_fields => '{standard_cost}',
    boolean_fields => '{is_active}'
);
```

#### **material_inventory**
*Real-time stock levels per plant with computed available quantity*

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

-- RLS: Tenant isolation
ALTER TABLE material_inventory ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_inventory_tenant_isolation ON material_inventory
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_material_inventory_material ON material_inventory(material_id);
CREATE INDEX idx_material_inventory_plant ON material_inventory(plant_id);
CREATE INDEX idx_material_inventory_available ON material_inventory(material_id, plant_id)
    WHERE quantity_available > 0;
```

#### **material_transactions**
*Inventory movement history (FIFO/LIFO costing)*

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

-- RLS: Tenant isolation
ALTER TABLE material_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY material_transactions_tenant_isolation ON material_transactions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_material_transactions_material ON material_transactions(material_id);
CREATE INDEX idx_material_transactions_created ON material_transactions(created_at DESC);
CREATE INDEX idx_material_transactions_reference ON material_transactions(reference_type, reference_id);

-- timescaledb: Convert to hypertable for time-series optimization
SELECT create_hypertable('material_transactions', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy (75% storage reduction)
ALTER TABLE material_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, material_id, plant_id'
);
SELECT add_compression_policy('material_transactions', INTERVAL '7 days', if_not_exists => TRUE);

-- timescaledb: Retention policy (auto-delete old data)
SELECT add_retention_policy('material_transactions', INTERVAL '3 years', if_not_exists => TRUE);
```

#### **suppliers**
*Supplier master with rating*

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

-- RLS: Tenant isolation
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
CREATE POLICY suppliers_tenant_isolation ON suppliers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- pg_search: Full-text search on suppliers
SELECT paradedb.create_bm25(
    table_name => 'suppliers',
    index_name => 'suppliers_search_idx',
    key_field => 'id',
    text_fields => '{name, code, contact_person, email}',
    numeric_fields => '{rating}'
);
```

#### **rfqs**
*Request for Quotations*

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

-- RLS: Tenant isolation
ALTER TABLE rfqs ENABLE ROW LEVEL SECURITY;
CREATE POLICY rfqs_tenant_isolation ON rfqs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_rfqs_plant ON rfqs(plant_id);
CREATE INDEX idx_rfqs_status ON rfqs(status);
```

---

### 3. Project Management (5 tables)

#### **projects**
*Manufacturing projects with SAP integration*

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

-- RLS: Tenant isolation
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY projects_tenant_isolation ON projects
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_sap_so ON projects(sap_sales_order);
CREATE INDEX idx_projects_plant ON projects(primary_plant_id);
CREATE INDEX idx_projects_manager ON projects(project_manager_id);

-- pg_search: Full-text search on projects
SELECT paradedb.create_bm25(
    table_name => 'projects',
    index_name => 'projects_search_idx',
    key_field => 'id',
    text_fields => '{project_number, name, description, customer_name, customer_code, sap_sales_order}'
);
```

#### **project_bom**
*Bill of Materials for projects*

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

-- RLS: Tenant isolation
ALTER TABLE project_bom ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_bom_tenant_isolation ON project_bom
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_project_bom_project ON project_bom(project_id);
CREATE INDEX idx_project_bom_material ON project_bom(material_id);
```

#### **project_documents**
*Document management (stored in MinIO)*

```sql
CREATE TABLE project_documents (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    document_type VARCHAR(50) NOT NULL, -- 'drawing', 'specification', 'contract', 'other'
    document_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path (s3://unison-files/...)
    file_size BIGINT,
    mime_type VARCHAR(100),
    version INTEGER DEFAULT 1,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS: Tenant isolation
ALTER TABLE project_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_documents_tenant_isolation ON project_documents
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_project_documents_project ON project_documents(project_id);
CREATE INDEX idx_project_documents_type ON project_documents(document_type);

-- pg_search: Full-text search on document names
SELECT paradedb.create_bm25(
    table_name => 'project_documents',
    index_name => 'project_documents_search_idx',
    key_field => 'id',
    text_fields => '{document_name, document_type}'
);
```

#### **rda_drawings**
*Drawing approval workflow (RDA = Request for Design Approval)*

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

-- RLS: Tenant isolation
ALTER TABLE rda_drawings ENABLE ROW LEVEL SECURITY;
CREATE POLICY rda_drawings_tenant_isolation ON rda_drawings
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_rda_drawings_project ON rda_drawings(project_id);
CREATE INDEX idx_rda_drawings_status ON rda_drawings(status);
CREATE INDEX idx_rda_drawings_number ON rda_drawings(drawing_number);
```

#### **project_milestones**
*Project timeline tracking*

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

-- RLS: Tenant isolation
ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_milestones_tenant_isolation ON project_milestones
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_project_milestones_project ON project_milestones(project_id);
CREATE INDEX idx_project_milestones_date ON project_milestones(planned_date);
```

---

### 4. Production Management (10 tables)

#### **work_orders**
*Production orders with SAP integration*

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

-- RLS: Tenant isolation
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY work_orders_tenant_isolation ON work_orders
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_work_orders_plant ON work_orders(plant_id);
CREATE INDEX idx_work_orders_project ON work_orders(project_id);
CREATE INDEX idx_work_orders_sap ON work_orders(sap_production_order);

-- pg_search: Full-text search on work orders
SELECT paradedb.create_bm25(
    table_name => 'work_orders',
    index_name => 'work_orders_search_idx',
    key_field => 'id',
    text_fields => '{work_order_number, description, operation_type, sap_production_order}'
);

-- LISTEN/NOTIFY: Real-time work order status updates
CREATE OR REPLACE FUNCTION notify_work_order_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        PERFORM pg_notify('work_order_status_changed',
            json_build_object(
                'id', NEW.id,
                'work_order_number', NEW.work_order_number,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'plant_id', NEW.plant_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER work_order_status_notify
AFTER UPDATE ON work_orders
FOR EACH ROW EXECUTE FUNCTION notify_work_order_status_change();
```

#### **work_order_operations**
*Operations within work orders*

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

-- RLS: Tenant isolation
ALTER TABLE work_order_operations ENABLE ROW LEVEL SECURITY;
CREATE POLICY work_order_operations_tenant_isolation ON work_order_operations
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_work_order_operations_wo ON work_order_operations(work_order_id);
CREATE INDEX idx_work_order_operations_status ON work_order_operations(status);
```

#### **lanes**
*Production lines/stations (visual scheduling)*

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

-- RLS: Tenant isolation
ALTER TABLE lanes ENABLE ROW LEVEL SECURITY;
CREATE POLICY lanes_tenant_isolation ON lanes
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_lanes_plant ON lanes(plant_id);
CREATE INDEX idx_lanes_status ON lanes(status) WHERE is_active = TRUE;
```

#### **lane_assignments**
*Work order to lane assignment history*

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

-- RLS: Tenant isolation
ALTER TABLE lane_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY lane_assignments_tenant_isolation ON lane_assignments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_lane_assignments_lane ON lane_assignments(lane_id);
CREATE INDEX idx_lane_assignments_wo ON lane_assignments(work_order_id);
CREATE INDEX idx_lane_assignments_assigned ON lane_assignments(assigned_at DESC);
```

#### **production_logs**
*Real-time production logging (PWA mobile)*

```sql
CREATE TABLE production_logs (
    id BIGSERIAL PRIMARY KEY,
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

-- RLS: Tenant isolation
ALTER TABLE production_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY production_logs_tenant_isolation ON production_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_production_logs_work_order ON production_logs(work_order_id);
CREATE INDEX idx_production_logs_logged_at ON production_logs(logged_at DESC);

-- timescaledb: Convert to hypertable for time-series optimization
SELECT create_hypertable('production_logs', 'logged_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy (75% storage reduction)
ALTER TABLE production_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, work_order_id, logged_by'
);
SELECT add_compression_policy('production_logs', INTERVAL '7 days', if_not_exists => TRUE);

-- timescaledb: Retention policy (2 years for compliance)
SELECT add_retention_policy('production_logs', INTERVAL '2 years', if_not_exists => TRUE);

-- timescaledb: Continuous aggregate for daily production summary
CREATE MATERIALIZED VIEW daily_production_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', logged_at) AS day,
    organization_id,
    work_order_id,
    plant_id,
    COUNT(*) AS log_count,
    SUM(quantity_completed) AS total_quantity
FROM production_logs pl
JOIN work_orders wo ON pl.work_order_id = wo.id
GROUP BY day, organization_id, work_order_id, plant_id
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('daily_production_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- LISTEN/NOTIFY: Real-time production log notifications
CREATE OR REPLACE FUNCTION notify_production_log_created() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('production_log_created',
        json_build_object(
            'id', NEW.id,
            'work_order_id', NEW.work_order_id,
            'log_type', NEW.log_type,
            'quantity_completed', NEW.quantity_completed
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER production_log_notify
AFTER INSERT ON production_logs
FOR EACH ROW EXECUTE FUNCTION notify_production_log_created();
```

#### **manpower_allocation**
*Worker assignments to work orders*

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

-- RLS: Tenant isolation
ALTER TABLE manpower_allocation ENABLE ROW LEVEL SECURITY;
CREATE POLICY manpower_allocation_tenant_isolation ON manpower_allocation
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_manpower_allocation_wo ON manpower_allocation(work_order_id);
CREATE INDEX idx_manpower_allocation_user ON manpower_allocation(user_id);
```

#### **rbs_schedules**
*Resource-Based Scheduling (visual Gantt)*

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

-- RLS: Tenant isolation
ALTER TABLE rbs_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY rbs_schedules_tenant_isolation ON rbs_schedules
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_rbs_schedules_date ON rbs_schedules(schedule_date);
CREATE INDEX idx_rbs_schedules_plant ON rbs_schedules(plant_id);
CREATE INDEX idx_rbs_schedules_wo ON rbs_schedules(work_order_id);
```

#### **rps_sheets**
*Resource Planning Sheets*

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

-- RLS: Tenant isolation
ALTER TABLE rps_sheets ENABLE ROW LEVEL SECURITY;
CREATE POLICY rps_sheets_tenant_isolation ON rps_sheets
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_rps_sheets_project ON rps_sheets(project_id);
CREATE INDEX idx_rps_sheets_status ON rps_sheets(status);
```

#### **daily_work_logs**
*Daily shift work summary*

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

-- RLS: Tenant isolation
ALTER TABLE daily_work_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY daily_work_logs_tenant_isolation ON daily_work_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_daily_work_logs_date ON daily_work_logs(work_date DESC);
CREATE INDEX idx_daily_work_logs_plant ON daily_work_logs(plant_id);
```

#### **delivery_predictions**
*AI-based delivery date predictions*

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

-- RLS: Tenant isolation
ALTER TABLE delivery_predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY delivery_predictions_tenant_isolation ON delivery_predictions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_delivery_predictions_project ON delivery_predictions(project_id);
CREATE INDEX idx_delivery_predictions_date ON delivery_predictions(predicted_date);
```

---

### 5. Quality Management (4 tables)

#### **ncr_reports**
*Non-Conformance Reports with workflow*

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

-- RLS: Tenant isolation
ALTER TABLE ncr_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY ncr_reports_tenant_isolation ON ncr_reports
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_ncr_reports_status ON ncr_reports(status);
CREATE INDEX idx_ncr_reports_project ON ncr_reports(project_id);
CREATE INDEX idx_ncr_reports_severity ON ncr_reports(severity);

-- pg_search: Full-text search on NCR reports
SELECT paradedb.create_bm25(
    table_name => 'ncr_reports',
    index_name => 'ncr_reports_search_idx',
    key_field => 'id',
    text_fields => '{ncr_number, description, root_cause, corrective_action}'
);
```

#### **ncr_photos**
*Photo attachments for NCR reports (stored in MinIO)*

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

-- RLS: Tenant isolation
ALTER TABLE ncr_photos ENABLE ROW LEVEL SECURITY;
CREATE POLICY ncr_photos_tenant_isolation ON ncr_photos
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_ncr_photos_ncr ON ncr_photos(ncr_id);
```

#### **quality_inspections**
*Inspection records*

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

-- RLS: Tenant isolation
ALTER TABLE quality_inspections ENABLE ROW LEVEL SECURITY;
CREATE POLICY quality_inspections_tenant_isolation ON quality_inspections
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_quality_inspections_wo ON quality_inspections(work_order_id);
CREATE INDEX idx_quality_inspections_result ON quality_inspections(result);
CREATE INDEX idx_quality_inspections_date ON quality_inspections(inspection_date DESC);
```

#### **quality_checkpoints**
*Individual checkpoint results within inspections*

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

-- RLS: Tenant isolation
ALTER TABLE quality_checkpoints ENABLE ROW LEVEL SECURITY;
CREATE POLICY quality_checkpoints_tenant_isolation ON quality_checkpoints
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_quality_checkpoints_inspection ON quality_checkpoints(inspection_id);
```

---

### 6. Logistics & Tracking (4 tables)

#### **shipments**
*Shipment tracking*

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

-- RLS: Tenant isolation
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
CREATE POLICY shipments_tenant_isolation ON shipments
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_shipments_project ON shipments(project_id);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);

-- pg_search: Full-text search on shipments
SELECT paradedb.create_bm25(
    table_name => 'shipments',
    index_name => 'shipments_search_idx',
    key_field => 'id',
    text_fields => '{shipment_number, tracking_number, carrier}'
);
```

#### **shipment_items**
*Line items in shipments*

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

-- RLS: Tenant isolation
ALTER TABLE shipment_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY shipment_items_tenant_isolation ON shipment_items
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_shipment_items_shipment ON shipment_items(shipment_id);
CREATE INDEX idx_shipment_items_material ON shipment_items(material_id);
```

#### **qr_code_scans**
*QR/Barcode scan events for tracking*

```sql
CREATE TABLE qr_code_scans (
    id BIGSERIAL PRIMARY KEY,
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

-- RLS: Tenant isolation
ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY qr_code_scans_tenant_isolation ON qr_code_scans
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_qr_code_scans_data ON qr_code_scans(qr_code_data);
CREATE INDEX idx_qr_code_scans_scanned_at ON qr_code_scans(scanned_at DESC);
CREATE INDEX idx_qr_code_scans_reference ON qr_code_scans(reference_type, reference_id);

-- timescaledb: Convert to hypertable for time-series optimization
SELECT create_hypertable('qr_code_scans', 'scanned_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy
ALTER TABLE qr_code_scans SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, scan_type'
);
SELECT add_compression_policy('qr_code_scans', INTERVAL '30 days', if_not_exists => TRUE);
```

#### **barcode_labels**
*Generated barcode/QR labels (stored in MinIO)*

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

-- RLS: Tenant isolation
ALTER TABLE barcode_labels ENABLE ROW LEVEL SECURITY;
CREATE POLICY barcode_labels_tenant_isolation ON barcode_labels
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_barcode_labels_data ON barcode_labels(barcode_data);
CREATE INDEX idx_barcode_labels_reference ON barcode_labels(reference_type, reference_id);
```

---

### 7. SAP Integration (3 tables)

#### **sap_sync_logs**
*SAP integration audit trail*

```sql
CREATE TABLE sap_sync_logs (
    id BIGSERIAL PRIMARY KEY,
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

-- RLS: Tenant isolation
ALTER TABLE sap_sync_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sap_sync_logs_tenant_isolation ON sap_sync_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_sap_sync_logs_status ON sap_sync_logs(status);
CREATE INDEX idx_sap_sync_logs_synced_at ON sap_sync_logs(synced_at DESC);
CREATE INDEX idx_sap_sync_logs_entity ON sap_sync_logs(entity_type, entity_id);

-- timescaledb: Convert to hypertable
SELECT create_hypertable('sap_sync_logs', 'synced_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression and retention
ALTER TABLE sap_sync_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, sync_type, status'
);
SELECT add_compression_policy('sap_sync_logs', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('sap_sync_logs', INTERVAL '1 year', if_not_exists => TRUE);
```

#### **sap_mappings**
*Entity to SAP reference mappings*

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

-- RLS: Tenant isolation
ALTER TABLE sap_mappings ENABLE ROW LEVEL SECURITY;
CREATE POLICY sap_mappings_tenant_isolation ON sap_mappings
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_sap_mappings_entity ON sap_mappings(entity_type, entity_id);
CREATE INDEX idx_sap_mappings_sap_ref ON sap_mappings(sap_reference);
```

#### **pgmq_background_jobs**
*Background job queue (using PGMQ extension)*

**Note**: This table is automatically created by PGMQ extension, documented here for reference.

```sql
-- Queue creation (in init-extensions.sql)
SELECT pgmq.create('background_jobs');
SELECT pgmq.create('sap_sync_jobs');
SELECT pgmq.create('email_notifications');
SELECT pgmq.create('report_generation');
SELECT pgmq.create('barcode_generation');

-- Queue operations (Python/API code)
-- Enqueue: queue.send('background_jobs', {'job_type': 'sap_sync', 'entity_id': 123})
-- Dequeue: messages = queue.read('background_jobs', vt=60, qty=5)
-- Delete: queue.delete('background_jobs', msg_id)
-- Archive: queue.archive('background_jobs', msg_id)

-- Monitor queue depth
SELECT queue_name, queue_length, oldest_msg_age_sec, total_messages
FROM pgmq.metrics_all();
```

---

### 8. Reporting & Analytics (3 tables)

#### **reports**
*Report definitions*

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

-- RLS: Tenant isolation
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY reports_tenant_isolation ON reports
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### **report_executions**
*Report generation history (PDFs stored in MinIO)*

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

-- RLS: Tenant isolation
ALTER TABLE report_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY report_executions_tenant_isolation ON report_executions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_report_executions_report ON report_executions(report_id);
CREATE INDEX idx_report_executions_executed_at ON report_executions(executed_at DESC);
```

#### **dashboards**
*Dashboard configurations*

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

-- RLS: Tenant isolation
ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;
CREATE POLICY dashboards_tenant_isolation ON dashboards
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

---

### 9. Audit & System (4 tables)

#### **audit_logs**
*Comprehensive audit trail with trigger-based tracking*

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

-- RLS: Tenant isolation
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_performed_at ON audit_logs(performed_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(performed_by);

-- timescaledb: Convert to hypertable
SELECT create_hypertable('audit_logs', 'performed_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression and retention
ALTER TABLE audit_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, table_name'
);
SELECT add_compression_policy('audit_logs', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('audit_logs', INTERVAL '7 years', if_not_exists => TRUE);
```

#### **notifications**
*In-app notifications*

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

-- RLS: Tenant isolation
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY notifications_tenant_isolation ON notifications
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

#### **system_settings**
*Organization-level configuration*

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

-- Indexes
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
```

#### **file_uploads**
*File upload tracking (files stored in MinIO)*

```sql
CREATE TABLE file_uploads (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- MinIO path (s3://unison-files/...)
    file_size BIGINT,
    mime_type VARCHAR(100),
    bucket_name VARCHAR(100),
    entity_type VARCHAR(50), -- 'ncr_photo', 'project_document', 'report'
    entity_id INTEGER,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS: Tenant isolation
ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
CREATE POLICY file_uploads_tenant_isolation ON file_uploads
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_file_uploads_entity ON file_uploads(entity_type, entity_id);
CREATE INDEX idx_file_uploads_uploaded ON file_uploads(uploaded_at DESC);
```

---

### 10. PostgreSQL-Native Cache (UNLOGGED Table)

#### **cache**
*High-speed cache using UNLOGGED table (replaces Redis)*

```sql
CREATE UNLOGGED TABLE cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_cache_expires ON cache(expires_at);

-- pg_cron: Auto-cleanup expired cache entries every 5 minutes
SELECT cron.schedule(
    'cache-cleanup',
    '*/5 * * * *',
    $DELETE FROM cache WHERE expires_at < NOW()$
);

-- Usage example (Python):
-- # Set cache
-- db.execute(
--     "INSERT INTO cache (cache_key, cache_value, expires_at) VALUES (:key, :value, NOW() + INTERVAL '10 minutes')
--      ON CONFLICT (cache_key) DO UPDATE SET cache_value = EXCLUDED.cache_value, expires_at = EXCLUDED.expires_at",
--     {"key": "user:123:profile", "value": json.dumps(user_data)}
-- )
--
-- # Get cache
-- result = db.execute("SELECT cache_value FROM cache WHERE cache_key = :key AND expires_at > NOW()", {"key": "user:123:profile"})
```

**UNLOGGED Benefits**:
- **2x faster writes** than regular tables
- **1-2ms latency** (vs Redis <1ms - acceptable trade-off)
- **No network overhead** (same database connection)
- **Survives database restart** (data lost, but table structure remains)
- **Eliminates Redis dependency** (simplifies stack)

---

### 11. MES Modules (15 tables)

#### **machines**
*Equipment and machine registry*

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

-- RLS: Tenant isolation
ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
CREATE POLICY machines_tenant_isolation ON machines
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_machines_plant ON machines(plant_id);
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_next_maintenance ON machines(next_maintenance_due) WHERE is_active = TRUE;

-- pg_search: Full-text search on machines
SELECT paradedb.create_bm25(
    table_name => 'machines',
    index_name => 'machines_search_idx',
    key_field => 'id',
    text_fields => '{machine_code, name, description, machine_type, manufacturer, model_number, serial_number}'
);
```

#### **machine_status_history**
*Machine status change history for OEE calculation*

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

-- RLS: Tenant isolation
ALTER TABLE machine_status_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY machine_status_history_tenant_isolation ON machine_status_history
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_machine_status_history_machine ON machine_status_history(machine_id, changed_at DESC);
CREATE INDEX idx_machine_status_history_status ON machine_status_history(new_status);

-- timescaledb: Convert to hypertable for OEE time-series analysis
SELECT create_hypertable('machine_status_history', 'changed_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy
ALTER TABLE machine_status_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, machine_id, new_status'
);
SELECT add_compression_policy('machine_status_history', INTERVAL '30 days', if_not_exists => TRUE);

-- timescaledb: Continuous aggregate for daily OEE
CREATE MATERIALIZED VIEW daily_machine_oee
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', changed_at) AS day,
    organization_id,
    machine_id,
    -- Availability: (Total Time - Downtime) / Total Time
    SUM(CASE WHEN new_status = 'running' THEN duration_minutes ELSE 0 END) AS running_minutes,
    SUM(CASE WHEN new_status = 'down' THEN duration_minutes ELSE 0 END) AS down_minutes,
    -- Calculate OEE
    (SUM(CASE WHEN new_status = 'running' THEN duration_minutes ELSE 0 END)::DECIMAL /
     NULLIF(SUM(duration_minutes), 0)) * 100 AS availability_percent
FROM machine_status_history
GROUP BY day, organization_id, machine_id
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('daily_machine_oee',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

#### **shifts**
*Shift pattern definitions*

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

-- RLS: Tenant isolation
ALTER TABLE shifts ENABLE ROW LEVEL SECURITY;
CREATE POLICY shifts_tenant_isolation ON shifts
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_shifts_plant ON shifts(plant_id);
```

#### **shift_handovers**
*Shift handover notes*

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

-- RLS: Tenant isolation
ALTER TABLE shift_handovers ENABLE ROW LEVEL SECURITY;
CREATE POLICY shift_handovers_tenant_isolation ON shift_handovers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_shift_handovers_shift_date ON shift_handovers(shift_id, date DESC);
```

#### **shift_performance**
*Shift performance metrics*

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

-- RLS: Tenant isolation
ALTER TABLE shift_performance ENABLE ROW LEVEL SECURITY;
CREATE POLICY shift_performance_tenant_isolation ON shift_performance
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_shift_performance_shift_date ON shift_performance(shift_id, date DESC);
```

#### **pm_schedules**
*Preventive Maintenance schedules*

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

-- RLS: Tenant isolation
ALTER TABLE pm_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY pm_schedules_tenant_isolation ON pm_schedules
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_pm_schedules_machine ON pm_schedules(machine_id);
CREATE INDEX idx_pm_schedules_next_due ON pm_schedules(next_due_date) WHERE is_active = TRUE;

-- pg_cron: Auto-generate PM work orders daily at 6 AM
SELECT cron.schedule(
    'pm-work-order-generation',
    '0 6 * * *',
    $
    INSERT INTO pm_work_orders (organization_id, work_order_number, pm_schedule_id, machine_id, pm_type, scheduled_date)
    SELECT
        ps.organization_id,
        'PM-' || TO_CHAR(NOW(), 'YYYY-MM-DD') || '-' || LPAD(ps.id::TEXT, 4, '0'),
        ps.id,
        ps.machine_id,
        ps.pm_type,
        ps.next_due_date
    FROM pm_schedules ps
    WHERE ps.is_active = TRUE
    AND ps.next_due_date <= CURRENT_DATE + ps.lead_time_days
    AND NOT EXISTS (
        SELECT 1 FROM pm_work_orders pwo
        WHERE pwo.pm_schedule_id = ps.id
        AND pwo.status IN ('planned', 'in_progress')
    );
    $
);
```

#### **pm_work_orders**
*Preventive Maintenance work orders*

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

-- RLS: Tenant isolation
ALTER TABLE pm_work_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY pm_work_orders_tenant_isolation ON pm_work_orders
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_pm_work_orders_machine ON pm_work_orders(machine_id);
CREATE INDEX idx_pm_work_orders_status ON pm_work_orders(status);
CREATE INDEX idx_pm_work_orders_scheduled ON pm_work_orders(scheduled_date);
CREATE INDEX idx_pm_work_orders_overdue ON pm_work_orders(is_overdue) WHERE is_overdue = TRUE;
```

#### **downtime_events**
*Machine downtime tracking for MTBF/MTTR*

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

-- RLS: Tenant isolation
ALTER TABLE downtime_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY downtime_events_tenant_isolation ON downtime_events
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_downtime_events_machine ON downtime_events(machine_id, started_at DESC);
CREATE INDEX idx_downtime_events_reason ON downtime_events(downtime_reason_code);
CREATE INDEX idx_downtime_events_category ON downtime_events(downtime_category);

-- timescaledb: Convert to hypertable for Pareto analysis
SELECT create_hypertable('downtime_events', 'started_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy
ALTER TABLE downtime_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, machine_id, downtime_category'
);
SELECT add_compression_policy('downtime_events', INTERVAL '30 days', if_not_exists => TRUE);

-- pg_duckdb: Pareto analysis for downtime reasons (executed via API)
-- SELECT downtime_reason_code, SUM(duration_minutes) AS total_downtime
-- FROM downtime_events
-- WHERE machine_id = ? AND started_at >= NOW() - INTERVAL '30 days'
-- GROUP BY downtime_reason_code
-- ORDER BY total_downtime DESC;
```

#### **inspection_plans**
*Inspection plan definitions for products*

```sql
CREATE TABLE inspection_plans (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    product_id INTEGER REFERENCES materials(id), -- Which product this applies to
    plan_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, product_id, plan_name)
);

-- RLS: Tenant isolation
ALTER TABLE inspection_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_plans_tenant_isolation ON inspection_plans
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_inspection_plans_product ON inspection_plans(product_id);
```

#### **inspection_points**
*Inspection checkpoints within plans*

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

-- RLS: Tenant isolation
ALTER TABLE inspection_points ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_points_tenant_isolation ON inspection_points
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_inspection_points_plan ON inspection_points(inspection_plan_id);
```

#### **inspection_characteristics**
*Measurable characteristics at inspection points*

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

-- RLS: Tenant isolation
ALTER TABLE inspection_characteristics ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_characteristics_tenant_isolation ON inspection_characteristics
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_inspection_characteristics_point ON inspection_characteristics(inspection_point_id);
```

#### **inspection_logs**
*Inspection execution records*

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

-- RLS: Tenant isolation
ALTER TABLE inspection_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_logs_tenant_isolation ON inspection_logs
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_inspection_logs_work_order ON inspection_logs(work_order_id);
CREATE INDEX idx_inspection_logs_result ON inspection_logs(overall_result);
CREATE INDEX idx_inspection_logs_inspected_at ON inspection_logs(inspected_at DESC);

-- timescaledb: Convert to hypertable for SPC analysis
SELECT create_hypertable('inspection_logs', 'inspected_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy
ALTER TABLE inspection_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, work_order_id, overall_result'
);
SELECT add_compression_policy('inspection_logs', INTERVAL '90 days', if_not_exists => TRUE);
```

#### **inspection_measurements**
*Individual measurement values for SPC (Cp/Cpk calculation)*

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

-- RLS: Tenant isolation
ALTER TABLE inspection_measurements ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspection_measurements_tenant_isolation ON inspection_measurements
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_inspection_measurements_log ON inspection_measurements(inspection_log_id);
CREATE INDEX idx_inspection_measurements_characteristic ON inspection_measurements(characteristic_id, measured_at DESC);

-- timescaledb: Convert to hypertable for Cp/Cpk analysis
SELECT create_hypertable('inspection_measurements', 'measured_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- timescaledb: Compression policy
ALTER TABLE inspection_measurements SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, characteristic_id'
);
SELECT add_compression_policy('inspection_measurements', INTERVAL '90 days', if_not_exists => TRUE);

-- timescaledb: Continuous aggregate for Cp/Cpk calculation
CREATE MATERIALIZED VIEW daily_spc_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', measured_at) AS day,
    organization_id,
    characteristic_id,
    AVG(measured_value) AS mean_value,
    STDDEV(measured_value) AS std_dev,
    COUNT(*) AS sample_count,
    MIN(measured_value) AS min_value,
    MAX(measured_value) AS max_value
FROM inspection_measurements
WHERE measured_value IS NOT NULL
GROUP BY day, organization_id, characteristic_id
WITH NO DATA;

-- Refresh policy for SPC aggregate
SELECT add_continuous_aggregate_policy('daily_spc_metrics',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

#### **lot_numbers**
*Lot-based traceability (raw materials, components)*

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

-- RLS: Tenant isolation
ALTER TABLE lot_numbers ENABLE ROW LEVEL SECURITY;
CREATE POLICY lot_numbers_tenant_isolation ON lot_numbers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_lot_numbers_material ON lot_numbers(material_id);
CREATE INDEX idx_lot_numbers_expiry ON lot_numbers(expiry_date) WHERE is_active = TRUE;
CREATE INDEX idx_lot_numbers_remaining ON lot_numbers(material_id, remaining_quantity) WHERE remaining_quantity > 0;

-- pg_search: Full-text search on lot numbers
SELECT paradedb.create_bm25(
    table_name => 'lot_numbers',
    index_name => 'lot_numbers_search_idx',
    key_field => 'id',
    text_fields => '{lot_number, supplier_lot_number}'
);
```

#### **serial_numbers**
*Serial number traceability (finished products)*

```sql
CREATE TABLE serial_numbers (
    id BIGSERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    serial_number VARCHAR(100) UNIQUE NOT NULL, -- 'PUMP-2511-00001'
    product_id INTEGER REFERENCES materials(id),
    work_order_id INTEGER NOT NULL REFERENCES work_orders(id),
    production_date DATE NOT NULL,
    shipment_id INTEGER REFERENCES shipments(id), -- If shipped
    shipped_date DATE,
    customer_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'in_stock', -- 'in_stock', 'shipped', 'returned', 'scrapped'
    location VARCHAR(255), -- Current physical location
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- RLS: Tenant isolation
ALTER TABLE serial_numbers ENABLE ROW LEVEL SECURITY;
CREATE POLICY serial_numbers_tenant_isolation ON serial_numbers
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_serial_numbers_product ON serial_numbers(product_id);
CREATE INDEX idx_serial_numbers_work_order ON serial_numbers(work_order_id);
CREATE INDEX idx_serial_numbers_status ON serial_numbers(status);
CREATE INDEX idx_serial_numbers_shipment ON serial_numbers(shipment_id) WHERE shipment_id IS NOT NULL;

-- pg_search: Full-text search on serial numbers
SELECT paradedb.create_bm25(
    table_name => 'serial_numbers',
    index_name => 'serial_numbers_search_idx',
    key_field => 'id',
    text_fields => '{serial_number, customer_name}'
);
```

#### **genealogy_records**
*Forward/backward genealogy for lot and serial number traceability*

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

-- RLS: Tenant isolation
ALTER TABLE genealogy_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY genealogy_records_tenant_isolation ON genealogy_records
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Indexes
CREATE INDEX idx_genealogy_records_parent ON genealogy_records(parent_type, parent_id);
CREATE INDEX idx_genealogy_records_child ON genealogy_records(child_type, child_id);
CREATE INDEX idx_genealogy_records_recorded ON genealogy_records(recorded_at DESC);

-- Composite index for forward genealogy (given parent, find children)
CREATE INDEX idx_genealogy_forward ON genealogy_records(parent_type, parent_id, child_type);

-- Composite index for backward genealogy (given child, find parents)
CREATE INDEX idx_genealogy_backward ON genealogy_records(child_type, child_id, parent_type);
```

---

## Multi-Tenancy & RLS

### RLS Context Setting (JWT Middleware)

```python
# app/infrastructure/security/rls_context.py
from sqlalchemy import text

def set_rls_context(db: Session, organization_id: int, user_id: int, plant_id: int = None):
    """Set RLS context variables from JWT claims"""
    db.execute(text(f"SET app.current_organization_id = {organization_id}"))
    db.execute(text(f"SET app.current_user_id = {user_id}"))
    if plant_id:
        db.execute(text(f"SET app.current_plant_id = {plant_id}"))
```

### RLS Policy Template

```sql
-- Template for all multi-tenant tables
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
CREATE POLICY {table_name}_tenant_isolation ON {table_name}
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

---

## Indexes & Performance

### Index Strategy

1. **Primary Keys**: Automatic B-tree indexes on all `id` columns
2. **Foreign Keys**: Indexes on all FK columns for join performance
3. **RLS Columns**: `organization_id` indexed on all multi-tenant tables
4. **Search Columns**: pg_search BM25 indexes on text-heavy tables
5. **Time-Series**: timescaledb hypertables on time-stamped tables
6. **Composite Indexes**: For common query patterns (e.g., `(plant_id, status)`)

### Performance Monitoring

```sql
-- pg_stat_statements: Track query performance
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%_pkey';
```

---

## Data Partitioning

### timescaledb Hypertables (Time-Series Data)

**Partitioned Tables** (automatic chunk management):
- `production_logs` (1-month chunks, 75% compression, 2-year retention)
- `material_transactions` (1-month chunks, 75% compression, 3-year retention)
- `qr_code_scans` (1-month chunks, 75% compression, 1-year retention)
- `sap_sync_logs` (1-month chunks, 75% compression, 1-year retention)
- `audit_logs` (1-month chunks, 75% compression, 7-year retention)
- `machine_status_history` (1-month chunks, 75% compression, 2-year retention)
- `downtime_events` (1-month chunks, 75% compression, 2-year retention)

### Continuous Aggregates (Pre-computed Views)

```sql
-- daily_production_summary (hourly refresh)
-- daily_machine_oee (hourly refresh)
-- monthly_inventory_turnover (daily refresh)
-- weekly_quality_metrics (hourly refresh)
```

---

## Schema Version & Migrations

**Current Version**: 2.0 (PostgreSQL-Native Architecture)
**Migration Tool**: Alembic 1.12.1
**Migration Path**: v1.0 (Redis/Celery) → v2.0 (PostgreSQL-Native)

See: `docs/03-postgresql/MIGRATION_GUIDE.md` for detailed migration steps.

---

## Cross-References

- **Technology Stack**: `docs/02-architecture/TECH_STACK.md`
- **PostgreSQL Extensions**: `docs/03-postgresql/EXTENSIONS.md`
- **Migration Guide**: `docs/03-postgresql/MIGRATION_GUIDE.md`
- **Initialization Script**: `docs/03-postgresql/init-extensions.sql`
- **API Design**: `docs/02-architecture/API_DESIGN.md` (to be created)
- **Domain Models**: `docs/04-domains/*.md` (to be created)
