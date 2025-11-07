# Technology Stack - PostgreSQL-Native Architecture

**Version**: 2.0
**Date**: 2025-11-07
**Decision**: PostgreSQL-native stack (eliminated Redis, Celery, RabbitMQ, Elasticsearch)

---

## Table of Contents
1. [Architecture Decision](#architecture-decision)
2. [Backend Stack](#backend-stack)
3. [Frontend Stack](#frontend-stack)
4. [PostgreSQL Extensions](#postgresql-extensions)
5. [PostgreSQL Native Features](#postgresql-native-features)
6. [Infrastructure](#infrastructure)
7. [Performance Benchmarks](#performance-benchmarks)
8. [Migration Path](#migration-path)

---

## Architecture Decision

### Context
Building B2B SaaS Manufacturing ERP for MSME (Micro, Small, Medium Enterprises) with:
- **Job Volume**: 2-5 background jobs per customer (very low)
- **Cache Latency**: 1-5ms acceptable for dashboards
- **Team Expertise**: Minimal, startup team comfortable with PostgreSQL
- **Deployment**: Both on-premise and cloud
- **Scale**: 10-500 users per customer

### Decision: PostgreSQL-Only Stack

**Eliminated Services**:
- ❌ Redis (cache + message broker)
- ❌ Celery (task queue + worker)
- ❌ RabbitMQ (message queue)
- ❌ Elasticsearch (full-text search)

**Replaced With PostgreSQL Extensions**:
- ✅ **pgmq**: Message queue (30K msgs/sec)
- ✅ **pg_cron**: Scheduled tasks
- ✅ **pg_search (ParadeDB)**: Full-text search with BM25 ranking
- ✅ **pg_duckdb**: Analytics engine
- ✅ **timescaledb**: Time-series optimization

**Replaced With PostgreSQL Native Features**:
- ✅ **UNLOGGED tables**: High-speed cache (2x faster writes)
- ✅ **LISTEN/NOTIFY**: Pub/sub messaging
- ✅ **RLS (Row-Level Security)**: Multi-tenancy data isolation
- ✅ **SKIP LOCKED**: Concurrent queue processing

### Rationale

#### 1. Simplicity (Primary Driver)
- **Before**: 8-10 containers (Postgres, Redis, RabbitMQ, Celery Worker, Celery Beat, Backend, Frontend, MinIO, Nginx)
- **After**: 3-4 containers (Postgres, Backend, Frontend, MinIO)
- **Result**: 60% fewer containers, single database to backup/monitor/manage

#### 2. Cost Optimization
- **Infrastructure**: 60% fewer containers = 40-60% lower cloud costs
- **Operations**: Single service to monitor vs 4-5 separate services
- **Licensing**: No separate cache/queue services to license/support

#### 3. Performance (More Than Sufficient)
- **Queue**: PGMQ (30K msgs/sec) >> Celery (~100-500 jobs/hour) for MSME scale
- **Search**: pg_search BM25 ranking 20x faster than tsvector, sufficient for <100K records
- **Analytics**: pg_duckdb 10-1500x faster than materialized views
- **Cache**: UNLOGGED tables 1-2ms latency vs Redis <1ms - acceptable for dashboards

#### 4. Developer Experience
- **Single Skill**: PostgreSQL >> Redis + Celery + RabbitMQ + Elasticsearch
- **Debugging**: All data in one place, standard SQL queries
- **Transactions**: ACID across all operations (queue, cache, data)
- **Tooling**: Standard PostgreSQL tools (pgAdmin, psql, DataGrip)

#### 5. Operational Simplicity
- **Backup**: Single database dump vs separate Redis + queue backups
- **Monitoring**: One connection pool vs multiple service health checks
- **Deployment**: Simpler Docker Compose, fewer moving parts
- **Disaster Recovery**: Restore one database vs coordinating multiple services

### Trade-offs Accepted

| Aspect | PostgreSQL-Native | Traditional | Verdict |
|--------|-------------------|-------------|---------|
| **Cache Latency** | 1-2ms (UNLOGGED) | <1ms (Redis) | ✅ Acceptable for MSME dashboards |
| **Queue Throughput** | 30K msgs/sec (PGMQ) | 500 jobs/hr (Celery) | ✅ Massive overkill for 2-5 jobs/customer |
| **Search Scale** | <100K docs (pg_search) | Millions (Elasticsearch) | ✅ Sufficient for MSME scale |
| **Analytics** | 1500x faster (pg_duckdb) | Materialized views | ✅ Better performance |
| **Operational Complexity** | Low (1 service) | High (4-5 services) | ✅ Major win for startups |

---

## Backend Stack

### Core Framework
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+
- **Architecture**: Domain-Driven Design (DDD)

### Data Layer
- **ORM**: SQLAlchemy 2.0.23
- **Migrations**: Alembic 1.12.1
- **Validation**: Pydantic v2

### Security & Auth
- **Authentication**: PyJWT 2.8.0
- **Authorization**: PyCasbin 1.25.0 (RBAC)
- **Multi-Tenancy**: PostgreSQL Row-Level Security (RLS)

### Storage & Files
- **Object Storage**: MinIO (S3-compatible)
- **Barcode Generation**: python-barcode, qrcode, Pillow

### Background Jobs (PostgreSQL-Native)
- **Queue**: PGMQ (PostgreSQL extension)
  - 30,000 messages/second throughput
  - Built-in retry logic, dead-letter queue
  - ACID transactions
- **Scheduled Tasks**: pg_cron (PostgreSQL extension)
  - Cron-like syntax for scheduling
  - Runs inside PostgreSQL
  - No separate scheduler service

---

## Frontend Stack

### Core Framework
- **Framework**: React 18
- **Language**: TypeScript 5.2.2
- **Build Tool**: Vite 5.0.8

### Styling & Components
- **Styling**: Tailwind CSS 3.3.6
- **UI Components**: ShadCN UI (Radix primitives)
- **Icons**: Lucide React

### State Management
- **Client State**: Zustand 4.4.7 (global state)
- **Server State**: TanStack Query 5.8.4 (API data caching)
- **Forms**: React Hook Form 7.48.2

### Validation & HTTP
- **Validation**: Zod 3.22.4
- **HTTP Client**: Axios 1.6.2

### Data Visualization
- **Charts**: Recharts 2.10.3
- **Gantt**: Frappe-Gantt (visual production scheduling)

### PWA Capabilities
- **PWA Plugin**: Vite PWA Plugin
- **Offline Support**: Service Workers
- **Mobile**: Camera API, Geolocation

---

## PostgreSQL Extensions

### 1. PGMQ (Message Queue)
**Purpose**: Replace Celery + RabbitMQ

**Capabilities**:
- 30,000 messages/second throughput
- ACID transactions (queue + data in same transaction)
- Visibility timeout (message locks)
- Dead-letter queue for failed messages
- Partitioned queues for scaling

**Installation**:
```sql
CREATE EXTENSION pgmq;
```

**Usage**:
```python
# Enqueue job
from pgmq import PGMQueue

queue = PGMQueue(db_url)
queue.send('background_jobs', {
    'job_type': 'sap_sync',
    'entity': 'work_order',
    'entity_id': 123
})

# Process job (worker)
message = queue.read('background_jobs', vt=30)  # 30s visibility timeout
if message:
    process_job(message['message'])
    queue.delete('background_jobs', message['msg_id'])
```

**Use Cases**:
- SAP synchronization (work orders, materials, BOMs)
- Barcode generation (PDF batch generation)
- Report generation (large Excel exports)
- Email notifications (NCR approvals, alerts)

### 2. pg_cron (Scheduled Tasks)
**Purpose**: Replace Celery Beat

**Capabilities**:
- Cron-like scheduling syntax
- Runs SQL or functions on schedule
- Job history and logging
- Timezone support

**Installation**:
```sql
CREATE EXTENSION pg_cron;
```

**Usage**:
```sql
-- Daily KPI calculation at 6:00 AM
SELECT cron.schedule(
    'daily-kpi-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);

-- Hourly inventory alert check
SELECT cron.schedule(
    'inventory-alerts',
    '0 * * * *',
    $$SELECT check_inventory_thresholds()$$
);

-- Auto-generate PM work orders (7 days before due)
SELECT cron.schedule(
    'pm-work-order-generation',
    '0 6 * * *',
    $$SELECT generate_pm_work_orders()$$
);
```

**Use Cases**:
- Daily OEE/KPI calculation
- Inventory threshold alerts
- PM work order auto-generation
- Shift performance aggregation
- Expired inspection plan notifications

### 3. pg_search (ParadeDB Full-Text Search)
**Purpose**: Replace Elasticsearch

**Capabilities**:
- BM25 ranking algorithm (same as Elasticsearch)
- 20x faster than PostgreSQL tsvector
- Typo tolerance, fuzzy search
- Faceted search, aggregations
- Real-time indexing

**Installation**:
```sql
CREATE EXTENSION pg_search;
```

**Usage**:
```sql
-- Create search index
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number, tags}'
);

-- Search with BM25 ranking
SELECT * FROM materials.search(
    query => 'steel bearing',
    limit_rows => 10
) ORDER BY score DESC;
```

**Use Cases**:
- Material search (part numbers, descriptions)
- Work order search (project names, customer orders)
- NCR search (problem descriptions, root causes)
- Document search (procedure titles, tags)

### 4. pg_duckdb (Analytics Engine)
**Purpose**: OLAP queries, fast aggregations

**Capabilities**:
- 10-1500x faster than standard PostgreSQL for analytics
- Columnar storage for analytics queries
- Parallel query execution
- Window functions optimized

**Installation**:
```sql
CREATE EXTENSION pg_duckdb;
```

**Usage**:
```sql
-- Fast aggregation across millions of production logs
SELECT
    date_trunc('day', logged_at) as day,
    SUM(quantity_produced) as total_qty,
    AVG(hours_spent) as avg_hours
FROM duckdb.query('
    SELECT * FROM production_logs
    WHERE logged_at >= NOW() - INTERVAL ''90 days''
')
GROUP BY day
ORDER BY day DESC;
```

**Use Cases**:
- KPI dashboard queries (OEE, FPY, utilization)
- Historical production analysis
- Cost analysis (material + labor aggregations)
- Quality trend analysis (NCR, inspections)

### 5. timescaledb (Time-Series Optimization)
**Purpose**: Optimize time-series data (production logs, sensor data)

**Capabilities**:
- Hypertable partitioning (automatic chunking by time)
- 75% storage compression
- Continuous aggregates (real-time materialized views)
- Data retention policies (auto-delete old data)

**Installation**:
```sql
CREATE EXTENSION timescaledb;
```

**Usage**:
```sql
-- Convert production_logs to hypertable
SELECT create_hypertable(
    'production_logs',
    'logged_at',
    chunk_time_interval => INTERVAL '1 month'
);

-- Add compression (75% storage savings)
ALTER TABLE production_logs
SET (timescaledb.compress,
     timescaledb.compress_segmentby = 'work_order_id');

SELECT add_compression_policy(
    'production_logs',
    INTERVAL '7 days'
);

-- Auto-delete data older than 2 years
SELECT add_retention_policy(
    'production_logs',
    INTERVAL '2 years'
);
```

**Use Cases**:
- Production logs (10K+ entries per day)
- Machine sensor data (temperature, pressure)
- Downtime tracking (timestamp-based)
- Shift performance logs

---

## PostgreSQL Native Features

### 1. UNLOGGED Tables (Cache)
**Purpose**: Replace Redis for caching

**Characteristics**:
- 2x faster writes than logged tables
- 1-2ms latency (vs <1ms Redis)
- Data lost on database crash (acceptable for cache)
- No WAL overhead

**Implementation**:
```sql
CREATE UNLOGGED TABLE cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Auto-delete expired cache entries
CREATE INDEX idx_cache_expires ON cache(expires_at);

-- Cleanup job (pg_cron)
SELECT cron.schedule(
    'cache-cleanup',
    '*/5 * * * *',  -- Every 5 minutes
    $$DELETE FROM cache WHERE expires_at < NOW()$$
);
```

**Use Cases**:
- Dashboard KPI caching (10-minute TTL)
- Material inventory snapshot (5-minute TTL)
- Work order status aggregations (3-minute TTL)
- User session data

### 2. LISTEN/NOTIFY (Pub/Sub)
**Purpose**: Real-time notifications

**Characteristics**:
- Lightweight pub/sub messaging
- No additional service needed
- Async notifications to clients

**Implementation**:
```sql
-- Publisher (trigger on production_logs)
CREATE OR REPLACE FUNCTION notify_production_log()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'production_log_created',
        json_build_object(
            'id', NEW.id,
            'work_order_id', NEW.work_order_id,
            'quantity', NEW.quantity_produced
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER production_log_notify
AFTER INSERT ON production_logs
FOR EACH ROW EXECUTE FUNCTION notify_production_log();
```

```python
# Subscriber (FastAPI WebSocket)
import asyncpg

conn = await asyncpg.connect(db_url)
await conn.add_listener('production_log_created', callback)
```

**Use Cases**:
- Real-time dashboard updates (production quantities)
- Notification badges (new NCRs, alerts)
- Live machine status updates
- Shift handover notifications

### 3. Row-Level Security (RLS)
**Purpose**: Multi-tenant data isolation

**Implementation**:
```sql
-- Enable RLS
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;

-- Policy: Users only see their organization's data
CREATE POLICY work_orders_tenant_isolation ON work_orders
USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

```python
# Set context in middleware (FastAPI)
@app.middleware("http")
async def set_rls_context(request: Request, call_next):
    org_id = get_org_from_jwt(request)
    async with db.begin():
        await db.execute(
            text("SET LOCAL app.current_organization_id = :org_id"),
            {"org_id": org_id}
        )
        response = await call_next(request)
    return response
```

**Use Cases**:
- Multi-tenant SaaS data isolation
- Plant-level data access control
- Department-level permissions
- Automatic filtering on all queries

### 4. SKIP LOCKED (Concurrent Queue Processing)
**Purpose**: Multiple workers processing queue without conflicts

**Implementation**:
```sql
-- Worker picks next job without blocking
SELECT * FROM background_jobs
WHERE status = 'pending'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

**Use Cases**:
- Multiple PGMQ workers processing jobs
- Concurrent report generation
- Parallel barcode generation

---

## Infrastructure

### Container Architecture

**Development**:
```yaml
services:
  postgres:
    image: tembo/tembo-pg-slim:latest  # Includes extensions
    ports: ["5432:5432"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]

  minio:
    image: minio/minio:latest
    ports: ["9000:9000"]
```

**Production**:
```yaml
services:
  postgres:
    image: tembo/tembo-pg-slim:latest
    command: >
      postgres
      -c shared_preload_libraries='pg_cron,timescaledb,pgmq'
      -c shared_buffers='4GB'
      -c effective_cache_size='12GB'
      -c maintenance_work_mem='1GB'
      -c max_connections='200'
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    image: unison-backend:latest
    replicas: 2  # Load balanced

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
```

### Deployment Comparison

| Aspect | Traditional Stack | PostgreSQL-Native |
|--------|-------------------|-------------------|
| **Containers** | 8-10 | 3-4 |
| **Memory** | 8-12 GB | 4-6 GB |
| **Monitoring** | 5 services | 1 service |
| **Backup** | 3 separate backups | 1 database dump |
| **Startup Time** | 60-90 seconds | 20-30 seconds |

---

## Performance Benchmarks

### 1. Message Queue Performance

| Queue | Throughput | Latency | Scalability |
|-------|------------|---------|-------------|
| **PGMQ** | 30,000 msgs/sec | 5-10ms | Partitioned queues |
| **Celery + RabbitMQ** | 500 jobs/hour | 50-200ms | Requires cluster |
| **For MSME**: 2-5 jobs/customer | Both sufficient | PGMQ: 6000x overkill | PGMQ wins (simpler) |

### 2. Full-Text Search Performance

| Search Engine | 10K docs | 100K docs | 1M docs |
|---------------|----------|-----------|---------|
| **pg_search (BM25)** | 5ms | 50ms | 500ms |
| **tsvector** | 100ms | 1000ms | 10s |
| **Elasticsearch** | 2ms | 20ms | 100ms |
| **MSME Scale** | <100K docs | pg_search sufficient | ES overkill |

### 3. Analytics Performance (90-day aggregation)

| Engine | 10K rows | 100K rows | 1M rows |
|--------|----------|-----------|---------|
| **pg_duckdb** | 50ms | 200ms | 2s |
| **Materialized View** | 500ms | 5s | 50s |
| **Standard Query** | 2s | 20s | 5min |
| **Improvement** | 10x | 25x | 150x |

### 4. Cache Performance

| Cache | Latency | Throughput | Persistence |
|-------|---------|------------|-------------|
| **Redis** | <1ms | 100K ops/sec | Durable |
| **UNLOGGED Table** | 1-2ms | 50K ops/sec | Lost on crash |
| **For Dashboards** | 1-5ms acceptable | 1K ops/sec needed | Cache = OK to lose |

---

## Migration Path

### Phase 1: Replace Celery with PGMQ (Week 1)
1. Install PGMQ extension
2. Create `background_jobs` queue
3. Migrate Celery tasks → PGMQ jobs
4. Run PGMQ worker alongside Celery (parallel)
5. Verify job processing
6. Remove Celery + RabbitMQ

### Phase 2: Replace Redis Cache with UNLOGGED (Week 2)
1. Create UNLOGGED cache table
2. Migrate cache keys → table
3. Update cache service to use PostgreSQL
4. Monitor latency (should be 1-2ms)
5. Remove Redis

### Phase 3: Add pg_cron Scheduled Jobs (Week 3)
1. Install pg_cron
2. Migrate Celery Beat schedules → pg_cron
3. Test scheduled job execution
4. Remove Celery Beat

### Phase 4: Add pg_search (Week 4)
1. Install pg_search extension
2. Create BM25 indexes on materials, work_orders, NCRs
3. Migrate search queries → pg_search
4. Verify search performance

### Phase 5: Optimize with pg_duckdb & timescaledb (Week 5)
1. Install pg_duckdb, timescaledb
2. Convert production_logs → hypertable
3. Add compression policy (7 days)
4. Migrate analytics queries → pg_duckdb

**Total Migration Time**: 5 weeks
**Rollback Strategy**: Keep old services running in parallel for 2 weeks

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-07 | Eliminate Redis/Celery | Simplicity, cost, sufficient performance for MSME |
| 2025-11-07 | Use PGMQ for queue | 30K msgs/sec >> 2-5 jobs/customer (6000x overkill) |
| 2025-11-07 | Use UNLOGGED for cache | 1-2ms latency acceptable for dashboards |
| 2025-11-07 | Use pg_search vs ES | <100K docs, BM25 ranking, 20x faster than tsvector |
| 2025-11-07 | Add pg_duckdb | 10-1500x faster analytics vs materialized views |
| 2025-11-07 | Add timescaledb | 75% compression for production logs |

---

**Last Updated**: 2025-11-07
**Next Review**: 2026-11-07 (or when scaling beyond 1000 customers)
