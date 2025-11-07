# Migration Guide: Redis/Celery → PostgreSQL-Native

**Version**: 1.0
**Date**: 2025-11-07
**Purpose**: Step-by-step migration from traditional stack to PostgreSQL-native

---

## Table of Contents
1. [Migration Overview](#migration-overview)
2. [Phase 1: Install Extensions](#phase-1-install-extensions)
3. [Phase 2: Migrate Celery Tasks to PGMQ](#phase-2-migrate-celery-tasks-to-pgmq)
4. [Phase 3: Migrate Redis Cache to UNLOGGED](#phase-3-migrate-redis-cache-to-unlogged)
5. [Phase 4: Migrate Celery Beat to pg_cron](#phase-4-migrate-celery-beat-to-pg_cron)
6. [Phase 5: Add Search & Analytics](#phase-5-add-search--analytics)
7. [Rollback Strategy](#rollback-strategy)
8. [Validation & Testing](#validation--testing)

---

## Migration Overview

### Timeline
**Total Duration**: 5 weeks (1 week per phase)
**Recommended**: Run phases in parallel environment first, then cutover

### Risk Assessment
- **Low Risk**: Extensions run inside PostgreSQL, no new services
- **Rollback**: Keep old services running for 2 weeks during migration
- **Data Safety**: No data loss - only changing how background jobs run

### Prerequisites
- PostgreSQL 15+ with superuser access
- Tembo PostgreSQL image or manual extension installation
- Backup of current database
- Test environment for validation

---

## Phase 1: Install Extensions

**Duration**: 1-2 days
**Risk**: Low (extensions don't affect existing code)

### Step 1.1: Update Docker Compose

```yaml
# docker-compose.yml
services:
  postgres:
    image: tembo/tembo-pg-slim:latest  # Includes all extensions
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
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docs/03-postgresql/init-extensions.sql:/docker-entrypoint-initdb.d/01-extensions.sql
```

### Step 1.2: Restart PostgreSQL

```bash
# Stop old PostgreSQL
docker-compose down postgres

# Start with new image
docker-compose up -d postgres

# Wait for startup
docker-compose logs -f postgres
```

### Step 1.3: Initialize Extensions

```bash
# Run initialization script
docker-compose exec postgres psql -U unison -d unison_erp -f /docker-entrypoint-initdb.d/01-extensions.sql

# Verify extensions loaded
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT name, installed_version
FROM pg_available_extensions
WHERE name IN ('pgmq', 'pg_cron', 'pg_search', 'pg_duckdb', 'timescaledb')
ORDER BY name;
"
```

### Step 1.4: Verify Queues Created

```bash
# Check PGMQ queues
docker-compose exec postgres psql -U unison -d unison_erp -c "SELECT * FROM pgmq.list_queues();"

# Expected output:
# queue_name        | created_at
# ------------------+------------
# background_jobs   | ...
# dlq               | ...
# email_notifications | ...
# report_generation | ...
```

---

## Phase 2: Migrate Celery Tasks to PGMQ

**Duration**: 3-5 days
**Risk**: Medium (requires code changes)

### Step 2.1: Create PGMQ Service

```python
# backend/app/infrastructure/queue/pgmq_client.py
from pgmq import PGMQueue
from typing import Dict, Any, Optional
import os

class PGMQService:
    """PGMQ queue service (replaces Celery)"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.queue = PGMQueue(self.db_url)
        self.default_queue = "background_jobs"

    def enqueue(
        self,
        job_type: str,
        payload: Dict[Any, Any],
        queue_name: Optional[str] = None,
        delay_seconds: int = 0
    ) -> int:
        """Enqueue a background job"""
        message = {
            "job_type": job_type,
            **payload
        }

        queue = queue_name or self.default_queue
        msg_id = self.queue.send(
            queue,
            message,
            delay_seconds=delay_seconds
        )
        return msg_id

    def enqueue_sap_sync(self, entity_type: str, entity_id: int):
        """SAP sync job"""
        return self.enqueue("sap_sync", {
            "entity_type": entity_type,
            "entity_id": entity_id
        })

    def enqueue_barcode_generation(self, work_order_id: int):
        """Barcode generation job"""
        return self.enqueue("barcode_generation", {
            "work_order_id": work_order_id
        })

    def enqueue_email(self, to: str, subject: str, body: str):
        """Email notification job"""
        return self.enqueue("email_notification", {
            "to": to,
            "subject": subject,
            "body": body
        }, queue_name="email_notifications")
```

### Step 2.2: Create PGMQ Worker

```python
# backend/app/workers/pgmq_worker.py
import asyncio
import logging
from pgmq import PGMQueue
from app.infrastructure.queue.pgmq_client import PGMQService
from app.infrastructure.sap.sap_adapter import SAPAdapter
from app.infrastructure.barcode.barcode_service import BarcodeService
from app.infrastructure.email.email_service import EmailService

logger = logging.getLogger(__name__)

class PGMQWorker:
    """Background worker for processing PGMQ jobs"""

    def __init__(self):
        self.queue_service = PGMQService()
        self.queue = self.queue_service.queue
        self.sap_adapter = SAPAdapter()
        self.barcode_service = BarcodeService()
        self.email_service = EmailService()

        # Job handlers
        self.handlers = {
            "sap_sync": self.handle_sap_sync,
            "barcode_generation": self.handle_barcode_generation,
            "email_notification": self.handle_email_notification,
        }

    async def process_queue(self, queue_name: str = "background_jobs"):
        """Main worker loop"""
        logger.info(f"PGMQ Worker started for queue: {queue_name}")

        while True:
            try:
                # Read up to 5 messages (batch processing)
                messages = self.queue.read(
                    queue_name,
                    vt=60,  # 60s visibility timeout
                    qty=5
                )

                if not messages:
                    await asyncio.sleep(1)  # No messages, wait 1s
                    continue

                # Process messages
                for msg in messages:
                    await self.process_message(queue_name, msg)

            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(5)  # Error recovery delay

    async def process_message(self, queue_name: str, msg: dict):
        """Process a single message"""
        try:
            job = msg["message"]
            job_type = job.get("job_type")

            if job_type not in self.handlers:
                logger.error(f"Unknown job type: {job_type}")
                self.queue.delete(queue_name, msg["msg_id"])
                return

            # Execute handler
            handler = self.handlers[job_type]
            await handler(job)

            # Success: delete message
            self.queue.delete(queue_name, msg["msg_id"])
            logger.info(f"Processed job {job_type}: msg_id={msg['msg_id']}")

        except Exception as e:
            logger.error(f"Job processing error: {str(e)}")

            # Retry logic
            if msg["read_ct"] >= 3:  # Max 3 retries
                # Move to dead letter queue
                self.queue.send("dlq", msg["message"])
                self.queue.delete(queue_name, msg["msg_id"])
                logger.warning(f"Job moved to DLQ after 3 retries: {msg['msg_id']}")
            # Else: message will become visible again after VT

    async def handle_sap_sync(self, job: dict):
        """Handle SAP sync job"""
        entity_type = job["entity_type"]
        entity_id = job["entity_id"]
        await self.sap_adapter.sync_entity(entity_type, entity_id)

    async def handle_barcode_generation(self, job: dict):
        """Handle barcode generation job"""
        work_order_id = job["work_order_id"]
        await self.barcode_service.generate_barcode(work_order_id)

    async def handle_email_notification(self, job: dict):
        """Handle email notification job"""
        await self.email_service.send_email(
            to=job["to"],
            subject=job["subject"],
            body=job["body"]
        )

# Entry point
if __name__ == "__main__":
    import os

    worker = PGMQWorker()
    queue_name = os.getenv("QUEUE_NAME", "background_jobs")
    asyncio.run(worker.process_queue(queue_name))
```

### Step 2.3: Update API Endpoints

**Before (Celery)**:
```python
# Old code using Celery
from app.infrastructure.tasks.celery_app import celery_app

@app.post("/api/v1/work-orders/{id}/sync-sap")
def sync_work_order_to_sap(id: int, db: Session = Depends(get_db)):
    # Enqueue Celery task
    celery_app.send_task(
        "app.infrastructure.tasks.sap_sync.sync_work_order",
        args=[id]
    )
    return {"status": "queued"}
```

**After (PGMQ)**:
```python
# New code using PGMQ
from app.infrastructure.queue.pgmq_client import PGMQService

@app.post("/api/v1/work-orders/{id}/sync-sap")
def sync_work_order_to_sap(
    id: int,
    db: Session = Depends(get_db),
    queue: PGMQService = Depends(get_pgmq_service)
):
    # Enqueue PGMQ job
    msg_id = queue.enqueue_sap_sync("work_order", id)
    return {"status": "queued", "message_id": msg_id}
```

### Step 2.4: Run PGMQ Worker

```yaml
# docker-compose.yml
services:
  pgmq_worker:
    build: ./backend
    container_name: unison_pgmq_worker
    environment:
      DATABASE_URL: postgresql://unison:password@postgres:5432/unison_erp
      QUEUE_NAME: background_jobs
    depends_on:
      - postgres
    command: python -m app.workers.pgmq_worker
    restart: unless-stopped
```

### Step 2.5: Parallel Testing (2 weeks)

```bash
# Keep both Celery and PGMQ running
docker-compose up -d celery_worker pgmq_worker

# Monitor both queues
docker-compose logs -f celery_worker pgmq_worker

# Compare: jobs should process successfully in both
```

### Step 2.6: Cutover

```bash
# After 2 weeks of parallel operation:
# 1. Stop Celery worker
docker-compose stop celery_worker

# 2. Monitor PGMQ only
docker-compose logs -f pgmq_worker

# 3. After 1 week, remove Celery from docker-compose.yml
```

---

## Phase 3: Migrate Redis Cache to UNLOGGED

**Duration**: 2-3 days
**Risk**: Low (cache data is temporary)

### Step 3.1: Create Cache Service

```python
# backend/app/infrastructure/cache/postgres_cache.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional, Any
import json
from datetime import datetime, timedelta

class PostgresCacheService:
    """UNLOGGED table cache (replaces Redis)"""

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        result = self.db.execute(
            text("""
                SELECT cache_value
                FROM cache
                WHERE cache_key = :key
                  AND expires_at > NOW()
            """),
            {"key": key}
        ).fetchone()

        if result:
            return json.loads(result[0])
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 600
    ):
        """Set value in cache with TTL"""
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        self.db.execute(
            text("""
                INSERT INTO cache (cache_key, cache_value, expires_at)
                VALUES (:key, :value, :expires_at)
                ON CONFLICT (cache_key) DO UPDATE
                SET cache_value = EXCLUDED.cache_value,
                    expires_at = EXCLUDED.expires_at
            """),
            {
                "key": key,
                "value": json.dumps(value),
                "expires_at": expires_at
            }
        )
        self.db.commit()

    def delete(self, key: str):
        """Delete key from cache"""
        self.db.execute(
            text("DELETE FROM cache WHERE cache_key = :key"),
            {"key": key}
        )
        self.db.commit()

    def clear_expired(self):
        """Clear expired cache entries (called by pg_cron)"""
        self.db.execute(
            text("DELETE FROM cache WHERE expires_at < NOW()")
        )
        self.db.commit()
```

### Step 3.2: Update Cache Calls

**Before (Redis)**:
```python
from app.infrastructure.cache.redis_cache import RedisCache

cache = RedisCache()
dashboard_data = cache.get("dashboard:oee")
if not dashboard_data:
    dashboard_data = calculate_oee()
    cache.set("dashboard:oee", dashboard_data, ttl=600)
```

**After (PostgreSQL UNLOGGED)**:
```python
from app.infrastructure.cache.postgres_cache import PostgresCacheService

cache = PostgresCacheService(db)
dashboard_data = cache.get("dashboard:oee")
if not dashboard_data:
    dashboard_data = calculate_oee()
    cache.set("dashboard:oee", dashboard_data, ttl_seconds=600)
```

### Step 3.3: Benchmark Cache Performance

```python
# Test script: benchmark_cache.py
import time
from app.infrastructure.cache.postgres_cache import PostgresCacheService

def benchmark_cache(iterations=1000):
    cache = PostgresCacheService(db)

    # Write benchmark
    start = time.time()
    for i in range(iterations):
        cache.set(f"test_key_{i}", {"value": i}, ttl_seconds=300)
    write_time = time.time() - start

    # Read benchmark
    start = time.time()
    for i in range(iterations):
        cache.get(f"test_key_{i}")
    read_time = time.time() - start

    print(f"Write: {iterations / write_time:.0f} ops/sec")
    print(f"Read: {iterations / read_time:.0f} ops/sec")
    print(f"Avg read latency: {read_time / iterations * 1000:.2f}ms")

# Expected: 1-2ms latency, 500-1000 ops/sec
```

---

## Phase 4: Migrate Celery Beat to pg_cron

**Duration**: 2-3 days
**Risk**: Low (scheduled jobs continue working)

### Step 4.1: Identify Celery Beat Schedules

```python
# OLD: celerybeat-schedule.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'calculate-daily-oee': {
        'task': 'app.tasks.calculate_daily_oee',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
    },
    'inventory-threshold-alerts': {
        'task': 'app.tasks.check_inventory_thresholds',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate-pm-work-orders': {
        'task': 'app.tasks.generate_pm_work_orders',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
    },
}
```

### Step 4.2: Convert to pg_cron

```sql
-- NEW: pg_cron schedules (already in init-extensions.sql)

-- Daily OEE calculation at 6:00 AM
SELECT cron.schedule(
    'daily-oee-calculation',
    '0 6 * * *',
    $$SELECT calculate_daily_oee()$$
);

-- Inventory alerts every 5 minutes
SELECT cron.schedule(
    'inventory-alerts',
    '*/5 * * * *',
    $$SELECT check_inventory_thresholds()$$
);

-- PM work order generation daily at 6 AM
SELECT cron.schedule(
    'pm-work-order-generation',
    '0 6 * * *',
    $$SELECT generate_pm_work_orders()$$
);
```

### Step 4.3: Create PostgreSQL Functions

```sql
-- Convert Celery tasks to PostgreSQL functions

CREATE OR REPLACE FUNCTION calculate_daily_oee()
RETURNS void AS $$
BEGIN
    -- Call business logic via PGMQ
    PERFORM pgmq.send(
        'background_jobs',
        jsonb_build_object(
            'job_type', 'calculate_oee',
            'date', CURRENT_DATE - INTERVAL '1 day'
        )
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_inventory_thresholds()
RETURNS void AS $$
BEGIN
    -- Queue email notifications for low inventory
    PERFORM pgmq.send(
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
END;
$$ LANGUAGE plpgsql;
```

### Step 4.4: Monitor Scheduled Jobs

```bash
# Check scheduled jobs
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT jobname, schedule, active
FROM cron.job
ORDER BY jobname;
"

# Check job execution history
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT
    j.jobname,
    jr.status,
    jr.start_time,
    jr.end_time,
    jr.return_message
FROM cron.job_run_details jr
JOIN cron.job j ON jr.jobid = j.jobid
WHERE jr.start_time >= NOW() - INTERVAL '24 hours'
ORDER BY jr.start_time DESC
LIMIT 20;
"
```

---

## Phase 5: Add Search & Analytics

**Duration**: 3-5 days
**Risk**: Low (additive features)

### Step 5.1: Create Search Indexes

```sql
-- Already in init-extensions.sql
-- Just verify they're created

SELECT paradedb.list_bm25_indexes();
```

### Step 5.2: Update Search Queries

**Before (tsvector)**:
```python
# Old full-text search
results = db.query(Material).filter(
    Material.search_vector.match("steel bearing")
).all()
```

**After (pg_search BM25)**:
```python
# New BM25 search
results = db.execute(text("""
    SELECT m.*, s.score
    FROM materials.search(
        query => 'steel bearing',
        limit_rows => 20
    ) s
    JOIN materials m ON m.id = s.id
    ORDER BY s.score DESC
""")).fetchall()
```

### Step 5.3: Optimize Analytics with pg_duckdb

```python
# Heavy analytics query
results = db.execute(text("""
    SELECT
        date_trunc('day', logged_at) as day,
        SUM(quantity_produced) as total_qty,
        AVG(labor_cost) as avg_labor_cost
    FROM duckdb.query('
        SELECT * FROM production_logs
        WHERE logged_at >= NOW() - INTERVAL ''90 days''
    ')
    GROUP BY day
    ORDER BY day DESC
""")).fetchall()
```

---

## Rollback Strategy

### If Migration Fails

**Phase 2 Rollback (PGMQ → Celery)**:
```bash
# 1. Stop PGMQ worker
docker-compose stop pgmq_worker

# 2. Start Celery worker
docker-compose up -d celery_worker celery_beat

# 3. Revert code changes (restore Celery task calls)
git revert <migration_commit>

# 4. Redeploy
docker-compose restart backend
```

**Phase 3 Rollback (UNLOGGED → Redis)**:
```bash
# 1. Start Redis
docker-compose up -d redis

# 2. Revert cache service changes
git revert <cache_migration_commit>

# 3. Redeploy
docker-compose restart backend
```

**Phase 4 Rollback (pg_cron → Celery Beat)**:
```bash
# 1. Unschedule pg_cron jobs
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT cron.unschedule(jobname) FROM cron.job;
"

# 2. Start Celery Beat
docker-compose up -d celery_beat

# 3. Restore Celery Beat schedule
git revert <celery_beat_migration_commit>
```

---

## Validation & Testing

### Pre-Migration Checklist
- [ ] Backup database
- [ ] Test environment setup complete
- [ ] Extensions installed and verified
- [ ] All stakeholders notified
- [ ] Rollback plan documented

### During Migration Checklist
- [ ] Phase 1: Extensions loaded successfully
- [ ] Phase 2: PGMQ worker processing jobs
- [ ] Phase 2: No jobs stuck in queue
- [ ] Phase 3: Cache hit rate >80%
- [ ] Phase 3: Cache latency <5ms
- [ ] Phase 4: Scheduled jobs running on time
- [ ] Phase 5: Search results accurate

### Post-Migration Validation

```bash
# 1. Check queue metrics
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT * FROM pgmq.metrics('background_jobs');
"

# 2. Check cache performance
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT
    COUNT(*) as total_keys,
    COUNT(*) FILTER (WHERE expires_at > NOW()) as active_keys,
    COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired_keys
FROM cache;
"

# 3. Check scheduled jobs
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT COUNT(*) as successful_jobs
FROM cron.job_run_details
WHERE status = 'succeeded'
  AND start_time >= NOW() - INTERVAL '24 hours';
"

# 4. Check search indexes
docker-compose exec postgres psql -U unison -d unison_erp -c "
SELECT paradedb.list_bm25_indexes();
"
```

### Performance Validation

```python
# benchmark_migration.py
def validate_migration():
    # 1. Queue throughput
    assert queue_throughput() > 1000  # msgs/sec

    # 2. Cache latency
    assert cache_latency() < 5  # milliseconds

    # 3. Scheduled jobs
    assert scheduled_jobs_success_rate() > 0.95  # 95%+

    # 4. Search performance
    assert search_latency() < 50  # milliseconds

    print("✅ Migration validation passed!")
```

---

## Success Criteria

Migration is successful when:
- ✅ All background jobs processing through PGMQ
- ✅ Cache hit rate >80%, latency <5ms
- ✅ Scheduled jobs running on time (pg_cron)
- ✅ Search results accurate (pg_search)
- ✅ No Redis/Celery services running
- ✅ Container count reduced from 8-10 to 3-4
- ✅ Zero data loss
- ✅ All tests passing

---

**Last Updated**: 2025-11-07
**Migration Owner**: Engineering Team
