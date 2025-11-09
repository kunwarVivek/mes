-- =============================================================================
-- pg_cron Job: Auto-generate PM Work Orders
-- =============================================================================
-- This script sets up a pg_cron job to automatically generate PM work orders
-- based on active PM schedules (both calendar-based and meter-based triggers).
--
-- Prerequisites:
-- - pg_cron extension must be installed: CREATE EXTENSION pg_cron;
-- - Database superuser privileges required to schedule cron jobs
--
-- Execution:
-- Run this script as a PostgreSQL superuser to create the cron job
-- =============================================================================

-- Function to generate PM work orders for calendar-based schedules
CREATE OR REPLACE FUNCTION generate_calendar_pm_work_orders()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    schedule_record RECORD;
    next_pm_number TEXT;
    next_scheduled_date TIMESTAMP WITH TIME ZONE;
    next_due_date TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Loop through all active calendar-based PM schedules
    FOR schedule_record IN
        SELECT
            ps.id,
            ps.organization_id,
            ps.plant_id,
            ps.schedule_code,
            ps.machine_id,
            ps.frequency_days,
            COALESCE(
                (SELECT MAX(pmwo.scheduled_date)
                 FROM pm_work_order pmwo
                 WHERE pmwo.pm_schedule_id = ps.id),
                NOW()
            ) AS last_pm_date
        FROM pm_schedule ps
        WHERE ps.is_active = TRUE
          AND ps.trigger_type = 'CALENDAR'
          AND ps.frequency_days IS NOT NULL
    LOOP
        -- Calculate next scheduled date
        next_scheduled_date := schedule_record.last_pm_date + (schedule_record.frequency_days || ' days')::INTERVAL;
        next_due_date := next_scheduled_date + INTERVAL '7 days';  -- Default 7-day grace period

        -- Only create PM work order if the next scheduled date is within the next 30 days
        IF next_scheduled_date <= NOW() + INTERVAL '30 days' THEN
            -- Check if PM work order already exists for this scheduled date
            IF NOT EXISTS (
                SELECT 1
                FROM pm_work_order
                WHERE pm_schedule_id = schedule_record.id
                  AND scheduled_date = next_scheduled_date
            ) THEN
                -- Generate unique PM number
                next_pm_number := 'PM-' || schedule_record.schedule_code || '-' ||
                                  TO_CHAR(next_scheduled_date, 'YYYYMMDD') || '-' ||
                                  LPAD(NEXTVAL('pm_work_order_id_seq')::TEXT, 6, '0');

                -- Insert new PM work order
                INSERT INTO pm_work_order (
                    organization_id,
                    plant_id,
                    pm_schedule_id,
                    machine_id,
                    pm_number,
                    status,
                    scheduled_date,
                    due_date,
                    created_at
                ) VALUES (
                    schedule_record.organization_id,
                    schedule_record.plant_id,
                    schedule_record.id,
                    schedule_record.machine_id,
                    next_pm_number,
                    'SCHEDULED',
                    next_scheduled_date,
                    next_due_date,
                    NOW()
                );

                RAISE NOTICE 'Created PM work order % for schedule %', next_pm_number, schedule_record.schedule_code;
            END IF;
        END IF;
    END LOOP;
END;
$$;

-- Function to generate PM work orders for meter-based schedules
-- Note: This requires machine meter readings to be tracked separately
CREATE OR REPLACE FUNCTION generate_meter_pm_work_orders()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    schedule_record RECORD;
    next_pm_number TEXT;
    current_meter_reading FLOAT;
    last_pm_meter_reading FLOAT;
