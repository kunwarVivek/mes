# Quality Management Domain

**Domain**: Quality Management
**Bounded Context**: Non-Conformance Management, Inspection Plans, Statistical Process Control (SPC)
**Owner**: Quality Assurance & Control
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

The Quality Management domain ensures product quality through Non-Conformance Report (NCR) workflows, inspection plans, and Statistical Process Control (SPC). It provides real-time quality metrics (FPY, Cp/Cpk) and drives continuous improvement through root cause analysis and corrective actions.

### Scope

**In Scope**:
- Non-Conformance Report (NCR) workflows (detection → investigation → resolution → closure)
- NCR photo attachments (MinIO object storage)
- Quality inspections (incoming, in-process, final)
- Quality checkpoints (inspection criteria)
- Inspection plans (product-specific quality requirements)
- Inspection points (first piece, periodic, sampling, final)
- Inspection characteristics (dimensional, weight, visual, functional)
- Inspection logs (inspection execution history)
- Inspection measurements (SPC data for control charts)
- Statistical Process Control (SPC) charts (X-bar/R, Cp/Cpk)
- First Pass Yield (FPY) calculation
- Real-time quality alerts (LISTEN/NOTIFY)

**Out of Scope**:
- Material quality at receipt → Handled as incoming inspection type
- Product certification and compliance → Project documents
- Customer complaints → Handled via NCR workflow
- Supplier quality performance → Supplier domain with NCR references

### Key Business Goals

1. **Reduce Defects**: Target 95%+ First Pass Yield (FPY)
2. **Fast NCR Resolution**: 90% of NCRs resolved within 7 days
3. **Process Stability**: Cp ≥ 1.33, Cpk ≥ 1.0 for critical characteristics
4. **Root Cause Analysis**: 100% of major/critical NCRs have documented root cause and corrective action
5. **Real-Time Visibility**: SPC charts updated hourly via timescaledb continuous aggregates
6. **Mobile-First**: PWA-based inspection logging with photo capture

---

## Core Concepts

### Non-Conformance Report (NCR)

**Definition**: A formal record of a quality issue (defect, deviation, non-conformance) requiring investigation and resolution.

**NCR Types**:
- **material**: Incoming material from supplier does not meet specifications
- **process**: In-process defect discovered during production
- **final_inspection**: Final product fails inspection before shipment

**Severity Levels**:
- **minor**: Cosmetic defect, does not affect function or safety
- **major**: Functional defect, affects performance but not safety
- **critical**: Safety-related defect, requires immediate action and customer notification

**NCR Workflow**:
```
open → in_review → resolved → closed
   ↓
(assignee investigates, documents root cause and corrective action)
```

**Example NCR**:
```
NCR-2025-001
Type: process
Severity: major
Description: Weld porosity found in frame assembly (Work Order WO-2025-001)
Root Cause: Incorrect welding wire used (AWS ER70S-6 instead of ER309L)
Corrective Action: Re-train operators on wire selection, implement wire color coding
Preventive Action: Add wire verification checkpoint to welding SOP
Status: resolved → closed
```

### Quality Inspection

**Definition**: A structured evaluation of materials or products against quality standards at specific points in the production process.

**Inspection Types**:
- **incoming**: Inspect material received from supplier (before use in production)
- **in_process**: Inspect work-in-progress during production (at critical operations)
- **final**: Inspect finished product before shipment to customer

**Inspection Result**:
- **passed**: Meets all quality criteria
- **failed**: One or more characteristics out of specification → triggers NCR creation
- **conditional**: Marginal acceptance with engineering disposition

### Quality Checkpoint

**Definition**: A specific criterion within an inspection (e.g., "Shaft diameter: 25mm ± 0.1mm").

**Checkpoint Structure**:
```python
checkpoint = {
    "checkpoint_name": "Shaft Diameter",
    "expected_value": "25.0 mm",
    "tolerance": "±0.1 mm",
    "actual_value": "25.05 mm",
    "result": "passed"  # 25.05 within [24.9, 25.1]
}
```

### Inspection Plan (MES Module)

**Definition**: A product-specific blueprint defining what, when, and how to inspect during production.

**Structure**:
```
Inspection Plan (Product: Hydraulic Pump)
├── Inspection Point 1: First Piece (before full production)
│   ├── Characteristic 1: Housing Diameter (24.5-25.5mm)
│   ├── Characteristic 2: Thread Depth (10-11mm)
│   └── Characteristic 3: Surface Finish (Ra < 3.2 μm)
├── Inspection Point 2: In-Process (every 50 units)
│   ├── Characteristic 1: Housing Diameter (24.5-25.5mm)
│   └── Characteristic 2: Weight (480-520g)
└── Inspection Point 3: Final (100% inspection)
    ├── Characteristic 1: Pressure Test (150 bar, no leaks)
    └── Characteristic 2: Visual Inspection (no scratches, dents)
```

