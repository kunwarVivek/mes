# Celery Async Tasks

## Configuration

**Broker:** Redis (redis://redis:6379/0)
**Backend:** Redis (same)
**Worker:** Runs in Docker container `unison-celery-worker`

## Available Tasks

### 1. Send Welcome Email
```python
from app.infrastructure.tasks import send_welcome_email

# Trigger task
send_welcome_email.delay("user@example.com", "John Doe")

# Returns: AsyncResult with task ID
```

**Purpose:** Send welcome email to new users asynchronously
**Usage:** Call after user creation in CreateUserUseCase
**Implementation:** Logs email (production: integrate SendGrid/AWS SES)

### 2. Cleanup Inactive Users
```python
from app.infrastructure.tasks import cleanup_inactive_users

# Trigger task (typically from scheduled job)
cleanup_inactive_users.delay()
```

**Purpose:** Periodic cleanup of inactive accounts
**Usage:** Schedule with Celery Beat (not yet configured)
**Logic:** Find users inactive > 365 days, deactivate/delete

### 3. Generate User Report
```python
from app.infrastructure.tasks import generate_user_report

# Trigger task
task = generate_user_report.delay(user_id=123)
print(task.id)  # Track task progress
```

**Purpose:** Generate comprehensive user activity report
**Usage:** Called from admin dashboard for reporting
**Returns:** Report URL after completion

## Adding New Tasks

### 1. Create Task
```python
# app/infrastructure/tasks/my_tasks.py
from app.infrastructure.tasks.celery_app import celery_app

@celery_app.task(name="my_long_task")
def my_long_task(param1: str, param2: int):
    # Long-running logic here
    return {"status": "completed", "result": "data"}
```

### 2. Import in __init__.py
```python
# app/infrastructure/tasks/__init__.py
from app.infrastructure.tasks.my_tasks import my_long_task

__all__ = [..., "my_long_task"]
```

### 3. Use in Application Layer
```python
# In use case
from app.infrastructure.tasks import my_long_task

class MyUseCase:
    def execute(self, data):
        # Trigger async task
        task = my_long_task.delay(data.param1, data.param2)
        return {"task_id": task.id, "status": "processing"}
```

## Task Monitoring

### Check Task Status
```python
from app.infrastructure.tasks.celery_app import celery_app

task_id = "abc-123-def-456"
result = celery_app.AsyncResult(task_id)

print(result.status)  # PENDING, SUCCESS, FAILURE
print(result.result)  # Task return value
```

### View Logs
```bash
# Live worker logs
docker-compose logs -f celery_worker

# Check specific task
docker-compose exec celery_worker celery -A app.infrastructure.tasks.celery_app inspect active
```

## Celery Beat (Scheduled Tasks)

**Not yet configured, but here's how to add:**

1. **Add to docker-compose.yml:**
```yaml
celery_beat:
  build: ./backend
  command: celery -A app.infrastructure.tasks.celery_app beat --loglevel=info
  depends_on: [redis]
```

2. **Configure Schedule:**
```python
# app/infrastructure/tasks/celery_app.py
celery_app.conf.beat_schedule = {
    'cleanup-every-day': {
        'task': 'cleanup_inactive_users',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

## Best Practices

✅ **Keep tasks idempotent** - Safe to retry
✅ **Set timeouts** - Prevent hanging tasks
✅ **Log progress** - For debugging
✅ **Return structured data** - JSON serializable
✅ **Handle errors gracefully** - Don't crash worker
✅ **Use task IDs** - Track async operations
✅ **Separate critical vs non-critical** - Different queues

## Common Patterns

### Pattern 1: Fire and Forget
```python
# Don't need result, just trigger
send_welcome_email.delay(email, username)
```

### Pattern 2: Track Result
```python
# Need to check status later
task = generate_user_report.delay(user_id)
# Store task.id in database
# Check later via API endpoint
```

### Pattern 3: Chain Tasks
```python
from celery import chain

# Execute tasks in sequence
workflow = chain(
    task1.s(arg1),
    task2.s(),
    task3.s()
)
workflow.apply_async()
```

### Pattern 4: Group Tasks
```python
from celery import group

# Execute tasks in parallel
job = group(
    task1.s(user1),
    task1.s(user2),
    task1.s(user3)
)
result = job.apply_async()
```
