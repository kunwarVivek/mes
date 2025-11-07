# PostgreSQL Extensions - Comprehensive Guide

**Version**: 1.0
**Date**: 2025-11-07
**Purpose**: Technical guide for all PostgreSQL extensions used in Unison ERP

---

## Table of Contents
1. [Installation](#installation)
2. [PGMQ (Message Queue)](#pgmq-message-queue)
3. [pg_cron (Scheduled Tasks)](#pg_cron-scheduled-tasks)
4. [pg_search (Full-Text Search)](#pg_search-full-text-search)
5. [pg_duckdb (Analytics Engine)](#pg_duckdb-analytics-engine)
6. [timescaledb (Time-Series)](#timescaledb-time-series)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Docker Setup (Recommended)

Use Tembo PostgreSQL image which includes all extensions:

```yaml
# docker-compose.yml
services:
  postgres:
    image: tembo/tembo-pg-slim:latest
    environment:
      POSTGRES_USER: unison
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: unison_erp
    command: >
      postgres
      -c shared_preload_libraries='pg_cron,timescaledb,pgmq'
      -c cron.database_name='unison_erp'
      -c shared_buffers='4GB'
      -c effective_cache_size='12GB'
      -c maintenance_work_mem='1GB'
      -c max_worker_processes='8'
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docs/03-postgresql/init-extensions.sql:/docker-entrypoint-initdb.d/01-extensions.sql
```

### Manual Installation (Ubuntu/Debian)

```bash
# Install PostgreSQL 15
sudo apt-get install postgresql-15 postgresql-contrib-15

# Install extensions
sudo apt-get install postgresql-15-pgmq
sudo apt-get install postgresql-15-cron
sudo apt-get install postgresql-15-pg-search
sudo apt-get install postgresql-15-pg-duckdb
sudo apt-get install timescaledb-2-postgresql-15

# Enable extensions in postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add:
shared_preload_libraries = 'pg_cron,timescaledb,pgmq'
cron.database_name = 'unison_erp'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Enable Extensions in Database

```sql
-- Connect to database
\c unison_erp

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pgmq;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_search;
CREATE EXTENSION IF NOT EXISTS pg_duckdb;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify installation
SELECT * FROM pg_available_extensions
WHERE name IN ('pgmq', 'pg_cron', 'pg_search', 'pg_duckdb', 'timescaledb');
```

---

## PGMQ (Message Queue)

### Overview
High-performance message queue built on PostgreSQL. 30,000 msgs/sec throughput, ACID transactions, built-in retry logic.

### Core Concepts
- **Queue**: Named channel for messages (e.g., `background_jobs`)
- **Message**: JSONB payload with metadata
- **Visibility Timeout (VT)**: Lock duration for message processing
- **Dead Letter Queue (DLQ)**: Failed messages after max retries

### Create Queue

```sql
-- Create queue
SELECT pgmq.create('background_jobs');

-- Create queue with partitioning (for high volume)
SELECT pgmq.create_partitioned('high_volume_jobs',
    partition_interval => '1 day',
    retention_interval => '7 days'
);

-- List all queues
SELECT * FROM pgmq.list_queues();
```

### Send Messages (Enqueue)

```sql
-- Send single message
SELECT pgmq.send(
    'background_jobs',
    '{"job_type": "sap_sync", "entity": "work_order", "entity_id": 123}'::jsonb
);

-- Send with delay (5 minutes)
SELECT pgmq.send(
    'background_jobs',
    '{"job_type": "email_notification", "to": "user@example.com"}'::jsonb,
    delay_seconds => 300
);

-- Send batch (more efficient)
SELECT pgmq.send_batch(
    'background_jobs',
    ARRAY[
        '{"job_type": "barcode_generation", "wo_id": 1}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 2}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 3}'::jsonb
    ]
);
```

### Read Messages (Dequeue)

```sql
-- Read one message (30s visibility timeout)
SELECT * FROM pgmq.read('background_jobs', vt => 30, qty => 1);

-- Returns:
-- msg_id | read_ct | enqueued_at | vt | message
-- 1      | 1       | 2025-11-07  | 30 | {"job_type": "sap_sync", ...}

-- Read multiple messages
SELECT * FROM pgmq.read('background_jobs', vt => 30, qty => 10);

-- Poll (wait for message, max 5 seconds)
SELECT * FROM pgmq.read_with_poll(
    'background_jobs',
    vt => 30,
    qty => 1,
    max_poll_seconds => 5
);
```

### Delete Messages (Acknowledge)

```sql
-- Delete single message after successful processing
SELECT pgmq.delete('background_jobs', msg_id => 1);

-- Archive message (keep history)
SELECT pgmq.archive('background_jobs', msg_id => 1);
```

### Python Integration

```python
from pgmq import PGMQueue
from sqlalchemy import create_engine

# Initialize queue
queue = PGMQueue(database_url="postgresql://user:pass@localhost/unison_erp")

# Producer: Send job
def enqueue_sap_sync(work_order_id: int):
    msg_id = queue.send(
        'background_jobs',
        {
            'job_type': 'sap_sync',
            'entity': 'work_order',
            'entity_id': work_order_id
        }
    )
    return msg_id

# Consumer: Process jobs
def worker():
    while True:
        # Read message with 30s visibility timeout
        message = queue.read('background_jobs', vt=30, qty=1)

        if not message:
            time.sleep(1)  # No messages, wait 1 second
            continue

        msg = message[0]
        try:
            # Process job
            if msg['message']['job_type'] == 'sap_sync':
                sync_to_sap(msg['message']['entity_id'])

            # Delete message after success
            queue.delete('background_jobs', msg['msg_id'])

        except Exception as e:
            # Message will become visible again after VT expires
            # Implement retry logic with max attempts
            if msg['read_ct'] >= 3:  # Max 3 retries
                # Move to dead letter queue
                queue.send('dlq', msg['message'])
                queue.delete('background_jobs', msg['msg_id'])
            # Else: let message become visible again (automatic retry)
```

### FastAPI Background Worker

```python
# backend/app/workers/pgmq_worker.py
from pgmq import PGMQueue
import asyncio
from app.infrastructure.sap.sap_adapter import SAPAdapter

class BackgroundWorker:
    def __init__(self, db_url: str):
        self.queue = PGMQueue(db_url)
        self.sap = SAPAdapter()

    async def process_jobs(self):
        """Main worker loop"""
        while True:
            messages = self.queue.read('background_jobs', vt=60, qty=5)

            if not messages:
                await asyncio.sleep(1)
                continue

            for msg in messages:
                await self.process_job(msg)

    async def process_job(self, msg: dict):
        try:
            job = msg['message']

            if job['job_type'] == 'sap_sync':
                await self.sap.sync_entity(
                    entity_type=job['entity'],
                    entity_id=job['entity_id']
                )

            elif job['job_type'] == 'barcode_generation':
                await self.generate_barcode(job['wo_id'])

            elif job['job_type'] == 'email_notification':
                await self.send_email(job['to'], job['subject'], job['body'])

            # Success: delete message
            self.queue.delete('background_jobs', msg['msg_id'])

        except Exception as e:
            # Retry logic
            if msg['read_ct'] >= 3:
                # Max retries reached: move to DLQ
                self.queue.send('dlq', msg['message'])
                self.queue.delete('background_jobs', msg['msg_id'])
            # Else: automatic retry (message becomes visible after VT)

# Run worker
if __name__ == "__main__":
    worker = BackgroundWorker(os.getenv("DATABASE_URL"))
    asyncio.run(worker.process_jobs())
```

### Monitoring Queues

```sql
-- Queue metrics
SELECT
    queue_name,
    queue_length,
    newest_msg_age_sec,
    oldest_msg_age_sec,
    total_messages
FROM pgmq.metrics('background_jobs');

-- Dead letter queue check
SELECT * FROM pgmq.read('dlq', vt => 300, qty => 100);
```

---

## pg_cron (Scheduled Tasks)

### Overview
Cron-like scheduler that runs inside PostgreSQL. No separate service needed.

### Schedule Jobs

```sql
-- Daily OEE calculation at 6:00 AM
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);

-- Every 5 minutes: inventory threshold alerts
SELECT cron.schedule(
    'inventory-alerts',
    '*/5 * * * *',
    $$SELECT check_inventory_thresholds()$$
);

-- Every hour: cache cleanup
SELECT cron.schedule(
    'cache-cleanup',
    '0 * * * *',
    $$DELETE FROM cache WHERE expires_at < NOW()$$
);

-- Auto-generate PM work orders (daily at 6 AM)
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

### Manage Jobs

```sql
-- List all scheduled jobs
SELECT
    jobid,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active
FROM cron.job;

-- Unschedule job
SELECT cron.unschedule('daily-oee-calculation');

-- Disable job temporarily
UPDATE cron.job SET active = FALSE WHERE jobname = 'inventory-alerts';

-- Enable job
UPDATE cron.job SET active = TRUE WHERE jobname = 'inventory-alerts';
```

### View Job History

```sql
-- Recent job runs
SELECT
    jobid,
    runid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
WHERE start_time >= NOW() - INTERVAL '24 hours'
ORDER BY start_time DESC;

-- Failed jobs in last 24 hours
SELECT * FROM cron.job_run_details
WHERE status = 'failed'
  AND start_time >= NOW() - INTERVAL '24 hours';
```

### Python Integration (Schedule from Code)

```python
from sqlalchemy import text

def schedule_daily_report(db: Session, report_type: str, schedule: str):
    """Schedule a daily report generation"""
    job_name = f"daily-{report_type}-report"

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
```

---

## pg_search (Full-Text Search)

### Overview
Full-text search with BM25 ranking (same algorithm as Elasticsearch). 20x faster than PostgreSQL tsvector.

### Create Search Index

```sql
-- Create BM25 index on materials
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number, tags}',
    numeric_fields => '{unit_cost, reorder_point}',
    boolean_fields => '{is_active}'
);

-- Create index on work_orders
SELECT paradedb.create_bm25(
    table_name => 'work_orders',
    index_name => 'work_orders_search_idx',
    key_field => 'id',
    text_fields => '{work_order_number, project_name, customer_order_reference, notes}',
    numeric_fields => '{quantity_ordered, quantity_completed}'
);

-- Create index on ncr_reports
SELECT paradedb.create_bm25(
    table_name => 'ncr_reports',
    index_name => 'ncr_search_idx',
    key_field => 'id',
    text_fields => '{ncr_number, problem_description, root_cause, corrective_action, tags}'
);
```

### Search Queries

```sql
-- Basic search
SELECT * FROM materials.search(
    query => 'steel bearing',
    limit_rows => 10
) ORDER BY score DESC;

-- Search with filters
SELECT * FROM materials.search(
    query => 'bearing',
    filter => 'is_active = true AND unit_cost < 100',
    limit_rows => 20
) ORDER BY score DESC;

-- Fuzzy search (typo tolerance)
SELECT * FROM materials.search(
    query => 'bering~1',  -- Allows 1 character difference
    limit_rows => 10
) ORDER BY score DESC;

-- Phrase search
SELECT * FROM work_orders.search(
    query => '"customer order" AND project',
    limit_rows => 20
) ORDER BY score DESC;

-- Faceted search (aggregations)
SELECT
    category,
    COUNT(*) as count
FROM materials.search(
    query => 'bearing',
    facets => 'category'
)
GROUP BY category;
```

### Python Integration

```python
from sqlalchemy import text

def search_materials(db: Session, query: str, limit: int = 20):
    """Search materials with BM25 ranking"""
    results = db.execute(text("""
        SELECT
            m.id,
            m.part_number,
            m.name,
            m.description,
            m.unit_cost,
            s.score
        FROM materials.search(
            query => :query,
            filter => 'is_active = true',
            limit_rows => :limit
        ) s
        JOIN materials m ON m.id = s.id
        ORDER BY s.score DESC
    """), {"query": query, "limit": limit})

    return [dict(row) for row in results]

# Usage
materials = search_materials(db, "steel bearing", limit=10)
```

---

## pg_duckdb (Analytics Engine)

### Overview
Columnar analytics engine embedded in PostgreSQL. 10-1500x faster for OLAP queries.

### Enable for Analytics Queries

```sql
-- Use DuckDB for analytics query
SELECT
    date_trunc('day', logged_at) as day,
    work_order_id,
    SUM(quantity_produced) as total_qty,
    SUM(hours_spent) as total_hours,
    AVG(labor_cost) as avg_labor_cost
FROM duckdb.query('
    SELECT * FROM production_logs
    WHERE logged_at >= NOW() - INTERVAL ''90 days''
')
GROUP BY day, work_order_id
ORDER BY day DESC;

-- Complex aggregation (10-100x faster)
SELECT
    m.name as material,
    SUM(pl.quantity_produced * m.unit_cost) as total_cost,
    COUNT(DISTINCT pl.work_order_id) as num_work_orders
FROM duckdb.query('
    SELECT * FROM production_logs pl
    JOIN work_orders wo ON pl.work_order_id = wo.id
    JOIN materials m ON wo.material_id = m.id
    WHERE pl.logged_at >= NOW() - INTERVAL ''6 months''
')
GROUP BY m.name
ORDER BY total_cost DESC
LIMIT 20;
```

### Window Functions (Optimized)

```sql
-- Running totals (fast with pg_duckdb)
SELECT
    logged_at,
    quantity_produced,
    SUM(quantity_produced) OVER (
        PARTITION BY work_order_id
        ORDER BY logged_at
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_qty
FROM duckdb.query('SELECT * FROM production_logs')
ORDER BY work_order_id, logged_at;
```

---

## timescaledb (Time-Series)

### Overview
Optimizes time-series data with automatic partitioning and compression. 75% storage savings.

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
```

### Add Compression (75% Storage Savings)

```sql
-- Enable compression
ALTER TABLE production_logs
SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'work_order_id, user_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy(
    'production_logs',
    INTERVAL '7 days'
);

-- Check compression stats
SELECT
    chunk_name,
    before_compression_total_bytes,
    after_compression_total_bytes,
    100 - (after_compression_total_bytes::numeric / before_compression_total_bytes * 100) as compression_ratio
FROM timescaledb_information.compressed_chunk_stats
ORDER BY chunk_name;
```

### Data Retention (Auto-Delete Old Data)

```sql
-- Delete data older than 2 years
SELECT add_retention_policy(
    'production_logs',
    INTERVAL '2 years'
);

-- Delete sensor data older than 90 days
SELECT add_retention_policy(
    'machine_sensor_data',
    INTERVAL '90 days'
);
```

### Continuous Aggregates (Real-Time Materialized Views)

```sql
-- Create continuous aggregate for daily OEE
CREATE MATERIALIZED VIEW daily_oee_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', logged_at) as day,
    work_order_id,
    SUM(quantity_produced) as total_qty,
    SUM(hours_spent) as total_hours
FROM production_logs
GROUP BY day, work_order_id;

-- Add refresh policy (refresh every hour)
SELECT add_continuous_aggregate_policy(
    'daily_oee_summary',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Query continuous aggregate (fast!)
SELECT * FROM daily_oee_summary
WHERE day >= NOW() - INTERVAL '30 days'
ORDER BY day DESC;
```

---

## Performance Tuning

### PostgreSQL Configuration

```ini
# postgresql.conf

# Extensions
shared_preload_libraries = 'pg_cron,timescaledb,pgmq'
cron.database_name = 'unison_erp'

# Memory
shared_buffers = 4GB               # 25% of RAM
effective_cache_size = 12GB        # 75% of RAM
maintenance_work_mem = 1GB         # For indexes, vacuum
work_mem = 64MB                    # Per query

# Parallelism
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1             # For SSD
effective_io_concurrency = 200     # For SSD

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### PGMQ Optimization

```sql
-- Partition queue for high volume (1M+ msgs/day)
SELECT pgmq.create_partitioned(
    'high_volume_jobs',
    partition_interval => '1 day',
    retention_interval => '7 days'
);

-- Index for faster dequeue
CREATE INDEX idx_background_jobs_vt
ON pgmq.q_background_jobs (vt)
WHERE status = 'pending';
```

### pg_search Optimization

```sql
-- Rebuild index for better performance
SELECT paradedb.drop_bm25('materials_search_idx');
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}',
    -- Add custom BM25 parameters for tuning
    k1 => 1.2,  -- Term frequency saturation (default 1.2)
    b => 0.75   -- Length normalization (default 0.75)
);
```

---

## Troubleshooting

### PGMQ Issues

**Problem**: Messages not being processed
```sql
-- Check queue metrics
SELECT * FROM pgmq.metrics('background_jobs');

-- Check for stuck messages (visible but old)
SELECT * FROM pgmq.read('background_jobs', vt => 0, qty => 100)
WHERE enqueued_at < NOW() - INTERVAL '1 hour';

-- Reset visibility timeout (make messages available)
UPDATE pgmq.q_background_jobs
SET vt = NOW()
WHERE vt > NOW() + INTERVAL '5 minutes';
```

**Problem**: Queue growing too fast
```sql
-- Check DLQ for failed messages
SELECT COUNT(*) FROM pgmq.q_dlq;

-- Archive old processed messages
SELECT pgmq.archive('background_jobs', msg_id)
FROM pgmq.q_background_jobs_archive
WHERE enqueued_at < NOW() - INTERVAL '30 days';
```

### pg_cron Issues

**Problem**: Jobs not running
```sql
-- Check if pg_cron is loaded
SHOW shared_preload_libraries;  -- Should include 'pg_cron'

-- Check job status
SELECT * FROM cron.job WHERE active = TRUE;

-- Check recent failures
SELECT * FROM cron.job_run_details
WHERE status = 'failed'
ORDER BY start_time DESC
LIMIT 10;
```

**Problem**: Job running but erroring
```sql
-- Get error details
SELECT
    command,
    return_message,
    start_time
FROM cron.job_run_details
WHERE status = 'failed'
  AND jobid = 123;  -- Replace with your jobid

-- Test command manually
SELECT calculate_daily_oee();  -- Run the function directly
```

### timescaledb Issues

**Problem**: Compression not working
```sql
-- Check compression policy
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_compression';

-- Manually compress chunks
SELECT compress_chunk(i.show_chunks)
FROM show_chunks('production_logs') i
WHERE i.range_end < NOW() - INTERVAL '7 days';

-- Check compression stats
SELECT * FROM timescaledb_information.compressed_chunk_stats;
```

**Problem**: Slow queries on hypertable
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

**Last Updated**: 2025-11-07
**Maintained By**: Unison Engineering Team
