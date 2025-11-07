# Production Management Domain

**Domain**: Production Management
**Bounded Context**: Work Order Management, Shop Floor Execution, Resource Scheduling
**Owner**: Production Planning & Control
**Status**: Core Domain (High Strategic Importance)

---

## Table of Contents

1. [Domain Overview](#domain-overview)
2. [Core Concepts](#core-concepts)
3. [Database Schema](#database-schema)
4. [Business Rules](#business-rules)
5. [Use Cases](#use-cases)
6. [API Endpoints](#api-endpoints)
7. [PostgreSQL-Native Features](#postgresql-native-features)
8. [Integration Points](#integration-points)

---

## Domain Overview

### Purpose

The Production Management domain orchestrates all shop floor execution activities, from work order creation to completion tracking. It manages resource allocation (lanes, equipment, manpower), production logging, and scheduling for discrete manufacturing operations.

### Scope

**In Scope**:
- Work order lifecycle management (planned → released → in_progress → completed)
- Work order operations (routing steps) and sequencing
- Lane management (production workstations/areas)
- Lane assignments (work order to lane mapping)
- Production logging (start, pause, resume, complete events)
- Manpower allocation tracking (operator assignments, hours worked)
- Resource-Based Scheduling (RBS) - daily schedules by lane/resource
- Resource Planning Sheet (RPS) - multi-week project planning
- Daily work logs (shift-level production reporting)
- Delivery predictions (data-driven ETA forecasting)
- Real-time shop floor visibility (WebSocket updates via LISTEN/NOTIFY)

**Out of Scope**:
- Project and sales order management → Project domain
- Bill of Materials (BOM) → Project domain
- Material consumption tracking → Material domain (cross-referenced)
- Quality inspections → Quality domain
- Equipment/machine management → Equipment domain
- Shift handovers → Shift Management domain

### Key Business Goals

1. **On-Time Delivery (OTD)**: 90%+ of projects delivered on time
2. **Shop Floor Visibility**: Real-time production status across 5-10 lanes
3. **Resource Utilization**: 75%+ lane occupancy rate
4. **Production Throughput**: Track actual vs planned hours (95%+ accuracy)
5. **Data-Driven Planning**: Delivery predictions based on historical velocity
6. **Mobile-First**: PWA-based production logging for operators

---

## Core Concepts

### Work Order

**Definition**: An instruction to produce a specific quantity of a product or perform an operation (fabrication, machining, assembly, testing) for a project.

**Key Attributes**:
- **Work Order Number**: Unique identifier (e.g., "WO-2025-001")
- **Project**: Parent project (customer order)
- **Plant**: Production facility where work is performed
- **Operation Type**: fabrication, machining, assembly, testing
- **Quantity**: Ordered vs completed quantity
- **Status**: planned, released, in_progress, completed, cancelled
- **Priority**: low, medium, high, urgent (affects scheduling)
- **Dates**: Planned start/end, actual start/end
- **SAP Production Order**: External ERP reference (optional)

**Work Order Lifecycle**:
```
planned → released → in_progress → completed
                         ↓
                    (cancelled)
```

**Status Transitions**:
- **planned**: Created but not yet released to shop floor
- **released**: Released to production, ready for lane assignment
- **in_progress**: At least one operation started
- **completed**: All operations completed, quantity met
- **cancelled**: Cancelled before completion (customer change, project cancellation)

### Work Order Operation

**Definition**: A single routing step within a work order (e.g., "Cut material", "Weld assembly", "Quality inspection").

**Key Attributes**:
- **Operation Number**: Sequence number (10, 20, 30... for future insertions)
- **Operation Name**: Human-readable name
- **Planned Hours**: Estimated labor hours
- **Actual Hours**: Recorded labor hours
- **Status**: pending, in_progress, completed, cancelled
- **Assignee**: Operator or supervisor responsible

**Operation Sequence**:
```
Operation 10: Cut raw material (pending)
    ↓
Operation 20: Weld subassembly (pending)
    ↓
Operation 30: Grind and finish (pending)
    ↓
Operation 40: Quality inspection (pending)
```

### Lane

**Definition**: A physical production workstation or area where work orders are executed (e.g., "Lane 1 - Fabrication", "Lane 5 - Assembly").

**Key Attributes**:
- **Lane Number**: Unique identifier (e.g., "L01", "L05")
- **Lane Name**: Human-readable name
- **Lane Type**: fabrication, assembly, testing
- **Capacity**: Max concurrent work orders (usually 1)
- **Status**: available, occupied, maintenance, inactive
- **Current Work Order**: FK to work_orders (if occupied)

**Lane Status Workflow**:
```
available → (assign work order) → occupied → (release work order) → available
                                      ↓
                                (maintenance) → available
```

### Production Log

**Definition**: A timestamped event recording production activity (start, pause, resume, complete, issue).

**Log Types**:
- **start**: Work order/operation started on lane
- **pause**: Temporary stop (break, material shortage, tool change)
- **resume**: Resume after pause
- **complete**: Operation or work order completed (quantity recorded)
- **issue**: Problem/downtime event (cross-referenced with downtime tracking)

**Example Log Sequence**:
```
2025-11-07 08:00 | start   | WO-2025-001 assigned to Lane 1
2025-11-07 10:30 | pause   | Material shortage (waiting for welding wire)
2025-11-07 11:15 | resume  | Material received, work resumed
2025-11-07 15:00 | complete| 25 units completed
```

### Manpower Allocation

**Definition**: Assignment of operators/supervisors to work orders with hours tracking.

**Roles**:
- **operator**: Direct labor (welding, machining, assembly)
- **supervisor**: Oversight and coordination
- **qc_inspector**: Quality inspection during production

**Hours Tracking**:
```python
# Calculate labor cost
labor_cost = hours_worked * hourly_rate * workers_count

# Example:
# 2 operators × 8 hours × $25/hour = $400 labor cost
```

### Resource-Based Scheduling (RBS)

**Definition**: Daily production schedule mapping work orders to lanes with time slots.

**Purpose**: Optimize lane utilization and sequence work orders based on priority, due dates, and resource availability.

**Schedule Structure**:
```
Date: 2025-11-07
Lane 1 - Fabrication
  08:00-12:00 | WO-2025-001 (Cutting steel plates) [in_progress]
  13:00-17:00 | WO-2025-003 (Welding frames) [scheduled]

Lane 2 - Assembly
  08:00-16:00 | WO-2025-002 (Final assembly) [in_progress]
```

### Resource Planning Sheet (RPS)

**Definition**: Multi-week production planning document for a project, showing resource requirements and timeline.

**Purpose**: Long-term planning (2-4 weeks) to allocate lanes, manpower, and equipment for project completion.

**RPS Workflow**:
```
draft → approved → (execute via RBS daily schedules) → archived
```

### Daily Work Log

**Definition**: Shift-level production summary (workers present, hours worked, quantity produced).

**Purpose**: High-level reporting for daily production meetings and OEE calculation.

**Example Log**:
```json
{
  "work_date": "2025-11-07",
  "shift": "morning",
  "plant_id": 1,
  "lane_id": 1,
  "work_order_id": 123,
  "workers_present": 3,
  "hours_worked": 24.0,
  "quantity_produced": 25,
  "notes": "Smooth production, no issues"
}
```

### Delivery Prediction

**Definition**: Data-driven forecast of project delivery date based on historical production velocity.

**Factors**:
- Historical production rates (units/day by operation type)
- Current WIP (work in progress) status
- Remaining work order quantity
- Lane availability and schedule conflicts
- Historical on-time delivery rate

**Confidence Levels**:
- **high**: >80% historical accuracy, similar project complexity
- **medium**: 60-80% historical accuracy, moderate variability
- **low**: <60% historical accuracy, high variability or new project type

---

## Database Schema

### Tables (10 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL with PostgreSQL-native features.

#### 1. work_orders

Master table for production work orders.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `work_order_number`: Unique identifier (e.g., "WO-2025-001")
- `project_id`: FK to projects (customer order)
- `plant_id`: FK to plants (production facility)
- `department_id`: FK to departments (optional)
- `operation_type`: Enum (fabrication, machining, assembly, testing)
- `description`: Work order details
- `quantity_ordered`: Total quantity to produce
- `quantity_completed`: Quantity completed so far
- `status`: Enum (planned, released, in_progress, completed, cancelled)
- `priority`: Enum (low, medium, high, urgent)
- `planned_start_date`: Planned start date
- `planned_end_date`: Planned completion date
- `actual_start_date`: Actual start date
- `actual_end_date`: Actual completion date
- `sap_production_order`: External SAP reference (optional)
- `assigned_to`: FK to users (supervisor/lead)
- `created_by`: FK to users

**Indexes**:
- pg_search BM25: work_order_number, description, sap_production_order
- B-tree: status, plant_id, project_id, priority
- Partial index: `WHERE status IN ('released', 'in_progress')` (active work orders)

**Row-Level Security**:
```sql
CREATE POLICY work_orders_tenant_isolation ON work_orders
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**LISTEN/NOTIFY Trigger** (real-time status updates):
```sql
CREATE OR REPLACE FUNCTION notify_work_order_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        PERFORM pg_notify('work_order_status_changed',
            json_build_object(
                'id', NEW.id,
                'work_order_number', NEW.work_order_number,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'plant_id', NEW.plant_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER work_order_status_notify
AFTER UPDATE ON work_orders
FOR EACH ROW EXECUTE FUNCTION notify_work_order_status_change();
```

#### 2. work_order_operations

Routing steps for work orders (operation sequence).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `work_order_id`: FK to work_orders
- `operation_number`: Sequence number (10, 20, 30...)
- `operation_name`: Operation description
- `description`: Detailed operation notes
- `planned_hours`: Estimated labor hours
- `actual_hours`: Recorded labor hours
- `status`: Enum (pending, in_progress, completed, cancelled)
- `assigned_to`: FK to users (operator)
- `completed_by`: FK to users (who completed)
- `completed_at`: Timestamp

**Unique Constraint**: `(work_order_id, operation_number)`

**Indexes**:
- B-tree: work_order_id, status

#### 3. lanes

Physical production workstations/areas.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `plant_id`: FK to plants
- `lane_number`: Unique identifier (e.g., "L01")
- `lane_name`: Human-readable name
- `lane_type`: Enum (fabrication, assembly, testing)
- `capacity`: Max concurrent work orders (usually 1)
- `status`: Enum (available, occupied, maintenance, inactive)
- `current_work_order_id`: FK to work_orders (if occupied)
- `is_active`: Soft delete flag

**Unique Constraint**: `(organization_id, plant_id, lane_number)`

**Indexes**:
- B-tree: plant_id, status
- Partial index: `WHERE status = 'available'` (available lanes)

#### 4. lane_assignments

Work order to lane assignment history.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `lane_id`: FK to lanes
- `work_order_id`: FK to work_orders
- `assigned_at`: Assignment timestamp
- `released_at`: Release timestamp (when work order moved off lane)
- `notes`: Assignment notes
- `assigned_by`: FK to users

**Indexes**:
- B-tree: lane_id, work_order_id, assigned_at DESC

#### 5. production_logs

Timestamped production events (timescaledb hypertable for time-series optimization).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `work_order_id`: FK to work_orders
- `operation_id`: FK to work_order_operations (optional)
- `lane_id`: FK to lanes (optional)
- `log_type`: Enum (start, pause, resume, complete, issue)
- `quantity_completed`: Quantity completed (for complete events)
- `notes`: Event details
- `logged_by`: FK to users
- `logged_at`: Timestamp (auto-generated)

**timescaledb Hypertable**:
```sql
SELECT create_hypertable('production_logs', 'logged_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 75% compression after 7 days
ALTER TABLE production_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, work_order_id, logged_by'
);
SELECT add_compression_policy('production_logs', INTERVAL '7 days', if_not_exists => TRUE);

-- 2-year retention policy
SELECT add_retention_policy('production_logs', INTERVAL '2 years', if_not_exists => TRUE);
```

**Continuous Aggregate** (daily production summary):
```sql
CREATE MATERIALIZED VIEW daily_production_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', logged_at) AS day,
    organization_id,
    work_order_id,
    plant_id,
    COUNT(*) AS log_count,
    SUM(quantity_completed) AS total_quantity
FROM production_logs pl
JOIN work_orders wo ON pl.work_order_id = wo.id
WHERE pl.log_type = 'complete'
GROUP BY day, organization_id, work_order_id, plant_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_production_summary',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

**Indexes**:
- B-tree: work_order_id, log_type
- Time-series: logged_at DESC (timescaledb optimized)

#### 6. manpower_allocation

Operator assignments to work orders.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `work_order_id`: FK to work_orders
- `user_id`: FK to users (operator)
- `role`: Enum (operator, supervisor, qc_inspector)
- `allocated_at`: Assignment timestamp
- `released_at`: Release timestamp
- `hours_worked`: Recorded labor hours
- `allocated_by`: FK to users (supervisor)

**Indexes**:
- B-tree: work_order_id, user_id, allocated_at DESC

#### 7. rbs_schedules (Resource-Based Scheduling)

Daily production schedules by lane and time slot.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `plant_id`: FK to plants
- `schedule_date`: Date (e.g., 2025-11-07)
- `work_order_id`: FK to work_orders
- `lane_id`: FK to lanes (optional)
- `planned_start_time`: Time (e.g., 08:00)
- `planned_end_time`: Time (e.g., 12:00)
- `actual_start_time`: Actual start time
- `actual_end_time`: Actual end time
- `status`: Enum (scheduled, in_progress, completed, cancelled)
- `created_by`: FK to users

**Indexes**:
- B-tree: schedule_date, plant_id, lane_id, status
- Partial index: `WHERE schedule_date >= CURRENT_DATE` (future schedules)

#### 8. rps_sheets (Resource Planning Sheet)

Multi-week project planning documents.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `project_id`: FK to projects
- `sheet_number`: Unique identifier (e.g., "RPS-2025-W45")
- `planning_period_start`: Start date
- `planning_period_end`: End date
- `status`: Enum (draft, approved, archived)
- `created_by`: FK to users
- `approved_by`: FK to users (optional)
- `approved_at`: Approval timestamp (optional)

**Unique Constraint**: `(organization_id, sheet_number)`

**Indexes**:
- B-tree: project_id, status, planning_period_start

#### 9. daily_work_logs

Shift-level production summaries.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `plant_id`: FK to plants
- `work_date`: Date
- `shift`: Enum (morning, afternoon, night)
- `work_order_id`: FK to work_orders (optional)
- `lane_id`: FK to lanes (optional)
- `workers_present`: Worker count
- `hours_worked`: Total labor hours
- `quantity_produced`: Total quantity produced
- `notes`: Shift notes
- `logged_by`: FK to users

**Indexes**:
- B-tree: work_date DESC, plant_id, shift

#### 10. delivery_predictions

Data-driven project delivery forecasts.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `project_id`: FK to projects
- `predicted_date`: Forecasted delivery date
- `confidence_level`: Enum (low, medium, high)
- `factors`: JSONB (factors affecting prediction)
- `calculated_at`: Timestamp
- `calculated_by`: System or user identifier

**Indexes**:
- B-tree: project_id, calculated_at DESC

---

## Business Rules

### BR-PROD-001: Work Order Number Uniqueness

**Rule**: Work order numbers must be unique across the organization.

**Validation**:
```python
class CreateWorkOrderUseCase:
    def execute(self, dto: CreateWorkOrderDTO) -> WorkOrder:
        # Check uniqueness
        existing = self.work_order_repo.find_by_number(
            dto.work_order_number, dto.organization_id
        )
        if existing:
            raise WorkOrderNumberAlreadyExistsError(dto.work_order_number)

        # Create work order
        work_order = WorkOrder(
            work_order_number=dto.work_order_number,
            project_id=dto.project_id,
            quantity_ordered=dto.quantity_ordered,
            status=WorkOrderStatus.PLANNED
        )
        return self.work_order_repo.save(work_order)
```

### BR-PROD-002: Quantity Completed Cannot Exceed Quantity Ordered

**Rule**: Work order quantity_completed must be ≤ quantity_ordered.

**Validation**:
```python
class CompleteProductionUseCase:
    def execute(self, dto: CompleteProductionDTO) -> ProductionLog:
        work_order = self.work_order_repo.find_by_id(dto.work_order_id)

        # Validate quantity
        new_quantity = work_order.quantity_completed + dto.quantity
        if new_quantity > work_order.quantity_ordered:
            raise QuantityExceedsOrderedError(
                ordered=work_order.quantity_ordered,
                completed=work_order.quantity_completed,
                attempting=dto.quantity
            )

        # Create production log
        log = ProductionLog(
            work_order_id=dto.work_order_id,
            log_type=LogType.COMPLETE,
            quantity_completed=dto.quantity,
            logged_by=dto.logged_by
        )

        # Update work order quantity
        work_order.quantity_completed += dto.quantity
        if work_order.quantity_completed == work_order.quantity_ordered:
            work_order.status = WorkOrderStatus.COMPLETED

        return self.production_log_repo.save(log)
```

### BR-PROD-003: Lane Can Only Have One Active Work Order

**Rule**: A lane with capacity=1 can only have one active work order at a time (status='occupied').

**Validation**:
```python
class AssignWorkOrderToLaneUseCase:
    def execute(self, dto: AssignToLaneDTO) -> LaneAssignment:
        lane = self.lane_repo.find_by_id(dto.lane_id)

        # Check lane availability
        if lane.status == LaneStatus.OCCUPIED:
            raise LaneOccupiedError(
                lane_number=lane.lane_number,
                current_work_order_id=lane.current_work_order_id
            )

        if lane.status != LaneStatus.AVAILABLE:
            raise LaneUnavailableError(
                lane_number=lane.lane_number,
                status=lane.status
            )

        # Assign work order
        assignment = LaneAssignment(
            lane_id=dto.lane_id,
            work_order_id=dto.work_order_id,
            assigned_by=dto.assigned_by
        )

        # Update lane status
        lane.status = LaneStatus.OCCUPIED
        lane.current_work_order_id = dto.work_order_id

        return self.lane_assignment_repo.save(assignment)
```

### BR-PROD-004: Work Order Status Transitions

**Rule**: Work order status transitions must follow allowed paths:
- `planned` → `released` or `cancelled`
- `released` → `in_progress` or `cancelled`
- `in_progress` → `completed` or `cancelled`
- `completed` → (terminal state)
- `cancelled` → (terminal state)

**Validation**:
```python
class WorkOrderStatusMachine:
    ALLOWED_TRANSITIONS = {
        WorkOrderStatus.PLANNED: {WorkOrderStatus.RELEASED, WorkOrderStatus.CANCELLED},
        WorkOrderStatus.RELEASED: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
        WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
        WorkOrderStatus.COMPLETED: set(),  # Terminal
        WorkOrderStatus.CANCELLED: set()   # Terminal
    }

    @classmethod
    def validate_transition(cls, from_status: WorkOrderStatus, to_status: WorkOrderStatus):
        if to_status not in cls.ALLOWED_TRANSITIONS.get(from_status, set()):
            raise InvalidStatusTransitionError(
                from_status=from_status,
                to_status=to_status,
                allowed=cls.ALLOWED_TRANSITIONS[from_status]
            )
```

### BR-PROD-005: Production Log Start Event Required

**Rule**: A work order must have a 'start' production log before 'pause', 'resume', or 'complete' logs.

**Validation**:
```python
class CreateProductionLogUseCase:
    def execute(self, dto: CreateProductionLogDTO) -> ProductionLog:
        # For non-start events, validate start event exists
        if dto.log_type != LogType.START:
            start_log = self.production_log_repo.find_start_log(dto.work_order_id)
            if not start_log:
                raise ProductionNotStartedError(dto.work_order_id)

        # For resume events, validate pause event exists
        if dto.log_type == LogType.RESUME:
            recent_logs = self.production_log_repo.find_recent_logs(
                dto.work_order_id, limit=1
            )
            if not recent_logs or recent_logs[0].log_type != LogType.PAUSE:
                raise CannotResumeWithoutPauseError(dto.work_order_id)

        # Create log
        log = ProductionLog(
            work_order_id=dto.work_order_id,
            log_type=dto.log_type,
            quantity_completed=dto.quantity_completed,
            logged_by=dto.logged_by
        )

        # Update work order status if starting
        if dto.log_type == LogType.START:
            work_order = self.work_order_repo.find_by_id(dto.work_order_id)
            work_order.status = WorkOrderStatus.IN_PROGRESS
            work_order.actual_start_date = datetime.utcnow().date()

        return self.production_log_repo.save(log)
```

### BR-PROD-006: Operation Sequence Enforcement

**Rule**: Operations must be completed in sequence (operation 10 before 20, etc.).

**Validation**:
```python
class CompleteOperationUseCase:
    def execute(self, dto: CompleteOperationDTO) -> WorkOrderOperation:
        operation = self.operation_repo.find_by_id(dto.operation_id)

        # Check if previous operations are completed
        previous_operations = self.operation_repo.find_previous_operations(
            operation.work_order_id,
            operation.operation_number
        )

        incomplete = [op for op in previous_operations if op.status != OperationStatus.COMPLETED]
        if incomplete:
            raise PreviousOperationsIncompleteError(
                operation_number=operation.operation_number,
                incomplete_operations=[op.operation_number for op in incomplete]
            )

        # Complete operation
        operation.status = OperationStatus.COMPLETED
        operation.actual_hours = dto.actual_hours
        operation.completed_by = dto.completed_by
        operation.completed_at = datetime.utcnow()

        return self.operation_repo.save(operation)
```

---

## Use Cases

### UC-PROD-001: Create Work Order

**Actor**: Production Planner

**Preconditions**: Project exists, user has `work_order:create` permission

**Flow**:
1. Planner submits work order details (project, operation type, quantity, dates)
2. System validates work order number uniqueness (BR-PROD-001)
3. System creates work order with status='planned'
4. System optionally creates work order operations (routing)
5. System returns work order ID

**Postconditions**: Work order exists, status='planned'

**API**: `POST /api/v1/work-orders`

### UC-PROD-002: Assign Work Order to Lane

**Actor**: Production Supervisor

**Preconditions**: Work order status='released', lane status='available'

**Flow**:
1. Supervisor selects work order and target lane
2. System validates lane availability (BR-PROD-003)
3. System creates lane assignment record
4. System updates lane status='occupied' and current_work_order_id
5. System updates work order status='in_progress' (if first assignment)
6. System triggers LISTEN/NOTIFY for real-time dashboard update

**Postconditions**: Work order assigned to lane, lane occupied

**API**: `POST /api/v1/work-orders/{id}/assign-lane`

### UC-PROD-003: Start Production (Log Start Event)

**Actor**: Operator (mobile PWA)

**Preconditions**: Work order assigned to lane, operator has `production:log` permission

**Flow**:
1. Operator scans work order barcode or selects from lane view
2. Operator clicks "Start Production"
3. System creates production log (log_type='start')
4. System updates work order status='in_progress' (BR-PROD-005)
5. System records actual_start_date (if first start)
6. System triggers LISTEN/NOTIFY for real-time update

**Postconditions**: Work order in progress, production log created

**API**: `POST /api/v1/production-logs`

### UC-PROD-004: Complete Production (Log Complete Event)

**Actor**: Operator

**Preconditions**: Production started (start log exists), operator has `production:log` permission

**Flow**:
1. Operator enters quantity completed
2. System validates quantity doesn't exceed ordered (BR-PROD-002)
3. System validates start event exists (BR-PROD-005)
4. System creates production log (log_type='complete', quantity_completed)
5. System updates work_order.quantity_completed
6. System updates work_order.status='completed' if quantity met
7. System triggers LISTEN/NOTIFY for real-time update

**Postconditions**: Quantity recorded, work order possibly completed

**API**: `POST /api/v1/production-logs`

### UC-PROD-005: Release Work Order from Lane

**Actor**: Production Supervisor

**Preconditions**: Work order assigned to lane, work order completed or cancelled

**Flow**:
1. Supervisor releases work order from lane
2. System updates lane_assignment.released_at timestamp
3. System updates lane status='available'
4. System clears lane.current_work_order_id
5. System triggers LISTEN/NOTIFY for real-time update

**Postconditions**: Lane available for new assignment

**API**: `POST /api/v1/lanes/{id}/release`

### UC-PROD-006: Create RBS Daily Schedule

**Actor**: Production Planner

**Preconditions**: User has `schedule:create` permission

**Flow**:
1. Planner selects date, plant, and work orders to schedule
2. Planner assigns work orders to lanes with time slots
3. System validates lane availability (no conflicts)
4. System creates rbs_schedule records
5. System displays Gantt chart of daily schedule

**Postconditions**: Daily schedule created, visible to operators

**API**: `POST /api/v1/schedules/rbs`

### UC-PROD-007: Calculate Delivery Prediction

**Actor**: System (scheduled job via pg_cron)

**Preconditions**: Project has work orders in progress

**Flow**:
1. System calculates historical production velocity (units/day by operation type)
2. System calculates remaining work (quantity_ordered - quantity_completed)
3. System estimates remaining days = remaining_work / avg_velocity
4. System considers lane availability and schedule conflicts
5. System assigns confidence level based on historical accuracy
6. System creates delivery_prediction record
7. System triggers LISTEN/NOTIFY to update project dashboard

**Postconditions**: Delivery prediction available for project

**pg_cron Job**:
```sql
SELECT cron.schedule(
    'delivery-prediction-update',
    '0 6 * * *',  -- Daily at 6 AM
    $$
    INSERT INTO delivery_predictions (organization_id, project_id, predicted_date, confidence_level, factors)
    SELECT
        p.organization_id,
        p.id,
        CURRENT_DATE + (
            SUM(wo.quantity_ordered - wo.quantity_completed) /
            NULLIF(AVG(dps.total_quantity), 0)
        )::INTEGER,
        CASE
            WHEN AVG(dps.total_quantity) > 10 THEN 'high'
            WHEN AVG(dps.total_quantity) > 5 THEN 'medium'
            ELSE 'low'
        END,
        json_build_object(
            'remaining_quantity', SUM(wo.quantity_ordered - wo.quantity_completed),
            'avg_daily_velocity', AVG(dps.total_quantity)
        )
    FROM projects p
    JOIN work_orders wo ON p.id = wo.project_id
    LEFT JOIN daily_production_summary dps ON wo.id = dps.work_order_id
        AND dps.day >= CURRENT_DATE - INTERVAL '30 days'
    WHERE wo.status IN ('released', 'in_progress')
    GROUP BY p.organization_id, p.id;
    $$
);
```

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Production Endpoints (25 total)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/work-orders` | Create work order | JWT + `work_order:create` |
| GET | `/api/v1/work-orders` | List work orders (paginated, filterable) | JWT + `work_order:read` |
| GET | `/api/v1/work-orders/{id}` | Get work order details | JWT + `work_order:read` |
| PUT | `/api/v1/work-orders/{id}` | Update work order | JWT + `work_order:update` |
| POST | `/api/v1/work-orders/{id}/release` | Release to shop floor (status=released) | JWT + `work_order:release` |
| POST | `/api/v1/work-orders/{id}/assign-lane` | Assign to lane | JWT + `work_order:assign` |
| POST | `/api/v1/work-orders/{id}/cancel` | Cancel work order | JWT + `work_order:cancel` |
| GET | `/api/v1/work-orders/{id}/operations` | List operations | JWT + `work_order:read` |
| POST | `/api/v1/work-orders/{id}/operations` | Create operation | JWT + `work_order:update` |
| PUT | `/api/v1/operations/{id}` | Update operation | JWT + `work_order:update` |
| POST | `/api/v1/operations/{id}/complete` | Complete operation | JWT + `work_order:update` |
| GET | `/api/v1/lanes` | List lanes (by plant) | JWT + `lane:read` |
| GET | `/api/v1/lanes/{id}` | Get lane details | JWT + `lane:read` |
| POST | `/api/v1/lanes/{id}/release` | Release work order from lane | JWT + `lane:manage` |
| POST | `/api/v1/production-logs` | Create production log | JWT + `production:log` |
| GET | `/api/v1/production-logs` | List logs (filterable by WO, date) | JWT + `production:read` |
| GET | `/api/v1/work-orders/{id}/logs` | Get work order logs | JWT + `work_order:read` |
| POST | `/api/v1/schedules/rbs` | Create RBS daily schedule | JWT + `schedule:create` |
| GET | `/api/v1/schedules/rbs` | List schedules (by date, plant) | JWT + `schedule:read` |
| GET | `/api/v1/schedules/gantt` | Get Gantt chart data (visual scheduling) | JWT + `schedule:read` |
| POST | `/api/v1/schedules/rps` | Create RPS sheet | JWT + `schedule:create` |
| GET | `/api/v1/schedules/rps/{id}` | Get RPS sheet | JWT + `schedule:read` |
| POST | `/api/v1/daily-work-logs` | Create daily work log | JWT + `production:log` |
| GET | `/api/v1/daily-work-logs` | List daily logs (by date, plant) | JWT + `production:read` |
| GET | `/api/v1/delivery-predictions/{project_id}` | Get delivery prediction | JWT + `project:read` |

### Example: Create Work Order

```http
POST /api/v1/work-orders
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "work_order_number": "WO-2025-001",
  "project_id": 15,
  "plant_id": 1,
  "operation_type": "fabrication",
  "description": "Fabricate steel frame for Project Alpha",
  "quantity_ordered": 10,
  "priority": "high",
  "planned_start_date": "2025-11-10",
  "planned_end_date": "2025-11-15",
  "operations": [
    {"operation_number": 10, "operation_name": "Cut steel plates", "planned_hours": 4.0},
    {"operation_number": 20, "operation_name": "Weld frame assembly", "planned_hours": 8.0},
    {"operation_number": 30, "operation_name": "Grind and finish", "planned_hours": 2.0}
  ]
}
```

**Response (201 Created)**:
```json
{
  "id": 123,
  "work_order_number": "WO-2025-001",
  "project_id": 15,
  "project_name": "Project Alpha - Customer XYZ",
  "plant_id": 1,
  "plant_name": "Plant 1 - Main Fabrication",
  "operation_type": "fabrication",
  "description": "Fabricate steel frame for Project Alpha",
  "quantity_ordered": 10,
  "quantity_completed": 0,
  "status": "planned",
  "priority": "high",
  "planned_start_date": "2025-11-10",
  "planned_end_date": "2025-11-15",
  "operations": [
    {
      "id": 201,
      "operation_number": 10,
      "operation_name": "Cut steel plates",
      "planned_hours": 4.0,
      "status": "pending"
    },
    {
      "id": 202,
      "operation_number": 20,
      "operation_name": "Weld frame assembly",
      "planned_hours": 8.0,
      "status": "pending"
    },
    {
      "id": 203,
      "operation_number": 30,
      "operation_name": "Grind and finish",
      "planned_hours": 2.0,
      "status": "pending"
    }
  ],
  "created_at": "2025-11-07T18:00:00Z",
  "updated_at": "2025-11-07T18:00:00Z"
}
```

### Example: Create Production Log (Start)

```http
POST /api/v1/production-logs
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "work_order_id": 123,
  "lane_id": 1,
  "log_type": "start",
  "notes": "Starting fabrication on Lane 1"
}
```

**Response (201 Created)**:
```json
{
  "id": 5001,
  "work_order_id": 123,
  "work_order_number": "WO-2025-001",
  "lane_id": 1,
  "lane_number": "L01",
  "log_type": "start",
  "quantity_completed": null,
  "notes": "Starting fabrication on Lane 1",
  "logged_by": 45,
  "logged_by_name": "John Smith",
  "logged_at": "2025-11-07T18:15:00Z",
  "work_order_status_updated": "in_progress"
}
```

**Real-Time WebSocket Notification**:
```json
{
  "event": "work_order_status_changed",
  "data": {
    "id": 123,
    "work_order_number": "WO-2025-001",
    "old_status": "released",
    "new_status": "in_progress",
    "plant_id": 1
  },
  "timestamp": "2025-11-07T18:15:00Z"
}
```

---

## PostgreSQL-Native Features

### 1. timescaledb Hypertable (production_logs)

**Purpose**: Time-series optimization for production log history with 75% compression.

**Query Performance**:
- **Standard PostgreSQL**: 2s for 1M production logs
- **timescaledb**: 200ms for 1M production logs
- **Improvement**: 10x faster

**Continuous Aggregate** (daily production summary):
```sql
-- Query daily production summary (auto-refreshed hourly)
SELECT * FROM daily_production_summary
WHERE day BETWEEN '2025-11-01' AND '2025-11-07'
AND plant_id = 1
ORDER BY day DESC;

-- Result: Instant query (pre-aggregated data)
```

### 2. LISTEN/NOTIFY for Real-Time Work Order Updates

**Purpose**: Pub/sub messaging for live shop floor dashboard (no polling required).

**WebSocket Integration**:
```javascript
// Frontend (React)
const ws = new WebSocket(`wss://api.example.com/ws?token=${token}`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  switch(update.event) {
    case 'work_order_status_changed':
      updateWorkOrderCard(update.data);
      break;
    case 'lane_status_changed':
      updateLaneBoard(update.data);
      break;
  }
};
```

### 3. pg_search BM25 Full-Text Search (work_orders)

**Purpose**: Fast work order search (20x faster than tsvector).

**Query Example**:
```sql
-- Search work orders by number, description, or SAP reference
SELECT * FROM work_orders
WHERE work_orders @@@ 'fabrication steel frame'
ORDER BY paradedb.rank('work_orders_search_idx') DESC
LIMIT 20;

-- Execution time: 5ms for 10K work orders
```

### 4. pg_cron for Delivery Prediction Updates

**Purpose**: Daily automated delivery forecasting (replaces Celery Beat).

**Performance**:
- **Celery Beat**: ~500 jobs/hour, requires Redis + RabbitMQ
- **pg_cron**: Native PostgreSQL, runs SQL directly

### 5. Row-Level Security (RLS) for Multi-Tenancy

**Purpose**: Database-level tenant isolation (no application-level filtering).

**Automatic Filtering**:
```python
# All queries automatically filtered by organization_id
work_orders = session.query(WorkOrder).all()
# RLS policy ensures only current org's work orders returned
```

---

## Integration Points

### Upstream Dependencies (Data Consumed)

1. **Project Domain** (`projects`)
   - Work orders belong to projects
   - Project budget, due dates drive work order planning

2. **Multi-Tenancy Domain** (`organizations`, `plants`, `departments`)
   - Work orders executed at specific plants
   - RLS context from JWT

3. **User Domain** (`users`)
   - Work order assignments, production logging
   - Manpower allocation

### Downstream Consumers (Data Provided)

1. **Material Domain** (Material Consumption)
   - Work orders trigger material issues
   - Production logs drive material transactions

2. **Quality Domain** (Inspections)
   - Quality inspections tied to work orders
   - NCRs reference work orders

3. **Equipment Domain** (Machine Utilization)
   - Machines assigned to lanes for work orders
   - OEE calculated from production logs

4. **Shift Management Domain** (Shift Handovers)
   - Active work orders at shift end
   - Production progress reported in handovers

5. **Traceability Domain** (Lot/Serial Numbers)
   - Serial numbers created during production
   - Genealogy records link work orders to materials

6. **Reporting Domain** (OTD, Throughput KPIs)
   - On-Time Delivery calculated from actual_end_date vs planned_end_date
   - Production throughput from daily_production_summary

### External Integrations

1. **SAP ERP** (Optional)
   - Production order sync (inbound/outbound)
   - SAP production order numbers mapped to work orders

---

## Summary

The Production Management domain orchestrates shop floor execution from work order creation to completion. Key PostgreSQL-native features include:

- **timescaledb**: 10x faster production log queries with 75% compression
- **LISTEN/NOTIFY**: Real-time shop floor dashboard updates (no polling)
- **pg_search BM25**: 20x faster work order search
- **pg_cron**: Automated delivery prediction updates (daily)
- **RLS**: Database-level tenant isolation

**Performance Targets**:
- Work order search: <100ms for 10K+ work orders
- Production log query: <200ms for 1M+ logs
- Real-time updates: <50ms latency via WebSocket
- Daily production summary: Instant (pre-aggregated via continuous aggregate)

**Next Domain**: [QUALITY.md](./QUALITY.md) - NCR Workflows, Inspection Plans, and SPC Charts
