# Bottom-Up Implementation Plan: Schema → Backend

**Date**: 2025-11-10
**Approach**: Database → Models → Repositories → Use Cases → APIs
**Duration**: 5 days (Phases 1-3 only - Critical path)

---

## Overview

This plan addresses critical gaps identified in the backend debt analysis, following a bottom-up approach:

1. **Database Layer** (Schema, Extensions, Triggers)
2. **Infrastructure Layer** (Models, Repositories, Services)
3. **Application Layer** (Use Cases, Business Logic)
4. **Presentation Layer** (API Endpoints, DTOs)

---

## Phase 1: Critical Security & Infrastructure (Day 1-2)

### Day 1 Morning: Security Fixes (4 hours)

#### Task 1.1: Fix SQL Injection in RLS Context (Priority: IMMEDIATE)
**File**: `/home/user/mes/backend/app/infrastructure/security/dependencies.py`

**Changes**:
```python
# Line 109-114: Replace
def _set_rls_context(db: Session, organization_id: int, plant_id: int = None) -> None:
    db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))
    if plant_id is not None:
        db.execute(text(f"SET LOCAL app.current_plant_id = {plant_id}"))

# With (using parameterized queries):
def _set_rls_context(db: Session, organization_id: int, plant_id: int = None) -> None:
    db.execute(
        text("SET LOCAL app.current_organization_id = :org_id"),
        {"org_id": organization_id}
    )
    if plant_id is not None:
        db.execute(
            text("SET LOCAL app.current_plant_id = :plant_id"),
            {"plant_id": plant_id}
        )
```

**Testing**:
1. Create test with malicious JWT payload
2. Verify injection is prevented
3. Verify RLS still works correctly

---

#### Task 1.2: Create Custom Exception Hierarchy (2 hours)
**New File**: `/home/user/mes/backend/app/core/exceptions.py`

**Create**:
```python
class DomainException(Exception):
    """Base for all domain exceptions"""
    pass

class EntityNotFoundException(DomainException):
    """Entity not found"""
    pass

class ValidationException(DomainException):
    """Business rule violation"""
    pass

class UnauthorizedException(DomainException):
    """Permission denied"""
    pass

class DuplicateEntityException(DomainException):
    """Duplicate key violation"""
    pass
```

---

#### Task 1.3: Create Global Exception Handler (1 hour)
**File**: `/home/user/mes/backend/app/presentation/middleware/exception_handler.py`

**Create middleware** that maps domain exceptions to HTTP status codes

---

### Day 1 Afternoon: PostgreSQL Extensions (4 hours)

#### Task 1.4: Add Missing Extensions to Migration
**File**: `/home/user/mes/backend/migrations/versions/001_initial_schema.py`

**Add after line 66**:
```python
# Additional extensions for PostgreSQL-native architecture
op.execute('CREATE EXTENSION IF NOT EXISTS pgmq')       # Message queue
op.execute('CREATE EXTENSION IF NOT EXISTS pg_cron')    # Scheduled tasks
# Note: pg_search and pg_duckdb require ParadeDB installation
# op.execute('CREATE EXTENSION IF NOT EXISTS pg_search')  # Full-text search
# op.execute('CREATE EXTENSION IF NOT EXISTS pg_duckdb')  # Analytics
```

---

#### Task 1.5: Create UNLOGGED Cache Table
**Add after extensions**:
```sql
# UNLOGGED table for caching (replaces Redis)
op.execute("""
    CREATE UNLOGGED TABLE IF NOT EXISTS cache (
        cache_key VARCHAR(255) PRIMARY KEY,
        cache_value JSONB NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Index for expiration cleanup
    CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at);
""")
```

---

#### Task 1.6: Add Missing Hypertables
**Add to migration**:
```python
# Material Transactions - 1 month chunks
op.execute("""
    SELECT create_hypertable('material_transactions', 'created_at',
        chunk_time_interval => INTERVAL '1 month',
        if_not_exists => TRUE
    );
""")

# Machine Status History - 1 week chunks
op.execute("""
    SELECT create_hypertable('machine_status_history', 'start_timestamp',
        chunk_time_interval => INTERVAL '1 week',
        if_not_exists => TRUE
    );
""")
```

