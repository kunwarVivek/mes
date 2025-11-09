# PGMQ Background Jobs

PostgreSQL Message Queue (PGMQ) implementation for background job processing, replacing Celery.

## Overview

PGMQ uses PostgreSQL's native message queue extension (`pgmq`) to provide reliable background job processing without external dependencies like Redis or RabbitMQ.

### Benefits over Celery

- **Simpler Architecture**: No separate broker (Redis/RabbitMQ) needed
- **PostgreSQL Native**: Uses existing database infrastructure
- **ACID Guarantees**: Leverages PostgreSQL's transaction safety
- **Unified Stack**: One less service to manage and monitor
- **Built-in Persistence**: Messages stored in PostgreSQL tables
- **Lower Operational Overhead**: Fewer moving parts

## Prerequisites

### PostgreSQL Extension Setup

PGMQ requires the `pgmq` extension to be installed in your PostgreSQL database:

```sql
-- Install pgmq extension (requires superuser)
CREATE EXTENSION IF NOT EXISTS pgmq CASCADE;
```

For development, ensure your PostgreSQL instance has the extension available. See [Tembo PGMQ](https://github.com/tembo-io/pgmq) for installation instructions.

## Architecture

### Components

1. **PGMQClient**: Core client for queue operations
2. **PGMQMessage**: Message wrapper with metadata
3. **Task Handlers**: Business logic processors
4. **Worker Process**: Background consumer loop

### Queue Flow

```
Enqueue → Queue → Dequeue (with VT) → Process → Archive
                      ↓ (on failure)
                    Retry (3x)
                      ↓ (max retries)
                  Dead-Letter Queue
```

## Usage

### 1. Enqueue a Task

```python
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

# Get client
client = get_pgmq_client()

# Enqueue welcome email task
client.enqueue("user_tasks", {
    "task": "send_welcome_email",
    "email": "user@example.com",
    "username": "John Doe"
})
```

### 2. Process Tasks (Worker)

```python
# Run the worker process
python -m app.infrastructure.messaging.pgmq_tasks
```

Or programmatically:

```python
from app.infrastructure.messaging.pgmq_tasks import run_user_task_worker

# Starts infinite loop processing user_tasks queue
run_user_task_worker()
```

### 3. Add New Task Handler

```python
# In pgmq_tasks.py

def my_new_task(param1: str, param2: int) -> Dict[str, Any]:
    """
    New background task handler

    Args:
        param1: Description
        param2: Description

    Returns:
        Result dictionary
    """
    # Task logic here
    return {"status": "success"}

# Register in dispatcher
def process_user_task(message: Dict[str, Any]) -> Dict[str, Any]:
    task_type = message.get("task")

    if task_type == "my_new_task":
        return my_new_task(
            param1=message["param1"],
            param2=message["param2"]
        )
    # ... existing handlers
```

## Configuration

Settings in `app/core/config.py`:

```python
# PGMQ Configuration
PGMQ_QUEUE_PREFIX: str = "unison"
PGMQ_RETRY_COUNT: int = 3              # Max retry attempts
PGMQ_VISIBILITY_TIMEOUT: int = 30      # Seconds message is locked
```

## API Reference

### PGMQClient

#### `enqueue(queue_name: str, message: Dict[str, Any]) -> int`

Add message to queue.

**Args:**
- `queue_name`: Queue name (created automatically if doesn't exist)
- `message`: Message payload as dictionary

**Returns:** Message ID

**Example:**
```python
msg_id = client.enqueue("user_tasks", {
    "task": "send_email",
    "email": "test@example.com"
})
```

#### `dequeue(queue_name: str, vt: int = 30) -> Optional[PGMQMessage]`

Read message from queue with visibility timeout.

**Args:**
- `queue_name`: Queue name
- `vt`: Visibility timeout in seconds (default 30)

**Returns:** PGMQMessage or None if queue empty

**Example:**
```python
message = client.dequeue("user_tasks", vt=60)
if message:
    print(f"Processing: {message.message}")
```

#### `archive(queue_name: str, msg_id: int) -> bool`

Mark message as completed and move to archive.

**Args:**
- `queue_name`: Queue name
- `msg_id`: Message ID

**Returns:** True if successful

#### `process_with_retry(queue_name: str, message: PGMQMessage, processor: Callable) -> Optional[Any]`

Process message with automatic retry logic.

**Args:**
- `queue_name`: Queue name
- `message`: Message to process
- `processor`: Function to process message payload

**Returns:** Result from processor or None if failed

**Example:**
```python
def process_task(msg: Dict[str, Any]) -> Dict[str, Any]:
    # Process message
    return {"status": "success"}

result = client.process_with_retry("user_tasks", message, process_task)
```

## Retry Logic

### Automatic Retries

Failed tasks automatically retry with exponential backoff:

1. **First Failure**: Retry immediately (retry_count=1)
2. **Second Failure**: Retry (retry_count=2)
3. **Third Failure**: Retry (retry_count=3)
4. **Max Retries**: Move to Dead-Letter Queue (DLQ)

### Dead-Letter Queue (DLQ)

Failed messages after max retries move to `{queue_name}_dlq`:

```python
# Check DLQ for failed messages
dlq_message = client.dequeue("user_tasks_dlq")
if dlq_message:
    print(f"Failed task: {dlq_message.message}")
    print(f"Error: {dlq_message.message['error']}")
    print(f"Original queue: {dlq_message.message['original_queue']}")
```

## Monitoring

### Queue Metrics

```sql
-- Check queue depth
SELECT * FROM pgmq.metrics('user_tasks');

-- View archive (completed messages)
SELECT * FROM pgmq.user_tasks_archive ORDER BY archived_at DESC LIMIT 10;

-- Check DLQ
SELECT * FROM pgmq.metrics('user_tasks_dlq');
```

### Log Monitoring

```python
# All PGMQ operations are logged
logger.info("Enqueued message 123 to queue 'user_tasks'")
logger.warning("Message 123 failed, retrying (attempt 2/3)")
logger.error("Message 123 failed after 3 retries: Connection timeout")
```

## Migration from Celery

### Before (Celery)

```python
# celery_app.py
from celery import Celery

celery_app = Celery("unison", broker="redis://localhost:6379")

@celery_app.task
def send_welcome_email(user_email: str, username: str):
    # Task logic
    pass

# Usage
send_welcome_email.delay("user@example.com", "John")
```

### After (PGMQ)

```python
# pgmq_tasks.py
from app.infrastructure.messaging.pgmq_tasks import get_pgmq_client

def send_welcome_email(user_email: str, username: str) -> Dict[str, Any]:
    # Task logic
    return {"status": "sent"}

# Usage
client = get_pgmq_client()
client.enqueue("user_tasks", {
    "task": "send_welcome_email",
    "email": "user@example.com",
    "username": "John"
})
```

### Migration Checklist

- [x] Install `pgmq` PostgreSQL extension
- [x] Add `tembo-pgmq-python` to requirements.txt
- [x] Create PGMQClient wrapper
- [x] Migrate task handlers to standalone functions
- [x] Create task dispatcher (process_user_task)
- [x] Update task enqueueing code
- [x] Deploy worker process
- [ ] Remove Celery dependencies (when ready)
- [ ] Update deployment scripts

## Production Deployment

### Docker Compose

```yaml
services:
  pgmq-worker:
    build: .
    command: python -m app.infrastructure.messaging.pgmq_tasks
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=unison
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    depends_on:
      - db
    restart: unless-stopped
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgmq-worker
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: worker
        image: unison-backend:latest
        command: ["python", "-m", "app.infrastructure.messaging.pgmq_tasks"]
        env:
        - name: POSTGRES_SERVER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: host
```

### Systemd Service

```ini
[Unit]
Description=PGMQ Worker for Unison
After=postgresql.service

[Service]
Type=simple
User=unison
WorkingDirectory=/opt/unison/backend
ExecStart=/opt/unison/venv/bin/python -m app.infrastructure.messaging.pgmq_tasks
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Testing

### Unit Tests

```bash
# Test PGMQClient
pytest tests/unit/test_pgmq_client.py -v

# Test task handlers
pytest tests/unit/test_pgmq_tasks.py -v
```

### Integration Tests

```bash
# Requires PostgreSQL with pgmq extension
pytest tests/integration/test_pgmq_integration.py -v

# Skip integration tests
SKIP_INTEGRATION_TESTS=true pytest
```

## Troubleshooting

### Extension Not Installed

```
Error: extension "pgmq" does not exist
```

**Solution:** Install pgmq extension in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS pgmq CASCADE;
```

### Connection Issues

```
Error: could not connect to server
```

**Solution:** Verify PostgreSQL connection settings in `.env`:
```bash
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=unison
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### Messages Stuck in Queue

**Cause:** Worker process crashed or visibility timeout expired

**Solution:** Check worker logs and restart worker:
```bash
python -m app.infrastructure.messaging.pgmq_tasks
```

### High DLQ Count

**Cause:** Tasks repeatedly failing

**Solution:** Investigate DLQ messages:
```python
client = get_pgmq_client()
dlq_msg = client.dequeue("user_tasks_dlq")
print(f"Error: {dlq_msg.message['error']}")
```

## References

- [Tembo PGMQ](https://github.com/tembo-io/pgmq) - PostgreSQL Message Queue extension
- [tembo-pgmq-python](https://github.com/tembo-io/pgmq-python) - Python client library
- [PGMQ Documentation](https://pgmq.tembo.io/) - Official PGMQ docs
