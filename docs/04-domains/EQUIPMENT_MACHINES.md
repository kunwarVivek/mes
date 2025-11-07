# Equipment & Machines Domain

**Domain**: Equipment & Machines (MES Module)
**Bounded Context**: Machine Registry, OEE Tracking, Equipment Utilization
**Owner**: Production & Maintenance
**Status**: Supporting Domain (Medium Strategic Importance)

---

## Domain Overview

### Purpose

The Equipment & Machines domain maintains the machine/equipment registry and tracks real-time equipment performance through Overall Equipment Effectiveness (OEE) and utilization metrics. It provides the foundation for production capacity planning and maintenance scheduling.

### Scope

**In Scope**:
- Machine master data (registry, specifications, location)
- Machine status tracking (available, running, idle, down, setup, maintenance)
- Machine status history (timescaledb hypertable for time-series data)
- OEE calculation (Availability × Performance × Quality)
- Equipment utilization tracking (running hours, idle hours, down hours)
- Machine assignment to work orders
- Real-time machine status dashboard (LISTEN/NOTIFY)

**Out of Scope**:
- Preventive maintenance scheduling → Maintenance domain
- Downtime event details → Maintenance domain
- Production logging → Production domain

### Key Business Goals

1. **High OEE**: Target 85%+ OEE for critical equipment
2. **Equipment Utilization**: 75%+ utilization rate (running + setup)
3. **Real-Time Visibility**: Live machine status across plant
4. **Capacity Planning**: Accurate capacity data for scheduling
5. **Performance Trends**: OEE trends for continuous improvement

---

## Core Concepts

### Machine

**Definition**: A physical piece of equipment used in production (CNC machine, lathe, press, welder, etc.).

**Machine Types**:
- **CNC**: Computer Numerical Control machines
- **Lathe**: Turning/boring machines
- **Press**: Stamping/forming presses
- **Welder**: Welding equipment
- **Assembly**: Assembly workstations
- **Testing**: Test/inspection equipment

**Machine Status**:
```python
class MachineStatus(Enum):
    AVAILABLE = "available"     # Ready for work, not assigned
    RUNNING = "running"         # Actively producing
    IDLE = "idle"               # Assigned but not producing
    DOWN = "down"               # Failure/breakdown
    SETUP = "setup"             # Changeover/setup in progress
    MAINTENANCE = "maintenance" # PM or corrective maintenance
    DECOMMISSIONED = "decommissioned"  # Retired/scrapped
```

**Machine Attributes**:
```python
machine = {
    "machine_code": "CNC-001",
    "name": "Haas VF-2 CNC Mill",
    "machine_type": "CNC",
    "capacity_units_per_hour": 12.0,  # Rated capacity
    "status": "running",
    "current_work_order_id": 123,
    "last_maintenance_date": "2025-10-15",
    "next_maintenance_due": "2025-11-15",
    "installation_date": "2020-05-01",
    "manufacturer": "Haas Automation",
    "model_number": "VF-2",
    "serial_number": "1234567",
    "location": "Plant 1 - Bay A"
}
```

### Machine Status History

**Definition**: Time-series log of machine status changes for OEE calculation.

**Status Transition Example**:
```
2025-11-07 08:00 | available → running (WO-2025-001 started)
2025-11-07 10:30 | running → idle (waiting for material)
2025-11-07 11:00 | idle → running (material received)
2025-11-07 15:00 | running → setup (changeover to WO-2025-002)
2025-11-07 16:00 | setup → running (WO-2025-002 started)
2025-11-07 18:00 | running → available (WO-2025-002 completed)
```

**Duration Calculation**:
```python
# When status changes, calculate duration of previous status
duration_minutes = (new_changed_at - previous_changed_at).total_seconds() / 60

# Example:
# Running: 08:00 - 10:30 = 150 minutes
# Idle: 10:30 - 11:00 = 30 minutes
# Running: 11:00 - 15:00 = 240 minutes
```

### Overall Equipment Effectiveness (OEE)

**Definition**: Manufacturing best practice metric = Availability × Performance × Quality

**Components**:
```python
# Availability: % of scheduled time machine was available for production
availability = (running_time + setup_time) / (running_time + setup_time + down_time)

# Performance: Actual output vs theoretical maximum output
performance = actual_units / (running_time * capacity_per_hour)

# Quality: Good units / total units produced
quality = good_units / total_units  # From FPY (First Pass Yield)

# OEE
oee = availability * performance * quality
```