---

#### Task 1.7: Add Compression Policies
```python
# Compress material transactions after 7 days (75% space savings)
op.execute("""
    ALTER TABLE material_transactions SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'organization_id, material_id, plant_id'
    );
    SELECT add_compression_policy('material_transactions', INTERVAL '7 days');
""")

# Compress production logs after 7 days
op.execute("""
    ALTER TABLE production_logs SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'organization_id, work_order_id'
    );
    SELECT add_compression_policy('production_logs', INTERVAL '7 days');
""")
```

---

### Day 2 Morning: Cache Service (4 hours)

#### Task 1.8: Implement CacheService
**New File**: `/home/user/mes/backend/app/infrastructure/cache/cache_service.py`

**Features**:
- get(key) - Retrieve cached value
- set(key, value, ttl) - Store value with expiration
- delete(key) - Remove cached value
- clear() - Clear all expired entries
- exists(key) - Check if key exists

**Integration Points**:
- Dashboard metrics
- OEE calculations
- Material search results

---

### Day 2 Afternoon: Database Triggers & Functions (4 hours)

#### Task 1.9: Create PostgreSQL Triggers for Automation

**Add to migration**:

```sql
-- Trigger: Auto-calculate downtime duration
CREATE OR REPLACE FUNCTION calculate_downtime_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL THEN
        NEW.duration_minutes := EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) / 60;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_downtime_duration
BEFORE INSERT OR UPDATE ON downtime_events
FOR EACH ROW
EXECUTE FUNCTION calculate_downtime_duration();

-- Trigger: Low stock alert via LISTEN/NOTIFY
CREATE OR REPLACE FUNCTION notify_low_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity_on_hand < NEW.reorder_point THEN
        PERFORM pg_notify(
            'low_stock_alert',
            json_build_object(
                'material_id', NEW.id,
                'material_code', NEW.material_code,
                'quantity', NEW.quantity_on_hand,
                'reorder_point', NEW.reorder_point,
                'organization_id', NEW.organization_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_low_stock_alert
AFTER INSERT OR UPDATE OF quantity_on_hand ON materials
FOR EACH ROW
EXECUTE FUNCTION notify_low_stock();

-- Trigger: Work order status change notification
CREATE OR REPLACE FUNCTION notify_work_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.order_status IS DISTINCT FROM NEW.order_status THEN
        PERFORM pg_notify(
            'work_order_status_changed',
            json_build_object(
                'work_order_id', NEW.id,
                'work_order_number', NEW.work_order_number,
                'old_status', OLD.order_status,
                'new_status', NEW.order_status,
                'organization_id', NEW.organization_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_work_order_status_notification
AFTER UPDATE OF order_status ON work_orders
FOR EACH ROW
EXECUTE FUNCTION notify_work_order_status_change();
```

---

## Phase 2: Missing Critical Features (Day 3-4)

### Day 3: Material Transaction APIs (Bottom-Up)

#### Step 1: Add Missing Model Fields (if needed)
**File**: `/home/user/mes/backend/app/models/inventory.py`

Verify MaterialTransaction model has:
- transaction_type (RECEIPT, ISSUE, ADJUSTMENT, TRANSFER)
- reference_type (WORK_ORDER, PURCHASE_ORDER, ADJUSTMENT, TRANSFER)
- reference_id
- cost_per_unit
- total_cost

#### Step 2: Create Material Transaction Repository
**New File**: `/home/user/mes/backend/app/infrastructure/repositories/material_transaction_repository.py`

**Methods**:
- create_transaction()
- get_by_material_id()
- get_by_reference()
- get_transaction_history()

---

#### Step 3: Create Inventory Service
**New File**: `/home/user/mes/backend/app/application/services/inventory_service.py`

**Features**:
- Calculate available quantity (on_hand - reserved)
- Validate sufficient quantity for issue
- Integration with costing service

