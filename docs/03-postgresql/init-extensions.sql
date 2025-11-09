-- ============================================================================
-- Unison Manufacturing ERP - PostgreSQL Extensions Initialization
-- ============================================================================
-- Version: 1.0
-- Date: 2025-11-07
-- Purpose: Initialize all PostgreSQL extensions and configure for MES ERP
-- ============================================================================

-- Enable extensions
-- ============================================================================

-- Message queue (replaces Celery + RabbitMQ)
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Scheduled tasks (replaces Celery Beat)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Full-text search with BM25 (replaces Elasticsearch)
CREATE EXTENSION IF NOT EXISTS pg_search;

-- Analytics engine (10-1500x faster OLAP)
CREATE EXTENSION IF NOT EXISTS pg_duckdb;

-- Time-series optimization (75% compression)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Standard extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Trigram similarity for fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- GIN indexes for multi-column queries

-- ============================================================================
-- 1. PGMQ: Create Message Queues
-- ============================================================================

-- Main background jobs queue (SAP sync, barcode generation, reports, emails)
SELECT pgmq.create('background_jobs');

-- Dead letter queue for failed messages (max retries exceeded)
SELECT pgmq.create('dlq');

-- Email notification queue (separate for prioritization)
SELECT pgmq.create('email_notifications');

-- Report generation queue (heavy workload, separate processing)
SELECT pgmq.create('report_generation');

-- Partitioned queue for high-volume jobs (if needed in future)
-- SELECT pgmq.create_partitioned(
--     'high_volume_jobs',
--     partition_interval => '1 day',
--     retention_interval => '7 days'
-- );

-- ============================================================================
-- 2. Cache: UNLOGGED Table for High-Speed Caching
-- ============================================================================

CREATE UNLOGGED TABLE IF NOT EXISTS cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient expiry cleanup
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);

-- ============================================================================
-- 3. pg_cron: Schedule Recurring Jobs
-- ============================================================================

-- Daily OEE calculation (6:00 AM)
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$
    -- Calculate OEE for previous day
    INSERT INTO kpi_calculations (
        organization_id, plant_id, kpi_type, period_start, period_end,
        value_numeric, calculated_at
    )
    SELECT
        pl.organization_id,
        pl.plant_id,
        'oee' as kpi_type,
        CURRENT_DATE - INTERVAL '1 day' as period_start,
        CURRENT_DATE as period_end,
        (
            -- OEE = Availability × Performance × Quality
            -- Simplified calculation, actual logic in domain service
            (SUM(pl.hours_spent) / 24.0) * -- Availability
            (SUM(pl.quantity_produced) / NULLIF(SUM(wo.quantity_ordered), 0)) * -- Performance
            (1.0 - (SUM(pl.quantity_rejected) / NULLIF(SUM(pl.quantity_produced), 0))) -- Quality
        ) as value_numeric,
        NOW() as calculated_at
    FROM production_logs pl
    JOIN work_orders wo ON pl.work_order_id = wo.id
    WHERE pl.logged_at >= CURRENT_DATE - INTERVAL '1 day'
      AND pl.logged_at < CURRENT_DATE
    GROUP BY pl.organization_id, pl.plant_id;
    $$
);

-- Cache cleanup (every 5 minutes) - remove expired entries
SELECT cron.schedule(
    'cache-cleanup',
    '*/5 * * * *',
    $$DELETE FROM cache WHERE expires_at < NOW()$$
);

-- Inventory threshold alerts (every hour)
SELECT cron.schedule(
    'inventory-alerts',
    '0 * * * *',
    $$
    -- Send queue message for low inventory alerts
    SELECT pgmq.send(
        'email_notifications',
        jsonb_build_object(
            'job_type', 'low_inventory_alert',
            'material_id', mi.material_id,
            'current_quantity', mi.quantity,
            'reorder_point', m.reorder_point
        )
    )
    FROM material_inventory mi
    JOIN materials m ON mi.material_id = m.id
    WHERE mi.quantity <= m.reorder_point
      AND m.is_active = TRUE;
    $$
);

