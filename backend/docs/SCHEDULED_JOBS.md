# Scheduled Jobs System

**Version**: 1.0
**Last Updated**: 2025-11-11
**Architecture**: PostgreSQL-native using pg_cron

---

## Overview

The platform uses **pg_cron** (PostgreSQL-native job scheduler) to automate recurring tasks without external dependencies like Celery or cron daemons.

**Why pg_cron?**
- ✅ No additional infrastructure (no Celery, RabbitMQ, Redis)
- ✅ ACID transactions across job execution
- ✅ Built-in monitoring via `cron.job_run_details`
- ✅ Simple SQL-based configuration
- ✅ Persistent across restarts

---

## Scheduled Jobs

### 1. **Usage Tracking Job**

**Purpose**: Calculate and store current resource usage for all active organizations.

**Schedule**: Every 6 hours (`0 */6 * * *`)
**Endpoint**: `POST /api/v1/jobs/track-usage`
**Use Case**: `TrackUsageUseCase`

**What it does**:
1. Queries all organizations with `trial` or `active` subscriptions
2. For each organization:
   - Counts active users
   - Counts plants
   - Calculates total storage (files/attachments)
3. Updates `subscription_usage` table
4. Logs results to `scheduled_job_logs`

**Why every 6 hours?**
- Balances freshness vs database load
- Usage changes gradually (not real-time critical)
- 4 runs per day = sufficient for analytics

**Example Output**:
```json
{
  "success": true,
  "message": "Tracked usage for 247 organizations (2 errors)",
  "processed_count": 247,
  "error_count": 2,
  "details": {
    "errors": [
      "Org 123: Database connection timeout",
      "Org 456: Division by zero in storage calculation"
    ]
  },
  "executed_at": "2025-11-11T12:00:00Z"
}
```

---

### 2. **Trial Expiration Check Job**

**Purpose**: Find expired trials and suspend access if not converted to paid.

**Schedule**: Daily at 2 AM UTC (`0 2 * * *`)
**Endpoint**: `POST /api/v1/jobs/check-trial-expirations`
**Use Case**: `HandleTrialExpirationUseCase`

**What it does**:
1. Queries subscriptions where:
   - `status = 'trial'`
   - `trial_ends_at < NOW()`
   - `trial_converted = FALSE`
2. For each expired trial:
   - Updates status to `suspended`
   - Logs suspension event
   - (Optional) Triggers email notification
3. Logs results to `scheduled_job_logs`

**Why 2 AM UTC?**
- Low traffic period (off-peak)
- Trials expire at end of day (midnight customer timezone)
- 2 AM UTC = safe buffer for global timezones

**Example Output**:
```json
{
  "success": true,
  "message": "Handled 12 expired trials (0 errors)",
  "processed_count": 12,
  "error_count": 0,
  "details": {},
  "executed_at": "2025-11-11T02:00:00Z"
}
```

---

## Architecture

### Job Flow

```
┌─────────────┐
│  pg_cron    │  ← Scheduler (in PostgreSQL)
└──────┬──────┘
       │ Triggers every N hours
       │
       ▼
┌─────────────┐
│  pg_net     │  ← HTTP client (in PostgreSQL)
│ http_post() │
└──────┬──────┘
       │ POST request with API key
       │
       ▼
┌──────────────────┐
│  FastAPI         │  ← API endpoint (/api/v1/jobs/*)
│  jobs.py         │
└──────┬───────────┘
       │ Calls job runner
       │
       ▼
┌──────────────────┐
│  job_runner.py   │  ← Execution logic
│  track_usage_job │
│  check_trials    │
└──────┬───────────┘
       │ Invokes use cases
       │
       ▼
┌──────────────────┐
│  Use Cases       │  ← Business logic
│  TrackUsageUseCase
│  HandleTrialExpirationUseCase
└──────────────────┘
```

---

## Database Schema

### `scheduled_job_logs`

Tracks execution history for all scheduled jobs.

```sql
CREATE TABLE scheduled_job_logs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure')),
    message TEXT,
    processed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    details JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER
);
```

**Indexes**:
- `idx_scheduled_job_logs_job_name` (job_name)
- `idx_scheduled_job_logs_executed_at` (executed_at DESC)
- `idx_scheduled_job_logs_status` (status)

