# PostgreSQL Extensions - Overview

**Version**: 1.0
**Last Updated**: 2025-11-10
**Purpose**: High-level overview, installation, and architecture decision

---

## Table of Contents

1. [Why PostgreSQL Extensions?](#why-postgresql-extensions)
2. [Extensions Overview](#extensions-overview)
3. [Architecture Decision](#architecture-decision)
4. [Installation](#installation)
5. [Verification](#verification)
6. [pg_duckdb (Analytics Engine)](#pg_duckdb-analytics-engine)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Why PostgreSQL Extensions?

Unison ERP uses PostgreSQL extensions to **eliminate external dependencies** and reduce infrastructure complexity.

### Traditional Stack vs PostgreSQL-Native

| Service | Traditional | PostgreSQL-Native | Savings |
|---------|-------------|-------------------|---------|
| **Message Queue** | RabbitMQ/Redis + Celery | **PGMQ** | -2 services |
| **Full-Text Search** | Elasticsearch | **pg_search** | -1 service, $800/mo |
| **Job Scheduler** | Celery Beat | **pg_cron** | -1 service |
| **Analytics** | Data warehouse | **pg_duckdb** | -1 service |
| **Time-Series** | InfluxDB/Prometheus | **timescaledb** | -1 service |
| **Total Containers** | 8-10 | 3-4 | **-5 services** |

**Cost Savings**: $1,200-1,500/month in infrastructure costs
**Operational Benefits**: Single database to backup, monitor, and scale

---

## Extensions Overview

### PGMQ (Message Queue)
- **Purpose**: High-performance async job processing
- **Performance**: 30,000 msgs/sec throughput
- **Features**: ACID transactions, visibility timeout, dead letter queue
- **Replaces**: Celery + RabbitMQ/Redis
- **Guide**: [PGMQ_GUIDE.md](./PGMQ_GUIDE.md)

### pg_cron (Job Scheduler)
- **Purpose**: Cron-like scheduled tasks inside PostgreSQL
- **Performance**: Runs inside database, no separate service
- **Features**: Standard cron syntax, job history, enable/disable
- **Replaces**: Celery Beat
- **Guide**: [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md)

### pg_search (Full-Text Search)
- **Purpose**: BM25 full-text search with relevance ranking
- **Performance**: 20x faster than PostgreSQL tsvector
- **Features**: Same algorithm as Elasticsearch, fuzzy search, facets
- **Replaces**: Elasticsearch
- **Guide**: [PG_SEARCH_GUIDE.md](./PG_SEARCH_GUIDE.md)

### timescaledb (Time-Series)
- **Purpose**: Optimize time-series data storage and queries
- **Performance**: 75% storage reduction via compression
- **Features**: Automatic partitioning, continuous aggregates, retention policies
- **Replaces**: InfluxDB, Prometheus
- **Guide**: [TIMESCALEDB_GUIDE.md](./TIMESCALEDB_GUIDE.md)

### pg_duckdb (Analytics Engine)
- **Purpose**: Columnar analytics for OLAP queries
- **Performance**: 10-1500x faster for analytical queries
- **Features**: Embedded DuckDB engine, window functions, aggregations
- **Replaces**: Data warehouse for analytics
- **Details**: [See below](#pg_duckdb-analytics-engine)

---

## Architecture Decision

### Why This Approach?

**1. Simplicity**: One database instead of 6+ services
- Single backup strategy
- Single monitoring system
- Single connection pool
- Fewer Docker containers

**2. Cost**: $1,200-1,500/month savings
- No Elasticsearch hosting ($800/mo)
- No Redis hosting ($100/mo)
- No RabbitMQ hosting ($100/mo)
- Reduced server costs

**3. Performance**: Extensions run **inside** PostgreSQL
- No network latency between services
- ACID transactions across queue + database
- Shared memory for caching
- Single connection pool

**4. Reliability**: PostgreSQL's maturity
- Battle-tested since 1996
- ACID compliance
- Replication and high availability
- Point-in-time recovery

### Trade-offs

**Pros:**
- Simpler infrastructure
- Lower operational cost
- Better ACID guarantees
- Easier to debug (single database)
- Faster local development

**Cons:**
- PostgreSQL becomes single point of failure (mitigated by replication)
- All extensions must support PostgreSQL version
- Slightly higher PostgreSQL resource usage

**Mitigation:**
- Use PostgreSQL replication for high availability
- Monitor PostgreSQL resources (CPU, memory, disk)
- Use connection pooling (PgBouncer)

---

## Installation

### Option 1: Docker Setup (Recommended)

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

volumes:
  postgres_data:
```

**Start the container:**

```bash
docker-compose up -d postgres
docker-compose logs -f postgres  # Wait for startup
```

---

### Option 2: Manual Installation (Ubuntu/Debian)

```bash
# Install PostgreSQL 15
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-contrib-15

# Install extensions
sudo apt-get install postgresql-15-pgmq
sudo apt-get install postgresql-15-cron
sudo apt-get install postgresql-15-pg-search
sudo apt-get install postgresql-15-pg-duckdb
sudo apt-get install timescaledb-2-postgresql-15

# Enable extensions in postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add the following lines:
shared_preload_libraries = 'pg_cron,timescaledb,pgmq'
cron.database_name = 'unison_erp'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

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

**Expected output:**

```
    name     | installed_version | comment
-------------+-------------------+----------------------------------
 pgmq        | 1.0.0             | Message queue for PostgreSQL
 pg_cron     | 1.5.2             | Job scheduler
 pg_search   | 0.3.4             | Full-text search with BM25
 pg_duckdb   | 0.1.0             | DuckDB analytics engine
 timescaledb | 2.11.0            | Time-series database
```

---

## Verification

### Using Python API

```python
from app.core.extensions import verify_extensions_with_report
from app.core.database import engine

with engine.connect() as conn:
    report = verify_extensions_with_report(conn)

    if report['all_installed']:
        print(f"✓ All {report['total_required']} extensions installed")
        print(f"  Versions: {report['versions']}")
    else:
        print(f"✗ Missing: {report['missing']}")
```

### Using CLI

```bash
# Check extension status
cd backend
python3 scripts/check_extensions.py

# Detailed output
python3 scripts/check_extensions.py -v

# List all available extensions
python3 scripts/check_extensions.py -a
```

### Using SQL

```sql
-- Check installed extensions
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('pgmq', 'pg_cron', 'pg_search', 'pg_duckdb', 'timescaledb')
ORDER BY extname;

-- Check available but not installed
SELECT name, default_version, comment
FROM pg_available_extensions
WHERE name IN ('pgmq', 'pg_cron', 'pg_search', 'pg_duckdb', 'timescaledb')
  AND name NOT IN (SELECT extname FROM pg_extension);
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

### Python Integration

```python
from sqlalchemy import text

def get_production_analytics(db: Session, days: int = 90):
    """Get production analytics using DuckDB acceleration"""
    results = db.execute(text("""
        SELECT
            date_trunc('day', logged_at) as day,
            work_order_id,
            SUM(quantity_produced) as total_qty,
            SUM(hours_spent) as total_hours
        FROM duckdb.query('
            SELECT * FROM production_logs
            WHERE logged_at >= NOW() - INTERVAL ''{days} days''
        ')
        GROUP BY day, work_order_id
        ORDER BY day DESC
    """), {"days": days})

    return [dict(row) for row in results]
```

---

## Performance Tuning

### PostgreSQL Configuration

```ini
# postgresql.conf

# Extensions
shared_preload_libraries = 'pg_cron,timescaledb,pgmq'
cron.database_name = 'unison_erp'

# Memory (for 16GB RAM server)
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

# Query planner (for SSD)
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### Memory Recommendations

| Total RAM | shared_buffers | effective_cache_size | maintenance_work_mem |
|-----------|----------------|---------------------|---------------------|
| 4GB       | 1GB            | 3GB                 | 256MB               |
| 8GB       | 2GB            | 6GB                 | 512MB               |
| 16GB      | 4GB            | 12GB                | 1GB                 |
| 32GB      | 8GB            | 24GB                | 2GB                 |

---

## Troubleshooting

### Extension Not Available

**Error:** `extension "pgmq" is not available`

**Diagnosis:**
```sql
-- Check available extensions
SELECT name, default_version, comment
FROM pg_available_extensions
WHERE name = 'pgmq';
```

**Solution:**
1. Use Tembo PostgreSQL Docker image (includes all extensions)
2. Or install extension manually:
   ```bash
   sudo apt-get install postgresql-15-pgmq
   sudo systemctl restart postgresql
   ```

---

### Extension Won't Load

**Error:** `could not access file "$libdir/pgmq"`

**Diagnosis:**
```sql
SHOW shared_preload_libraries;
```

**Solution:**
1. Add extension to `shared_preload_libraries` in `postgresql.conf`
2. Restart PostgreSQL (required for preload)
   ```bash
   sudo systemctl restart postgresql
   ```

---

### Permission Denied

**Error:** `must be superuser to create this extension`

**Diagnosis:**
```sql
-- Check your privileges
SELECT * FROM pg_roles WHERE rolname = current_user;
```

**Solution:**
```sql
-- Grant superuser (as postgres user)
ALTER USER unison WITH SUPERUSER;

-- Or create extension as postgres user, then revoke
SET ROLE postgres;
CREATE EXTENSION pgmq;
RESET ROLE;
```

---

### pg_cron Jobs Not Running

**Error:** Jobs scheduled but not executing

**Diagnosis:**
```sql
-- Check if pg_cron is loaded
SHOW shared_preload_libraries;  -- Should include 'pg_cron'

-- Check cron database setting
SHOW cron.database_name;  -- Should match your database name

-- Check job status
SELECT * FROM cron.job;

-- Check recent job runs
SELECT * FROM cron.job_run_details
ORDER BY start_time DESC LIMIT 10;
```

**Solution:**
1. Ensure `pg_cron` in `shared_preload_libraries`
2. Set `cron.database_name = 'unison_erp'` in `postgresql.conf`
3. Restart PostgreSQL
4. Verify jobs are active: `UPDATE cron.job SET active = TRUE WHERE active = FALSE;`

---

### Out of Memory Errors

**Error:** `out of memory` or slow queries

**Diagnosis:**
```sql
-- Check current settings
SHOW shared_buffers;
SHOW work_mem;
SHOW maintenance_work_mem;

-- Check database size
SELECT pg_size_pretty(pg_database_size('unison_erp'));

-- Check largest tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**Solution:**
1. Increase `shared_buffers` (25% of RAM)
2. Increase `effective_cache_size` (75% of RAM)
3. Adjust `work_mem` for complex queries
4. Add indexes for frequently queried columns
5. Use TimescaleDB compression for time-series data

---

### High CPU Usage

**Diagnosis:**
```sql
-- Find slow queries
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;

-- Check for missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
ORDER BY n_distinct DESC;
```

**Solution:**
1. Optimize slow queries (add indexes, rewrite)
2. Use `EXPLAIN ANALYZE` to identify bottlenecks
3. Consider using pg_duckdb for analytical queries
4. Enable query logging: `log_min_duration_statement = 1000`

---

## Next Steps

- **Message Queue**: [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) - Learn PGMQ queuing
- **Job Scheduling**: [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md) - Schedule periodic tasks
- **Full-Text Search**: [PG_SEARCH_GUIDE.md](./PG_SEARCH_GUIDE.md) - Implement search
- **Time-Series**: [TIMESCALEDB_GUIDE.md](./TIMESCALEDB_GUIDE.md) - Optimize time-series data
- **Migration**: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migrate from Celery/Redis

---

**For Python API documentation, see:**
- [/backend/app/core/EXTENSIONS_PYTHON_API.md](../../backend/app/core/EXTENSIONS_PYTHON_API.md)
- [/backend/app/core/EXTENSIONS_QUICKREF.md](../../backend/app/core/EXTENSIONS_QUICKREF.md)