**Example Calculation**:
```python
# 8-hour shift (480 minutes)
running_time = 360 minutes
setup_time = 60 minutes
down_time = 60 minutes

availability = (360 + 60) / (360 + 60 + 60) = 0.875 = 87.5%

# Machine capacity: 12 units/hour
# Running time: 6 hours
# Theoretical output: 72 units
# Actual output: 65 units
performance = 65 / 72 = 0.903 = 90.3%

# Total produced: 65 units
# Good units (passed inspection): 62 units
quality = 62 / 65 = 0.954 = 95.4%

oee = 0.875 * 0.903 * 0.954 = 0.753 = 75.3%
```

**OEE Classification**:
- **World Class**: OEE >85%
- **Good**: OEE 65-85%
- **Fair**: OEE 40-65%
- **Poor**: OEE <40%

### Equipment Utilization

**Definition**: Percentage of time equipment is actively used (running + setup) vs available time.

**Calculation**:
```python
utilization = (running_hours + setup_hours) / total_available_hours

# Example:
# Total shift: 8 hours
# Running: 6 hours
# Setup: 1 hour
# Idle: 0.5 hours
# Down: 0.5 hours
utilization = (6 + 1) / 8 = 0.875 = 87.5%
```

---

## Database Schema

### Tables (2 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL.

#### 1. machines

Machine master data registry.

**Key Columns**:
- `machine_code`: Unique identifier (e.g., "CNC-001")
- `name`: Human-readable name
- `machine_type`: Enum (CNC, Lathe, Press, Welder, etc.)
- `capacity_units_per_hour`: Rated production capacity
- `status`: Enum (available, running, idle, down, setup, maintenance, decommissioned)
- `current_work_order_id`: FK to work_orders (if assigned)
- `last_maintenance_date`: Last PM completion date
- `next_maintenance_due`: Next PM due date
- `installation_date`: Commission date
- `manufacturer`, `model_number`, `serial_number`: Equipment specs
- `location`: Physical location in plant

**Indexes**:
- B-tree: plant_id, status, next_maintenance_due
- Partial index: `WHERE is_active = TRUE AND status != 'decommissioned'`

**LISTEN/NOTIFY Trigger** (real-time machine status updates):
```sql
CREATE OR REPLACE FUNCTION notify_machine_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        PERFORM pg_notify('machine_status_changed',
            json_build_object(
                'machine_id', NEW.id,
                'machine_code', NEW.machine_code,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'work_order_id', NEW.current_work_order_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER machine_status_notify
AFTER UPDATE ON machines
FOR EACH ROW EXECUTE FUNCTION notify_machine_status_change();
```

#### 2. machine_status_history

Time-series log of machine status changes (timescaledb hypertable).

**Key Columns**:
- `machine_id`: FK to machines
- `previous_status`: Previous status
- `new_status`: New status
- `work_order_id`: FK to work_orders (if status change related to WO)
- `reason_code`: For 'down' transitions (e.g., "mechanical_failure")
- `notes`: Status change notes
- `changed_by`: FK to users
- `changed_at`: Timestamp
- `duration_minutes`: Duration in previous status (calculated when next status change occurs)

**timescaledb Hypertable**:
```sql
SELECT create_hypertable('machine_status_history', 'changed_at',
    chunk_time_interval => INTERVAL '1 month'
);

-- Compression after 7 days
ALTER TABLE machine_status_history SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, machine_id, new_status'
);
SELECT add_compression_policy('machine_status_history', INTERVAL '7 days');

-- 2-year retention
SELECT add_retention_policy('machine_status_history', INTERVAL '2 years');
```

