# Celery to PGMQ Migration Guide

## Overview

This guide documents the migration from Celery + Redis to PGMQ (PostgreSQL Message Queue) for background job processing in the Unison application.

## Migration Status

**Status:** Implementation Complete, Ready for Testing

### What's Done

- [x] PGMQClient implementation with full retry logic
- [x] Task handlers migrated (send_welcome_email, cleanup_inactive_users, generate_user_report)
- [x] Task dispatcher (process_user_task)
- [x] Worker process (run_user_task_worker)
- [x] Unit tests (18 passing tests)
- [x] Integration tests
- [x] Documentation (README.md)
- [x] Configuration updates (settings in config.py)
- [x] Dependency added (tembo-pgmq-python==0.10.0)

### What's Pending

- [ ] PostgreSQL pgmq extension installation in production
- [ ] Update API endpoints to use PGMQ instead of Celery
- [ ] Deploy worker process to production
- [ ] Remove Celery dependencies (when fully migrated)
- [ ] Update CI/CD pipelines

## Side-by-Side Comparison

### Architecture

**Before (Celery + Redis):**
```
FastAPI → Celery Task → Redis Broker → Celery Worker → Task Execution
```

**After (PGMQ):**
```
FastAPI → PGMQClient → PostgreSQL Queue → PGMQ Worker → Task Execution
```

### Code Comparison

#### Enqueueing Tasks

**Before (Celery):**
```python
# app/infrastructure/tasks/user_tasks.py
from app.infrastructure.tasks.celery_app import celery_app

@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, username: str):
    # Task logic
    return {"status": "sent", "email": user_email}

# Usage in API
from app.infrastructure.tasks.user_tasks import send_welcome_email
send_welcome_email.delay("user@example.com", "John Doe")
```

**After (PGMQ):**
```python
# app/infrastructure/messaging/pgmq_tasks.py
def send_welcome_email(user_email: str, username: str) -> Dict[str, Any]:
    # Task logic
    return {"status": "sent", "email": user_email}

# Usage in API
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client
client = get_pgmq_client()
client.enqueue("user_tasks", {
    "task": "send_welcome_email",
    "email": "user@example.com",
    "username": "John Doe"
})
```

#### Running Workers

**Before (Celery):**
```bash
celery -A app.infrastructure.tasks.celery_app worker --loglevel=info
```

**After (PGMQ):**
```bash
python -m app.infrastructure.messaging.pgmq_tasks
```

## Migration Steps

### 1. PostgreSQL Extension Setup

Install the pgmq extension in your PostgreSQL database:

```sql
-- Connect to database as superuser
psql -U postgres -d unison

-- Install extension
CREATE EXTENSION IF NOT EXISTS pgmq CASCADE;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'pgmq';
```

### 2. Update API Endpoints

Replace Celery task calls with PGMQ:

```python
# Before
from app.infrastructure.tasks.user_tasks import send_welcome_email

@router.post("/register")
async def register(user_data: UserCreate):
    # ... create user ...
    send_welcome_email.delay(user.email, user.username)
    return user

# After
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

@router.post("/register")
async def register(user_data: UserCreate):
    # ... create user ...
    client = get_pgmq_client()
    client.enqueue("user_tasks", {
        "task": "send_welcome_email",
        "email": user.email,
        "username": user.username
    })
    return user
```

### 3. Deploy Worker Process

#### Docker Compose

Add worker service to `docker-compose.yml`:

```yaml
services:
  # Existing services...

  pgmq-worker:
    build: ./backend
    command: python -m app.infrastructure.messaging.pgmq_tasks
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=unison
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    depends_on:
      - db
    restart: unless-stopped
```

#### Systemd (Production)

Create `/etc/systemd/system/pgmq-worker.service`:

```ini
[Unit]
Description=PGMQ Worker for Unison
After=postgresql.service network.target

[Service]
Type=simple
User=unison
WorkingDirectory=/opt/unison/backend
Environment="PYTHONPATH=/opt/unison/backend"
ExecStart=/opt/unison/venv/bin/python -m app.infrastructure.messaging.pgmq_tasks
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable pgmq-worker
sudo systemctl start pgmq-worker
sudo systemctl status pgmq-worker
```

### 4. Testing

#### Unit Tests

```bash
# Test PGMQ client
pytest tests/unit/test_pgmq_client.py -v

# Test task handlers
pytest tests/unit/test_pgmq_tasks.py -v
```

#### Integration Tests

```bash
# Requires PostgreSQL with pgmq extension
pytest tests/integration/test_pgmq_integration.py -v
```

#### Manual Testing

```python
# 1. Enqueue a test message
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

client = get_pgmq_client()
msg_id = client.enqueue("user_tasks", {
    "task": "send_welcome_email",
    "email": "test@example.com",
    "username": "Test User"
})
print(f"Enqueued message: {msg_id}")

# 2. Check queue depth
# In psql:
# SELECT * FROM pgmq.metrics('user_tasks');

# 3. Start worker and watch logs
# python -m app.infrastructure.messaging.pgmq_tasks
```