**Sample Query**:
```sql
-- Get last 10 job runs with errors
SELECT job_name, message, error_count, executed_at
FROM scheduled_job_logs
WHERE status = 'failure'
ORDER BY executed_at DESC
LIMIT 10;
```

---

## Configuration

### Environment Variables

**Required**:
- `INTERNAL_API_KEY` - Secret key for job endpoint authentication
- `API_BASE_URL` - Base URL for API (e.g., `http://backend:8000`)

**Optional**:
- `JOB_TIMEOUT_SECONDS` - Max execution time (default: 300)

### Example `.env`

```bash
INTERNAL_API_KEY=super-secret-internal-key-change-me
API_BASE_URL=http://backend:8000
```

---

## Deployment

### 1. Run Migration

```bash
cd backend
alembic upgrade head
```

This creates:
- pg_cron scheduled jobs
- `scheduled_job_logs` table

### 2. Verify Jobs Created

```sql
-- Check scheduled jobs
SELECT * FROM cron.job;

-- Expected output:
-- jobid | schedule     | command                      | nodename  | ...
-- 1     | 0 */6 * * *  | SELECT net.http_post(...)    | localhost | track-usage
-- 2     | 0 2 * * *    | SELECT net.http_post(...)    | localhost | check-trial-expirations
```

### 3. Test Jobs Manually

```bash
# Trigger usage tracking
curl -X POST http://localhost:8000/api/v1/jobs/track-usage \
  -H "X-API-Key: your-internal-api-key"

# Trigger trial expiration check
curl -X POST http://localhost:8000/api/v1/jobs/check-trial-expirations \
  -H "X-API-Key: your-internal-api-key"

# Trigger all jobs at once (testing only)
curl -X POST http://localhost:8000/api/v1/jobs/trigger-all \
  -H "X-API-Key: your-internal-api-key"
```

### 4. Monitor Job Execution

```sql
-- View job run history (pg_cron built-in)
SELECT *
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 20;

-- View our custom logs
SELECT *
FROM scheduled_job_logs
ORDER BY executed_at DESC
LIMIT 20;

-- Check for failures
SELECT job_name, COUNT(*) as failure_count
FROM scheduled_job_logs
WHERE status = 'failure'
  AND executed_at > NOW() - INTERVAL '7 days'
GROUP BY job_name;
```

---

## Monitoring & Alerts

### Health Checks

**Endpoint**: `GET /api/v1/jobs/stats`

Returns current state of subscriptions:
```json
{
  "trial_subscriptions": 45,
  "active_subscriptions": 202,
  "expired_trials_pending": 3,
  "total_to_track": 247,
  "checked_at": "2025-11-11T14:30:00Z"
}
```

### Alerting Rules

**Recommended alerts** (configure in monitoring tool):

1. **Job Failures**: Alert if >5% of job runs fail in 24 hours
2. **Job Not Running**: Alert if no job execution in >12 hours
3. **High Error Rate**: Alert if `error_count > 10` in single run
4. **Slow Execution**: Alert if job takes >5 minutes

### Grafana Dashboard

```sql
-- Panel 1: Job Success Rate (last 24h)
SELECT
  job_name,
  COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate
FROM scheduled_job_logs
WHERE executed_at > NOW() - INTERVAL '24 hours'
GROUP BY job_name;

-- Panel 2: Execution Duration Trend
SELECT
  date_trunc('hour', executed_at) as hour,
  job_name,
  AVG(duration_ms) as avg_duration_ms
FROM scheduled_job_logs
WHERE executed_at > NOW() - INTERVAL '7 days'
GROUP BY hour, job_name
ORDER BY hour;

-- Panel 3: Organizations Processed
SELECT
  date_trunc('day', executed_at) as day,
  SUM(processed_count) as total_processed,
  SUM(error_count) as total_errors
FROM scheduled_job_logs
WHERE job_name = 'track-usage'
  AND executed_at > NOW() - INTERVAL '30 days'
GROUP BY day
ORDER BY day;
```

---

## Troubleshooting

### Job Not Running

**Check pg_cron extension**:
```sql
SELECT * FROM pg_extension WHERE extname = 'pg_cron';
```

