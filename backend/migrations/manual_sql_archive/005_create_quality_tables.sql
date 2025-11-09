-- Migration: Create Quality Management tables (NCR, Inspection Plan, Inspection Log)
-- Version: 005
-- Description: Creates tables for NCR workflow, inspection plans, and FPY tracking
-- Dependencies: work_order, material tables

-- ============================================================================
-- NCR (Non-Conformance Report) Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS ncr (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    ncr_number VARCHAR(50) NOT NULL,
    work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
    material_id INTEGER NOT NULL REFERENCES material(id) ON DELETE CASCADE,
    defect_type VARCHAR(20) NOT NULL CHECK (defect_type IN ('DIMENSIONAL', 'VISUAL', 'FUNCTIONAL', 'MATERIAL', 'OTHER')),
    defect_description VARCHAR(500) NOT NULL,
    quantity_defective FLOAT NOT NULL CHECK (quantity_defective > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_REVIEW', 'RESOLVED', 'CLOSED')),
    reported_by_user_id INTEGER NOT NULL,
    attachment_urls JSONB DEFAULT NULL,
    resolution_notes VARCHAR(1000) DEFAULT NULL,
    resolved_by_user_id INTEGER DEFAULT NULL,
    resolved_at TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Indexes for NCR
CREATE INDEX idx_ncr_org_plant ON ncr(organization_id, plant_id);
CREATE INDEX idx_ncr_work_order ON ncr(work_order_id);
CREATE INDEX idx_ncr_material ON ncr(material_id);
CREATE INDEX idx_ncr_status ON ncr(status);
CREATE INDEX idx_ncr_number ON ncr(ncr_number);

-- Row-Level Security for NCR
ALTER TABLE ncr ENABLE ROW LEVEL SECURITY;

CREATE POLICY ncr_isolation_policy ON ncr
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ============================================================================
-- Inspection Plan Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS inspection_plan (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    material_id INTEGER NOT NULL REFERENCES material(id) ON DELETE CASCADE,
    inspection_frequency VARCHAR(20) NOT NULL CHECK (inspection_frequency IN ('PER_LOT', 'PER_SHIFT', 'HOURLY', 'CONTINUOUS')),
    sample_size INTEGER NOT NULL CHECK (sample_size > 0),
    characteristics JSONB DEFAULT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Indexes for Inspection Plan
CREATE INDEX idx_inspection_plan_org_plant ON inspection_plan(organization_id, plant_id);
CREATE INDEX idx_inspection_plan_material ON inspection_plan(material_id);

-- Row-Level Security for Inspection Plan
ALTER TABLE inspection_plan ENABLE ROW LEVEL SECURITY;

CREATE POLICY inspection_plan_isolation_policy ON inspection_plan
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ============================================================================
-- Inspection Log Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS inspection_log (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    inspection_plan_id INTEGER NOT NULL REFERENCES inspection_plan(id) ON DELETE CASCADE,
    work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
    inspected_quantity INTEGER NOT NULL CHECK (inspected_quantity > 0),
    passed_quantity INTEGER NOT NULL CHECK (passed_quantity >= 0),
    failed_quantity INTEGER NOT NULL CHECK (failed_quantity >= 0),
    inspector_user_id INTEGER NOT NULL,
    inspection_notes VARCHAR(500) DEFAULT NULL,
    measurement_data JSONB DEFAULT NULL,
    inspected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL,
    CONSTRAINT check_inspection_quantities_sum CHECK (passed_quantity + failed_quantity = inspected_quantity)
);

-- Indexes for Inspection Log
CREATE INDEX idx_inspection_log_org_plant ON inspection_log(organization_id, plant_id);
CREATE INDEX idx_inspection_log_plan ON inspection_log(inspection_plan_id);
CREATE INDEX idx_inspection_log_work_order ON inspection_log(work_order_id);
CREATE INDEX idx_inspection_log_inspected_at ON inspection_log(inspected_at);

-- Row-Level Security for Inspection Log
ALTER TABLE inspection_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY inspection_log_isolation_policy ON inspection_log
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================
COMMENT ON TABLE ncr IS 'Non-Conformance Reports for quality defects tracking';
COMMENT ON COLUMN ncr.defect_type IS 'Type of defect: DIMENSIONAL, VISUAL, FUNCTIONAL, MATERIAL, OTHER';
COMMENT ON COLUMN ncr.status IS 'NCR workflow status: OPEN -> IN_REVIEW -> RESOLVED -> CLOSED';
COMMENT ON COLUMN ncr.attachment_urls IS 'JSON array of MinIO URLs for defect photos';

COMMENT ON TABLE inspection_plan IS 'Inspection plans defining quality criteria for materials';
COMMENT ON COLUMN inspection_plan.inspection_frequency IS 'How often to inspect: PER_LOT, PER_SHIFT, HOURLY, CONTINUOUS';
COMMENT ON COLUMN inspection_plan.characteristics IS 'JSON array of inspection characteristics with tolerances';

COMMENT ON TABLE inspection_log IS 'Inspection results for calculating First Pass Yield (FPY)';
COMMENT ON COLUMN inspection_log.measurement_data IS 'JSON array of actual measurements for SPC charts';

-- ============================================================================
-- Migration Success
-- ============================================================================
SELECT 'Quality Management tables created successfully' AS status;