### Inspection Point

**Definition**: A specific stage in production where inspection occurs.

**Frequency Types**:
- **first_piece**: Inspect first unit before full production run
- **periodic**: Inspect every N units (e.g., every 50 units)
- **sampling**: Statistical sampling based on AQL (Acceptable Quality Level)
- **final**: 100% inspection of finished products

**Sampling Plan Example (AQL 1.0, Lot Size 500)**:
```json
{
  "aql": 1.0,
  "lot_size": 500,
  "sample_size": 80,
  "accept_number": 2,
  "reject_number": 3
}
```

### Inspection Characteristic

**Definition**: A measurable or observable attribute of a product (dimension, weight, visual appearance).

**Characteristic Types**:
- **dimensional**: Length, width, diameter, depth (measured with calipers, micrometers)
- **weight**: Product weight (measured with scale)
- **visual**: Color, surface finish, presence of defects (human judgment)
- **functional**: Performance test (pressure test, leak test, electrical test)

**Specification Structure**:
```python
characteristic = {
    "name": "Shaft Diameter",
    "type": "dimensional",
    "specification": "25.0 mm",
    "usl": 25.1,  # Upper Spec Limit
    "lsl": 24.9,  # Lower Spec Limit
    "tolerance": "±0.1 mm",
    "measurement_method": "Micrometer",
    "measurement_unit": "mm",
    "control_chart_enabled": True  # Enable SPC
}
```

### Inspection Log

**Definition**: A record of an inspection execution (which inspector, when, result).

**Structure**:
```python
log = {
    "work_order_id": 123,
    "inspection_point_id": 5,
    "overall_result": "pass",  # or "fail"
    "inspected_at": "2025-11-07T14:30:00Z",
    "inspector_id": 67,
    "notes": "All measurements within tolerance",
    "ncr_report_id": None  # NULL if passed, NCR ID if failed
}
```

### Inspection Measurement

**Definition**: A single measured value for a specific characteristic during inspection (SPC data).

**Structure**:
```python
measurement = {
    "inspection_log_id": 2001,
    "characteristic_id": 15,
    "measured_value": 25.02,  # Actual measurement
    "within_tolerance": True,  # 25.02 within [24.9, 25.1]
    "result": "pass",
    "measured_at": "2025-11-07T14:32:00Z"
}
```

**SPC Data Collection**:
```python
# Collect 30 measurements for Shaft Diameter over 1 week
measurements = [25.01, 25.03, 24.98, 25.05, 24.97, ...]

# Calculate SPC metrics (via timescaledb continuous aggregate)
mean = 25.02
std_dev = 0.035
cp = (usl - lsl) / (6 * std_dev) = 0.95
cpk = min((usl - mean) / (3 * std_dev), (mean - lsl) / (3 * std_dev)) = 0.89
```

### Statistical Process Control (SPC)

**Definition**: Statistical analysis of inspection measurements to monitor process stability and capability.

**Control Limits**:
```python
# X-bar control chart (mean chart)
ucl = mean + 3 * (std_dev / sqrt(n))  # Upper Control Limit
lcl = mean - 3 * (std_dev / sqrt(n))  # Lower Control Limit

# R chart (range chart)
r_bar = avg(ranges)
ucl_r = d4 * r_bar  # d4 from SPC table
lcl_r = d3 * r_bar  # d3 from SPC table
```

**Process Capability Indices**:
```python
# Cp (Process Potential): Can the process meet specs if centered?
cp = (usl - lsl) / (6 * std_dev)

# Cpk (Process Performance): Is the process centered and capable?
cpk = min((usl - mean) / (3 * std_dev), (mean - lsl) / (3 * std_dev))

# Interpretation:
# Cp/Cpk < 1.0: Process incapable, high defect risk
# Cp/Cpk = 1.0-1.33: Marginally capable, some defects expected
# Cp/Cpk > 1.33: Capable process, low defect rate
```

### First Pass Yield (FPY)

**Definition**: Percentage of products passing inspection on the first attempt (no rework).

**Calculation**:
```python
fpy = (units_passed_first_time / total_units_inspected) * 100

# Example:
# Inspected: 100 units
# Passed first time: 95 units
# Failed: 5 units (required rework)
# FPY = 95%
```

---

## Database Schema

### Tables (9 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL with PostgreSQL-native features.

