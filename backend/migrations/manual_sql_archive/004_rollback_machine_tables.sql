-- Rollback Migration: Drop Machine and MachineStatusHistory tables
-- Version: 004
-- Description: Rollback Equipment & Machines module

-- Drop hypertable if TimescaleDB was used (must drop before dropping table)
-- Uncomment if TimescaleDB hypertable was created:
-- SELECT drop_chunks('machine_status_history', older_than => INTERVAL '0 days');

-- Drop tables (cascade will drop foreign key constraints)
DROP TABLE IF EXISTS machine_status_history CASCADE;
DROP TABLE IF EXISTS machine CASCADE;

-- Drop enum type
DROP TYPE IF EXISTS machine_status CASCADE;

-- Revoke permissions
REVOKE SELECT, INSERT, UPDATE, DELETE ON machine FROM authenticated_user;
REVOKE SELECT, INSERT, UPDATE, DELETE ON machine_status_history FROM authenticated_user;
REVOKE USAGE, SELECT ON SEQUENCE machine_id_seq FROM authenticated_user;
REVOKE USAGE, SELECT ON SEQUENCE machine_status_history_id_seq FROM authenticated_user;
