-- Migration: Create Machine and MachineStatusHistory tables
-- Version: 004
-- Description: Equipment & Machines module with OEE tracking support
-- Dependencies: Requires PostgreSQL with TimescaleDB extension

-- Create machine status enum type
CREATE TYPE machine_status AS ENUM (
    'AVAILABLE',
    'RUNNING',
    'IDLE',
    'DOWN',
    'SETUP',
    'MAINTENANCE'
);

-- Create machine table
CREATE TABLE machine (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    machine_code VARCHAR(20) UNIQUE NOT NULL,
    machine_name VARCHAR(200) NOT NULL,
    description TEXT,
    work_center_id INTEGER NOT NULL,
    status machine_status NOT NULL DEFAULT 'AVAILABLE',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Create indexes for machine table
CREATE INDEX idx_machine_org_plant ON machine(organization_id, plant_id);
CREATE INDEX idx_machine_work_center ON machine(work_center_id);
CREATE INDEX idx_machine_status ON machine(status);
CREATE INDEX idx_machine_code ON machine(machine_code);

-- Create machine_status_history table for time-series tracking
CREATE TABLE machine_status_history (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER NOT NULL REFERENCES machine(id) ON DELETE CASCADE,
    status machine_status NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for machine_status_history
CREATE INDEX idx_machine_status_history_machine_time ON machine_status_history(machine_id, started_at);
CREATE INDEX idx_machine_status_history_time_range ON machine_status_history(started_at, ended_at);

-- Convert machine_status_history to TimescaleDB hypertable for efficient time-series queries
-- This requires TimescaleDB extension to be enabled
-- Uncomment the following line if TimescaleDB is available:
-- SELECT create_hypertable('machine_status_history', 'started_at', if_not_exists => TRUE);

-- Enable Row-Level Security (RLS) on machine table
ALTER TABLE machine ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for machine table (organization-level isolation)
CREATE POLICY machine_rls_policy ON machine
    USING (organization_id = current_setting('app.current_organization_id', true)::INTEGER);

-- Grant permissions (adjust as needed for your role structure)
GRANT SELECT, INSERT, UPDATE, DELETE ON machine TO authenticated_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON machine_status_history TO authenticated_user;
GRANT USAGE, SELECT ON SEQUENCE machine_id_seq TO authenticated_user;
GRANT USAGE, SELECT ON SEQUENCE machine_status_history_id_seq TO authenticated_user;

-- Add comments for documentation
COMMENT ON TABLE machine IS 'Production equipment and machinery tracking';
COMMENT ON TABLE machine_status_history IS 'Time-series tracking of machine status changes for OEE calculation';
COMMENT ON COLUMN machine.status IS 'Current machine status: AVAILABLE, RUNNING, IDLE, DOWN, SETUP, MAINTENANCE';
COMMENT ON COLUMN machine_status_history.started_at IS 'When the status period started';
COMMENT ON COLUMN machine_status_history.ended_at IS 'When the status period ended (NULL if ongoing)';

-- Sample data for testing (optional)
-- INSERT INTO machine (organization_id, plant_id, machine_code, machine_name, description, work_center_id, status)
-- VALUES
--     (1, 1, 'M001', 'CNC Machine 1', 'CNC Milling Machine', 1, 'AVAILABLE'),
--     (1, 1, 'M002', 'Lathe Machine 1', 'Precision Lathe', 1, 'RUNNING'),
--     (1, 1, 'M003', 'Press Machine 1', 'Hydraulic Press', 2, 'MAINTENANCE');
