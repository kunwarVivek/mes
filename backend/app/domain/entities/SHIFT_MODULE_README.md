# Shift Management Module

## Overview

The Shift Management module provides comprehensive shift pattern management, handover tracking, and performance monitoring capabilities for manufacturing operations.

## Architecture

This module follows DDD (Domain-Driven Design) architecture with clear separation of concerns:

```
Domain Layer (Business Logic)
├── app/domain/entities/shift.py          # ShiftDomain, ShiftHandoverDomain
│
Application Layer (DTOs)
├── app/application/dtos/shift_dto.py     # Request/Response schemas
│
Infrastructure Layer (Data Access)
├── app/models/shift.py                    # SQLAlchemy ORM models
├── app/infrastructure/repositories/shift_repository.py  # Data repositories
│
Presentation Layer (API)
└── app/presentation/api/v1/shifts.py     # FastAPI endpoints
```

## Domain Entities

### ShiftDomain
Represents a shift pattern with business rules:
- **Properties**: shift_code, shift_name, start_time, end_time, production_target
- **Business Methods**:
  - `activate()` - Activate shift
  - `deactivate()` - Deactivate shift
  - `calculate_duration_hours()` - Calculate shift duration (handles overnight shifts)
- **Validation Rules**:
  - Organization ID and Plant ID must be positive
  - Shift name and code cannot be empty
  - Production target cannot be negative
  - Shift code is automatically uppercased

### ShiftHandoverDomain
Represents shift handover with WIP tracking:
- **Properties**: from_shift_id, to_shift_id, wip_quantity, production_summary, quality_issues, machine_status, material_status, safety_incidents
- **Business Methods**:
  - `acknowledge(user_id)` - Acknowledge handover receipt
  - `is_acknowledged` - Check acknowledgment status
- **Validation Rules**:
  - Cannot handover to the same shift
  - WIP quantity cannot be negative
  - Cannot acknowledge already acknowledged handover

## API Endpoints

### Shifts

#### POST /shifts
Create a new shift pattern.

**Request:**
```json
{
  "shift_name": "Morning Shift",
  "shift_code": "MS",
  "start_time": "06:00:00",
  "end_time": "14:00:00",
  "production_target": 100.0,
  "is_active": true
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "organization_id": 1,
  "plant_id": 1,
  "shift_name": "Morning Shift",
  "shift_code": "MS",
  "start_time": "06:00:00",
  "end_time": "14:00:00",
  "production_target": 100.0,
  "is_active": true,
  "created_at": "2025-01-08T10:00:00Z",
  "updated_at": null
}
```

#### GET /shifts/{shift_id}
Retrieve a shift by ID.

**Response:** `200 OK` (Shift object)

#### GET /shifts
List shifts with pagination.

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 50, max: 100)
- `is_active` (optional filter)
- `shift_code` (optional filter)

**Response:** `200 OK`
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

#### PUT /shifts/{shift_id}
Update a shift (partial updates supported).

**Request:**
```json
{
  "production_target": 120.0,
  "is_active": true
}
```

**Response:** `200 OK` (Updated shift object)

### Shift Handovers

#### POST /shifts/handovers
Create a shift handover.

**Request:**
```json
{
  "from_shift_id": 1,
  "to_shift_id": 2,
  "handover_date": "2025-01-08T14:00:00Z",
  "wip_quantity": 50.0,
  "production_summary": "Completed 95 units, 5 in progress",
  "quality_issues": "2 units rejected due to dimensional defects",
  "machine_status": "All machines operational",
  "material_status": "Raw material sufficient for next shift",
  "safety_incidents": null
}
```

**Response:** `201 Created` (Handover object)

#### POST /shifts/handovers/{handover_id}/acknowledge
Acknowledge a shift handover.

**Response:** `200 OK` (Updated handover object with acknowledgment)

#### GET /shifts/handovers
List shift handovers with pagination.

**Query Parameters:**
- `page`, `page_size`
- `from_shift_id` (optional filter)
- `to_shift_id` (optional filter)
- `acknowledged` (optional boolean filter)

### Shift Performance

#### GET /shifts/performance
Get shift performance metrics.

**Query Parameters:**
- `shift_id` (required)
- `start_date` (optional)
- `end_date` (optional)
- `page`, `page_size`

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "shift_id": 1,
      "performance_date": "2025-01-08T06:00:00Z",
      "production_target": 100.0,
      "production_actual": 95.0,
      "target_attainment_percent": 95.0,
      "availability_percent": 90.0,
      "performance_percent": 95.0,
      "quality_percent": 98.0,
      "oee_percent": 83.8,
      "total_produced": 95.0,
      "total_good": 93.0,
      "total_rejected": 2.0,
      "fpy_percent": 97.9,
      "planned_production_time": 480.0,
      "actual_run_time": 432.0,
      "downtime_minutes": 48.0
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

