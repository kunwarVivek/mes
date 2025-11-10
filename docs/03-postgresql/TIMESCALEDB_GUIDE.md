# TimescaleDB (Time-Series) - Complete Guide

**Purpose**: Optimize time-series data storage and queries
**Performance**: 75% storage reduction via compression
**Last Updated**: 2025-11-10

---

## Table of Contents

1. [Overview](#overview)
2. [Hypertables](#hypertables)
3. [Compression](#compression)
4. [Data Retention](#data-retention)
5. [Continuous Aggregates](#continuous-aggregates)
6. [Queries](#queries)
7. [Python Integration](#python-integration)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

TimescaleDB is a PostgreSQL extension that optimizes time-series data with automatic partitioning, compression, and continuous aggregates.

### Why TimescaleDB?

**Replaces**: InfluxDB, Prometheus

**Benefits**:
- **75% storage savings** via compression
- **10-100x faster queries** on time-series data
- Automatic partitioning (no manual management)
- Continuous aggregates (real-time materialized views)
- Data retention policies (automatic deletion)
- Full SQL compatibility

**Use Cases**:
- Production logs (quantity, hours, labor cost)
- Machine sensor data (temperature, vibration, speed)
- OEE metrics over time
- Downtime tracking
- Quality metrics
- Inventory level history

---

## Hypertables

### What is a Hypertable?

A hypertable is a regular PostgreSQL table that TimescaleDB automatically partitions by time. You interact with it like any normal table, but it's optimized for time-series queries.

### Convert Table to Hypertable

```sql
-- Convert production_logs to hypertable
SELECT create_hypertable(
    'production_logs',
    'logged_at',
    chunk_time_interval => INTERVAL '1 month'
);

-- Convert machine_sensor_data to hypertable
SELECT create_hypertable(
    'machine_sensor_data',
    'recorded_at',
    chunk_time_interval => INTERVAL '1 day'
);

-- Convert downtime_logs to hypertable
SELECT create_hypertable(
    'downtime_logs',
    'started_at',
    chunk_time_interval => INTERVAL '1 week'
);
```

**Parameters:**
- First argument: Table name
- Second argument: Time column (must be timestamp/timestamptz)
- `chunk_time_interval`: Partition size (day, week, month)

**Choosing chunk_time_interval:**
| Data Volume | Recommended Interval |
|-------------|---------------------|
| Low (< 1K rows/day) | 1 month |
| Medium (1K-100K rows/day) | 1 week |
| High (100K-1M rows/day) | 1 day |
| Very High (> 1M rows/day) | 12 hours |

### Create Hypertable at Table Creation

```sql
-- Create table and convert to hypertable in one step
CREATE TABLE production_logs (
    id BIGSERIAL,
    work_order_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    quantity_produced INTEGER NOT NULL,
    hours_spent DECIMAL(10,2),
    labor_cost DECIMAL(10,2),
    logged_at TIMESTAMPTZ NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('production_logs', 'logged_at');
```

### Check Hypertable Info

```sql
-- List all hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Get chunk information
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'production_logs'
ORDER BY range_start DESC;
```

---

## Compression

### Enable Compression

```sql
-- Enable compression on production_logs
ALTER TABLE production_logs
SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'work_order_id, user_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);
```

**Parameters:**
- `timescaledb.compress`: Enable compression
- `compress_segmentby`: Group by these columns (improves query performance)
- `compress_orderby`: Sort order within segments

**Choosing segmentby:**
- Use columns frequently used in WHERE clauses
- Use low-cardinality columns (machine_id, not timestamp)
- Example: `machine_id`, `work_order_id`, `user_id`

### Add Compression Policy

```sql
-- Compress data older than 7 days
SELECT add_compression_policy(
    'production_logs',
    INTERVAL '7 days'
);

-- Compress sensor data older than 24 hours
SELECT add_compression_policy(
    'machine_sensor_data',
    INTERVAL '1 day'
);
```

**Note**: Data older than the interval will be automatically compressed. Compressed data is read-only.

### Manual Compression

```sql
-- Manually compress specific chunks
SELECT compress_chunk(i.show_chunks)
FROM show_chunks('production_logs') i
WHERE i.range_end < NOW() - INTERVAL '7 days';

-- Decompress chunk (make writable)
SELECT decompress_chunk('_timescaledb_internal._hyper_1_1_chunk');
```

### Check Compression Stats

```sql
-- View compression statistics
SELECT
    chunk_name,
    before_compression_total_bytes,
    after_compression_total_bytes,
    pg_size_pretty(before_compression_total_bytes) as before_size,
    pg_size_pretty(after_compression_total_bytes) as after_size,
    ROUND(
        100 - (after_compression_total_bytes::numeric / before_compression_total_bytes * 100),
        2
    ) as compression_ratio_percent
FROM timescaledb_information.compressed_chunk_stats
WHERE hypertable_name = 'production_logs'
ORDER BY chunk_name DESC;

-- Expected output:
-- chunk_name | before_size | after_size | compression_ratio_percent
-- -----------+-------------+------------+--------------------------
-- chunk_1    | 1024 MB     | 256 MB     | 75.00
-- chunk_2    | 512 MB      | 128 MB     | 75.00
```

---

## Data Retention

### Add Retention Policy

```sql
-- Delete production logs older than 2 years
SELECT add_retention_policy(
    'production_logs',
    INTERVAL '2 years'
);

-- Delete sensor data older than 90 days
SELECT add_retention_policy(
    'machine_sensor_data',
    INTERVAL '90 days'
);

-- Delete downtime logs older than 1 year
SELECT add_retention_policy(
    'downtime_logs',
    INTERVAL '1 year'
);
```

**Note**: Old data is automatically deleted. This runs as a background job.

### Remove Retention Policy

```sql
-- Remove retention policy
SELECT remove_retention_policy('production_logs');
```

### Manual Data Deletion

```sql
-- Manually drop old chunks
SELECT drop_chunks(
    'production_logs',
    older_than => INTERVAL '3 years'
);
```

---

## Continuous Aggregates

### What are Continuous Aggregates?

Continuous aggregates are materialized views that automatically update as new data arrives. Perfect for dashboards and reports.

### Create Continuous Aggregate

```sql
-- Daily OEE summary (auto-updates)
CREATE MATERIALIZED VIEW daily_oee_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', logged_at) as day,
    work_order_id,
    SUM(quantity_produced) as total_qty,
    SUM(hours_spent) as total_hours,
    AVG(labor_cost) as avg_labor_cost
FROM production_logs
GROUP BY day, work_order_id;

-- Hourly machine sensor averages
CREATE MATERIALIZED VIEW hourly_sensor_averages
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', recorded_at) as hour,
    machine_id,
    AVG(temperature) as avg_temperature,
    AVG(vibration) as avg_vibration,
    MAX(temperature) as max_temperature
FROM machine_sensor_data
GROUP BY hour, machine_id;

-- Daily inventory levels
CREATE MATERIALIZED VIEW daily_inventory_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', updated_at) as day,
    material_id,
    AVG(quantity) as avg_quantity,
    MIN(quantity) as min_quantity,
    MAX(quantity) as max_quantity
FROM material_inventory_history
GROUP BY day, material_id;
```

### Add Refresh Policy

```sql
-- Refresh every hour
SELECT add_continuous_aggregate_policy(
    'daily_oee_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Refresh every 15 minutes
SELECT add_continuous_aggregate_policy(
    'hourly_sensor_averages',
    start_offset => INTERVAL '1 week',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes'
);
```

**Parameters:**
- `start_offset`: How far back to refresh (older data not refreshed)
- `end_offset`: Buffer from current time (avoid incomplete data)
- `schedule_interval`: How often to refresh

### Query Continuous Aggregate

```sql
-- Query like a normal table (fast!)
SELECT * FROM daily_oee_summary
WHERE day >= NOW() - INTERVAL '30 days'
ORDER BY day DESC;

-- Join with other tables
SELECT
    dos.day,
    wo.work_order_number,
    dos.total_qty,
    dos.total_hours
FROM daily_oee_summary dos
JOIN work_orders wo ON dos.work_order_id = wo.id
WHERE dos.day >= NOW() - INTERVAL '7 days'
ORDER BY dos.day DESC;
```

### Manual Refresh

```sql
-- Manually refresh continuous aggregate
CALL refresh_continuous_aggregate('daily_oee_summary', NULL, NULL);

-- Refresh specific time range
CALL refresh_continuous_aggregate(
    'daily_oee_summary',
    '2025-01-01'::timestamptz,
    '2025-01-31'::timestamptz
);
```

### Drop Continuous Aggregate

```sql
-- Drop continuous aggregate
DROP MATERIALIZED VIEW daily_oee_summary;
```

---

## Queries

### time_bucket() - Group by Time Intervals

```sql
-- Daily production totals
SELECT
    time_bucket('1 day', logged_at) as day,
    SUM(quantity_produced) as total_qty
FROM production_logs
WHERE logged_at >= NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day DESC;

-- Hourly production
SELECT
    time_bucket('1 hour', logged_at) as hour,
    SUM(quantity_produced) as total_qty
FROM production_logs
WHERE logged_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;

-- 15-minute intervals
SELECT
    time_bucket('15 minutes', recorded_at) as interval,
    AVG(temperature) as avg_temp
FROM machine_sensor_data
WHERE recorded_at >= NOW() - INTERVAL '4 hours'
GROUP BY interval
ORDER BY interval DESC;
```

### first() and last() - Get First/Last Values

```sql
-- First and last reading per hour
SELECT
    time_bucket('1 hour', recorded_at) as hour,
    machine_id,
    first(temperature, recorded_at) as first_temp,
    last(temperature, recorded_at) as last_temp
FROM machine_sensor_data
WHERE recorded_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour, machine_id
ORDER BY hour DESC;
```

### Time-Range Queries (Optimized)

```sql
-- Last 7 days (uses chunks efficiently)
SELECT * FROM production_logs
WHERE logged_at >= NOW() - INTERVAL '7 days'
ORDER BY logged_at DESC;

-- Specific date range
SELECT * FROM production_logs
WHERE logged_at BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY logged_at DESC;
```

---

## Python Integration

### Query Hypertable

```python
from sqlalchemy import text
from datetime import datetime, timedelta

def get_production_last_7_days(db: Session):
    """Get production logs for last 7 days"""
    results = db.execute(text("""
        SELECT
            logged_at,
            work_order_id,
            quantity_produced,
            hours_spent
        FROM production_logs
        WHERE logged_at >= NOW() - INTERVAL '7 days'
        ORDER BY logged_at DESC
    """))

    return [dict(row) for row in results]
```

### Query Continuous Aggregate

```python
def get_daily_oee_summary(db: Session, days: int = 30):
    """Get daily OEE summary"""
    results = db.execute(text("""
        SELECT
            day,
            work_order_id,
            total_qty,
            total_hours,
            avg_labor_cost
        FROM daily_oee_summary
        WHERE day >= NOW() - INTERVAL ':days days'
        ORDER BY day DESC
    """), {"days": days})

    return [dict(row) for row in results]
```

### Insert Time-Series Data

```python
from datetime import datetime

def log_production(
    db: Session,
    work_order_id: int,
    user_id: int,
    quantity_produced: int,
    hours_spent: float,
    labor_cost: float
):
    """Insert production log"""
    db.execute(text("""
        INSERT INTO production_logs (
            work_order_id,
            user_id,
            quantity_produced,
            hours_spent,
            labor_cost,
            logged_at
        ) VALUES (
            :work_order_id,
            :user_id,
            :quantity_produced,
            :hours_spent,
            :labor_cost,
            NOW()
        )
    """), {
        "work_order_id": work_order_id,
        "user_id": user_id,
        "quantity_produced": quantity_produced,
        "hours_spent": hours_spent,
        "labor_cost": labor_cost
    })

    db.commit()
```

---

## Monitoring

### Hypertable Size

```sql
-- Size of hypertable
SELECT
    hypertable_name,
    pg_size_pretty(hypertable_size(hypertable_name::regclass)) as size,
    pg_size_pretty(
        hypertable_size(hypertable_name::regclass) -
        total_compressed_size
    ) as uncompressed_size,
    pg_size_pretty(total_compressed_size) as compressed_size
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'production_logs';
```

### Chunk Information

```sql
-- List chunks with sizes
SELECT
    chunk_name,
    range_start,
    range_end,
    pg_size_pretty(total_bytes) as size,
    is_compressed
FROM timescaledb_information.chunks
WHERE hypertable_name = 'production_logs'
ORDER BY range_start DESC
LIMIT 10;
```

### Compression Stats

```sql
-- Overall compression stats
SELECT
    hypertable_name,
    COUNT(*) as num_chunks,
    SUM(CASE WHEN is_compressed THEN 1 ELSE 0 END) as compressed_chunks,
    pg_size_pretty(SUM(before_compression_total_bytes)) as before_size,
    pg_size_pretty(SUM(after_compression_total_bytes)) as after_size,
    ROUND(
        100 - (
            SUM(after_compression_total_bytes)::numeric /
            NULLIF(SUM(before_compression_total_bytes), 0) * 100
        ),
        2
    ) as compression_ratio_percent
FROM timescaledb_information.compressed_chunk_stats
GROUP BY hypertable_name;
```

### Background Jobs

```sql
-- Check background jobs (compression, retention, continuous aggregates)
SELECT
    job_id,
    application_name,
    schedule_interval,
    retry_period,
    next_start,
    last_finish
FROM timescaledb_information.jobs
ORDER BY next_start;
```

---

## Troubleshooting

### Compression Not Working

**Diagnosis:**
```sql
-- Check compression policy
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_compression'
  AND hypertable_name = 'production_logs';

-- Check if any chunks are compressed
SELECT COUNT(*) as compressed_chunks
FROM timescaledb_information.chunks
WHERE hypertable_name = 'production_logs'
  AND is_compressed = TRUE;
```

**Solution:**
```sql
-- Manually compress chunks
SELECT compress_chunk(i.show_chunks)
FROM show_chunks('production_logs') i
WHERE i.range_end < NOW() - INTERVAL '7 days';

-- Check compression stats
SELECT * FROM timescaledb_information.compressed_chunk_stats
WHERE hypertable_name = 'production_logs';
```

---

### Slow Queries on Hypertable

**Diagnosis:**
```sql
-- Explain query
EXPLAIN ANALYZE
SELECT * FROM production_logs
WHERE work_order_id = 123
  AND logged_at >= NOW() - INTERVAL '30 days';
```

**Solution:**
```sql
-- Add indexes on commonly queried columns
CREATE INDEX idx_production_logs_wo_time
ON production_logs (work_order_id, logged_at DESC);

-- Reorder chunks for better query performance
SELECT reorder_chunk(
    chunk => '_timescaledb_internal._hyper_1_1_chunk',
    index => 'idx_production_logs_wo_time'
);
```

---

### Continuous Aggregate Not Updating

**Diagnosis:**
```sql
-- Check continuous aggregate policy
SELECT * FROM timescaledb_information.jobs
WHERE application_name LIKE '%daily_oee_summary%';

-- Check last refresh time
SELECT
    view_name,
    materialization_hypertable_name,
    completed_threshold,
    invalidation_threshold
FROM timescaledb_information.continuous_aggregates
WHERE view_name = 'daily_oee_summary';
```

**Solution:**
```sql
-- Manually refresh
CALL refresh_continuous_aggregate('daily_oee_summary', NULL, NULL);

-- Or update refresh policy
SELECT remove_continuous_aggregate_policy('daily_oee_summary');
SELECT add_continuous_aggregate_policy(
    'daily_oee_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

---

### Out of Disk Space

**Diagnosis:**
```sql
-- Check table sizes
SELECT
    hypertable_name,
    pg_size_pretty(hypertable_size(hypertable_name::regclass)) as size
FROM timescaledb_information.hypertables
ORDER BY hypertable_size(hypertable_name::regclass) DESC;
```

**Solution:**
```sql
-- Add retention policy (delete old data)
SELECT add_retention_policy('production_logs', INTERVAL '1 year');

-- Add compression (reduce size)
ALTER TABLE production_logs
SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'work_order_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_compression_policy('production_logs', INTERVAL '7 days');

-- Manually drop old chunks
SELECT drop_chunks('production_logs', older_than => INTERVAL '2 years');
```

---

## Best Practices

1. **Choose appropriate chunk_time_interval**: Match to data volume
2. **Enable compression**: 75% storage savings with minimal performance impact
3. **Use continuous aggregates**: Pre-compute common queries
4. **Add retention policies**: Automatically delete old data
5. **Index strategically**: Add indexes on frequently queried columns
6. **Use time_bucket()**: Group time-series data efficiently
7. **Monitor chunk sizes**: Keep chunks between 100MB-1GB for optimal performance

---

## See Also

- [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md) - Installation and architecture
- [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) - Message queue operations
- [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md) - Schedule maintenance jobs
- [TimescaleDB Documentation](https://docs.timescale.com/) - Official documentation