#### NCR Tables (4 tables)

##### 1. ncr_reports

Master table for non-conformance reports.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `ncr_number`: Unique identifier (e.g., "NCR-2025-001")
- `work_order_id`: FK to work_orders (optional)
- `project_id`: FK to projects (optional)
- `plant_id`: FK to plants
- `ncr_type`: Enum (material, process, final_inspection)
- `severity`: Enum (minor, major, critical)
- `description`: Problem description
- `root_cause`: Root cause analysis (required for resolution)
- `corrective_action`: Immediate fix taken
- `preventive_action`: Long-term prevention measures
- `status`: Enum (open, in_review, resolved, closed)
- `detected_by`: FK to users (who found the issue)
- `detected_at`: Detection timestamp
- `assigned_to`: FK to users (investigator)
- `resolved_by`: FK to users (who resolved)
- `resolved_at`: Resolution timestamp
- `closed_by`: FK to users (who closed)
- `closed_at`: Closure timestamp

**Indexes**:
- pg_search BM25: ncr_number, description, root_cause, corrective_action
- B-tree: status, severity, project_id, plant_id
- Partial index: `WHERE status IN ('open', 'in_review')` (active NCRs)

**LISTEN/NOTIFY Trigger** (real-time NCR alerts):
```sql
CREATE OR REPLACE FUNCTION notify_ncr_status_change() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status OR NEW.severity = 'critical' THEN
        PERFORM pg_notify('ncr_alert',
            json_build_object(
                'id', NEW.id,
                'ncr_number', NEW.ncr_number,
                'severity', NEW.severity,
                'status', NEW.status,
                'plant_id', NEW.plant_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ncr_status_notify
AFTER INSERT OR UPDATE ON ncr_reports
FOR EACH ROW EXECUTE FUNCTION notify_ncr_status_change();
```

##### 2. ncr_photos

Photo attachments for NCRs (MinIO object storage).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `ncr_id`: FK to ncr_reports
- `photo_name`: Original filename
- `file_path`: MinIO S3 path (e.g., "ncr-photos/NCR-2025-001-1.jpg")
- `file_size`: Bytes
- `mime_type`: image/jpeg, image/png
- `caption`: Photo description
- `uploaded_by`: FK to users
- `uploaded_at`: Upload timestamp

**MinIO Integration**:
```python
# Upload NCR photo
file_path = f"ncr-photos/{ncr_number}-{photo_id}.jpg"
minio_client.put_object(
    bucket_name='unison-files',
    object_name=file_path,
    data=photo_bytes,
    content_type='image/jpeg'
)

# Generate presigned URL (valid 7 days)
url = minio_client.presigned_get_object(
    bucket_name='unison-files',
    object_name=file_path,
    expires=timedelta(days=7)
)
```

##### 3. quality_inspections

Legacy simple inspection table (being replaced by inspection_plans module).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `work_order_id`: FK to work_orders
- `inspection_type`: Enum (in_process, final, incoming)
- `inspection_date`: Date
- `inspector_id`: FK to users
- `result`: Enum (passed, failed, conditional)
- `notes`: Inspection notes

**Note**: This table is being phased out in favor of the more comprehensive `inspection_plans` module (inspection_points, inspection_characteristics, inspection_logs, inspection_measurements).

##### 4. quality_checkpoints

Legacy checkpoint table linked to quality_inspections.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `inspection_id`: FK to quality_inspections
- `checkpoint_name`: Criterion name
- `expected_value`: Specification
- `actual_value`: Measured value
- `result`: Enum (passed, failed)
- `notes`: Checkpoint notes

**Note**: Being replaced by `inspection_characteristics` + `inspection_measurements` for better SPC support.

#### Inspection Plan Tables (5 tables - MES Module)

##### 5. inspection_plans

Product-specific inspection blueprint.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `product_id`: FK to products (which product this applies to)
- `plan_name`: Plan name (e.g., "Hydraulic Pump Inspection Plan")
- `description`: Plan description
- `is_active`: Soft delete flag

**Unique Constraint**: `(organization_id, product_id, plan_name)`

##### 6. inspection_points

Inspection stages within a plan (first piece, periodic, final).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `inspection_plan_id`: FK to inspection_plans
- `point_name`: Point name (e.g., "First Piece", "In-Process")
- `frequency_type`: Enum (first_piece, periodic, sampling, final)
- `frequency_value`: For periodic, inspect every N units
- `sampling_plan`: JSONB (AQL, sample size, accept/reject numbers)
- `sequence_order`: Display order

