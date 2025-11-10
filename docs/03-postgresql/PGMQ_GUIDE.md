# PGMQ (Message Queue) - Complete Guide

**Purpose**: High-performance async job processing with PostgreSQL
**Performance**: 30,000 msgs/sec throughput
**Last Updated**: 2025-11-10

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Queue Management](#queue-management)
4. [Sending Messages](#sending-messages)
5. [Reading Messages](#reading-messages)
6. [Deleting Messages](#deleting-messages)
7. [Python Integration](#python-integration)
8. [FastAPI Worker](#fastapi-worker)
9. [Monitoring](#monitoring)
10. [Performance Optimization](#performance-optimization)
11. [Troubleshooting](#troubleshooting)

---

## Overview

PGMQ is a high-performance message queue built on PostgreSQL. It provides async job processing with ACID transactions, built-in retry logic, and dead letter queue support.

### Why PGMQ?

**Replaces**: Celery + RabbitMQ/Redis

**Benefits**:
- **30,000 msgs/sec** throughput
- ACID transactions (queue + database in single transaction)
- Built-in retry logic with visibility timeout
- Dead letter queue for failed messages
- No external service required
- Simple SQL interface

**Use Cases**:
- SAP synchronization jobs
- Barcode generation
- Email notifications
- Background calculations
- Report generation
- Data imports

---

## Core Concepts

### Queue
Named channel for messages (e.g., `background_jobs`, `email_notifications`)

```sql
-- Create queue
SELECT pgmq.create('background_jobs');
```

### Message
JSONB payload with metadata (msg_id, read_ct, enqueued_at, vt)

```json
{
  "job_type": "sap_sync",
  "entity": "work_order",
  "entity_id": 123
}
```

### Visibility Timeout (VT)
Lock duration for message processing. Message becomes invisible to other workers during VT.

```sql
-- Read message with 30-second visibility timeout
SELECT * FROM pgmq.read('background_jobs', vt => 30, qty => 1);
```

### Dead Letter Queue (DLQ)
Failed messages after max retries. Review and reprocess manually.

```sql
-- Send to DLQ
SELECT pgmq.send('dlq', '{"original_msg": "..."}'::jsonb);
```

---

## Queue Management

### Create Queue

```sql
-- Standard queue
SELECT pgmq.create('background_jobs');

-- Partitioned queue (for high volume: 1M+ msgs/day)
SELECT pgmq.create_partitioned(
    'high_volume_jobs',
    partition_interval => '1 day',
    retention_interval => '7 days'
);

-- Create multiple queues
SELECT pgmq.create('email_notifications');
SELECT pgmq.create('report_generation');
SELECT pgmq.create('dlq');  -- Dead letter queue
```

### List Queues

```sql
-- List all queues
SELECT * FROM pgmq.list_queues();

-- Expected output:
-- queue_name           | created_at
-- --------------------+------------
-- background_jobs      | 2025-11-10 10:00:00
-- email_notifications  | 2025-11-10 10:00:00
-- dlq                  | 2025-11-10 10:00:00
```

### Drop Queue

```sql
-- Drop queue (deletes all messages)
SELECT pgmq.drop_queue('background_jobs');
```

---

## Sending Messages

### Send Single Message

```sql
-- Basic send
SELECT pgmq.send(
    'background_jobs',
    '{"job_type": "sap_sync", "entity": "work_order", "entity_id": 123}'::jsonb
);

-- Returns: msg_id (bigint)
-- Example: 1
```

### Send with Delay

```sql
-- Send message with 5-minute delay
SELECT pgmq.send(
    'background_jobs',
    '{"job_type": "email_notification", "to": "user@example.com"}'::jsonb,
    delay_seconds => 300
);

-- Message won't be visible until 5 minutes later
```

### Send Batch (More Efficient)

```sql
-- Send multiple messages at once (faster than individual sends)
SELECT pgmq.send_batch(
    'background_jobs',
    ARRAY[
        '{"job_type": "barcode_generation", "wo_id": 1}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 2}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 3}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 4}'::jsonb,
        '{"job_type": "barcode_generation", "wo_id": 5}'::jsonb
    ]
);

-- Returns: array of msg_ids
-- Example: {1,2,3,4,5}
```

---

## Reading Messages

### Read One Message

```sql
-- Read one message with 30-second visibility timeout
SELECT * FROM pgmq.read('background_jobs', vt => 30, qty => 1);

-- Returns:
-- msg_id | read_ct | enqueued_at         | vt                  | message
-- -------+---------+---------------------+---------------------+---------
-- 1      | 1       | 2025-11-10 10:00:00 | 2025-11-10 10:00:30 | {"job_type": "sap_sync", ...}
```

**Fields:**
- `msg_id`: Unique message ID
- `read_ct`: Number of times message has been read (for retry logic)
- `enqueued_at`: When message was created
- `vt`: Visibility timeout (when message becomes visible again)
- `message`: JSONB payload

### Read Multiple Messages

```sql
-- Read up to 10 messages (batch processing)
SELECT * FROM pgmq.read('background_jobs', vt => 30, qty => 10);
```

### Poll (Wait for Messages)

```sql
-- Wait up to 5 seconds for a message
SELECT * FROM pgmq.read_with_poll(
    'background_jobs',
    vt => 30,
    qty => 1,
    max_poll_seconds => 5
);

-- If no messages, waits up to 5 seconds before returning empty
-- Reduces CPU usage in worker loops
```

---

## Deleting Messages

### Delete (Acknowledge Success)

```sql
-- Delete message after successful processing
SELECT pgmq.delete('background_jobs', msg_id => 1);

-- Returns: boolean (true if deleted)
```

### Archive (Keep History)

```sql
-- Archive message instead of deleting (for audit trail)
SELECT pgmq.archive('background_jobs', msg_id => 1);

-- Message moved to pgmq.q_background_jobs_archive table
```

### Delete Batch

```sql
-- Delete multiple messages at once
SELECT pgmq.delete('background_jobs', msg_id => 1);
SELECT pgmq.delete('background_jobs', msg_id => 2);
SELECT pgmq.delete('background_jobs', msg_id => 3);

-- Or use array:
SELECT pgmq.delete('background_jobs', ARRAY[1,2,3]);
```

---

## Python Integration

### Producer: Enqueue Jobs

```python
from pgmq import PGMQueue
import os

# Initialize queue
queue = PGMQueue(database_url=os.getenv("DATABASE_URL"))

# Enqueue SAP sync job
def enqueue_sap_sync(work_order_id: int) -> int:
    """Queue SAP sync job for work order"""
    msg_id = queue.send(
        'background_jobs',
        {
            'job_type': 'sap_sync',
            'entity': 'work_order',
            'entity_id': work_order_id
        }
    )
    return msg_id

# Enqueue barcode generation
def enqueue_barcode_generation(work_order_id: int) -> int:
    """Queue barcode generation job"""
    msg_id = queue.send(
        'background_jobs',
        {
            'job_type': 'barcode_generation',
            'work_order_id': work_order_id
        }
    )
    return msg_id

# Enqueue delayed email (5 minutes)
def enqueue_delayed_email(to: str, subject: str, body: str) -> int:
    """Queue delayed email notification"""
    msg_id = queue.send(
        'email_notifications',
        {
            'job_type': 'email_notification',
            'to': to,
            'subject': subject,
            'body': body
        },
        delay_seconds=300
    )
    return msg_id
```

### Consumer: Process Jobs

```python
from pgmq import PGMQueue
import time
import os

queue = PGMQueue(database_url=os.getenv("DATABASE_URL"))

def worker():
    """Simple worker loop"""
    print("Worker started")

    while True:
        # Read message with 30s visibility timeout
        messages = queue.read('background_jobs', vt=30, qty=1)

        if not messages:
            time.sleep(1)  # No messages, wait 1 second
            continue

        msg = messages[0]

        try:
            # Process job
            job_type = msg['message']['job_type']

            if job_type == 'sap_sync':
                process_sap_sync(msg['message'])
            elif job_type == 'barcode_generation':
                process_barcode_generation(msg['message'])
            else:
                print(f"Unknown job type: {job_type}")

            # Success: delete message
            queue.delete('background_jobs', msg['msg_id'])
            print(f"✓ Processed msg_id={msg['msg_id']}")

        except Exception as e:
            print(f"✗ Error processing msg_id={msg['msg_id']}: {str(e)}")

            # Retry logic
            if msg['read_ct'] >= 3:  # Max 3 retries
                # Move to dead letter queue
                queue.send('dlq', msg['message'])
                queue.delete('background_jobs', msg['msg_id'])
                print(f"→ Moved to DLQ: msg_id={msg['msg_id']}")
            # Else: message becomes visible again after VT expires (automatic retry)

def process_sap_sync(message: dict):
    """Process SAP sync job"""
    entity_type = message['entity']
    entity_id = message['entity_id']
    # ... SAP sync logic ...
    print(f"Synced {entity_type} #{entity_id} to SAP")

def process_barcode_generation(message: dict):
    """Process barcode generation job"""
    work_order_id = message['work_order_id']
    # ... barcode generation logic ...
    print(f"Generated barcode for WO #{work_order_id}")

if __name__ == "__main__":
    worker()
```

---

## FastAPI Worker

### Complete Worker Implementation

```python
# backend/app/workers/pgmq_worker.py
import asyncio
import logging
import os
from pgmq import PGMQueue
from app.infrastructure.sap.sap_adapter import SAPAdapter
from app.infrastructure.barcode.barcode_service import BarcodeService
from app.infrastructure.email.email_service import EmailService

logger = logging.getLogger(__name__)

class PGMQWorker:
    """Background worker for processing PGMQ jobs"""

    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        self.queue = PGMQueue(self.db_url)
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
                messages = self.queue.read(queue_name, vt=60, qty=5)

                if not messages:
                    await asyncio.sleep(1)  # No messages, wait 1s
                    continue

                # Process messages concurrently
                await asyncio.gather(*[
                    self.process_message(queue_name, msg)
                    for msg in messages
                ])

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
            logger.info(f"✓ Processed {job_type}: msg_id={msg['msg_id']}")

        except Exception as e:
            logger.error(f"✗ Job error msg_id={msg['msg_id']}: {str(e)}")

            # Retry logic
            if msg["read_ct"] >= 3:  # Max 3 retries
                # Move to dead letter queue
                self.queue.send("dlq", msg["message"])
                self.queue.delete(queue_name, msg["msg_id"])
                logger.warning(f"→ DLQ: msg_id={msg['msg_id']} after {msg['read_ct']} retries")
            # Else: message becomes visible again after VT

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
    worker = PGMQWorker()
    queue_name = os.getenv("QUEUE_NAME", "background_jobs")
    asyncio.run(worker.process_queue(queue_name))
```

### Docker Compose

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

---

## Monitoring

### Queue Metrics

```sql
-- Queue metrics
SELECT
    queue_name,
    queue_length,
    newest_msg_age_sec,
    oldest_msg_age_sec,
    total_messages
FROM pgmq.metrics('background_jobs');

-- Expected output:
-- queue_name      | queue_length | newest_msg_age_sec | oldest_msg_age_sec | total_messages
-- ----------------+--------------+--------------------+--------------------+---------------
-- background_jobs | 5            | 2                  | 120                | 1523
```

### Dead Letter Queue Check

```sql
-- Check DLQ
SELECT * FROM pgmq.read('dlq', vt => 300, qty => 100);

-- Count DLQ messages
SELECT COUNT(*) FROM pgmq.q_dlq;
```

### Archive Query

```sql
-- Query archived messages
SELECT
    msg_id,
    enqueued_at,
    archived_at,
    message
FROM pgmq.q_background_jobs_archive
WHERE archived_at >= NOW() - INTERVAL '24 hours'
ORDER BY archived_at DESC
LIMIT 100;
```

---

## Performance Optimization

### Partition Queue (High Volume)

```sql
-- For queues with 1M+ msgs/day
SELECT pgmq.create_partitioned(
    'high_volume_jobs',
    partition_interval => '1 day',
    retention_interval => '7 days'
);
```

### Index for Faster Dequeue

```sql
-- Add index for pending messages
CREATE INDEX idx_background_jobs_vt
ON pgmq.q_background_jobs (vt)
WHERE status = 'pending';
```

### Batch Processing

```python
# Read and process multiple messages at once
messages = queue.read('background_jobs', vt=60, qty=10)

# Process concurrently
await asyncio.gather(*[process_message(msg) for msg in messages])
```

### Connection Pooling

```python
# Use connection pool for high throughput
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

---

## Troubleshooting

### Messages Not Being Processed

**Diagnosis:**
```sql
-- Check queue metrics
SELECT * FROM pgmq.metrics('background_jobs');

-- Check for stuck messages (visible but old)
SELECT * FROM pgmq.read('background_jobs', vt => 0, qty => 100)
WHERE enqueued_at < NOW() - INTERVAL '1 hour';
```

**Solution:**
```sql
-- Reset visibility timeout (make messages available)
UPDATE pgmq.q_background_jobs
SET vt = NOW()
WHERE vt > NOW() + INTERVAL '5 minutes';
```

---

### Queue Growing Too Fast

**Diagnosis:**
```sql
-- Check DLQ for failed messages
SELECT COUNT(*) FROM pgmq.q_dlq;

-- Check queue length
SELECT queue_length FROM pgmq.metrics('background_jobs');
```

**Solution:**
1. Increase number of workers
2. Optimize job processing code
3. Check for failing jobs in DLQ
4. Archive old processed messages

---

### High Memory Usage

**Diagnosis:**
```sql
-- Check queue table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'pgmq'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Solution:**
```sql
-- Archive old messages
SELECT pgmq.archive('background_jobs', msg_id)
FROM pgmq.q_background_jobs_archive
WHERE enqueued_at < NOW() - INTERVAL '30 days';

-- Vacuum tables
VACUUM ANALYZE pgmq.q_background_jobs;
```

---

## See Also

- [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md) - Installation and architecture
- [PG_CRON_GUIDE.md](./PG_CRON_GUIDE.md) - Schedule periodic jobs
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - Migrate from Celery
- [PGMQ Official Docs](https://github.com/tembo-io/pgmq)