---

#### Step 4: Create Use Cases

**File**: `/home/user/mes/backend/app/application/use_cases/materials/receive_material.py`
```python
class ReceiveMaterialUseCase:
    """
    Business Logic:
    1. Validate material exists
    2. Create MaterialTransaction (type=RECEIPT)
    3. Update material.quantity_on_hand
    4. Calculate cost using FIFO/LIFO/Weighted Average
    5. Create cost layer (if FIFO)
    6. Trigger low stock check (if applicable)
    """
    def execute(self, dto: ReceiveMaterialDTO) -> MaterialTransaction:
        pass
```

**File**: `/home/user/mes/backend/app/application/use_cases/materials/issue_material.py`
```python
class IssueMaterialUseCase:
    """
    Business Logic:
    1. Validate material exists
    2. Validate sufficient quantity (on_hand >= quantity)
    3. Create MaterialTransaction (type=ISSUE)
    4. Update material.quantity_on_hand
    5. Calculate cost using FIFO/LIFO
    6. Update work order actual_material_cost (if reference is WO)
    7. Trigger low stock alert (if threshold crossed)
    """
    def execute(self, dto: IssueMaterialDTO) -> MaterialTransaction:
        pass
```

---

#### Step 5: Create DTOs
**File**: `/home/user/mes/backend/app/presentation/schemas/inventory.py`

```python
class ReceiveMaterialRequest(BaseModel):
    quantity: Decimal = Field(gt=0, description="Quantity received")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Cost per unit")
    reference_type: str = Field(..., description="PURCHASE_ORDER, TRANSFER, ADJUSTMENT")
    reference_id: Optional[int] = None
    transaction_date: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

class IssueMaterialRequest(BaseModel):
    quantity: Decimal = Field(gt=0, description="Quantity to issue")
    reference_type: str = Field(..., description="WORK_ORDER, TRANSFER, ADJUSTMENT")
    reference_id: int = Field(..., description="Work order ID or transfer ID")
    transaction_date: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
```

---

#### Step 6: Create API Endpoints
**New File**: `/home/user/mes/backend/app/presentation/api/v1/inventory.py`

```python
@router.post("/materials/{material_id}/receive", response_model=MaterialTransactionResponse)
def receive_material(
    material_id: int,
    request: ReceiveMaterialRequest,
    use_case: ReceiveMaterialUseCase = Depends(get_receive_material_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Receive material into inventory (goods receipt).

    **Business Rules**:
    - Updates quantity_on_hand
    - Creates cost layer (if FIFO costing method)
    - Triggers SAP sync (if configured)

    **Permissions**: materials.receive
    """
    return use_case.execute(request, current_user)

@router.post("/materials/{material_id}/issue", response_model=MaterialTransactionResponse)
def issue_material(
    material_id: int,
    request: IssueMaterialRequest,
    use_case: IssueMaterialUseCase = Depends(get_issue_material_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Issue material from inventory (goods issue to work order).

    **Business Rules**:
    - Validates sufficient quantity available
    - Updates quantity_on_hand
    - Consumes oldest cost layers (FIFO) or newest (LIFO)
    - Updates work order actual_material_cost
    - Triggers low stock alert if threshold crossed

    **Permissions**: materials.issue
    """
    return use_case.execute(request, current_user)

@router.get("/materials/{material_id}/transactions", response_model=List[MaterialTransactionResponse])
def get_material_transactions(
    material_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None,
    repo: MaterialTransactionRepository = Depends(get_material_transaction_repo),
    current_user: User = Depends(get_current_user)
):
    """
    Get transaction history for a material.

    **Query Parameters**:
    - start_date: Filter by date range
    - end_date: Filter by date range
    - transaction_type: RECEIPT, ISSUE, ADJUSTMENT, TRANSFER

    **Permissions**: materials.view
    """
    return repo.get_by_material_id(material_id, start_date, end_date, transaction_type)
```

---

### Day 4: Gantt Scheduling API (Bottom-Up)