**Sampling Plan Example**:
```json
{
  "aql": 1.0,
  "lot_size": 500,
  "sample_size": 80,
  "accept_number": 2,
  "reject_number": 3,
  "inspection_level": "II"
}
```

##### 7. inspection_characteristics

Measurable attributes within an inspection point.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `inspection_point_id`: FK to inspection_points
- `characteristic_name`: Name (e.g., "Shaft Diameter", "Weight")
- `characteristic_type`: Enum (dimensional, weight, visual, functional)
- `specification`: Target value (e.g., "25mm", "500g")
- `usl`: Upper Spec Limit (decimal)
- `lsl`: Lower Spec Limit (decimal)
- `tolerance`: Tolerance string (e.g., "±0.1mm")
- `measurement_method`: Tool/method (e.g., "Micrometer", "Scale")
- `measurement_unit`: Unit (mm, g, kg, etc.)
- `control_chart_enabled`: Boolean (enable SPC charts)
- `sequence_order`: Display order

##### 8. inspection_logs

Inspection execution history (timescaledb hypertable for time-series optimization).

**Key Columns**:
- `id`: Primary key (BIGSERIAL)
- `organization_id`: Multi-tenant isolation
- `work_order_id`: FK to work_orders
- `inspection_point_id`: FK to inspection_points
- `overall_result`: Enum (pass, fail)
- `inspected_at`: Inspection timestamp
- `inspector_id`: FK to users
- `notes`: Inspection notes
- `ncr_report_id`: FK to ncr_reports (if failed)

**timescaledb Hypertable**:
```sql
SELECT create_hypertable('inspection_logs', 'inspected_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 75% compression after 7 days
ALTER TABLE inspection_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, work_order_id'
);
SELECT add_compression_policy('inspection_logs', INTERVAL '7 days', if_not_exists => TRUE);

-- 2-year retention policy
SELECT add_retention_policy('inspection_logs', INTERVAL '2 years', if_not_exists => TRUE);
```

##### 9. inspection_measurements

Individual measurement values for SPC (timescaledb hypertable).

**Key Columns**:
- `id`: Primary key (BIGSERIAL)
- `organization_id`: Multi-tenant isolation
- `inspection_log_id`: FK to inspection_logs
- `characteristic_id`: FK to inspection_characteristics
- `measured_value`: Measured value (decimal)
- `measured_text`: For non-numeric (e.g., "Pass", "Good")
- `within_tolerance`: Boolean (within USL/LSL)
- `result`: Enum (pass, fail)
- `measured_at`: Measurement timestamp

**timescaledb Hypertable**:
```sql
SELECT create_hypertable('inspection_measurements', 'measured_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Compression and retention same as inspection_logs
```

**Continuous Aggregate** (daily SPC metrics):
```sql
CREATE MATERIALIZED VIEW daily_spc_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', measured_at) AS day,
    organization_id,
    characteristic_id,
    AVG(measured_value) AS mean_value,
    STDDEV(measured_value) AS std_dev,
    COUNT(*) AS sample_count,
    MIN(measured_value) AS min_value,
    MAX(measured_value) AS max_value
FROM inspection_measurements
WHERE measured_value IS NOT NULL
GROUP BY day, organization_id, characteristic_id
WITH NO DATA;

-- Auto-refresh hourly
SELECT add_continuous_aggregate_policy('daily_spc_metrics',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

**Cp/Cpk Calculation View**:
```sql
CREATE VIEW spc_process_capability AS
SELECT
    ds.characteristic_id,
    ic.characteristic_name,
    ic.usl,
    ic.lsl,
    ds.mean_value,
    ds.std_dev,
    (ic.usl - ic.lsl) / (6 * ds.std_dev) AS cp,
    LEAST(
        (ic.usl - ds.mean_value) / (3 * ds.std_dev),
        (ds.mean_value - ic.lsl) / (3 * ds.std_dev)
    ) AS cpk
FROM daily_spc_metrics ds
JOIN inspection_characteristics ic ON ds.characteristic_id = ic.id
WHERE ic.control_chart_enabled = TRUE
AND ds.std_dev > 0;
```

---

## Business Rules

### BR-QUAL-001: NCR Number Uniqueness

**Rule**: NCR numbers must be unique across the organization.

**Validation**:
```python
class CreateNCRUseCase:
    def execute(self, dto: CreateNCRDTO) -> NCRReport:
        # Check uniqueness
        existing = self.ncr_repo.find_by_number(dto.ncr_number, dto.organization_id)
        if existing:
            raise NCRNumberAlreadyExistsError(dto.ncr_number)

        # Create NCR
        ncr = NCRReport(
            ncr_number=dto.ncr_number,
            ncr_type=dto.ncr_type,
            severity=dto.severity,
            description=dto.description,
            status=NCRStatus.OPEN
        )
        return self.ncr_repo.save(ncr)