### 5. Monitoring

#### Queue Metrics

```sql
-- Queue depth and age
SELECT * FROM pgmq.metrics('user_tasks');

-- Recent messages
SELECT * FROM pgmq.user_tasks ORDER BY enqueued_at DESC LIMIT 10;

-- Archived (completed) messages
SELECT * FROM pgmq.user_tasks_archive ORDER BY archived_at DESC LIMIT 10;

-- Dead-letter queue
SELECT * FROM pgmq.metrics('user_tasks_dlq');
SELECT * FROM pgmq.user_tasks_dlq ORDER BY enqueued_at DESC LIMIT 10;
```

#### Application Logs

```bash
# Worker logs (systemd)
journalctl -u pgmq-worker -f

# Worker logs (Docker)
docker-compose logs -f pgmq-worker
```

### 6. Rollback Plan

If issues arise, rollback to Celery:

1. Stop PGMQ worker: `systemctl stop pgmq-worker`
2. Start Celery worker: `systemctl start celery-worker`
3. Revert API endpoints to use Celery tasks
4. Messages in PGMQ queues can be manually processed or migrated

## Performance Considerations

### Throughput

- **Celery**: ~1000-5000 tasks/sec (Redis broker)
- **PGMQ**: ~500-2000 tasks/sec (PostgreSQL-based)

PGMQ is sufficient for most workloads. For extremely high-throughput scenarios (>5000 tasks/sec), consider keeping Celery for specific queues.

### Latency

- **Celery**: Sub-second task delivery
- **PGMQ**: 1-2 second task delivery (polling-based)

For time-sensitive tasks requiring immediate execution, consider hybrid approach or optimize worker polling interval.

### Scalability

- **Celery**: Horizontal scaling (add more workers)
- **PGMQ**: Horizontal scaling (add more workers) + PostgreSQL scaling

Both support multiple workers. PGMQ benefits from PostgreSQL's connection pooling and replication.

## Dependency Changes

### Remove (Future)

When fully migrated, remove:

```
# requirements.txt
celery[redis]==5.3.4  # Remove
redis==5.0.1          # Remove (unless used elsewhere)
```

### Add (Already Done)

```
# requirements.txt
tembo-pgmq-python==0.10.0  # Added
```

## Files Created

```
backend/app/infrastructure/messaging/
├── __init__.py                      # Module initialization
├── pgmq_client.py                   # PGMQ client implementation
├── pgmq_tasks.py                    # Task handlers and worker
├── README.md                        # Documentation
└── MIGRATION_GUIDE.md              # This file

backend/tests/unit/
├── test_pgmq_client.py             # PGMQClient unit tests
└── test_pgmq_tasks.py              # Task handler unit tests

backend/tests/integration/
└── test_pgmq_integration.py        # Integration tests
```

## Files to Remove (When Ready)

```
backend/app/infrastructure/tasks/
├── celery_app.py                   # Celery configuration
└── user_tasks.py                   # Celery task definitions
```

**Note:** Do NOT remove until all API endpoints are updated and PGMQ is fully tested in production.

## Troubleshooting

### Extension Not Found

**Error:** `extension "pgmq" does not exist`

**Solution:**
1. Install pgmq extension: https://github.com/tembo-io/pgmq
2. Or use Tembo Cloud with pre-installed extensions
3. For local dev: Use Docker image with pgmq pre-installed

### Connection Failures

**Error:** `could not connect to server`

**Solution:**
1. Verify PostgreSQL is running: `pg_isready`
2. Check connection settings in `.env`
3. Ensure database exists: `psql -l | grep unison`

### Worker Not Processing

**Symptoms:** Messages enqueued but not processed

**Solution:**
1. Check worker is running: `ps aux | grep pgmq_tasks`
2. Check worker logs for errors
3. Verify queue name matches: `SELECT * FROM pgmq.metrics('user_tasks');`

### High Retry Rate

**Symptoms:** Many messages in DLQ

**Solution:**
1. Check DLQ for error patterns: `SELECT * FROM pgmq.user_tasks_dlq;`
2. Fix underlying task errors
3. Re-enqueue from DLQ after fixing:
   ```python
   dlq_msg = client.dequeue("user_tasks_dlq")
   client.enqueue("user_tasks", dlq_msg.message)
   ```

## Support

For issues or questions:
1. Check README.md for usage examples
2. Review integration tests for working examples
3. Check PGMQ documentation: https://pgmq.tembo.io/
4. File issue in project repository

## Timeline

- **Week 1**: Implementation and testing (DONE)
- **Week 2**: Production deployment and monitoring
- **Week 3**: Performance validation
- **Week 4**: Celery deprecation (if successful)

## Success Criteria

- [ ] All background jobs processing successfully via PGMQ
- [ ] Zero message loss (archived count = enqueued count)
- [ ] DLQ rate < 1% of total messages
- [ ] Worker uptime > 99.9%
- [ ] Task latency < 5 seconds (p95)
- [ ] No Redis/Celery dependencies in production
