# Functional Requirements Document - API Contracts
# Unison Manufacturing ERP

**Version**: 4.0
**Date**: 2025-11-10
**Domain**: API Endpoints, Request/Response Specifications

---

## Overview

This document contains all REST API endpoint specifications for the Unison Manufacturing ERP system. All endpoints require authentication unless otherwise specified.

**Base URL**: `https://{organization_slug}.unison.com/api/v1`

**Authentication**: JWT Bearer token in Authorization header

---

### 6.1 Material Endpoints

**GET /api/v1/materials**
- **Description**: List all materials
- **Auth**: Required (JWT)
- **Query Params**:
  - `category_id` (optional): Filter by category
  - `search` (optional): Search by name or code
  - `page` (optional): Page number (default 1)
  - `per_page` (optional): Items per page (default 50, max 100)
- **Response 200**:
```json
{
  "materials": [
    {
      "id": 123,
      "material_code": "MTL-001",
      "name": "Steel Plate 10mm",
      "category_id": 5,
      "category_name": "Raw Materials - Steel",
      "unit_of_measure": "kg",
      "standard_cost": 150.00,
      "barcode_url": "https://minio.../barcode-123.png",
      "custom_fields": {
        "heat_treatment_required": true,
        "certification_type": "ISO"
      }
    }
  ],
  "total": 245,
  "page": 1,
  "per_page": 50
}
```

**POST /api/v1/materials**
- **Description**: Create new material
- **Auth**: Required (role: admin or materials_write)
- **Request Body**:
```json
{
  "material_code": "MTL-002",
  "name": "Aluminum Sheet 5mm",
  "description": "5052 aluminum alloy",
  "category_id": 6,
  "unit_of_measure": "kg",
  "standard_cost": 200.00,
  "minimum_stock_level": 500,
  "maximum_stock_level": 2000,
  "reorder_point": 1000,
  "custom_fields": {
    "supplier_lead_time": 30
  }
}
```
- **Response 201**: (same as GET single material)
- **Response 400**: Validation errors
```json
{
  "error": "Validation failed",
  "details": [
    {"field": "material_code", "message": "Material code MTL-002 already exists"}
  ]
}
```

### 6.2 Work Order Endpoints

**POST /api/v1/work-orders/{id}/start**
- **Description**: Start work order
- **Auth**: Required (role: supervisor or operator)
- **Path Params**: `id` - Work order ID
- **Request Body**: (empty, or optional note)
- **Response 200**:
```json
{
  "id": 456,
  "work_order_number": "WO-2025-001",
  "status": "in_progress",
  "started_at": "2025-11-06T10:00:00Z",
  "started_by": {"id": 23, "name": "John Doe"}
}
```
- **Response 400**: Cannot start (dependencies not met)
```json
{
  "error": "Cannot start work order",
  "reason": "Waiting for WO-2024-999 to complete"
}
```

**POST /api/v1/production-logs**
- **Description**: Log production progress
- **Auth**: Required (role: operator)
- **Request Body**:
```json
{
  "work_order_id": 456,
  "operation_id": 12,
  "quantity_completed": 50,
  "hours_worked": 4.5,
  "notes": "All units passed inspection"
}
```
- **Response 201**:
```json
{
  "id": 789,
  "work_order_id": 456,
  "work_order_number": "WO-2025-001",
  "quantity_completed": 50,
  "cumulative_completed": 150,
  "quantity_ordered": 200,
  "progress_percent": 75,
  "material_cost_added": 540.00,
  "labor_cost_added": 112.50,
  "logged_at": "2025-11-06T14:30:00Z"
}
```

### 6.3 NCR Endpoints

**POST /api/v1/ncr-reports**
- **Description**: Create NCR with photos
- **Auth**: Required (role: inspector)
- **Request Body** (multipart/form-data):
```
ncr_type_id: 3
severity: major
description: Cracks found on welded joint...
work_order_id: 456
photos[]: (file binary)
photos[]: (file binary)
```
- **Response 201**:
```json
{
  "id": 234,
  "ncr_number": "NCR-2025-042",
  "ncr_type": "Process Deviation",
  "severity": "major",
  "status": "submitted",
  "work_order_number": "WO-2025-001",
  "photos": [
    {"id": 1, "url": "https://minio.../ncr-234-photo-1.jpg"},
    {"id": 2, "url": "https://minio.../ncr-234-photo-2.jpg"}
  ],
  "current_assignee": {"id": 45, "name": "QC Manager"},
  "created_at": "2025-11-06T15:00:00Z"
}
```

### 6.4 Workflow Endpoints