```

### BR-QUAL-002: NCR Cannot Be Closed Without Root Cause and Corrective Action

**Rule**: NCRs with severity='major' or 'critical' must have root_cause and corrective_action before status='closed'.

**Validation**:
```python
class CloseNCRUseCase:
    def execute(self, ncr_id: int, closed_by: int) -> NCRReport:
        ncr = self.ncr_repo.find_by_id(ncr_id)

        # Validate root cause for major/critical NCRs
        if ncr.severity in [NCRSeverity.MAJOR, NCRSeverity.CRITICAL]:
            if not ncr.root_cause or not ncr.corrective_action:
                raise CannotCloseNCRWithoutRootCauseError(
                    ncr_number=ncr.ncr_number,
                    severity=ncr.severity
                )

        # Close NCR
        ncr.status = NCRStatus.CLOSED
        ncr.closed_by = closed_by
        ncr.closed_at = datetime.utcnow()

        return self.ncr_repo.save(ncr)
```

### BR-QUAL-003: Failed Inspection Must Create NCR

**Rule**: When an inspection fails (overall_result='fail'), an NCR must be automatically created.

**Implementation**:
```python
class RecordInspectionUseCase:
    def execute(self, dto: RecordInspectionDTO) -> InspectionLog:
        # Create inspection log
        log = InspectionLog(
            work_order_id=dto.work_order_id,
            inspection_point_id=dto.inspection_point_id,
            overall_result=dto.overall_result,
            inspector_id=dto.inspector_id
        )

        # If failed, auto-create NCR
        if dto.overall_result == InspectionResult.FAIL:
            ncr = self._create_ncr_from_failed_inspection(log, dto.failed_characteristics)
            log.ncr_report_id = ncr.id

        return self.inspection_log_repo.save(log)

    def _create_ncr_from_failed_inspection(
        self,
        log: InspectionLog,
        failed_characteristics: List[str]
    ) -> NCRReport:
        ncr = NCRReport(
            ncr_number=self._generate_ncr_number(),
            ncr_type=NCRType.PROCESS,
            severity=NCRSeverity.MAJOR,  # Default to major
            description=f"Failed inspection at {log.inspection_point.point_name}. "
                        f"Failed characteristics: {', '.join(failed_characteristics)}",
            work_order_id=log.work_order_id,
            detected_by=log.inspector_id,
            status=NCRStatus.OPEN
        )
        return self.ncr_repo.save(ncr)
```

### BR-QUAL-004: Measurement Out of Tolerance Fails Inspection

**Rule**: If any inspection measurement is `within_tolerance=False`, the overall inspection result must be 'fail'.

**Validation**:
```python
class RecordMeasurementUseCase:
    def execute(self, dto: RecordMeasurementDTO) -> InspectionMeasurement:
        characteristic = self.characteristic_repo.find_by_id(dto.characteristic_id)

        # Evaluate tolerance
        within_tolerance = (
            characteristic.lsl <= dto.measured_value <= characteristic.usl
        )

        measurement = InspectionMeasurement(
            inspection_log_id=dto.inspection_log_id,
            characteristic_id=dto.characteristic_id,
            measured_value=dto.measured_value,
            within_tolerance=within_tolerance,
            result=MeasurementResult.PASS if within_tolerance else MeasurementResult.FAIL
        )

        # If out of tolerance, fail the inspection
        if not within_tolerance:
            inspection_log = self.inspection_log_repo.find_by_id(dto.inspection_log_id)
            inspection_log.overall_result = InspectionResult.FAIL

        return self.measurement_repo.save(measurement)
```

### BR-QUAL-005: SPC Control Chart Requires ≥30 Samples

**Rule**: SPC control charts (Cp/Cpk) require at least 30 measurement samples for statistical validity.

**Validation**:
```python
class CalculateSPCMetricsUseCase:
    MINIMUM_SAMPLE_SIZE = 30

    def execute(self, characteristic_id: int, days: int = 30) -> SPCMetrics:
        # Query continuous aggregate
        metrics = self.spc_repo.get_daily_metrics(
            characteristic_id=characteristic_id,
            from_date=datetime.utcnow().date() - timedelta(days=days)
        )

        total_samples = sum(m.sample_count for m in metrics)

        if total_samples < self.MINIMUM_SAMPLE_SIZE:
            raise InsufficientSPCSamplesError(
                characteristic_id=characteristic_id,
                required=self.MINIMUM_SAMPLE_SIZE,
                actual=total_samples
            )

        # Calculate Cp/Cpk
        return self._calculate_process_capability(metrics)