**Check job exists**:
```sql
SELECT * FROM cron.job WHERE jobname IN ('track-usage', 'check-trial-expirations');
```

**Check recent runs**:
```sql
SELECT *
FROM cron.job_run_details
WHERE jobid IN (SELECT jobid FROM cron.job WHERE jobname = 'track-usage')
ORDER BY start_time DESC
LIMIT 10;
```

### Job Failing

**Check API logs**:
```bash
docker logs backend | grep "jobs"
```

**Check job execution logs**:
```sql
SELECT *
FROM scheduled_job_logs
WHERE status = 'failure'
ORDER BY executed_at DESC
LIMIT 10;
```

**Common issues**:
1. **401 Unauthorized**: `INTERNAL_API_KEY` mismatch
2. **Connection refused**: Backend not reachable from database container
3. **Timeout**: Job taking >5 minutes (increase timeout or optimize query)

### Reschedule Jobs

```sql
-- Unschedule old job
SELECT cron.unschedule('track-usage');

-- Reschedule with new timing
SELECT cron.schedule(
    'track-usage',
    '0 */4 * * *',  -- Every 4 hours instead of 6
    $$
    SELECT net.http_post(
        url := 'http://backend:8000/api/v1/jobs/track-usage',
        headers := '{"Content-Type": "application/json", "X-API-Key": "your-key"}'::jsonb
    );
    $$
);
```

---

## Performance Optimization

### Batch Processing

If you have >1000 organizations, consider batching:

```python
# In job_runner.py
def track_usage_job(batch_size: int = 100):
    subscriptions = db.query(SubscriptionModel).filter(...).all()

    for i in range(0, len(subscriptions), batch_size):
        batch = subscriptions[i:i + batch_size]
        for subscription in batch:
            # Process
        db.commit()  # Commit every batch
```

### Parallel Execution

For high-volume platforms (>10K organizations):

```python
from concurrent.futures import ThreadPoolExecutor

def track_usage_parallel(max_workers: int = 10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(track_usage_for_org, org_id)
            for org_id in organization_ids
        ]
```

---

## Security

### API Key Protection

**DO**:
- ✅ Use strong random key (32+ characters)
- ✅ Store in environment variables (not in code)
- ✅ Rotate keys quarterly
- ✅ Use different keys for staging/production

**DON'T**:
- ❌ Commit API keys to git
- ❌ Use weak keys like "password123"
- ❌ Share keys across environments

### Network Security

**Production setup**:
1. Restrict `/api/v1/jobs/*` endpoints to internal network only
2. Use IP whitelist (database container IP)
3. Enable HTTPS for all API calls
4. Use VPC/private subnet for database-to-API communication

**Example nginx config**:
```nginx
location /api/v1/jobs {
    allow 10.0.1.0/24;  # Database subnet
    deny all;
    proxy_pass http://backend:8000;
}
```

---

## Maintenance

### Log Retention

**Purge old logs** (runs monthly):
```sql
DELETE FROM scheduled_job_logs
WHERE executed_at < NOW() - INTERVAL '90 days';
```

**Archive logs** (for compliance):
```sql
CREATE TABLE scheduled_job_logs_archive AS
SELECT * FROM scheduled_job_logs
WHERE executed_at < NOW() - INTERVAL '90 days';
```

### Backup

pg_cron jobs are stored in `cron.job` table:
```bash
pg_dump -t cron.job > cron_jobs_backup.sql
```

---

## Future Enhancements

1. **Email notifications** after job completion
2. **Webhook callbacks** for job status
3. **Dead letter queue** for failed organizations
4. **Exponential backoff** for retries
5. **Prometheus metrics** export
6. **Slack alerts** for critical failures

---

**Next Steps**:
1. Run migration: `alembic upgrade head`
2. Set `INTERNAL_API_KEY` in environment
3. Test manually: `curl -X POST .../jobs/trigger-all`
4. Monitor logs: `SELECT * FROM scheduled_job_logs`
5. Set up alerts in monitoring tool

---

**Related Docs**:
- [pg_cron Guide](../../docs/03-postgresql/PG_CRON_GUIDE.md)
- [Subscription System](../../docs/SUBSCRIPTION_SYSTEM.md)
- [Usage Tracking](../../docs/USAGE_TRACKING.md)