**Continuous Aggregate** (daily machine OEE):
```sql
CREATE MATERIALIZED VIEW daily_machine_oee
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', changed_at) AS day,
    organization_id,
    machine_id,
    SUM(CASE WHEN new_status = 'running' THEN duration_minutes ELSE 0 END) AS running_minutes,
    SUM(CASE WHEN new_status = 'idle' THEN duration_minutes ELSE 0 END) AS idle_minutes,
    SUM(CASE WHEN new_status = 'down' THEN duration_minutes ELSE 0 END) AS down_minutes,
    SUM(CASE WHEN new_status = 'setup' THEN duration_minutes ELSE 0 END) AS setup_minutes,
    SUM(CASE WHEN new_status IN ('running', 'setup') THEN duration_minutes ELSE 0 END) AS available_minutes,
    SUM(duration_minutes) AS total_minutes,
    -- Availability calculation
    CASE WHEN SUM(duration_minutes) > 0 THEN
        SUM(CASE WHEN new_status IN ('running', 'setup') THEN duration_minutes ELSE 0 END)::FLOAT / SUM(duration_minutes)::FLOAT
    ELSE 0 END AS availability_percent
FROM machine_status_history
WHERE duration_minutes IS NOT NULL
GROUP BY day, organization_id, machine_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_machine_oee',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

---

## Business Rules

### BR-EQUIP-001: Machine Status Transitions

**Rule**: Machine status must follow allowed transitions:

```python
ALLOWED_TRANSITIONS = {
    MachineStatus.AVAILABLE: {MachineStatus.RUNNING, MachineStatus.SETUP, MachineStatus.MAINTENANCE, MachineStatus.DECOMMISSIONED},
    MachineStatus.RUNNING: {MachineStatus.IDLE, MachineStatus.DOWN, MachineStatus.SETUP, MachineStatus.MAINTENANCE, MachineStatus.AVAILABLE},
    MachineStatus.IDLE: {MachineStatus.RUNNING, MachineStatus.DOWN, MachineStatus.AVAILABLE},
    MachineStatus.DOWN: {MachineStatus.MAINTENANCE, MachineStatus.AVAILABLE},
    MachineStatus.SETUP: {MachineStatus.RUNNING, MachineStatus.AVAILABLE},
    MachineStatus.MAINTENANCE: {MachineStatus.AVAILABLE, MachineStatus.DECOMMISSIONED},
    MachineStatus.DECOMMISSIONED: set()  # Terminal state
}
```

### BR-EQUIP-002: Duration Calculation on Status Change

**Rule**: When machine status changes, calculate `duration_minutes` for the previous status change record.

**Implementation** (PostgreSQL trigger):
```sql
CREATE OR REPLACE FUNCTION calculate_status_duration() RETURNS TRIGGER AS $$
BEGIN
    -- Update previous status history record with duration
    UPDATE machine_status_history
    SET duration_minutes = EXTRACT(EPOCH FROM (NEW.changed_at - changed_at)) / 60
    WHERE machine_id = NEW.machine_id
    AND duration_minutes IS NULL
    AND id != NEW.id
    ORDER BY changed_at DESC
    LIMIT 1;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_duration_trigger
AFTER INSERT ON machine_status_history
FOR EACH ROW EXECUTE FUNCTION calculate_status_duration();
```

### BR-EQUIP-003: OEE Requires Availability, Performance, Quality

**Rule**: OEE calculation requires all three components (availability from machine_status_history, performance from production_logs, quality from FPY).

**Implementation**:
```python
class CalculateOEEUseCase:
    def execute(self, machine_id: int, date: date) -> OEEMetrics:
        # Get availability from timescaledb continuous aggregate
        machine_stats = self.machine_repo.get_daily_oee(machine_id, date)
        availability = machine_stats.availability_percent / 100.0

        # Get performance from production logs
        production = self.production_repo.get_daily_production(machine_id, date)
        theoretical_output = machine.capacity_units_per_hour * (machine_stats.running_minutes / 60.0)
        performance = production.actual_units / theoretical_output if theoretical_output > 0 else 0

        # Get quality from inspection logs (FPY)
        quality = self.quality_repo.get_daily_fpy(machine_id, date) / 100.0

        # Calculate OEE
        oee = availability * performance * quality

        return OEEMetrics(
            machine_id=machine_id,
            date=date,
            availability=availability,
            performance=performance,
            quality=quality,
            oee=oee
        )
