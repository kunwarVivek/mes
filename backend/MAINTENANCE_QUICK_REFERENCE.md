# Maintenance Management Module - Quick Reference

## API Endpoints

### PM Schedules
```
POST   /api/v1/maintenance/pm-schedules           Create PM schedule
GET    /api/v1/maintenance/pm-schedules           List PM schedules
GET    /api/v1/maintenance/pm-schedules/{id}      Get PM schedule
PATCH  /api/v1/maintenance/pm-schedules/{id}      Update PM schedule
DELETE /api/v1/maintenance/pm-schedules/{id}      Delete PM schedule
```

### PM Work Orders
```
POST   /api/v1/maintenance/pm-work-orders         Create PM work order
GET    /api/v1/maintenance/pm-work-orders         List PM work orders
GET    /api/v1/maintenance/pm-work-orders/{id}    Get PM work order
PATCH  /api/v1/maintenance/pm-work-orders/{id}    Update PM work order
```

### Downtime Events
```
POST   /api/v1/maintenance/downtime-events        Create downtime event
GET    /api/v1/maintenance/downtime-events        List downtime events
PATCH  /api/v1/maintenance/downtime-events/{id}   Update downtime event
```

### Metrics
```
GET    /api/v1/maintenance/metrics/mtbf-mttr      Calculate MTBF/MTTR metrics
```

## Example Requests

### Create Calendar-Based PM Schedule
```json
POST /api/v1/maintenance/pm-schedules
{
  "schedule_code": "PM-MONTHLY-001",
  "schedule_name": "Monthly CNC Maintenance",
  "machine_id": 1,
  "trigger_type": "CALENDAR",
  "frequency_days": 30,
  "is_active": true
}
```

### Create Meter-Based PM Schedule
```json
POST /api/v1/maintenance/pm-schedules
{
  "schedule_code": "PM-HOURS-001",
  "schedule_name": "Every 1000 Hours PM",
  "machine_id": 1,
  "trigger_type": "METER",
  "meter_threshold": 1000.0,
  "is_active": true
}
```

### Create Downtime Event
```json
POST /api/v1/maintenance/downtime-events
{
  "machine_id": 1,
  "category": "BREAKDOWN",
  "reason": "Motor bearing failure",
  "started_at": "2025-11-08T10:00:00Z",
  "ended_at": "2025-11-08T14:30:00Z",
  "notes": "Replaced bearing, tested OK"
}
```

### Calculate MTBF/MTTR Metrics
```
GET /api/v1/maintenance/metrics/mtbf-mttr?machine_id=1&start_date=2025-10-01T00:00:00Z&end_date=2025-11-01T00:00:00Z
```

## Domain Entities

### PMScheduleDomain
```python
from app.domain.entities.maintenance import PMScheduleDomain, TriggerType

schedule = PMScheduleDomain(
    id=None,
    organization_id=1,
    plant_id=1,
    schedule_code="PM-001",
    schedule_name="Weekly Maintenance",
    machine_id=1,
    trigger_type=TriggerType.CALENDAR,
    frequency_days=7,
    meter_threshold=None
)

schedule.activate()    # Activate schedule
schedule.deactivate()  # Deactivate schedule
```

### PMWorkOrderDomain
```python
from app.domain.entities.maintenance import PMWorkOrderDomain, PMStatus

work_order = PMWorkOrderDomain(
    id=None,
    organization_id=1,
    plant_id=1,
    pm_schedule_id=1,
    machine_id=1,
    pm_number="PMWO-001",
    status=PMStatus.SCHEDULED,
    scheduled_date=datetime.utcnow(),
    due_date=datetime.utcnow() + timedelta(days=7)
)

work_order.start()     # SCHEDULED → IN_PROGRESS
work_order.complete()  # IN_PROGRESS → COMPLETED
work_order.cancel()    # Cancel work order
```

### DowntimeEventDomain
```python
from app.domain.entities.maintenance import DowntimeEventDomain, DowntimeCategory

event = DowntimeEventDomain(
    id=None,
    organization_id=1,
    plant_id=1,
    machine_id=1,
    category=DowntimeCategory.BREAKDOWN,
    reason="Motor failure",
    started_at=datetime.utcnow(),
    ended_at=None
)

event.end_event(datetime.utcnow())  # End downtime
duration = event.get_duration_minutes()  # Get duration
```

### MTBF/MTTR Calculator
```python
from app.domain.entities.maintenance import MTBFMTTRCalculator

metrics = MTBFMTTRCalculator.calculate_metrics(
    total_operating_time=10000.0,  # minutes
    total_repair_time=600.0,       # minutes
    number_of_failures=5
)

print(f"MTBF: {metrics.mtbf} minutes")
print(f"MTTR: {metrics.mttr} minutes")
print(f"Availability: {metrics.availability * 100}%")
```

## Enums

### TriggerType
- `CALENDAR`: Time-based trigger (frequency_days)
- `METER`: Usage-based trigger (meter_threshold)

