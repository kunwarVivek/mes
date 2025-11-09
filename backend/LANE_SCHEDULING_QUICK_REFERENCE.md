# Lane Scheduling Module - Quick Reference

## API Endpoints

### Lanes

```http
POST   /api/v1/lanes                          Create lane
GET    /api/v1/lanes                          List lanes (filtered, paginated)
GET    /api/v1/lanes/{lane_id}                Get single lane
PUT    /api/v1/lanes/{lane_id}                Update lane
DELETE /api/v1/lanes/{lane_id}                Soft delete lane
GET    /api/v1/lanes/{lane_id}/capacity       Get capacity utilization
```

### Lane Assignments

```http
POST   /api/v1/lanes/assignments              Create assignment
GET    /api/v1/lanes/assignments              List assignments (filtered, paginated)
GET    /api/v1/lanes/assignments/{id}         Get single assignment
PUT    /api/v1/lanes/assignments/{id}         Update assignment
DELETE /api/v1/lanes/assignments/{id}         Delete assignment
```

## Request Examples

### Create Lane
```json
POST /api/v1/lanes
{
  "plant_id": 1,
  "lane_code": "L001",
  "lane_name": "Assembly Line 1",
  "capacity_per_day": "100.000"
}
```

### Create Assignment
```json
POST /api/v1/lanes/assignments
{
  "organization_id": 1,
  "plant_id": 1,
  "lane_id": 1,
  "work_order_id": 100,
  "project_id": 10,
  "scheduled_start": "2025-01-01",
  "scheduled_end": "2025-01-05",
  "allocated_capacity": "50.000",
  "priority": 1,
  "notes": "Priority production"
}
```

### List Lanes (Filtered)
```http
GET /api/v1/lanes?plant_id=1&is_active=true&page=1&page_size=20
```

### List Assignments (Calendar View)
```http
GET /api/v1/lanes/assignments?lane_id=1&start_date=2025-01-01&end_date=2025-01-31&status=ACTIVE
```

### Get Lane Capacity
```http
GET /api/v1/lanes/1/capacity?date=2025-01-15
```

## Response Examples

### Lane Response
```json
{
  "id": 1,
  "plant_id": 1,
  "lane_code": "L001",
  "lane_name": "Assembly Line 1",
  "capacity_per_day": "100.000",
  "is_active": true,
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": null
}
```

### Lane List Response
```json
{
  "items": [
    {
      "id": 1,
      "plant_id": 1,
      "lane_code": "L001",
      "lane_name": "Assembly Line 1",
      "capacity_per_day": "100.000",
      "is_active": true,
      "created_at": "2025-01-01T08:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

### Assignment Response
```json
{
  "id": 1,
  "organization_id": 1,
  "plant_id": 1,
  "lane_id": 1,
  "work_order_id": 100,
  "project_id": 10,
  "scheduled_start": "2025-01-01",
  "scheduled_end": "2025-01-05",
  "allocated_capacity": "50.000",
  "priority": 1,
  "status": "PLANNED",
  "notes": "Priority production",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": null
}
```

### Capacity Response
```json
{
  "lane_id": 1,
  "date": "2025-01-15",
  "total_capacity": "100.000",
  "allocated_capacity": "75.000",
  "available_capacity": "25.000",
  "utilization_rate": "75.00",
  "assignment_count": 3
}
```

## Status Values

```python
class LaneAssignmentStatus:
    PLANNED = "PLANNED"       # Assignment created but not started
    ACTIVE = "ACTIVE"         # Currently in production
    COMPLETED = "COMPLETED"   # Production finished
    CANCELLED = "CANCELLED"   # Assignment cancelled
```

## Validation Rules

### Lane
- **lane_code**: 1-50 characters, uppercase alphanumeric with dashes/underscores only
- **lane_name**: 1-200 characters
- **capacity_per_day**: Must be > 0
- **plant_id**: Must be valid plant
- **Uniqueness**: lane_code must be unique per plant

### Assignment
- **scheduled_end**: Must be >= scheduled_start
- **allocated_capacity**: Must be > 0, cannot exceed lane's capacity_per_day
- **priority**: Must be >= 0
- **lane_id**: Must exist
- **All IDs**: Must be positive integers

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Allocated capacity 150.000 exceeds lane daily capacity 100.000"
}
```

### 404 Not Found
```json
{
  "detail": "Lane 999 not found"
}
```

### 409 Conflict
```json
{
  "detail": "Lane code L001 already exists in plant 1"
}
```

