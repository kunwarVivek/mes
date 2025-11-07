# Visual Production Scheduling Domain

**Domain**: Visual Production Scheduling (MES Module)
**Bounded Context**: Gantt Chart Scheduling, Drag-and-Drop Planning, Capacity Visualization
**Owner**: Production Planning & Control
**Status**: Supporting Domain (Medium Strategic Importance)

---

## Domain Overview

### Purpose

The Visual Production Scheduling domain provides interactive Gantt chart visualization for production planning with drag-and-drop work order scheduling, real-time capacity visualization, and conflict detection. It enables planners to optimize resource utilization and meet delivery commitments.

### Scope

**In Scope**:
- Gantt chart data API (work orders, lanes, time slots)
- Drag-and-drop schedule updates (re-assign work orders to lanes/dates)
- Capacity visualization (lane availability, overload warnings)
- Schedule conflict detection (overlapping assignments)
- Multi-week view (2-4 week planning horizon)
- Schedule export (PDF, Excel)

**Out of Scope**:
- Gantt chart rendering → Frontend (frappe-gantt React component)
- Auto-scheduling algorithms → Future enhancement
- Material availability checking → Material domain (cross-check)
- Employee skill matching → HR system (future integration)

### Key Business Goals

1. **Visual Planning**: Drag-and-drop interface for intuitive scheduling
2. **Capacity Optimization**: 75%+ lane utilization
3. **Conflict Prevention**: Zero overlapping assignments
4. **On-Time Delivery**: 90%+ projects delivered on planned dates
5. **Multi-Week Visibility**: 2-4 week production visibility

---

## Core Concepts

### Gantt Chart Data Structure

**Definition**: Work orders displayed as bars on a timeline, grouped by lane (resource).

**Data Format** (frappe-gantt compatible):
```json
{
  "view_mode": "Week",
  "date_range": {
    "start": "2025-11-01",
    "end": "2025-11-28"
  },
  "lanes": [
    {
      "id": 1,
      "name": "Lane 1 - Fabrication",
      "capacity": 1,
      "work_orders": [
        {
          "id": "WO-2025-001",
          "name": "Fabricate steel frame",
          "start": "2025-11-07",
          "end": "2025-11-12",
          "progress": 60,
          "status": "in_progress",
          "custom_class": "bar-milestone"
        },
        {
          "id": "WO-2025-003",
          "name": "Weld assembly",
          "start": "2025-11-13",
          "end": "2025-11-15",
          "progress": 0,
          "status": "planned",
          "dependencies": ["WO-2025-001"]
        }
      ]
    },
    {
      "id": 2,
      "name": "Lane 2 - Assembly",
      "capacity": 1,
      "work_orders": [
        {
          "id": "WO-2025-002",
          "name": "Final assembly",
          "start": "2025-11-16",
          "end": "2025-11-20",
          "progress": 0,
          "status": "released",
          "dependencies": ["WO-2025-003"]
        }
      ]
    }
  ]
}
```

### Drag-and-Drop Schedule Update

**Definition**: User drags a work order bar to a new lane or date, triggering schedule update.

**Update Logic**:
```python
class UpdateScheduleUseCase:
    def execute(self, dto: UpdateScheduleDTO) -> RBSSchedule:
        # Validate new schedule
        conflicts = self._check_conflicts(
            lane_id=dto.new_lane_id,
            start_date=dto.new_start_date,
            end_date=dto.new_end_date,
            exclude_work_order_id=dto.work_order_id
        )

        if conflicts:
            raise ScheduleConflictError(conflicts)

        # Update RBS schedule
        schedule = self.schedule_repo.find_by_work_order(dto.work_order_id, dto.schedule_date)
        schedule.lane_id = dto.new_lane_id
        schedule.planned_start_time = dto.new_start_time
        schedule.planned_end_time = dto.new_end_time

        # Update work order dates
        work_order = self.work_order_repo.find_by_id(dto.work_order_id)
        work_order.planned_start_date = dto.new_start_date
        work_order.planned_end_date = dto.new_end_date

        return self.schedule_repo.save(schedule)
```

### Capacity Visualization

**Definition**: Visual indicators showing lane capacity utilization (green: <75%, yellow: 75-90%, red: >90%).