#### Step 1: Review Existing Domain Service
**File**: `/home/user/mes/backend/app/domain/services/operation_scheduling_service.py`

Verify `generate_gantt_chart_data()` method exists and works.

---

#### Step 2: Create Scheduling Use Case
**New File**: `/home/user/mes/backend/app/application/use_cases/scheduling/get_gantt_chart.py`

```python
class GetGanttChartUseCase:
    """
    Business Logic:
    1. Get all work orders for plant/date range
    2. Get lane assignments
    3. Generate Gantt chart data with dependencies
    4. Calculate critical path
    5. Detect conflicts (lane overload)
    """
    def execute(self, dto: GetGanttChartDTO) -> GanttChartData:
        pass
```

---

#### Step 3: Create DTOs
**File**: `/home/user/mes/backend/app/presentation/schemas/scheduling.py`

```python
class GetGanttChartRequest(BaseModel):
    plant_id: Optional[int] = None
    start_date: date
    end_date: date
    lane_ids: Optional[List[int]] = None
    include_completed: bool = False

class GanttTask(BaseModel):
    id: int
    name: str
    work_order_number: str
    start_date: datetime
    end_date: datetime
    duration_hours: float
    lane_id: Optional[int]
    lane_name: Optional[str]
    dependencies: List[int]  # Work order IDs
    progress_percent: float
    status: str
    is_critical_path: bool = False

class GanttChartResponse(BaseModel):
    tasks: List[GanttTask]
    conflicts: List[dict]  # Lane overload conflicts
    critical_path: List[int]  # Work order IDs on critical path
```

---

#### Step 4: Create API Endpoint
**New File**: `/home/user/mes/backend/app/presentation/api/v1/scheduling.py`

```python
@router.get("/gantt", response_model=GanttChartResponse)
def get_gantt_chart(
    request: GetGanttChartRequest = Depends(),
    use_case: GetGanttChartUseCase = Depends(get_gantt_chart_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Get Gantt chart data for visual scheduling.

    **Features**:
    - Shows all work orders in date range
    - Displays lane assignments
    - Shows dependencies between work orders
    - Highlights critical path
    - Detects scheduling conflicts (lane overload)

    **Permissions**: scheduling.view
    """
    return use_case.execute(request, current_user)

@router.put("/gantt/reschedule", response_model=dict)
def reschedule_work_order(
    request: RescheduleRequest,
    use_case: RescheduleWorkOrderUseCase = Depends(get_reschedule_use_case),
    current_user: User = Depends(get_current_user)
):
    """
    Reschedule work order (drag-and-drop in Gantt chart).

    **Business Rules**:
    - Validates lane availability
    - Checks dependency constraints
    - Detects conflicts
    - Updates work order dates and lane assignment

    **Permissions**: scheduling.update
    """
    return use_case.execute(request, current_user)
```

---

## Phase 3: KPI Dashboard APIs (Day 5)

### Day 5 Morning: OEE Aggregation API

#### Step 1: Create OEE Aggregation Use Case
**New File**: `/home/user/mes/backend/app/application/use_cases/metrics/calculate_oee.py`

```python
class CalculateOEEUseCase:
    """
    Business Logic:
    1. Get all machines for plant/date range
    2. For each machine, aggregate:
       - Planned production time
       - Actual runtime (excluding downtime)
       - Ideal cycle time × good pieces
       - Good pieces / total pieces
    3. Calculate: Availability × Performance × Quality
    4. Cache results (15-minute TTL)
    """
    def execute(self, dto: CalculateOEEDTO) -> OEEMetrics:
        pass
```

---

#### Step 2: Create API Endpoint
**File**: `/home/user/mes/backend/app/presentation/api/v1/metrics.py` (update existing)