-- Auto-generate PM work orders (daily at 6:00 AM) - 7 days before due
SELECT cron.schedule(
    'pm-work-order-generation',
    '0 6 * * *',
    $$
    INSERT INTO maintenance_work_orders (
        organization_id,
        plant_id,
        pm_schedule_id,
        machine_id,
        work_order_type,
        due_date,
        priority,
        status,
        created_at
    )
    SELECT
        ps.organization_id,
        ps.plant_id,
        ps.id as pm_schedule_id,
        ps.machine_id,
        'pm' as work_order_type,
        ps.next_due_date as due_date,
        ps.priority,
        'pending' as status,
        NOW() as created_at
    FROM pm_schedules ps
    WHERE ps.next_due_date <= CURRENT_DATE + INTERVAL '7 days'
      AND ps.is_active = TRUE
      AND NOT EXISTS (
          SELECT 1 FROM maintenance_work_orders mwo
          WHERE mwo.pm_schedule_id = ps.id
            AND mwo.due_date = ps.next_due_date
      );

    -- Update next_due_date for generated PM schedules
    UPDATE pm_schedules ps
    SET next_due_date = CASE
        WHEN frequency_type = 'calendar' THEN
            ps.next_due_date + (frequency_value || ' ' || frequency_unit)::INTERVAL
        WHEN frequency_type = 'meter_based' THEN
            -- For meter-based, keep same date until meter reading updated
            ps.next_due_date
    END,
    updated_at = NOW()
    WHERE ps.id IN (
        SELECT pm_schedule_id FROM maintenance_work_orders
        WHERE created_at >= NOW() - INTERVAL '5 minutes'
          AND work_order_type = 'pm'
    );
    $$
);

-- Shift performance aggregation (every 8 hours at shift changes)
SELECT cron.schedule(
    'shift-performance-aggregation',
    '0 6,14,22 * * *',  -- 6 AM, 2 PM, 10 PM
    $$
    -- Aggregate shift performance for previous shift
    INSERT INTO shift_performance_logs (
        organization_id,
        plant_id,
        shift_id,
        shift_date,
        total_production,
        total_downtime_minutes,
        efficiency_percentage,
        calculated_at
    )
    SELECT
        pl.organization_id,
        pl.plant_id,
        pl.shift_id,
        CURRENT_DATE as shift_date,
        SUM(pl.quantity_produced) as total_production,
        SUM(dt.duration_minutes) as total_downtime_minutes,
        (
            (SUM(pl.hours_spent) - SUM(dt.duration_minutes) / 60.0) /
            NULLIF(SUM(pl.hours_spent), 0) * 100
        ) as efficiency_percentage,
        NOW() as calculated_at
    FROM production_logs pl
    LEFT JOIN downtime_tracking dt ON pl.work_order_id = dt.work_order_id
        AND dt.started_at >= CURRENT_DATE
    WHERE pl.logged_at >= CURRENT_DATE
      AND pl.logged_at < NOW()
    GROUP BY pl.organization_id, pl.plant_id, pl.shift_id;
    $$
);

-- ============================================================================
-- 4. pg_search: Create Full-Text Search Indexes (BM25 Ranking)
-- ============================================================================

-- Materials search index
SELECT paradedb.create_bm25(
    table_name => 'material',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{material_number, material_name, description}',
    numeric_fields => '{safety_stock, reorder_point, lead_time_days}',
    boolean_fields => '{is_active}'
);

-- Work orders search index
SELECT paradedb.create_bm25(
    table_name => 'work_orders',
    index_name => 'work_orders_search_idx',
    key_field => 'id',
    text_fields => '{work_order_number, project_name, customer_order_reference, notes}',
    numeric_fields => '{quantity_ordered, quantity_completed}',
    boolean_fields => '{is_active}'
);

-- NCR reports search index
SELECT paradedb.create_bm25(
    table_name => 'ncr_reports',
    index_name => 'ncr_search_idx',
    key_field => 'id',
    text_fields => '{ncr_number, problem_description, root_cause, corrective_action, tags}'
);

