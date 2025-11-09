-- Rollback Migration: Drop Quality Management tables
-- Version: 005
-- Description: Rollback for quality management tables

-- Drop tables in reverse order (due to foreign key dependencies)
DROP TABLE IF EXISTS inspection_log CASCADE;
DROP TABLE IF EXISTS inspection_plan CASCADE;
DROP TABLE IF EXISTS ncr CASCADE;

-- Confirmation
SELECT 'Quality Management tables rolled back successfully' AS status;