**POST /api/v1/workflows/{entity_type}/{entity_id}/transition/{transition_code}**
- **Description**: Execute workflow transition
- **Auth**: Required (must be assigned user)
- **Path Params**:
  - `entity_type`: "ncr_report", "rda_drawing", "work_order", etc.
  - `entity_id`: Entity ID
  - `transition_code`: "approve", "reject", "assign", etc.
- **Request Body**:
```json
{
  "comment": "Root cause identified, approved for disposition"
}
```
- **Response 200**:
```json
{
  "previous_state": "submitted",
  "current_state": "approved",
  "current_assignee": {"id": 67, "name": "Plant Manager"},
  "performed_by": {"id": 45, "name": "QC Manager"},
  "performed_at": "2025-11-06T16:00:00Z"
}
```
- **Response 403**: Not authorized
```json
{
  "error": "Not authorized",
  "reason": "This task is assigned to QC Manager, not you"
}
```



### 6.5 Equipment Management Endpoints

**GET /api/v1/machines**
- **Description**: List all machines/equipment
- **Auth**: Required (JWT)
- **Query Params**:
  - `plant_id` (optional): Filter by plant
  - `status` (optional): Filter by status (available, running, down, maintenance)
  - `search` (optional): Search by name or code
- **Response 200**:
```json
{
  "machines": [
    {
      "id": 15,
      "machine_code": "CNC-001",
      "name": "CNC Lathe Machine",
      "plant_id": 3,
      "plant_name": "Fabrication Plant",
      "status": "running",
      "current_work_order": {
        "id": 456,
        "work_order_number": "WO-2025-001"
      },
      "capacity_units_per_hour": 50,
      "utilization_percent": 76.2,
      "last_maintenance_date": "2025-10-15",
      "next_maintenance_due": "2025-11-15"
    }
  ],
  "total": 24
}
```

**PUT /api/v1/machines/{id}/status**
- **Description**: Update machine status
- **Auth**: Required (role: operator or supervisor)
- **Request Body**:
```json
{
  "status": "down",
  "reason_code": "mechanical_failure",
  "notes": "Hydraulic pump failed, maintenance called"
}
```
- **Response 200**:
```json
{
  "id": 15,
  "machine_code": "CNC-001",
  "status": "down",
  "downtime_started_at": "2025-11-06T14:30:00Z",
  "downtime_reason": "Mechanical Failure"
}
```

**GET /api/v1/machines/{id}/utilization**
- **Description**: Get machine utilization metrics
- **Auth**: Required
- **Query Params**:
  - `start_date`: Start of date range (required)
  - `end_date`: End of date range (required)
- **Response 200**:
```json
{
  "machine_id": 15,
  "machine_name": "CNC Lathe Machine",
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-06"
  },
  "metrics": {
    "available_time_minutes": 2400,
    "productive_time_minutes": 1830,
    "utilization_percent": 76.25,
    "downtime_minutes": 360,
    "setup_time_minutes": 210
  },
  "downtime_breakdown": [
    {"reason": "Mechanical Failure", "minutes": 180, "occurrences": 2},
    {"reason": "Material Shortage", "minutes": 120, "occurrences": 3},
    {"reason": "Setup/Changeover", "minutes": 60, "occurrences": 1}
  ]
}
```

### 6.6 Shift Management Endpoints

**GET /api/v1/shifts**
- **Description**: List shift patterns
- **Auth**: Required
- **Query Params**:
  - `plant_id` (optional): Filter by plant
  - `active_only` (optional): Show only active shifts
- **Response 200**:
```json
{
  "shifts": [
    {
      "id": 5,
      "name": "Day Shift",
      "start_time": "06:00",
      "end_time": "14:00",
      "break_duration_minutes": 30,
      "active_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "production_target_units": 400,
      "oee_target_percent": 85
    },
    {
      "id": 6,
      "name": "Night Shift",
      "start_time": "22:00",
      "end_time": "06:00",
      "break_duration_minutes": 30,
      "active_days": ["sunday", "monday", "tuesday", "wednesday", "thursday"],
      "production_target_units": 350,
      "oee_target_percent": 80
    }
  ]
}
```