-- Projects search index
SELECT paradedb.create_bm25(
    table_name => 'projects',
    index_name => 'projects_search_idx',
    key_field => 'id',
    text_fields => '{project_name, project_code, customer_name, notes}'
);

-- Documents search index
SELECT paradedb.create_bm25(
    table_name => 'documents',
    index_name => 'documents_search_idx',
    key_field => 'id',
    text_fields => '{title, description, tags, file_name}'
);

-- ============================================================================
-- 5. timescaledb: Convert Time-Series Tables to Hypertables
-- ============================================================================

-- Production logs (10K+ entries per day)
SELECT create_hypertable(
    'production_logs',
    'logged_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Machine sensor data (if exists - for future IoT integration)
-- SELECT create_hypertable(
--     'machine_sensor_data',
--     'recorded_at',
--     chunk_time_interval => INTERVAL '1 day',
--     if_not_exists => TRUE
-- );

-- Downtime tracking
SELECT create_hypertable(
    'downtime_tracking',
    'started_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Shift performance logs
SELECT create_hypertable(
    'shift_performance_logs',
    'shift_date',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- ============================================================================
-- 6. timescaledb: Add Compression Policies (75% Storage Savings)
-- ============================================================================

-- Compress production_logs after 7 days
ALTER TABLE production_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, work_order_id, user_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_compression_policy(
    'production_logs',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Compress downtime_tracking after 7 days
ALTER TABLE downtime_tracking SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, machine_id',
    timescaledb.compress_orderby = 'started_at DESC'
);

SELECT add_compression_policy(
    'downtime_tracking',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ============================================================================
-- 7. timescaledb: Add Retention Policies (Auto-Delete Old Data)
-- ============================================================================

-- Delete production logs older than 2 years
SELECT add_retention_policy(
    'production_logs',
    INTERVAL '2 years',
    if_not_exists => TRUE
);

-- Delete downtime tracking older than 2 years
SELECT add_retention_policy(
    'downtime_tracking',
    INTERVAL '2 years',
    if_not_exists => TRUE
);

-- Delete shift performance logs older than 1 year
SELECT add_retention_policy(
    'shift_performance_logs',
    INTERVAL '1 year',
    if_not_exists => TRUE
);

-- ============================================================================
-- 8. timescaledb: Create Continuous Aggregates (Real-Time Materialized Views)
-- ============================================================================

-- Daily production summary (fast dashboard queries)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_production_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', logged_at) as day,
    organization_id,
    plant_id,
    work_order_id,
    COUNT(*) as log_count,
    SUM(quantity_produced) as total_qty_produced,
    SUM(quantity_rejected) as total_qty_rejected,
    SUM(hours_spent) as total_hours_spent,
    AVG(labor_cost) as avg_labor_cost,
    AVG(material_cost) as avg_material_cost
FROM production_logs
GROUP BY day, organization_id, plant_id, work_order_id;

-- Add refresh policy (refresh every hour)
SELECT add_continuous_aggregate_policy(
    'daily_production_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Weekly downtime summary
CREATE MATERIALIZED VIEW IF NOT EXISTS weekly_downtime_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', started_at) as week,
    organization_id,
    plant_id,
    machine_id,
    downtime_reason,
    COUNT(*) as incident_count,
    SUM(duration_minutes) as total_downtime_minutes,
    AVG(duration_minutes) as avg_downtime_minutes
FROM downtime_tracking
GROUP BY week, organization_id, plant_id, machine_id, downtime_reason;

-- Add refresh policy (refresh daily)
SELECT add_continuous_aggregate_policy(
    'weekly_downtime_summary',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ============================================================================
-- 9. Performance Indexes
-- ============================================================================

-- Cache expiry index (already created above)
-- CREATE INDEX idx_cache_expires ON cache(expires_at);

-- Production logs indexes (in addition to hypertable indexes)
CREATE INDEX IF NOT EXISTS idx_production_logs_wo_user
ON production_logs (work_order_id, user_id, logged_at DESC);

CREATE INDEX IF NOT EXISTS idx_production_logs_plant_date
ON production_logs (plant_id, logged_at DESC);

-- Downtime tracking indexes
CREATE INDEX IF NOT EXISTS idx_downtime_machine_date
ON downtime_tracking (machine_id, started_at DESC);

-- Work orders indexes
CREATE INDEX IF NOT EXISTS idx_work_orders_status_date
ON work_orders (status, start_date DESC)
WHERE is_active = TRUE;

-- Material inventory indexes
CREATE INDEX IF NOT EXISTS idx_material_inventory_location
ON material_inventory (warehouse_location_id, material_id);

-- ============================================================================
-- 10. LISTEN/NOTIFY: Pub/Sub Triggers for Real-Time Updates
-- ============================================================================

-- Production log created notification
CREATE OR REPLACE FUNCTION notify_production_log_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'production_log_created',
        json_build_object(
            'id', NEW.id,
            'work_order_id', NEW.work_order_id,
            'quantity_produced', NEW.quantity_produced,
            'plant_id', NEW.plant_id,
            'logged_at', NEW.logged_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER production_log_created_notify
AFTER INSERT ON production_logs
FOR EACH ROW EXECUTE FUNCTION notify_production_log_created();

-- NCR status change notification
CREATE OR REPLACE FUNCTION notify_ncr_status_changed()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status != OLD.status THEN
        PERFORM pg_notify(
            'ncr_status_changed',
            json_build_object(
                'id', NEW.id,
                'ncr_number', NEW.ncr_number,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'organization_id', NEW.organization_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ncr_status_changed_notify
AFTER UPDATE ON ncr_reports
FOR EACH ROW EXECUTE FUNCTION notify_ncr_status_changed();

-- Machine status change notification
CREATE OR REPLACE FUNCTION notify_machine_status_changed()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status != OLD.status THEN
        PERFORM pg_notify(
            'machine_status_changed',
            json_build_object(
                'id', NEW.id,
                'machine_code', NEW.machine_code,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'plant_id', NEW.plant_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER machine_status_changed_notify
AFTER UPDATE ON machines
FOR EACH ROW EXECUTE FUNCTION notify_machine_status_changed();

-- ============================================================================
-- 11. Verification Queries
-- ============================================================================

-- Check installed extensions
SELECT
    name,
    default_version,
    installed_version,
    comment
FROM pg_available_extensions
WHERE name IN ('pgmq', 'pg_cron', 'pg_search', 'pg_duckdb', 'timescaledb')
ORDER BY name;

-- Check created queues
SELECT * FROM pgmq.list_queues();

-- Check scheduled jobs
SELECT
    jobname,
    schedule,
    active,
    database
FROM cron.job
ORDER BY jobname;

-- Check hypertables
SELECT
    hypertable_schema,
    hypertable_name,
    num_chunks,
    compression_enabled,
    replication_factor
FROM timescaledb_information.hypertables;

-- Check continuous aggregates
SELECT
    view_name,
    materialization_hypertable_name,
    refresh_lag,
    refresh_interval
FROM timescaledb_information.continuous_aggregates;

-- ============================================================================
-- Initialization Complete
-- ============================================================================

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE '✅ PostgreSQL extensions initialized successfully';
    RAISE NOTICE '✅ PGMQ queues created: background_jobs, dlq, email_notifications, report_generation';
    RAISE NOTICE '✅ Cache table created (UNLOGGED)';
    RAISE NOTICE '✅ pg_cron jobs scheduled: 5 recurring jobs';
    RAISE NOTICE '✅ pg_search indexes created: 5 BM25 indexes';
    RAISE NOTICE '✅ timescaledb hypertables created: 3 tables';
    RAISE NOTICE '✅ timescaledb compression enabled: 75%% storage savings';
    RAISE NOTICE '✅ timescaledb retention policies: auto-delete old data';
    RAISE NOTICE '✅ Continuous aggregates created: 2 real-time views';
    RAISE NOTICE '✅ LISTEN/NOTIFY triggers created: 3 real-time notifications';
    RAISE NOTICE '🎉 Unison Manufacturing ERP - PostgreSQL-Native Stack Ready!';
END $$;