**Capacity Calculation**:
```python
def calculate_lane_capacity(lane_id: int, date_range: tuple) -> dict:
    # Get all scheduled work orders for lane
    schedules = rbs_repo.find_by_lane_and_date_range(lane_id, date_range)

    # Calculate total scheduled hours
    total_scheduled_hours = sum(
        (s.planned_end_time - s.planned_start_time).total_seconds() / 3600
        for s in schedules
    )

    # Calculate available hours (8 hours/day * days)
    days = (date_range[1] - date_range[0]).days
    total_available_hours = days * 8

    # Utilization percentage
    utilization = (total_scheduled_hours / total_available_hours) * 100

    return {
        "lane_id": lane_id,
        "utilization_percent": utilization,
        "status": "overloaded" if utilization > 100 else "high" if utilization > 75 else "normal",
        "color": "red" if utilization > 100 else "yellow" if utilization > 75 else "green"
    }
```

### Schedule Conflict Detection

**Definition**: Detect overlapping work order assignments to the same lane.

**Conflict Check**:
```sql
-- Check for overlapping schedules on same lane
SELECT * FROM rbs_schedules
WHERE lane_id = $1
AND schedule_date = $2
AND status != 'cancelled'
AND (
    (planned_start_time, planned_end_time) OVERLAPS ($3, $4)
);
```

---

## Database Schema

### Tables

**Primary Table**: `rbs_schedules` (Resource-Based Scheduling)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL.

**Key Columns**:
- `plant_id`: FK to plants
- `schedule_date`: Date (e.g., 2025-11-07)
- `work_order_id`: FK to work_orders
- `lane_id`: FK to lanes
- `planned_start_time`: Time (e.g., 08:00)
- `planned_end_time`: Time (e.g., 12:00)
- `actual_start_time`: Actual start (NULL if not started)
- `actual_end_time`: Actual end (NULL if not completed)
- `status`: Enum (scheduled, in_progress, completed, cancelled)

**Indexes**:
- B-tree: schedule_date, plant_id, lane_id, status
- Partial index: `WHERE schedule_date >= CURRENT_DATE` (future schedules)

**Conflict Detection Index**:
```sql
-- GiST index for time range overlap detection
CREATE INDEX idx_rbs_schedules_time_overlap ON rbs_schedules
USING GIST (
    lane_id,
    tstzrange(
        schedule_date + planned_start_time,
        schedule_date + planned_end_time
    )
)
WHERE status != 'cancelled';
```

---

## Business Rules

### BR-SCHED-001: No Overlapping Assignments

**Rule**: A lane cannot have overlapping work order assignments on the same date.

**Validation**: See conflict check SQL above

### BR-SCHED-002: Work Order Dates Must Match Schedule

**Rule**: When a work order is scheduled via RBS, the work order's `planned_start_date` and `planned_end_date` must be updated to match the schedule.

**Implementation**: UpdateScheduleUseCase (see above)

### BR-SCHED-003: Capacity Warning at 75% Utilization

**Rule**: Display warning when lane utilization exceeds 75% for any week.

**Implementation**: Frontend visualization with color coding

---

## Use Cases

### UC-SCHED-001: Get Gantt Chart Data

**Actor**: Production Planner

**Preconditions**: RBS schedules exist

**Flow**:
1. User requests Gantt chart for plant and date range
2. System queries rbs_schedules with lane assignments
3. System formats data for frappe-gantt library
4. System calculates capacity utilization for each lane
5. System returns Gantt chart JSON

**API**: `GET /api/v1/schedule/gantt?plant_id=1&from=2025-11-01&to=2025-11-28`

### UC-SCHED-002: Drag-and-Drop Reschedule

**Actor**: Production Planner

**Preconditions**: User has `schedule:update` permission

**Flow**:
1. User drags work order bar to new lane or date
2. Frontend sends schedule update request
3. System checks for conflicts (BR-SCHED-001)
4. System updates RBS schedule and work order dates (BR-SCHED-002)
5. System returns updated Gantt chart data
6. System triggers LISTEN/NOTIFY for real-time updates

**API**: `PUT /api/v1/schedule/reschedule`