**POST /api/v1/shift-handovers**
- **Description**: Log shift handover notes
- **Auth**: Required (role: operator or supervisor)
- **Request Body**:
```json
{
  "shift_id": 5,
  "date": "2025-11-06",
  "handover_notes": "WO-001 is 75% complete, waiting for aluminum delivery for WO-002. Machine CNC-003 has minor vibration issue.",
  "wip_work_orders": [
    {"work_order_id": 456, "status": "in_progress", "percent_complete": 75}
  ],
  "issues": [
    {"machine_id": 18, "description": "Minor vibration in spindle"}
  ]
}
```
- **Response 201**:
```json
{
  "id": 123,
  "shift_id": 5,
  "shift_name": "Day Shift",
  "date": "2025-11-06",
  "logged_by": {"id": 23, "name": "John Supervisor"},
  "handover_notes": "WO-001 is 75% complete...",
  "acknowledged_by": null,
  "acknowledged_at": null
}
```

**GET /api/v1/shift-performance**
- **Description**: Get shift performance metrics
- **Auth**: Required
- **Query Params**:
  - `shift_id`: Shift ID (required)
  - `date`: Date (required)
- **Response 200**:
```json
{
  "shift_id": 5,
  "shift_name": "Day Shift",
  "date": "2025-11-06",
  "metrics": {
    "target_units": 400,
    "actual_units": 385,
    "target_attainment_percent": 96.25,
    "oee_percent": 81.5,
    "downtime_minutes": 45,
    "quality_fpy_percent": 97.5
  },
  "comparison": {
    "vs_day_shift_avg": "+2.5%",
    "vs_night_shift_same_day": "+8.3%"
  }
}
```

### 6.7 Maintenance Management Endpoints

**GET /api/v1/pm-schedules**
- **Description**: List preventive maintenance schedules
- **Auth**: Required
- **Query Params**:
  - `machine_id` (optional): Filter by machine
  - `overdue_only` (optional): Show only overdue PMs
- **Response 200**:
```json
{
  "pm_schedules": [
    {
      "id": 8,
      "machine_id": 15,
      "machine_name": "CNC Lathe Machine",
      "pm_type": "lubrication",
      "frequency_type": "calendar",
      "frequency_value": 30,
      "frequency_unit": "days",
      "last_pm_date": "2025-10-07",
      "next_due_date": "2025-11-06",
      "status": "due",
      "lead_time_days": 7,
      "estimated_duration_hours": 2,
      "assigned_technician": {"id": 34, "name": "Mike Technician"}
    }
  ]
}
```

**POST /api/v1/pm-work-orders**
- **Description**: Create PM work order (manual or auto-generated)
- **Auth**: Required (role: maintenance or supervisor)
- **Request Body**:
```json
{
  "pm_schedule_id": 8,
  "scheduled_date": "2025-11-06",
  "assigned_technician_id": 34,
  "priority": "normal",
  "notes": "Routine lubrication and inspection"
}
```
- **Response 201**:
```json
{
  "id": 890,
  "work_order_number": "PM-2025-042",
  "work_order_type": "preventive_maintenance",
  "machine_id": 15,
  "machine_name": "CNC Lathe Machine",
  "pm_schedule_id": 8,
  "pm_type": "lubrication",
  "status": "planned",
  "scheduled_date": "2025-11-06",
  "checklist": [
    {"id": 1, "task": "Check oil level in hydraulic reservoir", "completed": false},
    {"id": 2, "task": "Lubricate spindle bearings", "completed": false},
    {"id": 3, "task": "Inspect belts for wear", "completed": false}
  ],
  "assigned_technician": {"id": 34, "name": "Mike Technician"}
}
```

**POST /api/v1/downtime-events**
- **Description**: Log machine downtime event
- **Auth**: Required (role: operator)
- **Request Body**:
```json
{
  "machine_id": 15,
  "work_order_id": 456,
  "downtime_reason_code": "mechanical_failure",
  "started_at": "2025-11-06T14:30:00Z",
  "ended_at": "2025-11-06T17:00:00Z",
  "notes": "Hydraulic pump replaced by maintenance team"
}
```
- **Response 201**:
```json
{
  "id": 234,
  "machine_id": 15,
  "machine_name": "CNC Lathe Machine",
  "downtime_reason": "Mechanical Failure",
  "duration_minutes": 150,
  "started_at": "2025-11-06T14:30:00Z",
  "ended_at": "2025-11-06T17:00:00Z",
  "mtbf_hours": 80.5,
  "mttr_hours": 2.5
}
```

**GET /api/v1/maintenance-metrics**
- **Description**: Get maintenance KPIs (MTBF, MTTR, PM Compliance)
- **Auth**: Required
- **Query Params**:
  - `plant_id` (optional): Filter by plant
  - `start_date`: Start of date range (required)
  - `end_date`: End of date range (required)