```python
@router.get("/oee", response_model=OEEDashboardResponse)
def get_oee_dashboard(
    plant_id: Optional[int] = None,
    start_date: date = Query(...),
    end_date: date = Query(...),
    machine_ids: Optional[List[int]] = Query(None),
    use_case: CalculateOEEUseCase = Depends(get_calculate_oee_use_case),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get OEE (Overall Equipment Effectiveness) metrics.

    **Calculation**:
    - Availability = Runtime / Planned Production Time
    - Performance = (Ideal Cycle Time × Total Pieces) / Runtime
    - Quality = Good Pieces / Total Pieces
    - OEE = Availability × Performance × Quality

    **Caching**: Results cached for 15 minutes

    **Permissions**: metrics.view
    """
    # Check cache first
    cache_key = f"oee:{plant_id}:{start_date}:{end_date}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    # Calculate and cache
    result = use_case.execute(request, current_user)
    cache_service.set(cache_key, result, ttl=900)  # 15 minutes
    return result
```

---

### Day 5 Afternoon: OTD and FPY APIs

#### Create remaining KPI endpoints:

1. **On-Time Delivery (OTD)**: `GET /api/v1/metrics/otd`
2. **First Pass Yield (FPY)**: `GET /api/v1/metrics/fpy`
3. **Cycle Time**: `GET /api/v1/metrics/cycle-time`

---

## Testing Strategy

### Unit Tests
- Test use cases with mocked repositories
- Test domain logic (OEECalculator, costing algorithms)
- Test validation rules

### Integration Tests
- Test API endpoints with test database
- Verify RLS context isolation
- Test transaction rollback

### E2E Tests
1. **Material Flow**: Receive → Issue → Work Order Cost Update
2. **Work Order Lifecycle**: Create → Release → Assign Lane → Log Production → Complete
3. **KPI Calculation**: Production Log → OEE Update → Dashboard Cache

---

## Verification Checklist

### Phase 1 (Security & Infrastructure)
- [ ] SQL injection vulnerability fixed and tested
- [ ] Custom exceptions created
- [ ] Global exception handler working
- [ ] PostgreSQL extensions added (pgmq, pg_cron)
- [ ] UNLOGGED cache table created
- [ ] CacheService implemented and tested
- [ ] Database triggers created and tested
- [ ] Migration runs successfully
- [ ] All tests passing

### Phase 2 (Material Transactions)
- [ ] MaterialTransaction model verified
- [ ] Repository created
- [ ] ReceiveMaterialUseCase implemented
- [ ] IssueMaterialUseCase implemented
- [ ] FIFO costing integrated
- [ ] API endpoints created
- [ ] Integration tests passing
- [ ] Work order cost updates working

### Phase 3 (Scheduling)
- [ ] GanttChartUseCase implemented
- [ ] Conflict detection working
- [ ] Critical path calculation working
- [ ] API endpoints created
- [ ] Reschedule validation working

### Phase 4 (KPIs)
- [ ] OEE aggregation working
- [ ] OTD calculation implemented
- [ ] FPY aggregation working
- [ ] Cache integration working
- [ ] Dashboard APIs responding <500ms

---

## Deployment Steps

1. **Run migration**: `alembic upgrade head`
2. **Restart application**: Ensure new environment variables loaded
3. **Verify extensions**: Check `pg_available_extensions`
4. **Test critical endpoints**:
   - POST /api/v1/materials/1/receive
   - GET /api/v1/scheduling/gantt
   - GET /api/v1/metrics/oee
5. **Monitor logs**: Watch for errors or warnings
6. **Check cache**: Verify UNLOGGED table working

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Security** | 0 SQL injection vulnerabilities | Security scan |
| **Performance** | Dashboard <500ms | API response time |
| **Functionality** | 3 critical features working | Manual testing |
| **Test Coverage** | >70% for new code | pytest-cov |
| **Migration Success** | 0 errors | Alembic upgrade |

---

## Rollback Plan

If critical issues arise:

1. **Database**: `alembic downgrade -1`
2. **Code**: `git revert <commit-hash>`
3. **Restart**: Application with previous code

---

**Plan Created By**: Claude (Sonnet 4.5)
**Estimated Total Effort**: 5 working days (Phases 1-3)
**Estimated Long-Term Effort**: 6 additional weeks for full architecture refactoring