### UC-SCHED-003: Detect Schedule Conflicts

**Actor**: System (validation)

**Preconditions**: Scheduling change requested

**Flow**:
1. System checks for overlapping assignments on target lane
2. If conflicts found, return error with conflicting work orders
3. User adjusts schedule to resolve conflicts

**API**: Validation within reschedule endpoint

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Scheduling Endpoints (5 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/schedule/gantt` | Get Gantt chart data (frappe-gantt format) |
| PUT | `/api/v1/schedule/reschedule` | Drag-and-drop schedule update |
| GET | `/api/v1/schedule/capacity` | Get lane capacity utilization |
| POST | `/api/v1/schedule/validate` | Check for schedule conflicts |
| GET | `/api/v1/schedule/export` | Export schedule (PDF/Excel) |

### Example: Get Gantt Chart Data

```http
GET /api/v1/schedule/gantt?plant_id=1&from=2025-11-01&to=2025-11-28&view_mode=Week
Authorization: Bearer {jwt_token}
```

**Response (200 OK)**: See Gantt Chart Data Structure above

### Example: Reschedule Work Order

```http
PUT /api/v1/schedule/reschedule
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "work_order_id": 123,
  "schedule_date": "2025-11-07",
  "new_lane_id": 2,
  "new_start_date": "2025-11-10",
  "new_end_date": "2025-11-12",
  "new_start_time": "08:00",
  "new_end_time": "16:00"
}
```

**Response (200 OK)**:
```json
{
  "schedule_id": 456,
  "work_order_id": 123,
  "work_order_number": "WO-2025-001",
  "lane_id": 2,
  "lane_name": "Lane 2 - Assembly",
  "schedule_date": "2025-11-10",
  "planned_start_time": "08:00",
  "planned_end_time": "16:00",
  "conflicts": null,
  "capacity_status": "normal"
}
```

---

## PostgreSQL-Native Features

### 1. GiST Index for Time Range Overlap Detection

**Purpose**: Fast conflict detection for overlapping schedules

**Query Performance**: O(log n) vs O(n) for sequential scan

**Query Example**:
```sql
-- Find overlapping schedules (uses GiST index)
SELECT * FROM rbs_schedules
WHERE lane_id = 1
AND tstzrange(
    schedule_date + planned_start_time,
    schedule_date + planned_end_time
) && tstzrange($1, $2);
```

### 2. LISTEN/NOTIFY for Real-Time Schedule Updates

**Purpose**: Live Gantt chart updates when schedules change

---

## Frontend Integration

### frappe-gantt React Component

**Library**: https://github.com/frappe/gantt

**Integration**:
```jsx
import Gantt from 'frappe-gantt-react';

function ScheduleGantt() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetch('/api/v1/schedule/gantt?plant_id=1&from=2025-11-01&to=2025-11-28')
      .then(res => res.json())
      .then(data => {
        // Flatten lanes into tasks for frappe-gantt
        const flatTasks = data.lanes.flatMap(lane =>
          lane.work_orders.map(wo => ({
            ...wo,
            lane_name: lane.name
          }))
        );
        setTasks(flatTasks);
      });
  }, []);

  const handleTaskChange = (task, start, end) => {
    // Send reschedule request
    fetch('/api/v1/schedule/reschedule', {
      method: 'PUT',
      body: JSON.stringify({
        work_order_id: task.id,
        new_start_date: start,
        new_end_date: end
      })
    });
  };

  return (
    <Gantt
      tasks={tasks}
      viewMode="Week"
      onDateChange={handleTaskChange}
    />
  );
}
```

---

## Summary

The Visual Production Scheduling domain provides interactive Gantt chart planning with drag-and-drop rescheduling. Key features:

- **GiST index**: Fast conflict detection (O(log n))
- **LISTEN/NOTIFY**: Real-time Gantt updates
- **frappe-gantt**: Modern React-based Gantt chart library
- **Capacity visualization**: Color-coded utilization warnings

**Targets**:
- Lane utilization: 75%+
- Zero scheduling conflicts
- 2-4 week planning visibility

**Next Domain**: [TRACEABILITY.md](./TRACEABILITY.md) (Final domain doc)
