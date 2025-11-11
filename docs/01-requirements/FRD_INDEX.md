# Functional Requirements Document - Index
# Unison Manufacturing ERP

**Version**: 4.0
**Date**: 2025-11-10
**Total Lines**: ~3400 (split across 13 files)

---

## Overview

The Functional Requirements Document (FRD) has been split into domain-specific files for better LLM consumption and maintainability. Each file is self-contained and focuses on a specific functional area.

**Why Split?**
- **Original FRD.md**: 3,411 lines, 32,669 tokens - exceeded LLM read limits
- **Split Structure**: 13 focused files, each under 600 lines
- **Better Organization**: Domain-driven structure for easier navigation
- **Duplicate Resolution**: Consolidated duplicate sections found in original

---

## Document Map

### 1. Core Architecture & Overview

**[FRD_OVERVIEW.md](FRD_OVERVIEW.md)** (~280 lines)
- Purpose and scope of the FRD
- Multi-tenancy isolation rules (RLS, subdomain routing)
- White-labeling behavior (logo, colors, favicon)
- RBAC permission evaluation (role hierarchy, resource-level access)
- Entity relationship diagram
- Work order lifecycle state machine

**Key Topics**: Multi-tenancy, RBAC, Data Relationships

---

### 2. Core Domain Areas

**[FRD_MATERIAL_MANAGEMENT.md](FRD_MATERIAL_MANAGEMENT.md)** (~180 lines)
- Material costing rules (FIFO, LIFO, Weighted Average)
- Costing method selection decision tree
- Material receipt workflow
- Material validation rules
- Material API endpoints (GET, POST)

**Key Topics**: Material Costing, Inventory, Receipt Workflow

---

**[FRD_WORK_ORDERS.md](FRD_WORK_ORDERS.md)** (~320 lines)
- Work order dependency rules (Finish-to-Start, Start-to-Start, Finish-to-Finish)
- Work order costing rules (Material + Labor + Overhead)
- Project & BOM management (hierarchy, explosion, validation)
- Production logging workflow (mobile PWA)
- Visual production scheduling (Gantt chart, drag-and-drop)
- Work order validation rules
- Work order API endpoints

**Key Topics**: Dependencies, Costing, BOM, Production Logging, Scheduling

---

**[FRD_QUALITY.md](FRD_QUALITY.md)** (~210 lines)
- NCR disposition rules (Rework, Scrap, Use-as-is, Return to Supplier)
- NCR disposition decision tree (conditional routing by severity)
- NCR approval workflow (standard template with escalations)
- Inspection plan rules (characteristics, frequency, SPC)
- Statistical Process Control (Cp/Cpk calculation)
- NCR validation rules
- NCR and inspection API endpoints

**Key Topics**: NCR, Inspections, Quality Control, SPC

---

**[FRD_EQUIPMENT.md](FRD_EQUIPMENT.md)** (~150 lines)
- Manufacturing KPI rules (OEE calculation)
- Equipment & machine management rules (status states)
- Machine status state machine (Available, Running, Down, Maintenance)
- Machine utilization calculation
- OEE components (Availability × Performance × Quality)
- Equipment API endpoints

**Key Topics**: OEE, Machine Status, Utilization

---

**[FRD_MAINTENANCE.md](FRD_MAINTENANCE.md)** (~180 lines)
- Preventive maintenance rules (PM schedules)
- PM schedule types (calendar-based, meter-based)
- PM work order auto-generation logic
- Downtime tracking & analysis rules
- Downtime reason taxonomy (Pareto analysis)
- MTBF and MTTR calculations
- Maintenance API endpoints

**Key Topics**: Preventive Maintenance, Downtime, MTBF/MTTR

---

**[FRD_TRACEABILITY.md](FRD_TRACEABILITY.md)** (~150 lines)
- Serial number & lot traceability rules
- Lot tracking rules (lot number format, assignment)
- Serial number tracking rules (serial format, genealogy)
- Forward trace (recall scenario: lot → customers)
- Backward trace (customer complaint: serial → materials)
- Recall report generation
- Traceability API endpoints

**Key Topics**: Serial Numbers, Lot Tracking, Genealogy, Recalls

---

**[FRD_SHIFTS.md](FRD_SHIFTS.md)** (~100 lines)
- Shift management rules (patterns, targets)
- Shift pattern types (Fixed, Rotating, Custom)
- Shift performance calculation (target attainment, OEE)
- Shift handover behavior (notes, acknowledgment)
- Shift comparison reports
- Shift API endpoints

