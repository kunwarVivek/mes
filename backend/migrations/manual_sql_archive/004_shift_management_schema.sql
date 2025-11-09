-- Migration: Shift Management Schema
-- Description: Create tables for shift patterns, handovers, and performance tracking
-- Dependencies: None (base tables)
-- Version: 004
-- Date: 2025-01-08

-- ==========================================
-- Shift Table - Shift Patterns
-- ==========================================
CREATE TABLE IF NOT EXISTS shift (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    shift_name VARCHAR(100) NOT NULL,
    shift_code VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    production_target FLOAT NOT NULL DEFAULT 0.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT check_production_target_non_negative CHECK (production_target >= 0),
    CONSTRAINT uq_shift_code_per_plant UNIQUE (organization_id, plant_id, shift_code)
);

-- Indexes for shift
CREATE INDEX IF NOT EXISTS idx_shift_org_plant ON shift(organization_id, plant_id);
CREATE INDEX IF NOT EXISTS idx_shift_code ON shift(shift_code);
CREATE INDEX IF NOT EXISTS idx_shift_active ON shift(is_active);

-- RLS Policy for shift (Enable RLS if not already enabled)
ALTER TABLE shift ENABLE ROW LEVEL SECURITY;

CREATE POLICY shift_tenant_isolation ON shift
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ==========================================
-- Shift Handover Table
-- ==========================================
CREATE TABLE IF NOT EXISTS shift_handover (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    from_shift_id INTEGER NOT NULL REFERENCES shift(id) ON DELETE CASCADE,
    to_shift_id INTEGER NOT NULL REFERENCES shift(id) ON DELETE CASCADE,
    handover_date TIMESTAMP WITH TIME ZONE NOT NULL,
    wip_quantity FLOAT NOT NULL DEFAULT 0.0,
    production_summary TEXT NOT NULL,
    quality_issues TEXT,
    machine_status TEXT,
    material_status TEXT,
    safety_incidents TEXT,
    handover_by_user_id INTEGER NOT NULL,
    acknowledged_by_user_id INTEGER,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT check_wip_quantity_non_negative CHECK (wip_quantity >= 0),
    CONSTRAINT check_different_shifts CHECK (from_shift_id != to_shift_id)
);

-- Indexes for shift_handover
CREATE INDEX IF NOT EXISTS idx_shift_handover_org_plant ON shift_handover(organization_id, plant_id);
CREATE INDEX IF NOT EXISTS idx_shift_handover_date ON shift_handover(handover_date);
CREATE INDEX IF NOT EXISTS idx_shift_handover_from_shift ON shift_handover(from_shift_id);
CREATE INDEX IF NOT EXISTS idx_shift_handover_to_shift ON shift_handover(to_shift_id);

-- RLS Policy for shift_handover
ALTER TABLE shift_handover ENABLE ROW LEVEL SECURITY;

CREATE POLICY shift_handover_tenant_isolation ON shift_handover
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ==========================================
-- Shift Performance Table
-- ==========================================
CREATE TABLE IF NOT EXISTS shift_performance (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL REFERENCES shift(id) ON DELETE CASCADE,
    performance_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Production metrics
    production_target FLOAT NOT NULL,
    production_actual FLOAT NOT NULL DEFAULT 0.0,
    target_attainment_percent FLOAT NOT NULL DEFAULT 0.0,

    -- OEE metrics (Overall Equipment Effectiveness)
    availability_percent FLOAT,
    performance_percent FLOAT,
    quality_percent FLOAT,
    oee_percent FLOAT,

    -- Quality metrics
    total_produced FLOAT NOT NULL DEFAULT 0.0,
    total_good FLOAT NOT NULL DEFAULT 0.0,
    total_rejected FLOAT NOT NULL DEFAULT 0.0,
    fpy_percent FLOAT,  -- First Pass Yield

    -- Time metrics (minutes)
    planned_production_time FLOAT,
    actual_run_time FLOAT,
    downtime_minutes FLOAT,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_shift_performance_per_date UNIQUE (organization_id, plant_id, shift_id, performance_date),
    CONSTRAINT check_perf_target_non_negative CHECK (production_target >= 0),
    CONSTRAINT check_perf_actual_non_negative CHECK (production_actual >= 0),
    CONSTRAINT check_target_attainment_non_negative CHECK (target_attainment_percent >= 0),
    CONSTRAINT check_total_produced_non_negative CHECK (total_produced >= 0),
    CONSTRAINT check_total_good_non_negative CHECK (total_good >= 0),
    CONSTRAINT check_total_rejected_non_negative CHECK (total_rejected >= 0)
);

-- Indexes for shift_performance
CREATE INDEX IF NOT EXISTS idx_shift_performance_org_plant ON shift_performance(organization_id, plant_id);
CREATE INDEX IF NOT EXISTS idx_shift_performance_date ON shift_performance(performance_date);
CREATE INDEX IF NOT EXISTS idx_shift_performance_shift ON shift_performance(shift_id);

-- RLS Policy for shift_performance
ALTER TABLE shift_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY shift_performance_tenant_isolation ON shift_performance
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- ==========================================
-- Comments for Documentation
-- ==========================================
COMMENT ON TABLE shift IS 'Shift patterns with start/end times and production targets';
COMMENT ON TABLE shift_handover IS 'Shift handover logs with WIP status and production summary';
COMMENT ON TABLE shift_performance IS 'Shift performance metrics including target attainment, OEE, and FPY';

COMMENT ON COLUMN shift.shift_code IS 'Unique shift code per organization and plant';
COMMENT ON COLUMN shift.production_target IS 'Target production quantity for the shift';
COMMENT ON COLUMN shift_handover.wip_quantity IS 'Work-in-progress quantity at handover time';
COMMENT ON COLUMN shift_performance.oee_percent IS 'Overall Equipment Effectiveness (Availability × Performance × Quality)';
COMMENT ON COLUMN shift_performance.fpy_percent IS 'First Pass Yield - percentage of units passing without rework';