### PMStatus
- `SCHEDULED`: PM work order created
- `IN_PROGRESS`: PM work started
- `COMPLETED`: PM work finished
- `CANCELLED`: PM work cancelled

### DowntimeCategory
- `BREAKDOWN`: Unplanned equipment failure
- `PLANNED_MAINTENANCE`: Scheduled maintenance
- `CHANGEOVER`: Product/tool changeover
- `NO_OPERATOR`: Operator unavailable
- `MATERIAL_SHORTAGE`: Material not available

## Database Tables

### pm_schedule
```sql
CREATE TABLE pm_schedule (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    schedule_code VARCHAR(50) NOT NULL,
    schedule_name VARCHAR(200) NOT NULL,
    machine_id INTEGER NOT NULL REFERENCES machine(id),
    trigger_type VARCHAR(20) NOT NULL,  -- CALENDAR or METER
    frequency_days INTEGER,
    meter_threshold FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (organization_id, plant_id, schedule_code)
);
```

### pm_work_order
```sql
CREATE TABLE pm_work_order (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    pm_schedule_id INTEGER NOT NULL REFERENCES pm_schedule(id),
    machine_id INTEGER NOT NULL REFERENCES machine(id),
    pm_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE (organization_id, plant_id, pm_number)
);
```

### downtime_event
```sql
CREATE TABLE downtime_event (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plant_id INTEGER NOT NULL,
    machine_id INTEGER NOT NULL REFERENCES machine(id),
    category VARCHAR(50) NOT NULL,  -- BREAKDOWN, PLANNED_MAINTENANCE, etc.
    reason VARCHAR(500) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## pg_cron Auto-Generation

### Schedule Job (Daily at 2:00 AM)
```sql
SELECT cron.schedule(
    'generate_pm_work_orders',
    '0 2 * * *',
    $$
    SELECT generate_calendar_pm_work_orders();
    SELECT generate_meter_pm_work_orders();
    $$
);
```

### Manual Execution
```sql
-- Test calendar-based PM generation
SELECT generate_calendar_pm_work_orders();

-- Test meter-based PM generation
SELECT generate_meter_pm_work_orders();

-- View scheduled jobs
SELECT * FROM cron.job;

-- View job execution history
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
```

## Testing

### Run Unit Tests
```bash
cd backend
python3 -m pytest tests/unit/test_maintenance_entity.py -v
```

### Run Integration Tests
```bash
cd backend
python3 -m pytest tests/integration/test_maintenance_api.py -v
```

### Test Coverage
```bash
cd backend
python3 -m pytest tests/unit/test_maintenance_entity.py --cov=app.domain.entities.maintenance --cov-report=term-missing
```

## Common Queries

### Find Overdue PM Work Orders
```sql
SELECT * FROM pm_work_order
WHERE status = 'SCHEDULED'
  AND due_date < NOW()
  AND organization_id = 1
  AND plant_id = 1
ORDER BY due_date;
```

### Calculate Machine Downtime (Last 30 Days)
```sql
SELECT
    machine_id,
    COUNT(*) AS breakdown_count,
    SUM(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60.0) AS total_downtime_minutes
FROM downtime_event
WHERE category = 'BREAKDOWN'
  AND started_at >= NOW() - INTERVAL '30 days'
  AND ended_at IS NOT NULL
  AND organization_id = 1
  AND plant_id = 1
GROUP BY machine_id
ORDER BY total_downtime_minutes DESC;
```

### Active PM Schedules by Machine
```sql
SELECT
    ps.schedule_code,
    ps.schedule_name,
    ps.trigger_type,
    ps.frequency_days,
    ps.meter_threshold,
    COUNT(pmwo.id) AS work_orders_generated
FROM pm_schedule ps
LEFT JOIN pm_work_order pmwo ON pmwo.pm_schedule_id = ps.id
WHERE ps.is_active = TRUE
  AND ps.organization_id = 1
  AND ps.plant_id = 1
GROUP BY ps.id
ORDER BY ps.schedule_code;
```

## Metrics Formulas

### MTBF (Mean Time Between Failures)
```
MTBF = Total Operating Time / Number of Failures
```

### MTTR (Mean Time To Repair)
```
MTTR = Total Repair Time / Number of Failures
```

### Availability
```
Availability = MTBF / (MTBF + MTTR)
```

### Operating Time
```
Operating Time = Total Time - All Downtime
```

## File Locations

```
backend/app/domain/entities/maintenance.py              # Domain logic
backend/app/models/maintenance.py                       # Database models
backend/app/application/dtos/maintenance_dto.py         # API contracts
backend/app/infrastructure/repositories/maintenance_repository.py  # Data access
backend/app/presentation/api/v1/maintenance.py          # API endpoints
backend/scripts/pg_cron_pm_generation.sql               # Auto-generation
backend/tests/unit/test_maintenance_entity.py           # Unit tests
backend/tests/integration/test_maintenance_api.py       # Integration tests
```
