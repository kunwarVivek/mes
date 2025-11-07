# Shift Management Domain

**Domain**: Shift Management (MES Module)
**Bounded Context**: Shift Patterns, Shift Handovers, Shift Performance Tracking
**Owner**: Production Management
**Status**: Supporting Domain (Medium Strategic Importance)

---

## Domain Overview

### Purpose

The Shift Management domain manages shift patterns, facilitates shift handovers, and tracks shift-level production performance. It enables 24/7 manufacturing operations with clear accountability and continuous production visibility.

### Scope

**In Scope**:
- Shift pattern definitions (day/night/rotating shifts)
- Shift handover log (WIP status, issues, notes)
- Shift performance tracking (target attainment, OEE, FPY)
- Shift comparison (performance benchmarking)
- Shift scheduling calendar

**Out of Scope**:
- Employee shift assignments → HR system (future integration)
- Attendance tracking → HR system
- Payroll/overtime calculation → HR system

### Key Business Goals

1. **Smooth Handovers**: 100% shift handovers completed before shift end
2. **Performance Visibility**: Real-time shift performance vs target
3. **Shift Accountability**: Track performance by shift for continuous improvement
4. **24/7 Operations**: Support multi-shift manufacturing (2-3 shifts/day)
5. **Best Practice Sharing**: Identify high-performing shifts and share practices

---

## Core Concepts

### Shift Pattern

**Definition**: A recurring work schedule with defined start/end times and target production levels.

**Shift Types**:
- **Day Shift**: Typically 06:00-14:00 (8 hours)
- **Afternoon Shift**: Typically 14:00-22:00 (8 hours)
- **Night Shift**: Typically 22:00-06:00 (8 hours)
- **Rotating Shifts**: Workers rotate through day/afternoon/night

**Shift Attributes**:
```python
shift = {
    "name": "Day Shift",
    "start_time": "06:00",
    "end_time": "14:00",
    "break_duration_minutes": 30,
    "active_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "production_target_units": 100,  # Target output per shift
    "oee_target_percent": 85.0  # Target OEE
}
```

### Shift Handover

**Definition**: A structured communication log at shift end summarizing work status, issues, and actions for the next shift.

**Handover Content**:
```python
handover = {
    "shift_id": 1,
    "date": "2025-11-07",
    "handover_notes": "Completed 95 units (95% target attainment). CNC-001 required tool change at 10:30.",
    "wip_summary": [
        {"work_order": "WO-2025-001", "status": "in_progress", "completion": "80%"},
        {"work_order": "WO-2025-002", "status": "planned", "completion": "0%"}
    ],
    "issues_reported": [
        {"type": "equipment", "description": "Lathe-002 vibration at high speed", "severity": "medium"},
        {"type": "material", "description": "Low stock of stainless steel sheets", "severity": "low"}
    ],
    "logged_by": "John Smith (Day Shift Supervisor)",
    "acknowledged_by": "Jane Doe (Afternoon Shift Supervisor)"
}
```

**Handover Workflow**:
```
1. Outgoing supervisor logs handover notes 15 minutes before shift end
2. System displays handover to incoming supervisor
3. Incoming supervisor acknowledges handover (confirmed read)
4. System tracks handover completion rate (KPI)
```

### Shift Performance

**Definition**: Aggregate production metrics for a specific shift on a specific date.

**Performance Metrics**:
```python
performance = {
    "shift_id": 1,
    "date": "2025-11-07",
    "target_units": 100,
    "actual_units": 95,
    "target_attainment_percent": 95.0,  # (95 / 100) * 100
    "oee_percent": 78.5,  # Availability × Performance × Quality
    "downtime_minutes": 45,
    "quality_fpy_percent": 96.8,  # First Pass Yield
    "calculated_at": "2025-11-07T14:05:00Z"  # 5 minutes after shift end
}
```