## Database Schema

### Lanes Table
```sql
id                  SERIAL PRIMARY KEY
plant_id            INTEGER NOT NULL → plants.id
lane_code           VARCHAR(50) NOT NULL
lane_name           VARCHAR(200) NOT NULL
capacity_per_day    NUMERIC(15,3) NOT NULL
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMPTZ DEFAULT NOW()
updated_at          TIMESTAMPTZ

UNIQUE (plant_id, lane_code)
CHECK (capacity_per_day > 0)
```

### Lane Assignments Table
```sql
id                  SERIAL PRIMARY KEY
organization_id     INTEGER NOT NULL → organizations.id
plant_id            INTEGER NOT NULL → plants.id
lane_id             INTEGER NOT NULL → lanes.id
work_order_id       INTEGER NOT NULL → work_order.id
project_id          INTEGER → projects.id (nullable)
scheduled_start     DATE NOT NULL
scheduled_end       DATE NOT NULL
allocated_capacity  NUMERIC(15,3) NOT NULL
priority            INTEGER DEFAULT 0
status              VARCHAR(20) DEFAULT 'PLANNED'
notes               TEXT
created_at          TIMESTAMPTZ DEFAULT NOW()
updated_at          TIMESTAMPTZ

CHECK (scheduled_end >= scheduled_start)
CHECK (allocated_capacity > 0)
```

## Key Indexes

```sql
-- Lane indexes
idx_lane_plant              (plant_id)
idx_lane_active             (is_active)

-- Assignment indexes
idx_lane_assign_org         (organization_id)
idx_lane_assign_plant       (plant_id)
idx_lane_assign_lane_dates  (lane_id, scheduled_start, scheduled_end)  -- Calendar queries
idx_lane_assign_wo          (work_order_id)
idx_lane_assign_project     (project_id) WHERE project_id IS NOT NULL
idx_lane_assign_status      (status)
```

## Common Use Cases

### 1. Calendar View (Gantt Chart)
```http
GET /api/v1/lanes/assignments?
    plant_id=1&
    start_date=2025-01-01&
    end_date=2025-01-31&
    status=ACTIVE,PLANNED
```

### 2. Lane Utilization
```http
GET /api/v1/lanes/1/capacity?date=2025-01-15
```

### 3. Work Order Scheduling
```http
POST /api/v1/lanes/assignments
{
  "lane_id": 1,
  "work_order_id": 100,
  "scheduled_start": "2025-01-10",
  "scheduled_end": "2025-01-15",
  "allocated_capacity": "40.000"
}
```

### 4. Plant Capacity Overview
```http
GET /api/v1/lanes?plant_id=1&is_active=true
```

### 5. Assignment Rescheduling
```http
PUT /api/v1/lanes/assignments/1
{
  "scheduled_start": "2025-01-12",
  "scheduled_end": "2025-01-17",
  "priority": 2
}
```

## Testing

### Run All Tests
```bash
python3 -m pytest tests/unit/test_lane_*.py -v
```

### Test Coverage
- **Entity Tests**: 16 tests
- **DTO Tests**: 20 tests
- **Repository Tests**: 26 tests
- **Total**: 62 tests (100% passing)

## File Locations

```
/backend/app/
├── domain/entities/lane.py              # Domain entities
├── application/dtos/lane_dto.py         # Request/response DTOs
├── models/lane.py                        # SQLAlchemy models
├── infrastructure/repositories/
│   └── lane_repository.py               # Data access layer
└── presentation/api/v1/
    └── lanes.py                          # API endpoints

/backend/tests/unit/
├── test_lane_entity.py                   # Entity tests
├── test_lane_dto.py                      # DTO tests
└── test_lane_repository.py               # Repository tests
```

## Implementation Notes

1. **Capacity Management**: Assignments cannot exceed lane's daily capacity
2. **Multi-Tenancy**: Lane codes unique per plant (not globally)
3. **Soft Delete**: Lanes use soft delete (is_active flag)
4. **Hard Delete**: Assignments use hard delete
5. **Cascading**: Deleting a lane deletes all assignments
6. **Calendar Queries**: Optimized with composite index on (lane_id, dates)
7. **Status Filtering**: Only PLANNED and ACTIVE assignments count toward capacity

## Performance Considerations

- Date range queries use composite index for fast calendar view
- Capacity calculations exclude completed/cancelled assignments
- Pagination supported on all list endpoints
- Database-level constraints prevent invalid data