BEGIN
    -- Loop through all active meter-based PM schedules
    FOR schedule_record IN
        SELECT
            ps.id,
            ps.organization_id,
            ps.plant_id,
            ps.schedule_code,
            ps.machine_id,
            ps.meter_threshold
        FROM pm_schedule ps
        WHERE ps.is_active = TRUE
          AND ps.trigger_type = 'METER'
          AND ps.meter_threshold IS NOT NULL
    LOOP
        -- Get current meter reading from machine_status_history or separate meter_reading table
        -- This is a placeholder - you'll need to implement actual meter reading tracking
        SELECT COALESCE(
            (SELECT SUM(EXTRACT(EPOCH FROM (COALESCE(ended_at, NOW()) - started_at)) / 3600.0)
             FROM machine_status_history
             WHERE machine_id = schedule_record.machine_id
               AND status = 'RUNNING'),
            0
        ) INTO current_meter_reading;

        -- Get last PM meter reading
        SELECT COALESCE(
            (SELECT current_meter_reading - (schedule_record.meter_threshold * COUNT(*))
             FROM pm_work_order
             WHERE pm_schedule_id = schedule_record.id
               AND status IN ('COMPLETED', 'IN_PROGRESS')),
            0
        ) INTO last_pm_meter_reading;

        -- Check if meter threshold exceeded
        IF (current_meter_reading - last_pm_meter_reading) >= schedule_record.meter_threshold THEN
            -- Check if PM work order already exists in SCHEDULED status
            IF NOT EXISTS (
                SELECT 1
                FROM pm_work_order
                WHERE pm_schedule_id = schedule_record.id
                  AND status = 'SCHEDULED'
            ) THEN
                -- Generate unique PM number
                next_pm_number := 'PM-' || schedule_record.schedule_code || '-' ||
                                  TO_CHAR(NOW(), 'YYYYMMDD') || '-' ||
                                  LPAD(NEXTVAL('pm_work_order_id_seq')::TEXT, 6, '0');

                -- Insert new PM work order
                INSERT INTO pm_work_order (
                    organization_id,
                    plant_id,
                    pm_schedule_id,
                    machine_id,
                    pm_number,
                    status,
                    scheduled_date,
                    due_date,
                    created_at
                ) VALUES (
                    schedule_record.organization_id,
                    schedule_record.plant_id,
                    schedule_record.id,
                    schedule_record.machine_id,
                    next_pm_number,
                    'SCHEDULED',
                    NOW(),
                    NOW() + INTERVAL '7 days',
                    NOW()
                );

                RAISE NOTICE 'Created meter-based PM work order % for schedule %', next_pm_number, schedule_record.schedule_code;
            END IF;
        END IF;
    END LOOP;
END;
$$;

-- Schedule pg_cron job to run daily at 2:00 AM
-- This job will auto-generate PM work orders for upcoming maintenance
SELECT cron.schedule(
    'generate_pm_work_orders',           -- Job name
    '0 2 * * *',                         -- Cron expression (daily at 2:00 AM)
    $$
    SELECT generate_calendar_pm_work_orders();
    SELECT generate_meter_pm_work_orders();
    $$
);

-- View scheduled cron jobs
-- SELECT * FROM cron.job;

-- Unschedule the job (if needed for maintenance)
-- SELECT cron.unschedule('generate_pm_work_orders');

-- =============================================================================
-- Manual Testing
-- =============================================================================
-- To test the functions manually without waiting for cron:
-- SELECT generate_calendar_pm_work_orders();
-- SELECT generate_meter_pm_work_orders();

-- =============================================================================
-- Notes
-- =============================================================================
-- 1. Calendar-based schedules:
--    - Automatically generate PM work orders 30 days in advance
--    - Default 7-day grace period after scheduled date
--    - PM number format: PM-{SCHEDULE_CODE}-{YYYYMMDD}-{SEQUENCE}
--
-- 2. Meter-based schedules:
--    - Require machine meter readings (operating hours) to be tracked
--    - Generate PM work order when meter threshold is exceeded
--    - Only one SCHEDULED PM work order exists at a time per schedule
--
-- 3. RLS (Row-Level Security):
--    - All PM work orders inherit organization_id and plant_id from schedules
--    - Ensures multi-tenant data isolation
--
-- 4. Monitoring:
--    - Check cron.job_run_details for execution history
--    - Monitor RAISE NOTICE messages in PostgreSQL logs
--
-- 5. Customization:
--    - Adjust grace period (currently 7 days) based on requirements
--    - Modify advance generation window (currently 30 days) as needed
--    - Implement custom meter reading logic for your use case
-- =============================================================================