**Key Topics**: Shifts, Handovers, Shift Performance

---

### 3. Special Workflows & Processes

**[FRD_ONBOARDING.md](FRD_ONBOARDING.md)** (~520 lines)
- Self-service onboarding workflow (4-step wizard)
- Step 1: Account creation (30 seconds)
- Step 2: Organization setup (1 minute)
- Step 3: First plant creation (30 seconds)
- Step 4: Invite team (optional, 1 minute)
- Onboarding complete page
- Progressive configuration (post-onboarding)
- Configuration defaults summary
- Sample data seeding (optional)
- Onboarding success metrics
- In-app guidance (tooltips, empty states)

**Key Topics**: Onboarding, Trial Setup, Customer Acquisition

---

**[FRD_WORKFLOWS.md](FRD_WORKFLOWS.md)** (~340 lines)
- SAP integration sync rules (scheduled, event-driven, manual)
- Data mapping rules (Materials, Work Orders)
- Conflict resolution logic (Last Write Wins, Field-Level Merge)
- Notification trigger rules (email, in-app, SMS)
- Notification delivery rules (retry logic, batch processing)
- Drawing approval flow
- Shipment creation & tracking flow
- Shipment status states (Pending, Shipped, Delivered)
- Custom field configuration flow
- Workflow API endpoints

**Key Topics**: SAP Integration, Notifications, Shipments, Drawing Approval

---

### 4. Technical Specifications

**[FRD_API_CONTRACTS.md](FRD_API_CONTRACTS.md)** (~810 lines)
- Material endpoints (GET, POST)
- Work order endpoints (POST start, POST production-logs)
- NCR endpoints (POST with photos)
- Workflow endpoints (POST transition)
- Equipment management endpoints (GET machines, PUT status, GET utilization)
- Shift management endpoints (GET shifts, POST handovers, GET performance)
- Maintenance management endpoints (GET pm-schedules, POST pm-work-orders, POST downtime-events, GET metrics)
- Inspection plan endpoints (GET inspection-plans, POST inspection-logs, GET spc-charts)
- Traceability endpoints (POST lot-numbers, POST serial-numbers, GET forward/backward trace, POST recall-reports)

**Key Topics**: REST API, Request/Response Specifications

---

**[FRD_UI_BEHAVIOR.md](FRD_UI_BEHAVIOR.md)** (~180 lines)
- Custom field validation rules
- Dynamic form rendering (standard + custom fields)
- Offline queue indicator (states, auto-sync)
- Barcode scanner UI (full-screen camera, scan overlay)
- Production summary report (inputs, columns, export formats)
- OEE dashboard (live KPI cards, chart, filters, drill-down)

**Key Topics**: UI Behavior, Forms, Reports, Dashboards

---

## Duplicates Found & Resolved

The original FRD.md contained duplicate section numbering due to copy-paste errors:

### Duplicate Section 2.2 (Work Order Dependency Rules)
- **Lines 64-89**: Costing Method Selection Decision Tree (actually belongs to 2.1 Material Costing)
- **Lines 91-117**: Work Order Dependency Rules (actual 2.2 content)
- **Resolution**: Merged decision tree into FRD_MATERIAL_MANAGEMENT.md, kept dependency rules in FRD_WORK_ORDERS.md

### Duplicate Section 2.3 (NCR Disposition Rules)
- **Lines 119-138**: Lane Assignment Sequence (not related to NCR)
- **Lines 140-180**: NCR Disposition Rules (actual 2.3 content)
- **Resolution**: Moved lane assignment to FRD_WORK_ORDERS.md (scheduling section), kept NCR rules in FRD_QUALITY.md

### Duplicate Section 2.4 (Work Order Costing Rules)
- **Lines 182-210**: Disposition Decision Tree (belongs to NCR)
- **Lines 212-247**: Work Order Costing Rules (actual 2.4 content)
- **Resolution**: Merged disposition tree into FRD_QUALITY.md (NCR section), kept costing in FRD_WORK_ORDERS.md

### Duplicate Section 3 (Workflows vs. Onboarding)
- **Lines 614-1126**: Self-Service Onboarding Workflow (labeled as Section 3)
- **Lines 1128-2277**: Generic Workflows (also labeled as Section 3)
- **Resolution**: Split into FRD_ONBOARDING.md and FRD_WORKFLOWS.md

---

## File Statistics

