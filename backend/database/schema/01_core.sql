-- Core Schema: Organizations, Users, Plants, Departments
-- Foundation tables for multi-tenant MES system

-- ============================================================================
-- ORGANIZATIONS TABLE
-- Top-level multi-tenant boundary with RLS isolation
-- ============================================================================
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    org_code VARCHAR(20) NOT NULL UNIQUE,
    org_name VARCHAR(200) NOT NULL,
    subdomain VARCHAR(100) UNIQUE,  -- For white-label access
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_org_code ON organizations(org_code);
CREATE INDEX idx_org_active ON organizations(is_active);

-- Comments
COMMENT ON TABLE organizations IS 'Top-level multi-tenant organization boundary';
COMMENT ON COLUMN organizations.org_code IS 'Unique organization code';
COMMENT ON COLUMN organizations.subdomain IS 'Custom subdomain for white-label access';


-- ============================================================================
-- USERS TABLE
-- System users with multi-tenant isolation
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    plant_id INTEGER,  -- FK added after plants table
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_plant ON users(plant_id);
CREATE INDEX idx_users_active ON users(is_active);

-- Comments
COMMENT ON TABLE users IS 'System users with role-based access control';
COMMENT ON COLUMN users.organization_id IS 'Primary organization affiliation';
COMMENT ON COLUMN users.plant_id IS 'Optional plant affiliation';


-- ============================================================================
-- PLANTS TABLE
-- Manufacturing sites within an organization
-- ============================================================================
CREATE TABLE plants (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plant_code VARCHAR(20) NOT NULL,
    plant_name VARCHAR(200) NOT NULL,
    location VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_plant_code_per_org UNIQUE (organization_id, plant_code)
);

-- Indexes
CREATE INDEX idx_plant_org ON plants(organization_id);
CREATE INDEX idx_plant_active ON plants(is_active);
CREATE INDEX idx_plant_org_code ON plants(organization_id, plant_code);

-- Comments
COMMENT ON TABLE plants IS 'Manufacturing sites within organization';
COMMENT ON COLUMN plants.plant_code IS 'Unique plant code within organization';


-- ============================================================================
-- DEPARTMENTS TABLE
-- Functional units within plants
-- ============================================================================
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    dept_code VARCHAR(20) NOT NULL,
    dept_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_dept_code_per_plant UNIQUE (plant_id, dept_code)
);

-- Indexes
CREATE INDEX idx_dept_plant ON departments(plant_id);
CREATE INDEX idx_dept_active ON departments(is_active);

-- Comments
COMMENT ON TABLE departments IS 'Functional units within plants (Production, Quality, Maintenance, etc.)';
COMMENT ON COLUMN departments.dept_code IS 'Unique department code within plant';


-- ============================================================================
-- Add foreign key constraint for users.plant_id
-- (Deferred until after plants table is created)
-- ============================================================================
ALTER TABLE users
ADD CONSTRAINT fk_users_plant
FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL;


-- ============================================================================
-- PROJECTS TABLE
-- Project management foundation
-- ============================================================================
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plant_id INTEGER NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    project_number VARCHAR(50) NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    project_description TEXT,
    customer_name VARCHAR(200),
    customer_po VARCHAR(100),
    project_manager VARCHAR(200),
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    project_status VARCHAR(50) NOT NULL DEFAULT 'PLANNING',
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT uq_project_number_per_org UNIQUE (organization_id, project_number),
    CONSTRAINT chk_project_status CHECK (project_status IN ('PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT chk_project_priority CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT'))
);

-- Indexes
CREATE INDEX idx_projects_org ON projects(organization_id);
CREATE INDEX idx_projects_plant ON projects(plant_id);
CREATE INDEX idx_projects_status ON projects(project_status);
CREATE INDEX idx_projects_number ON projects(project_number);

-- Comments
COMMENT ON TABLE projects IS 'Projects for job shop / make-to-order manufacturing';
COMMENT ON COLUMN projects.project_status IS 'Project lifecycle status';