```

### BR-QUAL-006: Critical NCRs Trigger Immediate Email Notification

**Rule**: NCRs with severity='critical' must trigger email notification to quality manager and plant manager.

**Implementation**:
```python
class CreateNCRUseCase:
    def execute(self, dto: CreateNCRDTO) -> NCRReport:
        ncr = NCRReport(...)
        ncr = self.ncr_repo.save(ncr)

        # Send email for critical NCRs
        if ncr.severity == NCRSeverity.CRITICAL:
            self.queue.send('email_notifications', {
                'template': 'critical_ncr_alert',
                'to': [
                    ncr.plant.quality_manager_email,
                    ncr.plant.plant_manager_email
                ],
                'ncr_id': ncr.id,
                'ncr_number': ncr.ncr_number,
                'description': ncr.description
            })

        return ncr
```

---

## Use Cases

### UC-QUAL-001: Create NCR

**Actor**: QC Inspector, Operator

**Preconditions**: Quality issue detected, user has `ncr:create` permission

**Flow**:
1. User submits NCR details (type, severity, description, work order/project reference)
2. System validates NCR number uniqueness (BR-QUAL-001)
3. System creates NCR with status='open'
4. System assigns NCR to quality manager (default) or specified user
5. System triggers LISTEN/NOTIFY for real-time dashboard update
6. If severity='critical', system queues email notification (BR-QUAL-006)
7. System returns NCR ID

**Postconditions**: NCR created, assignee notified

**API**: `POST /api/v1/ncr-reports`

### UC-QUAL-002: Record Inspection (with measurements)

**Actor**: QC Inspector (mobile PWA)

**Preconditions**: Work order in progress, inspection point defined

**Flow**:
1. Inspector selects work order and inspection point
2. System displays inspection characteristics to measure
3. Inspector records measurements for each characteristic
4. System evaluates each measurement against USL/LSL (BR-QUAL-004)
5. System calculates overall inspection result (pass/fail)
6. If any measurement fails, system auto-creates NCR (BR-QUAL-003)
7. System saves inspection log and measurements
8. System triggers LISTEN/NOTIFY for real-time SPC chart update

**Postconditions**: Inspection recorded, NCR created if failed, SPC data updated

**API**: `POST /api/v1/inspection-logs`

### UC-QUAL-003: View SPC Chart (Cp/Cpk)

**Actor**: Quality Manager, Process Engineer

**Preconditions**: Characteristic has control_chart_enabled=TRUE, ≥30 samples (BR-QUAL-005)

**Flow**:
1. User requests SPC chart for specific characteristic
2. System queries timescaledb continuous aggregate (daily_spc_metrics)
3. System calculates Cp/Cpk from aggregated statistics
4. System generates X-bar/R control chart data
5. System returns chart data (JSON) with control limits

**Postconditions**: SPC chart data displayed (frontend renders chart)

**API**: `GET /api/v1/spc-charts?characteristic_id=15&from=2025-11-01&to=2025-11-07`

### UC-QUAL-004: Resolve NCR (Root Cause Analysis)

**Actor**: Quality Engineer, Production Supervisor

**Preconditions**: NCR status='open' or 'in_review', user has `ncr:update` permission

**Flow**:
1. User investigates NCR and documents root cause
2. User documents corrective action (immediate fix)
3. User documents preventive action (long-term prevention)
4. User updates NCR status='resolved'
5. System validates root cause and corrective action provided (BR-QUAL-002)
6. System triggers LISTEN/NOTIFY for real-time dashboard update

**Postconditions**: NCR resolved, awaiting closure approval

**API**: `PUT /api/v1/ncr-reports/{id}/resolve`

### UC-QUAL-005: Close NCR

**Actor**: Quality Manager

**Preconditions**: NCR status='resolved', user has `ncr:close` permission

**Flow**:
1. Quality manager reviews resolved NCR
2. Quality manager verifies corrective action effective
3. Quality manager closes NCR (status='closed')
4. System validates root cause documented (BR-QUAL-002)
5. System triggers LISTEN/NOTIFY for real-time dashboard update

**Postconditions**: NCR closed, archived for historical analysis

**API**: `POST /api/v1/ncr-reports/{id}/close`

### UC-QUAL-006: Calculate First Pass Yield (FPY)

**Actor**: System (pg_cron daily job)

**Preconditions**: Inspection logs exist

**Flow**:
1. System queries inspection logs for date range (e.g., last 30 days)
2. System calculates FPY = (passed / total) * 100
3. System stores FPY metric in reporting table
4. System triggers alert if FPY < 90%

**pg_cron Job**:
```sql
SELECT cron.schedule(
    'fpy-calculation',
    '0 7 * * *',  -- Daily at 7 AM
    $$
    INSERT INTO quality_metrics (organization_id, metric_type, metric_value, calculated_at)
    SELECT
        organization_id,
        'fpy',
        (SUM(CASE WHEN overall_result = 'pass' THEN 1 ELSE 0 END)::FLOAT / COUNT(*)::FLOAT * 100) AS fpy,
        NOW()
    FROM inspection_logs
    WHERE inspected_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY organization_id;
    $$
);
```

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### NCR Endpoints (7 total)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ncr-reports` | Create NCR | JWT + `ncr:create` |
| GET | `/api/v1/ncr-reports` | List NCRs (paginated, filterable) | JWT + `ncr:read` |
| GET | `/api/v1/ncr-reports/{id}` | Get NCR details | JWT + `ncr:read` |
| PUT | `/api/v1/ncr-reports/{id}` | Update NCR | JWT + `ncr:update` |
| POST | `/api/v1/ncr-reports/{id}/resolve` | Resolve NCR (root cause + actions) | JWT + `ncr:update` |
| POST | `/api/v1/ncr-reports/{id}/close` | Close NCR | JWT + `ncr:close` |
| POST | `/api/v1/ncr-reports/{id}/photos` | Upload NCR photo (multipart) | JWT + `ncr:create` |