| File | Lines | Domain | Status |
|------|-------|--------|--------|
| FRD_ORIGINAL.md | 3,411 | Backup | Archived |
| FRD_OVERVIEW.md | ~280 | Architecture | Active |
| FRD_MATERIAL_MANAGEMENT.md | ~180 | Materials | Active |
| FRD_WORK_ORDERS.md | ~320 | Production | Active |
| FRD_QUALITY.md | ~210 | Quality | Active |
| FRD_EQUIPMENT.md | ~150 | Equipment | Active |
| FRD_MAINTENANCE.md | ~180 | Maintenance | Active |
| FRD_TRACEABILITY.md | ~150 | Traceability | Active |
| FRD_SHIFTS.md | ~100 | Shifts | Active |
| FRD_ONBOARDING.md | ~520 | Onboarding | Active |
| FRD_WORKFLOWS.md | ~340 | Workflows | Active |
| FRD_API_CONTRACTS.md | ~810 | API | Active |
| FRD_UI_BEHAVIOR.md | ~180 | UI | Active |
| **TOTAL (Active)** | **~3,420** | **All** | **Active** |

**Token Reduction**: Original file (32,669 tokens) now split into manageable chunks (each ~1,000-5,000 tokens)

---

## Navigation Guide

### By Use Case

**I want to understand...**

- **...how the system handles data isolation** → [FRD_OVERVIEW.md](FRD_OVERVIEW.md) (Multi-tenancy section)
- **...how materials are costed** → [FRD_MATERIAL_MANAGEMENT.md](FRD_MATERIAL_MANAGEMENT.md)
- **...how work orders flow through production** → [FRD_WORK_ORDERS.md](FRD_WORK_ORDERS.md)
- **...how quality issues are managed** → [FRD_QUALITY.md](FRD_QUALITY.md)
- **...how equipment efficiency is tracked** → [FRD_EQUIPMENT.md](FRD_EQUIPMENT.md)
- **...how maintenance is scheduled** → [FRD_MAINTENANCE.md](FRD_MAINTENANCE.md)
- **...how products are traced** → [FRD_TRACEABILITY.md](FRD_TRACEABILITY.md)
- **...how shifts are managed** → [FRD_SHIFTS.md](FRD_SHIFTS.md)
- **...how customers onboard** → [FRD_ONBOARDING.md](FRD_ONBOARDING.md)
- **...how the system integrates with SAP** → [FRD_WORKFLOWS.md](FRD_WORKFLOWS.md)
- **...what API endpoints exist** → [FRD_API_CONTRACTS.md](FRD_API_CONTRACTS.md)
- **...how the UI behaves** → [FRD_UI_BEHAVIOR.md](FRD_UI_BEHAVIOR.md)

### By Role

**Product Manager** → Start with [FRD_OVERVIEW.md](FRD_OVERVIEW.md), then explore domain files

**Backend Engineer** → Focus on [FRD_API_CONTRACTS.md](FRD_API_CONTRACTS.md), then business rules in domain files

**Frontend Engineer** → Start with [FRD_UI_BEHAVIOR.md](FRD_UI_BEHAVIOR.md), then [FRD_API_CONTRACTS.md](FRD_API_CONTRACTS.md)

**QA Engineer** → Review validation rules in each domain file, focus on [FRD_QUALITY.md](FRD_QUALITY.md)

**Sales/Demo** → Start with [FRD_ONBOARDING.md](FRD_ONBOARDING.md), then [FRD_OVERVIEW.md](FRD_OVERVIEW.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 4.0 | 2025-11-10 | Split massive FRD into 13 domain-specific files, resolved duplicates | Engineering |
| 3.0 | 2025-11-08 | Added Self-Service Onboarding section | Product |
| 2.0 | 2025-10-15 | Added Equipment, Maintenance, Traceability sections | Engineering |
| 1.0 | 2025-09-01 | Initial FRD creation | Product + Engineering |

---

## Maintenance Guidelines

**When updating the FRD**:

1. **Identify the correct domain file** using this index
2. **Update only the relevant file** (avoid cross-file changes when possible)
3. **Update the index** if you add new major sections
4. **Maintain cross-references** in "See Also" sections
5. **Keep FRD_ORIGINAL.md** as historical reference (do not modify)
6. **Version numbers** should be synced across all files

**File size guidelines**:
- Target: 150-600 lines per file
- Warning: >600 lines (consider further splitting)
- Critical: >800 lines (must split)

---

## Approvals

- [ ] Product Management
- [ ] Engineering Lead
- [ ] QA Lead

---

**Document Status**: Active
**Last Updated**: 2025-11-10
**Next Review**: 2025-12-01