- **Response 200**:
```json
{
  "period": {"start": "2025-11-01", "end": "2025-11-06"},
  "metrics": {
    "mtbf_hours": 82.3,
    "mttr_hours": 3.1,
    "pm_compliance_percent": 92.5,
    "total_downtime_minutes": 1450,
    "unplanned_downtime_percent": 35
  },
  "downtime_pareto": [
    {"reason": "Material Shortage", "minutes": 480, "percent": 33.1},
    {"reason": "Mechanical Failure", "minutes": 360, "percent": 24.8},
    {"reason": "Setup/Changeover", "minutes": 300, "percent": 20.7}
  ]
}
```

### 6.8 Inspection Plan Endpoints

**GET /api/v1/inspection-plans**
- **Description**: List inspection plans
- **Auth**: Required
- **Query Params**:
  - `product_id` (optional): Filter by product
  - `active_only` (optional): Show only active plans
- **Response 200**:
```json
{
  "inspection_plans": [
    {
      "id": 12,
      "product_id": 45,
      "product_name": "Steel Shaft 25mm",
      "inspection_points": [
        {
          "id": 1,
          "name": "First Piece Inspection",
          "frequency_type": "first_piece",
          "characteristics": [
            {
              "id": 101,
              "name": "Shaft Diameter",
              "type": "dimensional",
              "specification": "25mm",
              "tolerance": "±0.1mm",
              "usl": 25.1,
              "lsl": 24.9,
              "measurement_method": "Micrometer"
            }
          ]
        }
      ]
    }
  ]
}
```

**POST /api/v1/inspection-logs**
- **Description**: Log inspection results
- **Auth**: Required (role: inspector)
- **Request Body**:
```json
{
  "work_order_id": 456,
  "inspection_point_id": 1,
  "inspected_at": "2025-11-06T10:30:00Z",
  "measurements": [
    {
      "characteristic_id": 101,
      "measured_value": 25.05,
      "within_tolerance": true
    },
    {
      "characteristic_id": 102,
      "measured_value": 510,
      "within_tolerance": true
    }
  ],
  "notes": "All measurements within spec",
  "inspector_id": 67
}
```
- **Response 201**:
```json
{
  "id": 456,
  "inspection_point_name": "First Piece Inspection",
  "work_order_number": "WO-2025-001",
  "overall_result": "pass",
  "inspected_at": "2025-11-06T10:30:00Z",
  "inspector": {"id": 67, "name": "Jane Inspector"},
  "measurements": [
    {
      "characteristic": "Shaft Diameter",
      "measured_value": 25.05,
      "specification": "25mm ±0.1mm",
      "result": "pass"
    }
  ]
}
```

**GET /api/v1/spc-charts**
- **Description**: Get Statistical Process Control chart data
- **Auth**: Required
- **Query Params**:
  - `characteristic_id`: Inspection characteristic ID (required)
  - `start_date`: Start date (required)
  - `end_date`: End date (required)
- **Response 200**:
```json
{
  "characteristic_id": 101,
  "characteristic_name": "Shaft Diameter",
  "specification": "25mm ±0.1mm",
  "period": {"start": "2025-11-01", "end": "2025-11-06"},
  "control_limits": {
    "ucl": 25.08,
    "lcl": 24.92,
    "center_line": 25.0
  },
  "capability": {
    "cp": 1.67,
    "cpk": 1.45,
    "interpretation": "Good (4σ capable)"
  },
  "data_points": [
    {"timestamp": "2025-11-01T08:00:00Z", "value": 25.02},
    {"timestamp": "2025-11-01T10:00:00Z", "value": 25.05},
    {"timestamp": "2025-11-01T14:00:00Z", "value": 24.98}
  ],
  "alerts": [
    {
      "type": "trend",
      "message": "7 consecutive points above center line",
      "detected_at": "2025-11-05T12:00:00Z"
    }
  ]
}
```

### 6.9 Traceability Endpoints

**POST /api/v1/lot-numbers**
- **Description**: Generate lot number on material receipt
- **Auth**: Required (role: warehouse)
- **Request Body**:
```json
{
  "material_id": 123,
  "quantity": 500,
  "receipt_date": "2025-11-06"
}
```
- **Response 201**:
```json
{
  "lot_number": "STL001-20251106-001",
  "material_id": 123,
  "material_code": "STL-001",
  "material_name": "Steel Plate 10mm",
  "quantity": 500,
  "receipt_date": "2025-11-06",
  "expiry_date": null
}
```