### Inspection Endpoints (9 total)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/inspection-plans` | List inspection plans | JWT + `quality:read` |
| GET | `/api/v1/inspection-plans/{id}` | Get plan details | JWT + `quality:read` |
| POST | `/api/v1/inspection-logs` | Record inspection | JWT + `quality:log` |
| GET | `/api/v1/inspection-logs?work_order_id=123` | List logs by work order | JWT + `quality:read` |
| GET | `/api/v1/spc-charts?characteristic_id=15` | Get SPC chart data | JWT + `quality:read` |
| GET | `/api/v1/spc-charts/{characteristic_id}/cp-cpk` | Get Cp/Cpk metrics | JWT + `quality:read` |
| GET | `/api/v1/quality-metrics/fpy` | Get First Pass Yield | JWT + `quality:read` |
| GET | `/api/v1/quality-metrics/ncr-trend` | Get NCR trend (count by month) | JWT + `quality:read` |
| GET | `/api/v1/quality-metrics/defect-pareto` | Get Pareto chart data (top defects) | JWT + `quality:read` |

### Example: Record Inspection

```http
POST /api/v1/inspection-logs
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "work_order_id": 123,
  "inspection_point_id": 5,
  "measurements": [
    {
      "characteristic_id": 15,
      "measured_value": 25.02
    },
    {
      "characteristic_id": 16,
      "measured_value": 505.0
    }
  ],
  "notes": "First piece inspection - all within tolerance"
}
```

**Response (201 Created)**:
```json
{
  "id": 2001,
  "work_order_id": 123,
  "work_order_number": "WO-2025-001",
  "inspection_point_id": 5,
  "inspection_point_name": "First Piece",
  "overall_result": "pass",
  "inspected_at": "2025-11-07T19:00:00Z",
  "inspector_id": 67,
  "inspector_name": "Jane Smith",
  "measurements": [
    {
      "characteristic_id": 15,
      "characteristic_name": "Shaft Diameter",
      "measured_value": 25.02,
      "within_tolerance": true,
      "result": "pass"
    },
    {
      "characteristic_id": 16,
      "characteristic_name": "Weight",
      "measured_value": 505.0,
      "within_tolerance": true,
      "result": "pass"
    }
  ],
  "ncr_report_id": null
}
```

### Example: Get SPC Chart (Cp/Cpk)

```http
GET /api/v1/spc-charts/15/cp-cpk?from=2025-11-01&to=2025-11-07
Authorization: Bearer {jwt_token}
```

**Backend Query (timescaledb continuous aggregate)**:
```sql
SELECT * FROM spc_process_capability
WHERE characteristic_id = 15
AND day BETWEEN '2025-11-01' AND '2025-11-07';
```

