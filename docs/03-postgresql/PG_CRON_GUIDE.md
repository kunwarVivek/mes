# pg_cron (Job Scheduler) - Complete Guide

**Purpose**: Cron-like scheduled tasks inside PostgreSQL
**Performance**: Runs inside database, no separate service needed
**Last Updated**: 2025-11-10

---

## Table of Contents

1. [Overview](#overview)
2. [Cron Syntax](#cron-syntax)
3. [Scheduling Jobs](#scheduling-jobs)
4. [Managing Jobs](#managing-jobs)
5. [Job History](#job-history)
6. [Python Integration](#python-integration)
7. [Common Use Cases](#common-use-cases)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

pg_cron is a cron-like job scheduler that runs inside PostgreSQL. No external service (like Celery Beat) required.

### Why pg_cron?

**Replaces**: Celery Beat

**Benefits**:
- Runs inside PostgreSQL (no separate service)
- Standard cron syntax
- Job execution history
- Enable/disable jobs dynamically
- ACID transactions
- Simple SQL interface

**Use Cases**:
- Daily OEE calculations
- Inventory threshold alerts
- Preventive maintenance work order generation
- Cache cleanup
- Data retention policies
- Report generation
- Database maintenance (VACUUM, ANALYZE)

---

## Cron Syntax

pg_cron uses standard cron syntax:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday=0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Patterns

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every minute | `* * * * *` | Run every minute |
| Every 5 minutes | `*/5 * * * *` | Run every 5 minutes |
| Every hour | `0 * * * *` | Run at :00 of every hour |
| Every day at 6 AM | `0 6 * * *` | Run daily at 6:00 AM |
| Every Monday at 9 AM | `0 9 * * 1` | Run Mondays at 9:00 AM |
| Every weekday at 8 AM | `0 8 * * 1-5` | Run Mon-Fri at 8:00 AM |
| Every month on 1st at 3 AM | `0 3 1 * *` | Run monthly on 1st at 3:00 AM |

### Examples

```sql
-- Every minute
'* * * * *'

-- Every 5 minutes
'*/5 * * * *'

-- Every 15 minutes
'*/15 * * * *'

-- Every hour at :30
'30 * * * *'

-- Daily at 6:00 AM
'0 6 * * *'

-- Daily at 2:30 PM
'30 14 * * *'

-- Weekdays at 8:00 AM
'0 8 * * 1-5'

-- Weekends at 10:00 AM
'0 10 * * 0,6'
```

---

## Scheduling Jobs

### Schedule SQL Statement

```sql
-- Daily OEE calculation at 6:00 AM
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);

-- Returns: job_id (bigint)
-- Example: 1
```

### Schedule with Database Context

```sql
-- Schedule job in specific database
SELECT cron.schedule_in_database(
    'inventory-alerts',
    '*/5 * * * *',
    $$SELECT check_inventory_thresholds()$$,
    'unison_erp'  -- database name
);
```

### Common Scheduled Jobs

#### Every 5 Minutes: Inventory Threshold Alerts

```sql
SELECT cron.schedule(
    'inventory-alerts',
    '*/5 * * * *',
    $$SELECT check_inventory_thresholds()$$
);
```

#### Every Hour: Cache Cleanup

```sql
SELECT cron.schedule(
    'cache-cleanup',
    '0 * * * *',
    $$DELETE FROM cache WHERE expires_at < NOW()$$
);
```

#### Daily at 6 AM: OEE Calculation

```sql
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);
```

#### Daily at 6 AM: PM Work Order Generation

```sql
SELECT cron.schedule(
    'pm-work-order-generation',
    '0 6 * * *',
    $$
    INSERT INTO maintenance_work_orders (
        pm_schedule_id, machine_id, due_date, status
    )
    SELECT
        ps.id,
        ps.machine_id,
        ps.next_due_date,
        'pending'
    FROM pm_schedules ps
    WHERE ps.next_due_date <= CURRENT_DATE + INTERVAL '7 days'
      AND ps.is_active = TRUE
      AND NOT EXISTS (
          SELECT 1 FROM maintenance_work_orders mwo
          WHERE mwo.pm_schedule_id = ps.id
            AND mwo.due_date = ps.next_due_date
      )
    $$
);
```

#### Daily at 2 AM: Database Maintenance

```sql
SELECT cron.schedule(
    'database-maintenance',
    '0 2 * * *',
    $$VACUUM ANALYZE$$
);
```

---

## Managing Jobs

### List All Jobs

```sql
-- List all scheduled jobs
SELECT
    jobid,
    jobname,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active
FROM cron.job
ORDER BY jobname;
```

**Example output:**

```
jobid | jobname                    | schedule    | active
------+----------------------------+-------------+--------
1     | daily-oee-calculation      | 0 6 * * *   | t
2     | inventory-alerts           | */5 * * * * | t
3     | cache-cleanup              | 0 * * * *   | t
4     | pm-work-order-generation   | 0 6 * * *   | t
```

### Unschedule Job

```sql
-- Unschedule job (delete permanently)
SELECT cron.unschedule('daily-oee-calculation');

-- Or by job ID
SELECT cron.unschedule(1);

-- Returns: boolean (true if unscheduled)
```

### Disable Job Temporarily

```sql
-- Disable job (keep in database but don't run)
UPDATE cron.job
SET active = FALSE
WHERE jobname = 'inventory-alerts';

-- Job remains in database but won't execute
```

### Enable Job

```sql
-- Re-enable job
UPDATE cron.job
SET active = TRUE
WHERE jobname = 'inventory-alerts';
```

### Update Job Schedule

```sql
-- Change schedule (unschedule + reschedule)
SELECT cron.unschedule('daily-oee-calculation');

SELECT cron.schedule(
    'daily-oee-calculation',
    '0 7 * * *',  -- Changed from 6 AM to 7 AM
    $$SELECT calculate_daily_oee()$$
);
```

---

## Job History

### View Recent Job Runs

```sql
-- Recent job runs
SELECT
    j.jobname,
    jr.runid,
    jr.job_pid,
    jr.database,
    jr.status,
    jr.return_message,
    jr.start_time,
    jr.end_time,
    (jr.end_time - jr.start_time) as duration
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.start_time >= NOW() - INTERVAL '24 hours'
ORDER BY jr.start_time DESC;
```

**Example output:**

```
jobname                  | status    | start_time          | end_time            | duration
-------------------------+-----------+---------------------+---------------------+----------
daily-oee-calculation    | succeeded | 2025-11-10 06:00:00 | 2025-11-10 06:00:15 | 00:00:15
inventory-alerts         | succeeded | 2025-11-10 05:55:00 | 2025-11-10 05:55:01 | 00:00:01
cache-cleanup            | succeeded | 2025-11-10 05:00:00 | 2025-11-10 05:00:02 | 00:00:02
```

### Failed Jobs in Last 24 Hours

```sql
-- Failed jobs
SELECT
    j.jobname,
    jr.status,
    jr.return_message,
    jr.start_time
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.status = 'failed'
  AND jr.start_time >= NOW() - INTERVAL '24 hours'
ORDER BY jr.start_time DESC;
```

### Job Success Rate

```sql
-- Calculate success rate by job
SELECT
    j.jobname,
    COUNT(*) as total_runs,
    SUM(CASE WHEN jr.status = 'succeeded' THEN 1 ELSE 0 END) as successful_runs,
    ROUND(
        100.0 * SUM(CASE WHEN jr.status = 'succeeded' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) as success_rate_percent
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.start_time >= NOW() - INTERVAL '7 days'
GROUP BY j.jobname
ORDER BY success_rate_percent ASC;
```

---

## Python Integration

### Schedule Jobs from Python

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

def schedule_daily_report(db: Session, report_type: str, schedule: str = "0 7 * * *"):
    """Schedule a daily report generation"""
    job_name = f"daily-{report_type}-report"

    # Unschedule if exists
    db.execute(text("""
        SELECT cron.unschedule(:job_name)
        WHERE EXISTS (SELECT 1 FROM cron.job WHERE jobname = :job_name)
    """), {"job_name": job_name})

    # Schedule new job
    db.execute(text("""
        SELECT cron.schedule(
            :job_name,
            :schedule,
            $$SELECT generate_report(:report_type)$$
        )
    """), {"job_name": job_name, "schedule": schedule, "report_type": report_type})

    db.commit()

# Usage
schedule_daily_report(db, "production", "0 7 * * *")  # 7 AM daily
schedule_daily_report(db, "quality", "0 8 * * 1")  # 8 AM every Monday
```

### Call PGMQ from pg_cron

```sql
-- Schedule job that enqueues PGMQ message
CREATE OR REPLACE FUNCTION calculate_daily_oee()
RETURNS void AS $$
BEGIN
    -- Enqueue job to PGMQ
    PERFORM pgmq.send(
        'background_jobs',
        jsonb_build_object(
            'job_type', 'calculate_oee',
            'date', CURRENT_DATE - INTERVAL '1 day'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule to run daily at 6 AM
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);
```

### Check Job Status from Python

```python
from sqlalchemy import text

def get_job_status(db: Session, job_name: str):
    """Get status of scheduled job"""
    result = db.execute(text("""
        SELECT
            j.jobid,
            j.jobname,
            j.schedule,
            j.active,
            jr.status as last_status,
            jr.start_time as last_run,
            jr.return_message
        FROM cron.job j
        LEFT JOIN LATERAL (
            SELECT status, start_time, return_message
            FROM cron.job_run_details
            WHERE jobid = j.jobid
            ORDER BY start_time DESC
            LIMIT 1
        ) jr ON true
        WHERE j.jobname = :job_name
    """), {"job_name": job_name})

    return result.fetchone()

# Usage
status = get_job_status(db, "daily-oee-calculation")
if status:
    print(f"Job: {status.jobname}")
    print(f"Active: {status.active}")
    print(f"Last run: {status.last_run}")
    print(f"Last status: {status.last_status}")
```

---

## Common Use Cases

### Daily OEE Calculation

```sql
-- Function to calculate OEE
CREATE OR REPLACE FUNCTION calculate_daily_oee()
RETURNS void AS $$
BEGIN
    INSERT INTO oee_daily_summary (date, machine_id, oee_score)
    SELECT
        CURRENT_DATE - INTERVAL '1 day' as date,
        machine_id,
        calculate_oee_score(machine_id, CURRENT_DATE - INTERVAL '1 day')
    FROM machines
    WHERE is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Schedule
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);
```

### Inventory Threshold Alerts

```sql
-- Function to check inventory and send alerts
CREATE OR REPLACE FUNCTION check_inventory_thresholds()
RETURNS void AS $$
BEGIN
    -- Enqueue email notifications for low inventory
    PERFORM pgmq.send(
        'email_notifications',
        jsonb_build_object(
            'job_type', 'low_inventory_alert',
            'material_id', mi.material_id,
            'material_name', m.name,
            'current_quantity', mi.quantity,
            'reorder_point', m.reorder_point
        )
    )
    FROM material_inventory mi
    JOIN materials m ON mi.material_id = m.id
    WHERE mi.quantity <= m.reorder_point
      AND m.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Schedule every 5 minutes
SELECT cron.schedule(
    'inventory-alerts',
    '*/5 * * * *',
    $$SELECT check_inventory_thresholds()$$
);
```

### Data Retention Policy

```sql
-- Delete old production logs (keep 2 years)
SELECT cron.schedule(
    'data-retention-production-logs',
    '0 3 * * *',  -- 3 AM daily
    $$DELETE FROM production_logs WHERE logged_at < NOW() - INTERVAL '2 years'$$
);

-- Delete old cache entries
SELECT cron.schedule(
    'cache-cleanup',
    '0 * * * *',  -- Every hour
    $$DELETE FROM cache WHERE expires_at < NOW()$$
);
```

### Database Maintenance

```sql
-- VACUUM and ANALYZE daily at 2 AM
SELECT cron.schedule(
    'database-maintenance',
    '0 2 * * *',
    $$VACUUM ANALYZE$$
);

-- Update table statistics weekly
SELECT cron.schedule(
    'update-statistics',
    '0 3 * * 0',  -- Sunday 3 AM
    $$ANALYZE$$
);
```

---

## Monitoring

### Job Dashboard Query

```sql
-- Job monitoring dashboard
SELECT
    j.jobname,
    j.schedule,
    j.active,
    COUNT(jr.runid) as runs_last_24h,
    SUM(CASE WHEN jr.status = 'succeeded' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN jr.status = 'failed' THEN 1 ELSE 0 END) as failed,
    MAX(jr.start_time) as last_run,
    MAX(CASE WHEN jr.status = 'failed' THEN jr.return_message END) as last_error
FROM cron.job j
LEFT JOIN cron.job_run_details jr ON j.jobid = jr.jobid
    AND jr.start_time >= NOW() - INTERVAL '24 hours'
GROUP BY j.jobid, j.jobname, j.schedule, j.active
ORDER BY j.jobname;
```

### Alert on Failed Jobs

```sql
-- Get failed jobs that need attention
SELECT
    j.jobname,
    jr.status,
    jr.return_message,
    jr.start_time,
    jr.end_time
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.status = 'failed'
  AND jr.start_time >= NOW() - INTERVAL '1 hour'
ORDER BY jr.start_time DESC;
```

---

## Troubleshooting

### Jobs Not Running

**Diagnosis:**

```sql
-- Check if pg_cron is loaded
SHOW shared_preload_libraries;  -- Should include 'pg_cron'

-- Check cron database setting
SHOW cron.database_name;  -- Should match your database name

-- Check job status
SELECT jobid, jobname, schedule, active
FROM cron.job;

-- Check recent job runs
SELECT * FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 10;
```

**Solution:**

1. Ensure `pg_cron` in `shared_preload_libraries`
2. Set `cron.database_name = 'unison_erp'` in `postgresql.conf`
3. Restart PostgreSQL
4. Verify jobs are active:

```sql
UPDATE cron.job SET active = TRUE WHERE active = FALSE;
```

---

### Job Running But Erroring

**Diagnosis:**

```sql
-- Get error details
SELECT
    j.jobname,
    jr.command,
    jr.return_message,
    jr.start_time
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.status = 'failed'
  AND j.jobname = 'daily-oee-calculation'
ORDER BY jr.start_time DESC
LIMIT 1;
```

**Solution:**

1. Test command manually:

```sql
-- Test function directly
SELECT calculate_daily_oee();
```

2. Check function permissions:

```sql
-- Grant execute permission
GRANT EXECUTE ON FUNCTION calculate_daily_oee() TO unison;
```

3. Check function logs for errors

---

### Job Running Too Long

**Diagnosis:**

```sql
-- Find long-running jobs
SELECT
    j.jobname,
    jr.start_time,
    NOW() - jr.start_time as running_duration,
    jr.command
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.status = 'running'
  AND jr.start_time < NOW() - INTERVAL '10 minutes'
ORDER BY jr.start_time ASC;
```

**Solution:**

1. Optimize the SQL command
2. Add timeout to job:

```sql
-- Add statement timeout
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SET statement_timeout = '5min'; SELECT calculate_daily_oee();$$
);
```

3. Consider breaking into smaller jobs

---

### Job Missed Schedule

**Diagnosis:**

```sql
-- Check if job ran today
SELECT
    j.jobname,
    j.schedule,
    MAX(jr.start_time) as last_run,
    NOW() - MAX(jr.start_time) as time_since_last_run
FROM cron.job j
LEFT JOIN cron.job_run_details jr ON j.jobid = jr.jobid
WHERE j.jobname = 'daily-oee-calculation'
GROUP BY j.jobid, j.jobname, j.schedule;
```

**Solution:**

1. Check PostgreSQL logs for errors
2. Verify PostgreSQL was running during scheduled time
3. Check system time is correct
4. Run job manually to verify it works

---

## See Also

- [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md) - Installation and architecture
- [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) - Message queue integration
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migrate from Celery Beat
- [pg_cron Official Docs](https://github.com/citusdata/pg_cron)