**POST /api/v1/serial-numbers/generate**
- **Description**: Generate serial numbers for finished goods
- **Auth**: Required (role: operator or supervisor)
- **Request Body**:
```json
{
  "work_order_id": 456,
  "product_id": 45,
  "quantity": 5,
  "serial_prefix": "PUMP-2511"
}
```
- **Response 201**:
```json
{
  "work_order_id": 456,
  "work_order_number": "WO-2025-001",
  "serial_numbers": [
    "PUMP-2511-00001",
    "PUMP-2511-00002",
    "PUMP-2511-00003",
    "PUMP-2511-00004",
    "PUMP-2511-00005"
  ],
  "generated_at": "2025-11-06T16:00:00Z"
}
```

**GET /api/v1/traceability/forward**
- **Description**: Forward trace (lot/serial → customers)
- **Auth**: Required
- **Query Params**:
  - `lot_number` (optional): Lot number to trace
  - `serial_number` (optional): Serial number to trace
- **Response 200**:
```json
{
  "trace_type": "forward",
  "input": {
    "lot_number": "STL001-20251106-001",
    "material_name": "Steel Plate 10mm"
  },
  "affected_products": [
    {
      "work_order_number": "WO-2025-001",
      "product_name": "Steel Shaft 25mm",
      "quantity": 50,
      "serial_numbers": ["SHAFT-2511-00001", "SHAFT-2511-00002"],
      "shipments": [
        {
          "shipment_number": "SHIP-2025-042",
          "customer": {"id": 78, "name": "Acme Manufacturing"},
          "ship_date": "2025-11-08",
          "contact": "john@acme.com"
        }
      ]
    }
  ],
  "total_affected_customers": 1,
  "total_affected_units": 50
}
```

**GET /api/v1/traceability/backward**
- **Description**: Backward trace (customer/serial → material lots)
- **Auth**: Required
- **Query Params**:
  - `serial_number`: Serial number (required)
- **Response 200**:
```json
{
  "trace_type": "backward",
  "input": {
    "serial_number": "PUMP-2511-00003",
    "product_name": "Hydraulic Pump"
  },
  "genealogy": {
    "work_order": {
      "work_order_number": "WO-2025-001",
      "completed_date": "2025-11-06"
    },
    "materials_used": [
      {
        "material_name": "Motor",
        "lot_number": "MOT-20251101-001",
        "serial_number": "MOT-003",
        "supplier": "ABC Motors Inc",
        "receipt_date": "2025-11-01"
      },
      {
        "material_name": "Housing",
        "lot_number": "HSG-20251102-001",
        "supplier": "XYZ Castings",
        "receipt_date": "2025-11-02"
      }
    ],
    "operations_performed": [
      {"operation": "Assembly", "operator": "John Operator", "date": "2025-11-06"},
      {"operation": "Testing", "operator": "Jane Tester", "date": "2025-11-06"}
    ]
  }
}
```

**POST /api/v1/recall-reports**
- **Description**: Generate product recall report
- **Auth**: Required (role: quality_manager or admin)
- **Request Body**:
```json
{
  "recall_reason": "Defective hydraulic pump component - potential leak",
  "lot_number": "HSG-20251102-001",
  "severity": "critical"
}
```
- **Response 201**:
```json
{
  "recall_id": "RCL-2025-003",
  "recall_reason": "Defective hydraulic pump component - potential leak",
  "severity": "critical",
  "affected_lot": "HSG-20251102-001",
  "affected_customers": [
    {
      "customer_id": 78,
      "customer_name": "Acme Manufacturing",
      "contact_email": "john@acme.com",
      "contact_phone": "+1-555-0100",
      "products_shipped": [
        {
          "serial_number": "PUMP-2511-00003",
          "ship_date": "2025-11-08",
          "shipment_number": "SHIP-2025-042"
        }
      ]
    }
  ],
  "total_affected_units": 50,
  "total_affected_customers": 1,
  "generated_at": "2025-11-07T09:00:00Z",
  "export_url": "https://minio.../recall-reports/RCL-2025-003.pdf"
}
```

---

## See Also

- [FRD_MATERIAL_MANAGEMENT.md](FRD_MATERIAL_MANAGEMENT.md) - Material business rules
- [FRD_WORK_ORDERS.md](FRD_WORK_ORDERS.md) - Work order business rules
- [FRD_QUALITY.md](FRD_QUALITY.md) - NCR business rules
- [FRD_EQUIPMENT.md](FRD_EQUIPMENT.md) - Equipment business rules
- [FRD_TRACEABILITY.md](FRD_TRACEABILITY.md) - Traceability business rules
- [FRD_INDEX.md](FRD_INDEX.md) - Complete FRD index

---

**Document Status**: Active
**Last Updated**: 2025-11-10
**Line Count**: ~810 lines