**Response (200 OK)**:
```json
{
  "characteristic_id": 15,
  "characteristic_name": "Shaft Diameter",
  "specification": "25.0 mm",
  "usl": 25.1,
  "lsl": 24.9,
  "tolerance": "±0.1 mm",
  "statistics": {
    "mean": 25.02,
    "std_dev": 0.035,
    "cp": 0.95,
    "cpk": 0.89,
    "sample_count": 45
  },
  "control_limits": {
    "ucl": 25.125,
    "lcl": 24.915
  },
  "interpretation": {
    "process_capability": "marginally_capable",
    "recommendation": "Process average is off-center. Consider centering process to improve Cpk."
  }
}
```

---

## PostgreSQL-Native Features

### 1. timescaledb Hypertables (inspection_logs, inspection_measurements)

**Purpose**: Time-series optimization for inspection history with 75% compression.

**Query Performance**:
- **Standard PostgreSQL**: 2s for 1M inspection records
- **timescaledb**: 200ms for 1M inspection records
- **Improvement**: 10x faster

**Continuous Aggregate (daily_spc_metrics)**:
```sql
-- Query SPC metrics (instant, pre-aggregated)
SELECT * FROM daily_spc_metrics
WHERE characteristic_id = 15
AND day BETWEEN '2025-11-01' AND '2025-11-07';

-- Auto-refreshed hourly by timescaledb
```

### 2. LISTEN/NOTIFY for Real-Time NCR Alerts

**Purpose**: Pub/sub messaging for live quality dashboard (no polling required).

**WebSocket Integration**:
```javascript
// Frontend (React)
const ws = new WebSocket(`wss://api.example.com/ws?token=${token}`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.event === 'ncr_alert') {
    showNotification(update.data);
    updateNCRDashboard(update.data);
  }
};
```

### 3. pg_search BM25 Full-Text Search (ncr_reports)

**Purpose**: Fast NCR search by description, root cause, corrective action (20x faster than tsvector).

**Query Example**:
```sql
-- Search NCRs by description or root cause
SELECT * FROM ncr_reports
WHERE ncr_reports @@@ 'weld porosity stainless'
ORDER BY paradedb.rank('ncr_reports_search_idx') DESC
LIMIT 20;

-- Execution time: 5ms for 10K NCRs
```

### 4. pg_cron for FPY Calculation

**Purpose**: Daily automated First Pass Yield calculation (replaces Celery Beat).

### 5. MinIO Object Storage for NCR Photos

**Purpose**: S3-compatible object storage for NCR photo attachments.

**Integration**:
```python
# Upload photo
minio_client.put_object(
    bucket_name='unison-files',
    object_name=f"ncr-photos/{ncr_number}-{photo_id}.jpg",
    data=photo_bytes,
    content_type='image/jpeg'
)

# Generate presigned URL
url = minio_client.presigned_get_object(
    bucket_name='unison-files',
    object_name=file_path,
    expires=timedelta(days=7)
)
```

---

## Integration Points

### Upstream Dependencies (Data Consumed)

1. **Production Domain** (`work_orders`)
   - Inspections tied to work orders
   - NCRs reference work orders

2. **Project Domain** (`projects`)
   - NCRs can reference projects
   - Product-specific inspection plans

3. **User Domain** (`users`)
   - Inspectors, NCR assignees, resolvers

### Downstream Consumers (Data Provided)

1. **Reporting Domain** (KPI Dashboards)
   - FPY metric for quality dashboard
   - NCR trend analysis (count by month, severity)
   - Defect Pareto charts (top 5 defect types)

2. **Maintenance Domain** (PM Schedules)
   - NCRs for equipment failures drive PM schedule updates

3. **Traceability Domain** (Lot/Serial Numbers)
   - Failed inspections trigger lot holds
   - NCRs reference lot/serial numbers for recall management

---

## Summary

The Quality Management domain ensures product quality through NCR workflows, inspection plans, and SPC. Key PostgreSQL-native features include:

- **timescaledb**: 10x faster SPC queries with 75% compression
- **LISTEN/NOTIFY**: Real-time NCR alerts via WebSocket (no polling)
- **pg_search BM25**: 20x faster NCR search
- **pg_cron**: Automated FPY calculation (daily)
- **MinIO**: S3-compatible NCR photo storage

**Performance Targets**:
- NCR search: <100ms for 10K+ NCRs
- SPC chart query: <200ms for 1M+ measurements
- Real-time NCR alerts: <50ms latency via WebSocket
- Daily SPC metrics: Instant (pre-aggregated via continuous aggregate)

**Quality Targets**:
- First Pass Yield: >95%
- NCR Resolution Time: 90% within 7 days
- Process Capability: Cp ≥ 1.33, Cpk ≥ 1.0

**Next Domain**: [MAINTENANCE.md](./MAINTENANCE.md) - PM Schedules, Downtime Tracking, MTBF/MTTR
