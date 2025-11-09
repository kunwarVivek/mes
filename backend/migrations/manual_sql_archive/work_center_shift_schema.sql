-- Work Center Shift Support - Database Schema
-- Migration: Add work_center_shift table for multi-shift support
-- Date: 2025-11-08
-- Purpose: Enable work centers to operate on multiple shifts with different capacities

-- Create work_center_shift table
CREATE TABLE IF NOT EXISTS work_center_shift (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_center_id INTEGER NOT NULL,

    -- Shift identification
    shift_name VARCHAR(50) NOT NULL,
    shift_number INTEGER NOT NULL,

    -- Shift timing
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    -- Days of operation (JSON array: [1,2,3,4,5] for Mon-Fri)
    -- ISO 8601 standard: 1=Monday, 7=Sunday
    days_of_week JSON NOT NULL,

    -- Capacity and efficiency
    capacity_percentage FLOAT NOT NULL DEFAULT 100.0,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Audit fields
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    -- Foreign key
    FOREIGN KEY (work_center_id) REFERENCES work_center(id) ON DELETE CASCADE,

    -- Constraints
    CONSTRAINT uq_shift_number_per_work_center UNIQUE (work_center_id, shift_number),
    CONSTRAINT check_shift_number_positive CHECK (shift_number > 0),
    CONSTRAINT check_capacity_percentage_range CHECK (capacity_percentage > 0 AND capacity_percentage <= 200)
);

-- Create indexes for query performance
CREATE INDEX IF NOT EXISTS idx_shift_work_center ON work_center_shift(work_center_id);
CREATE INDEX IF NOT EXISTS idx_shift_active ON work_center_shift(is_active);

-- Sample data for testing (optional - remove in production migration)
-- Example: Two-shift operation (Morning and Evening) on weekdays
/*
INSERT INTO work_center_shift (work_center_id, shift_name, shift_number, start_time, end_time, days_of_week, capacity_percentage, is_active)
VALUES
    (1, 'Morning', 1, '06:00:00', '14:00:00', '[1,2,3,4,5]', 100.0, TRUE),
    (1, 'Evening', 2, '14:00:00', '22:00:00', '[1,2,3,4,5]', 85.0, TRUE),
    (1, 'Night', 3, '22:00:00', '06:00:00', '[1,2,3,4,5]', 80.0, FALSE);
*/

-- Migration rollback script
/*
DROP INDEX IF EXISTS idx_shift_active;
DROP INDEX IF EXISTS idx_shift_work_center;
DROP TABLE IF EXISTS work_center_shift;
*/