## Performance Metrics Explained

### Target Attainment
```
Target Attainment % = (Actual Production / Target Production) × 100
```

### OEE (Overall Equipment Effectiveness)
```
OEE % = Availability % × Performance % × Quality %
```

Where:
- **Availability %** = (Actual Run Time / Planned Production Time) × 100
- **Performance %** = (Actual Production / Theoretical Max Production) × 100
- **Quality %** = (Good Units / Total Units) × 100

### FPY (First Pass Yield)
```
FPY % = (Good Units / Total Units Produced) × 100
```

## Database Schema

### shift
- **Primary Key**: id
- **Unique Constraint**: (organization_id, plant_id, shift_code)
- **Indexes**: organization_id, plant_id, shift_code, is_active
- **RLS**: Filtered by organization_id

### shift_handover
- **Primary Key**: id
- **Foreign Keys**: from_shift_id, to_shift_id → shift(id)
- **Indexes**: organization_id, plant_id, handover_date, from_shift_id, to_shift_id
- **RLS**: Filtered by organization_id

### shift_performance
- **Primary Key**: id
- **Foreign Key**: shift_id → shift(id)
- **Unique Constraint**: (organization_id, plant_id, shift_id, performance_date)
- **Indexes**: organization_id, plant_id, performance_date, shift_id
- **RLS**: Filtered by organization_id

## Security

### Row-Level Security (RLS)
All tables enforce RLS based on `organization_id` from the authenticated user's JWT token. This ensures:
- Users can only access shifts from their organization
- Cross-organization data leakage is prevented at the database level

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <jwt_token>
```

## Testing

### Unit Tests
Domain entity tests: `tests/unit/test_shift_entity.py`

Run tests:
```bash
cd backend
python3 -m pytest tests/unit/test_shift_entity.py -v
```

### Test Coverage
- Shift creation and validation
- Shift duration calculation (including overnight shifts)
- Shift activation/deactivation
- Handover creation and validation
- Handover acknowledgment workflow
- Cannot acknowledge already acknowledged handover
- Business rule validation (same shift handover, negative quantities, etc.)

## Usage Examples

### Create Morning, Afternoon, and Night Shifts
```bash
# Morning Shift (6 AM - 2 PM)
curl -X POST http://localhost:8000/api/v1/shifts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_name": "Morning Shift",
    "shift_code": "MS",
    "start_time": "06:00:00",
    "end_time": "14:00:00",
    "production_target": 100.0
  }'

# Afternoon Shift (2 PM - 10 PM)
curl -X POST http://localhost:8000/api/v1/shifts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_name": "Afternoon Shift",
    "shift_code": "AS",
    "start_time": "14:00:00",
    "end_time": "22:00:00",
    "production_target": 100.0
  }'

# Night Shift (10 PM - 6 AM, overnight)
curl -X POST http://localhost:8000/api/v1/shifts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shift_name": "Night Shift",
    "shift_code": "NS",
    "start_time": "22:00:00",
    "end_time": "06:00:00",
    "production_target": 80.0
  }'
```

### Create Shift Handover
```bash
curl -X POST http://localhost:8000/api/v1/shifts/handovers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_shift_id": 1,
    "to_shift_id": 2,
    "handover_date": "2025-01-08T14:00:00Z",
    "wip_quantity": 50.0,
    "production_summary": "Completed 95 units, 5 in progress. Line 1 running smoothly.",
    "quality_issues": "2 units rejected - dimensional tolerance out of spec",
    "machine_status": "All machines operational. Machine 3 requires preventive maintenance tomorrow.",
    "material_status": "Raw material inventory: 500 kg remaining. Reorder point reached.",
    "safety_incidents": null
  }'
```

### Acknowledge Handover
```bash
curl -X POST http://localhost:8000/api/v1/shifts/handovers/1/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

## Future Enhancements

1. **Automated Performance Calculation**: Use pg_cron to automatically calculate shift performance metrics
2. **Real-time Dashboards**: WebSocket integration for live shift performance monitoring
3. **Shift Analytics**: Trend analysis and predictive insights for shift performance
4. **Shift Scheduling**: Advanced shift scheduling with resource allocation
5. **Mobile App Support**: Shift handover mobile application for shop floor supervisors

## Related Modules

- **Work Order Management**: Tracks production orders executed during shifts
- **Machine Management**: Monitors equipment performance during shifts (OEE calculation)
- **Quality Management**: Tracks quality metrics per shift (NCR, inspections, FPY)
- **Production Planning**: Uses shift capacity for production scheduling
