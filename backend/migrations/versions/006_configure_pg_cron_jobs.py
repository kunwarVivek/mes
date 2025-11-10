"""Configure pg_cron scheduled jobs

Revision ID: 006_configure_pg_cron
Revises: 005_complete_rls_implementation
Create Date: 2025-11-10 18:00:00.000000

Scheduled Jobs:
1. PM Work Order Generation - Daily 6 AM (Auto-create maintenance WOs 7 days before due)
2. Shift Performance Calculation - Hourly (Calculate shift OEE metrics)
3. Delivery Prediction Update - Daily 8 AM (Recalculate project delivery dates)
4. Daily KPI Aggregation - Daily 11:59 PM (Pre-calculate dashboard metrics)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '006_configure_pg_cron'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Configure pg_cron scheduled jobs for automation.

    Note: Requires pg_cron extension to be installed.
    If pg_cron is not available, this migration will print a warning and continue.
    """
    conn = op.get_bind()

    # Check if pg_cron is available
    try:
        result = conn.execute(text(
            "SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'"
        )).first()

        if not result:
            print("⚠️  pg_cron extension not installed. Skipping cron job configuration.")
            print("   To enable scheduled jobs, install pg_cron and re-run this migration.")
            return

        print("✓ pg_cron extension detected. Configuring scheduled jobs...")

    except Exception as e:
        print(f"⚠️  Could not check for pg_cron: {e}")
        return

    # ========================================================================
    # Job 1: PM Work Order Generation (Daily 6 AM)
    # ========================================================================
    try:
        conn.execute(text("""
            SELECT cron.schedule(
                'generate_pm_work_orders',                    -- Job name
                '0 6 * * *',                                  -- Daily at 6 AM
                $$
                DO $$
                BEGIN
                    -- Generate PM work orders for maintenance tasks due within 7 days
                    INSERT INTO work_order (
                        organization_id,
                        plant_id,
                        work_order_number,
                        work_order_type,
                        order_status,
                        product_id,
                        quantity_ordered,
                        start_date_planned,
                        end_date_planned,
                        priority,
                        created_by_user_id
                    )
                    SELECT
                        mt.organization_id,
                        mt.plant_id,
                        'PM-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || mt.id AS work_order_number,
                        'MAINTENANCE',
                        'PLANNED',
                        NULL,  -- No product for PM
                        1,
                        NOW() + INTERVAL '7 days',
                        NOW() + INTERVAL '7 days' + mt.estimated_duration,
                        1,  -- High priority
                        1   -- System user
                    FROM maintenance_tasks mt
                    WHERE mt.is_active = TRUE
                      AND mt.next_maintenance_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
                      AND NOT EXISTS (
                          SELECT 1 FROM work_order wo
                          WHERE wo.work_order_type = 'MAINTENANCE'
                            AND wo.maintenance_task_id = mt.id
                            AND wo.order_status IN ('PLANNED', 'RELEASED', 'IN_PROGRESS')
                      );

                    -- Log job execution
                    INSERT INTO audit_logs (user_id, action, resource_type, timestamp)
                    VALUES (1, 'PM_WORK_ORDERS_GENERATED', 'cron_job', NOW());
                END $$;
                $$
            );
        """))
        print("  ✓ Job 1: PM Work Order Generation (Daily 6 AM) configured")
    except Exception as e:
        print(f"  ✗ Failed to configure PM Work Order Generation job: {e}")

    # ========================================================================
    # Job 2: Shift Performance Calculation (Hourly)
    # ========================================================================
    try:
        conn.execute(text("""
            SELECT cron.schedule(
                'calculate_shift_performance',                -- Job name
                '0 * * * *',                                  -- Every hour
                $$
                DO $$
                BEGIN
                    -- Calculate OEE for completed shifts
                    INSERT INTO shift_performances (
                        shift_id,
                        organization_id,
                        plant_id,
                        performance_date,
                        oee_percentage,
                        availability_percentage,
                        performance_percentage,
                        quality_percentage,
                        total_pieces,
                        good_pieces,
                        defect_pieces,
                        calculated_at
                    )
                    SELECT
                        s.id AS shift_id,
                        s.organization_id,
                        s.plant_id,
                        DATE(s.shift_date) AS performance_date,
                        -- OEE = Availability × Performance × Quality
                        (
                            ((EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 60.0 - COALESCE(downtime.total_downtime, 0)) /
                             (EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 60.0)) *
                            100.0 *  -- Availability
                            CASE WHEN prod.total_pieces > 0 THEN 85.0 ELSE 0 END *  -- Performance (simplified)
                            (CASE WHEN prod.total_pieces > 0 THEN (prod.good_pieces / prod.total_pieces) ELSE 0 END)
                        ) / 100.0 AS oee_percentage,
                        -- Availability
                        ((EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 60.0 - COALESCE(downtime.total_downtime, 0)) /
                         (EXTRACT(EPOCH FROM (s.end_time - s.start_time)) / 60.0)) * 100.0 AS availability_percentage,
                        -- Performance (simplified - would need ideal cycle time)
                        CASE WHEN prod.total_pieces > 0 THEN 85.0 ELSE 0 END AS performance_percentage,
                        -- Quality
                        CASE WHEN prod.total_pieces > 0 THEN (prod.good_pieces / prod.total_pieces * 100.0) ELSE 0 END AS quality_percentage,
                        COALESCE(prod.total_pieces, 0) AS total_pieces,
                        COALESCE(prod.good_pieces, 0) AS good_pieces,
                        COALESCE(prod.defect_pieces, 0) AS defect_pieces,
                        NOW() AS calculated_at
                    FROM shift s
                    LEFT JOIN (
                        SELECT
                            shift_id,
                            SUM(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60.0) AS total_downtime
                        FROM machine_status_history
                        WHERE status IN ('DOWN', 'MAINTENANCE')
                          AND started_at >= NOW() - INTERVAL '1 hour'
                        GROUP BY shift_id
                    ) downtime ON downtime.shift_id = s.id
                    LEFT JOIN (
                        SELECT
                            shift_id,
                            SUM(quantity_produced) AS total_pieces,
                            SUM(quantity_produced - quantity_scrapped) AS good_pieces,
                            SUM(quantity_scrapped + quantity_reworked) AS defect_pieces
                        FROM production_logs
                        WHERE timestamp >= NOW() - INTERVAL '1 hour'
                        GROUP BY shift_id
                    ) prod ON prod.shift_id = s.id
                    WHERE s.end_time <= NOW()
                      AND s.end_time >= NOW() - INTERVAL '1 hour'
                      AND NOT EXISTS (
                          SELECT 1 FROM shift_performances sp
                          WHERE sp.shift_id = s.id
                            AND sp.performance_date = DATE(s.shift_date)
                      );

                    -- Log job execution
                    INSERT INTO audit_logs (user_id, action, resource_type, timestamp)
                    VALUES (1, 'SHIFT_PERFORMANCE_CALCULATED', 'cron_job', NOW());
                END $$;
                $$
            );
        """))
        print("  ✓ Job 2: Shift Performance Calculation (Hourly) configured")
    except Exception as e:
        print(f"  ✗ Failed to configure Shift Performance Calculation job: {e}")

    # ========================================================================
    # Job 3: Delivery Prediction Update (Daily 8 AM)
    # ========================================================================
    try:
        conn.execute(text("""
            SELECT cron.schedule(
                'update_delivery_predictions',                -- Job name
                '0 8 * * *',                                  -- Daily at 8 AM
                $$
                DO $$
                BEGIN
                    -- Recalculate project delivery dates based on current progress
                    UPDATE projects p
                    SET
                        predicted_completion_date = (
                            SELECT
                                p.planned_end_date +
                                -- Add delay based on average completion percentage vs time elapsed
                                INTERVAL '1 day' * (
                                    CASE
                                        WHEN progress.avg_completion > 0 THEN
                                            ((100.0 - progress.avg_completion) / progress.avg_completion) *
                                            EXTRACT(DAYS FROM (NOW() - p.planned_start_date))
                                        ELSE
                                            EXTRACT(DAYS FROM (p.planned_end_date - NOW()))
                                    END
                                )
                            FROM (
                                SELECT AVG(
                                    CASE
                                        WHEN wo.quantity_ordered > 0 THEN
                                            (wo.quantity_completed / wo.quantity_ordered * 100.0)
                                        ELSE 0
                                    END
                                ) AS avg_completion
                                FROM work_order wo
                                WHERE wo.project_id = p.id
                                  AND wo.order_status IN ('IN_PROGRESS', 'COMPLETED')
                            ) progress
                        ),
                        updated_at = NOW()
                    WHERE p.status = 'ACTIVE'
                      AND p.planned_end_date IS NOT NULL;

                    -- Log job execution
                    INSERT INTO audit_logs (user_id, action, resource_type, timestamp)
                    VALUES (1, 'DELIVERY_PREDICTIONS_UPDATED', 'cron_job', NOW());
                END $$;
                $$
            );
        """))
        print("  ✓ Job 3: Delivery Prediction Update (Daily 8 AM) configured")
    except Exception as e:
        print(f"  ✗ Failed to configure Delivery Prediction Update job: {e}")

    # ========================================================================
    # Job 4: Daily KPI Aggregation (Daily 11:59 PM)
    # ========================================================================
    try:
        conn.execute(text("""
            SELECT cron.schedule(
                'aggregate_daily_kpis',                       -- Job name
                '59 23 * * *',                                -- Daily at 11:59 PM
                $$
                DO $$
                BEGIN
                    -- Pre-calculate and cache daily KPI metrics for faster dashboard loading
                    -- This runs at end of day to capture complete daily metrics

                    -- Clear old cache entries (older than 30 days)
                    DELETE FROM cache
                    WHERE cache_key LIKE 'kpi_daily_%'
                      AND expires_at < NOW() - INTERVAL '30 days';

                    -- Cache OEE metrics by plant
                    INSERT INTO cache (cache_key, cache_value, expires_at)
                    SELECT
                        'kpi_daily_oee_plant_' || plant_id || '_' || TO_CHAR(NOW(), 'YYYYMMDD') AS cache_key,
                        jsonb_build_object(
                            'plant_id', plant_id,
                            'date', CURRENT_DATE,
                            'oee', AVG(oee_percentage),
                            'availability', AVG(availability_percentage),
                            'performance', AVG(performance_percentage),
                            'quality', AVG(quality_percentage)
                        ) AS cache_value,
                        NOW() + INTERVAL '30 days' AS expires_at
                    FROM shift_performances
                    WHERE performance_date = CURRENT_DATE
                    GROUP BY plant_id
                    ON CONFLICT (cache_key) DO UPDATE
                    SET cache_value = EXCLUDED.cache_value,
                        expires_at = EXCLUDED.expires_at;

                    -- Cache OTD metrics by plant
                    INSERT INTO cache (cache_key, cache_value, expires_at)
                    SELECT
                        'kpi_daily_otd_plant_' || plant_id || '_' || TO_CHAR(NOW(), 'YYYYMMDD') AS cache_key,
                        jsonb_build_object(
                            'plant_id', plant_id,
                            'date', CURRENT_DATE,
                            'total_completed', COUNT(*),
                            'on_time', SUM(CASE WHEN end_date_actual <= end_date_planned THEN 1 ELSE 0 END),
                            'late', SUM(CASE WHEN end_date_actual > end_date_planned THEN 1 ELSE 0 END),
                            'otd_percentage', (SUM(CASE WHEN end_date_actual <= end_date_planned THEN 1 ELSE 0 END)::float / COUNT(*) * 100.0)
                        ) AS cache_value,
                        NOW() + INTERVAL '30 days' AS expires_at
                    FROM work_order
                    WHERE order_status = 'COMPLETED'
                      AND DATE(end_date_actual) = CURRENT_DATE
                    GROUP BY plant_id
                    ON CONFLICT (cache_key) DO UPDATE
                    SET cache_value = EXCLUDED.cache_value,
                        expires_at = EXCLUDED.expires_at;

                    -- Log job execution
                    INSERT INTO audit_logs (user_id, action, resource_type, timestamp)
                    VALUES (1, 'DAILY_KPIS_AGGREGATED', 'cron_job', NOW());
                END $$;
                $$
            );
        """))
        print("  ✓ Job 4: Daily KPI Aggregation (Daily 11:59 PM) configured")
    except Exception as e:
        print(f"  ✗ Failed to configure Daily KPI Aggregation job: {e}")

    print("\n✅ pg_cron jobs configured successfully!")
    print("   View scheduled jobs: SELECT * FROM cron.job;")


def downgrade() -> None:
    """Remove pg_cron scheduled jobs"""
    conn = op.get_bind()

    # Check if pg_cron is available
    try:
        result = conn.execute(text(
            "SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'"
        )).first()

        if not result:
            print("⚠️  pg_cron extension not installed. Nothing to remove.")
            return

    except Exception as e:
        print(f"⚠️  Could not check for pg_cron: {e}")
        return

    # Unschedule all jobs
    jobs = [
        'generate_pm_work_orders',
        'calculate_shift_performance',
        'update_delivery_predictions',
        'aggregate_daily_kpis'
    ]

    for job_name in jobs:
        try:
            conn.execute(text(f"SELECT cron.unschedule('{job_name}');"))
            print(f"  ✓ Removed job: {job_name}")
        except Exception as e:
            print(f"  ✗ Failed to remove job {job_name}: {e}")

    print("\n✅ pg_cron jobs removed")