**Performance Calculation** (pg_cron job):
```sql
-- Run every hour to calculate shift performance for completed shifts
SELECT cron.schedule(
    'shift-performance-calculation',
    '0 * * * *',  -- Every hour
    $$
    INSERT INTO shift_performance (organization_id, shift_id, date, target_units, actual_units, target_attainment_percent, oee_percent, downtime_minutes, quality_fpy_percent)
    SELECT
        s.organization_id,
        s.id,
        CURRENT_DATE,
        s.production_target_units,
        COALESCE(SUM(pl.quantity_completed), 0),
        (COALESCE(SUM(pl.quantity_completed), 0)::FLOAT / s.production_target_units) * 100,
        AVG(dmo.oee_percent),
        SUM(dds.total_downtime_minutes),
        AVG(il.fpy_percent)
    FROM shifts s
    LEFT JOIN production_logs pl ON pl.logged_at::time BETWEEN s.start_time AND s.end_time AND pl.logged_at::date = CURRENT_DATE
    LEFT JOIN daily_machine_oee dmo ON dmo.day = CURRENT_DATE
    LEFT JOIN daily_downtime_summary dds ON dds.day = CURRENT_DATE
    LEFT JOIN inspection_logs il ON il.inspected_at::time BETWEEN s.start_time AND s.end_time AND il.inspected_at::date = CURRENT_DATE
    WHERE s.is_active = TRUE
    AND NOT EXISTS (SELECT 1 FROM shift_performance WHERE shift_id = s.id AND date = CURRENT_DATE)
    GROUP BY s.organization_id, s.id, s.production_target_units;
    $$
);
```

---

## Database Schema

### Tables (3 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL.

#### 1. shifts

Shift pattern master data.

