# PostgreSQL Extensions Documentation

**Purpose**: Complete documentation for PostgreSQL extensions used in Unison ERP
**Last Updated**: 2025-11-10

---

## Quick Links

- **New to extensions?** Start with [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md)
- **Python developer?** See [/backend/app/core/EXTENSIONS_PYTHON_API.md](../../backend/app/core/EXTENSIONS_PYTHON_API.md)
- **Need quick reference?** Check [/backend/app/core/EXTENSIONS_QUICKREF.md](../../backend/app/core/EXTENSIONS_QUICKREF.md)
- **Migrating from Celery/Redis?** Read [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

---

## Documentation Structure

### Overview & Installation

**[EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md)** - Start here!
- Why PostgreSQL extensions?
- Architecture decision & cost savings
- Installation (Docker + manual)
- Verification methods
- pg_duckdb analytics
- Performance tuning
- Troubleshooting

---

### Extension Guides (Deep Dives)

#### [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) - Message Queue
**Purpose**: Async job processing (replaces Celery + RabbitMQ)
**Performance**: 30,000 msgs/sec

Topics covered:
- Queue management (create, list, drop)
- Sending messages (single, batch, delayed)
- Reading messages (polling, visibility timeout)
- Python integration (producer/consumer)
- FastAPI worker implementation
- Dead letter queue handling
- Monitoring & troubleshooting

**Use cases**: SAP sync, barcode generation, email notifications

---

#### [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md) - Job Scheduler
**Purpose**: Scheduled tasks (replaces Celery Beat)
**Performance**: Runs inside PostgreSQL

Topics covered:
- Cron syntax reference
- Scheduling jobs (SQL functions, Python integration)
- Managing jobs (enable/disable, unschedule)
- Job history & monitoring
- Common use cases (OEE, inventory alerts, PM work orders)
- Troubleshooting failed jobs

**Use cases**: Daily reports, cache cleanup, data retention, PM scheduling

---

#### [PG_SEARCH_GUIDE.md](./PG_SEARCH_GUIDE.md) - Full-Text Search
**Purpose**: BM25 search (replaces Elasticsearch)
**Performance**: 20x faster than PostgreSQL tsvector

Topics covered:
- Creating BM25 indexes
- Search queries (basic, fuzzy, phrase, boolean)
- Python integration & FastAPI endpoints
- Advanced features (facets, boosting, highlighting)
- Performance optimization
- Index management

**Use cases**: Material search, work order search, NCR search, global search

---

#### [TIMESCALEDB_GUIDE.md](./TIMESCALEDB_GUIDE.md) - Time-Series
**Purpose**: Optimize time-series data (replaces InfluxDB)
**Performance**: 75% storage reduction

Topics covered:
- Hypertables (automatic partitioning)
- Compression (75% storage savings)
- Data retention policies
- Continuous aggregates (real-time materialized views)
- Time-series queries (time_bucket, first, last)
- Python integration
- Monitoring & troubleshooting

**Use cases**: Production logs, sensor data, OEE metrics, downtime tracking

---

### Migration & Advanced Topics

#### [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
**Purpose**: Step-by-step migration from traditional stack

Topics covered:
- Phase 1: Install extensions
- Phase 2: Migrate Celery → PGMQ
- Phase 3: Migrate Redis cache → UNLOGGED tables
- Phase 4: Migrate Celery Beat → pg_cron
- Phase 5: Add search & analytics
- Rollback strategies
- Validation & testing

---

## Python API Documentation

### [/backend/app/core/EXTENSIONS_PYTHON_API.md](../../backend/app/core/EXTENSIONS_PYTHON_API.md)
Documents the `extensions.py` Python module for verifying extensions.

**API Functions**:
- `verify_extensions_installed(conn)` - Check if all extensions installed
- `get_extension_versions(conn)` - Get version info
- `get_missing_extensions(conn)` - Identify missing extensions
- `verify_extensions_with_report(conn)` - Detailed report

**Use cases**: Application startup, health checks, deployment validation

---

### [/backend/app/core/EXTENSIONS_QUICKREF.md](../../backend/app/core/EXTENSIONS_QUICKREF.md)
One-page cheat sheet with:
- Quick installation commands
- Python API examples
- File structure reference
- CLI commands
- Common troubleshooting

---

## Architecture Overview

### Extensions Summary

| Extension | Purpose | Replaces | Savings |
|-----------|---------|----------|---------|
| **pgmq** | Message queue (30K msgs/sec) | Celery + RabbitMQ | -2 services |
| **pg_cron** | Job scheduler | Celery Beat | -1 service |
| **pg_search** | BM25 full-text search | Elasticsearch | $800/mo |
| **timescaledb** | Time-series optimization | InfluxDB | -1 service |
| **pg_duckdb** | Analytics acceleration | Data warehouse | -1 service |

**Total Impact**:
- **-5 services** (8-10 containers → 3-4)
- **$1,200-1,500/month** cost savings
- **Simpler operations** (single database to manage)

---

## Common Tasks

### Installation
```bash
# Docker (recommended)
docker-compose up -d postgres

# Check status
cd backend
python3 scripts/check_extensions.py
```
👉 See [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md#installation)

---

### Queue a Background Job
```python
from pgmq import PGMQueue

queue = PGMQueue(database_url)
msg_id = queue.send('background_jobs', {
    'job_type': 'sap_sync',
    'entity_id': 123
})
```
👉 See [PGMQ_GUIDE.md](./PGMQ_GUIDE.md#python-integration)

---

### Schedule a Daily Job
```sql
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);
```
👉 See [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md#scheduling-jobs)

---

### Search Materials
```sql
SELECT * FROM materials.search(
    query => 'steel bearing',
    filter => 'is_active = true',
    limit_rows => 20
) ORDER BY score DESC;
```
👉 See [PG_SEARCH_GUIDE.md](./PG_SEARCH_GUIDE.md#search-queries)

---

### Create Time-Series Table
```sql
SELECT create_hypertable(
    'production_logs',
    'logged_at',
    chunk_time_interval => INTERVAL '1 month'
);
```
👉 See [TIMESCALEDB_GUIDE.md](./TIMESCALEDB_GUIDE.md#hypertables)

---

## Troubleshooting

### Extension Not Available
```bash
# Check available extensions
python3 scripts/check_extensions.py -a

# Use Tembo PostgreSQL image
docker run -d -p 5432:5432 quay.io/tembo/standard-cnpg:15.3.0-1-1c1ba53
```
👉 See [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md#troubleshooting)

---

### Jobs Not Running
```sql
-- Check pg_cron configuration
SHOW shared_preload_libraries;  -- Should include 'pg_cron'
SHOW cron.database_name;        -- Should be 'unison_erp'

-- Check job status
SELECT * FROM cron.job WHERE active = TRUE;
```
👉 See [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md#troubleshooting)

---

### Queue Growing Too Fast
```sql
-- Check queue metrics
SELECT * FROM pgmq.metrics('background_jobs');

-- Check dead letter queue
SELECT COUNT(*) FROM pgmq.q_dlq;
```
👉 See [PGMQ_GUIDE.md](./PGMQ_GUIDE.md#troubleshooting)

---

## External Resources

- [PGMQ Official Docs](https://github.com/tembo-io/pgmq)
- [pg_cron Official Docs](https://github.com/citusdata/pg_cron)
- [ParadeDB (pg_search) Docs](https://docs.paradedb.com/)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [DuckDB PostgreSQL Extension](https://duckdb.org/docs/extensions/postgres)
- [Tembo PostgreSQL Image](https://tembo.io/)

---

## Quick Decision Matrix

**Choose the right guide for your task:**

| Task | Guide |
|------|-------|
| Install extensions | [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md) |
| Queue background job | [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) |
| Schedule periodic task | [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md) |
| Implement search | [PG_SEARCH_GUIDE.md](./PG_SEARCH_GUIDE.md) |
| Optimize time-series data | [TIMESCALEDB_GUIDE.md](./TIMESCALEDB_GUIDE.md) |
| Migrate from Celery/Redis | [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) |
| Python API reference | [EXTENSIONS_PYTHON_API.md](../../backend/app/core/EXTENSIONS_PYTHON_API.md) |
| Quick reference | [EXTENSIONS_QUICKREF.md](../../backend/app/core/EXTENSIONS_QUICKREF.md) |

---

**Questions?** Check the troubleshooting sections in each guide, or search for errors in the PostgreSQL logs.