```

---

## Use Cases

### UC-EQUIP-001: Change Machine Status

**Actor**: Operator, Maintenance Technician, System

**Preconditions**: Machine exists

**Flow**:
1. User/system changes machine status (e.g., available → running)
2. System validates allowed transition (BR-EQUIP-001)
3. System creates machine_status_history record
4. System updates machines.status
5. System calculates previous status duration (BR-EQUIP-002)
6. System triggers LISTEN/NOTIFY for real-time dashboard update

**API**: `PUT /api/v1/machines/{id}/status`

### UC-EQUIP-002: View Machine OEE Dashboard

**Actor**: Production Manager, Plant Manager

**Preconditions**: Machine status history exists

**Flow**:
1. User requests OEE dashboard for plant/date range
2. System queries timescaledb continuous aggregate (daily_machine_oee)
3. System calculates OEE for each machine (BR-EQUIP-003)
4. System returns OEE metrics with color coding (green >85%, yellow 65-85%, red <65%)

**API**: `GET /api/v1/machines/oee-dashboard?plant_id=1&from=2025-11-01&to=2025-11-07`

### UC-EQUIP-003: View Machine Utilization Report

**Actor**: Production Planner

**Preconditions**: Machine status history exists

**Flow**:
1. User requests utilization report for plant/date range
2. System queries daily_machine_oee continuous aggregate
3. System calculates utilization = (running + setup) / total
4. System returns utilization metrics sorted by utilization %

**API**: `GET /api/v1/machines/utilization-report?plant_id=1&from=2025-11-01&to=2025-11-07`

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Machine Endpoints (8 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/machines` | Create machine |
| GET | `/api/v1/machines` | List machines (by plant) |
| GET | `/api/v1/machines/{id}` | Get machine details |
| PUT | `/api/v1/machines/{id}` | Update machine |
| PUT | `/api/v1/machines/{id}/status` | Change machine status |
| GET | `/api/v1/machines/{id}/status-history` | Get status history |
| GET | `/api/v1/machines/oee-dashboard` | Get OEE metrics |
| GET | `/api/v1/machines/utilization-report` | Get utilization report |

### Example: Change Machine Status

```http
PUT /api/v1/machines/5/status
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "new_status": "running",
  "work_order_id": 123,
  "notes": "Started production on WO-2025-001"
}
```

**Response (200 OK)**:
```json
{
  "machine_id": 5,
  "machine_code": "CNC-001",
  "previous_status": "available",
  "new_status": "running",
  "work_order_id": 123,
  "changed_at": "2025-11-07T20:00:00Z",
  "status_history_id": 12345
}
```

### Example: Get OEE Dashboard

```http
GET /api/v1/machines/oee-dashboard?plant_id=1&from=2025-11-01&to=2025-11-07
Authorization: Bearer {jwt_token}
```

**Response (200 OK)**:
```json
{
  "plant_id": 1,
  "plant_name": "Plant 1 - Main Fabrication",
  "date_range": {
    "from": "2025-11-01",
    "to": "2025-11-07"
  },
  "machines": [
    {
      "machine_id": 5,
      "machine_code": "CNC-001",
      "machine_name": "Haas VF-2 CNC Mill",
      "oee_metrics": {
        "availability": 0.875,
        "performance": 0.903,
        "quality": 0.954,
        "oee": 0.753
      },
      "classification": "good",
      "color": "yellow",
      "running_hours": 42.0,
      "idle_hours": 3.0,
      "down_hours": 3.0,
      "setup_hours": 6.0
    }
  ],
  "plant_average_oee": 0.712
}
```

---

## PostgreSQL-Native Features

### 1. timescaledb Hypertable (machine_status_history)

**Purpose**: Time-series optimization for machine status history

**Query Performance**: 10x faster queries with 75% compression

**Continuous Aggregate**: daily_machine_oee (auto-refreshed hourly)

### 2. LISTEN/NOTIFY for Real-Time Machine Status

**Purpose**: Live machine status dashboard updates (no polling)

### 3. PostgreSQL Trigger for Duration Calculation

**Purpose**: Auto-calculate status duration when status changes

---

## Summary

The Equipment & Machines domain tracks machine registry and real-time performance through OEE and utilization metrics. Key features:

- **timescaledb**: 10x faster OEE queries with 75% compression
- **Continuous aggregate**: Real-time OEE dashboard (hourly refresh)
- **LISTEN/NOTIFY**: Live machine status updates
- **PostgreSQL trigger**: Auto-calculate status durations

**Targets**:
- OEE: >85% (world class)
- Utilization: >75%
- Real-time visibility: <50ms latency

**Next Domain**: [SHIFT_MANAGEMENT.md](./SHIFT_MANAGEMENT.md)