**Key Columns**:
- `plant_id`: FK to plants
- `name`: Shift name (e.g., "Day Shift", "Night Shift")
- `start_time`: Shift start time (e.g., 06:00)
- `end_time`: Shift end time (e.g., 14:00)
- `break_duration_minutes`: Break time (default 30)
- `active_days`: Array of days (e.g., ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
- `production_target_units`: Target output per shift
- `oee_target_percent`: Target OEE percentage
- `is_active`: Soft delete flag

**Unique Constraint**: `(organization_id, plant_id, name)`

#### 2. shift_handovers

Shift handover log.

**Key Columns**:
- `shift_id`: FK to shifts
- `date`: Handover date
- `handover_notes`: Shift summary (TEXT)
- `wip_summary`: JSONB (work-in-progress status)
- `issues_reported`: JSONB (problems for next shift)
- `logged_by`: FK to users (outgoing supervisor)
- `logged_at`: Timestamp
- `acknowledged_by`: FK to users (incoming supervisor)
- `acknowledged_at`: Timestamp (when incoming supervisor confirmed)

**Unique Constraint**: `(organization_id, shift_id, date)` (one handover per shift per day)

**Indexes**:
- B-tree: shift_id, date DESC
- Partial index: `WHERE acknowledged_by IS NULL` (pending acknowledgments)

#### 3. shift_performance

Shift-level production metrics (calculated by pg_cron).

**Key Columns**:
- `shift_id`: FK to shifts
- `date`: Performance date
- `target_units`: Target production (from shifts.production_target_units)
- `actual_units`: Actual production (from production_logs)
- `target_attainment_percent`: (actual / target) * 100
- `oee_percent`: Average OEE for shift (from daily_machine_oee)
- `downtime_minutes`: Total downtime (from daily_downtime_summary)
- `quality_fpy_percent`: First Pass Yield (from inspection_logs)
- `calculated_at`: Timestamp

**Unique Constraint**: `(organization_id, shift_id, date)`

**Indexes**:
- B-tree: shift_id, date DESC
- Partial index: `WHERE target_attainment_percent < 90` (underperforming shifts)

---

## Business Rules

### BR-SHIFT-001: Shift Times Cannot Overlap

**Rule**: Within a plant, shift time ranges must not overlap.

**Validation**:
```python
class CreateShiftUseCase:
    def execute(self, dto: CreateShiftDTO) -> Shift:
        # Check for overlapping shifts in same plant
        overlapping = self.shift_repo.find_overlapping_shifts(
            plant_id=dto.plant_id,
            start_time=dto.start_time,
            end_time=dto.end_time,
            active_days=dto.active_days
        )

        if overlapping:
            raise ShiftOverlapError(
                plant_id=dto.plant_id,
                conflicting_shift=overlapping[0].name
            )

        # Create shift
        shift = Shift(...)
        return self.shift_repo.save(shift)
```

### BR-SHIFT-002: Handover Required Before Shift End

**Rule**: Shift handover must be logged before shift end time (enforced with alerts, not blocking).

**Implementation**: 15-minute warning notification via LISTEN/NOTIFY

### BR-SHIFT-003: Performance Calculated After Shift Completion

**Rule**: Shift performance is calculated by pg_cron every hour for completed shifts.

**Implementation**: pg_cron job (see Shift Performance calculation above)

---

## Use Cases

### UC-SHIFT-001: Log Shift Handover

**Actor**: Shift Supervisor (outgoing)

**Preconditions**: Shift ending within 15 minutes

**Flow**:
1. Supervisor logs handover notes 15 minutes before shift end
2. Supervisor summarizes WIP status (work orders in progress)
3. Supervisor reports issues for next shift
4. System creates shift_handover record
5. System triggers LISTEN/NOTIFY to alert incoming supervisor

**API**: `POST /api/v1/shift-handovers`

### UC-SHIFT-002: Acknowledge Shift Handover

**Actor**: Shift Supervisor (incoming)

**Preconditions**: Handover logged by outgoing supervisor

**Flow**:
1. Incoming supervisor reviews handover notes
2. Incoming supervisor acknowledges handover (confirmed read)
3. System updates shift_handover.acknowledged_by and acknowledged_at
4. System tracks handover completion rate

**API**: `POST /api/v1/shift-handovers/{id}/acknowledge`

### UC-SHIFT-003: View Shift Performance Comparison

**Actor**: Production Manager

**Preconditions**: Shift performance data exists

**Flow**:
1. User requests shift performance comparison for date range
2. System queries shift_performance table
3. System calculates average metrics per shift
4. System returns comparison chart data (bar chart: Day vs Afternoon vs Night)

**API**: `GET /api/v1/shift-performance/comparison?plant_id=1&from=2025-11-01&to=2025-11-07`

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Shift Endpoints (6 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/shifts` | Create shift pattern |
| GET | `/api/v1/shifts?plant_id=1` | List shifts by plant |
| POST | `/api/v1/shift-handovers` | Log shift handover |
| GET | `/api/v1/shift-handovers?shift_id=1&date=2025-11-07` | Get handover |
| POST | `/api/v1/shift-handovers/{id}/acknowledge` | Acknowledge handover |
| GET | `/api/v1/shift-performance/comparison` | Compare shift performance |

---

## PostgreSQL-Native Features

### 1. pg_cron for Shift Performance Calculation

**Purpose**: Automated hourly calculation of shift performance metrics

**Performance**: Native PostgreSQL, no external services

### 2. JSONB for WIP Summary and Issues

**Purpose**: Flexible storage for structured shift handover data

**Query Example**:
```sql
-- Find handovers with material shortage issues
SELECT * FROM shift_handovers
WHERE issues_reported @> '[{"type": "material"}]'::jsonb;
```

### 3. LISTEN/NOTIFY for Handover Alerts

**Purpose**: Real-time alerts for incoming supervisors

---

## Summary

The Shift Management domain manages shift patterns, handovers, and performance tracking for 24/7 operations. Key features:

- **pg_cron**: Auto-calculate shift performance hourly
- **JSONB**: Flexible WIP and issue tracking
- **LISTEN/NOTIFY**: Real-time handover alerts

**Targets**:
- Handover completion: 100%
- Target attainment: >95%
- OEE by shift: >85%

**Next Domain**: [VISUAL_SCHEDULING.md](./VISUAL_SCHEDULING.md)
