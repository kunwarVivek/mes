# RLS Tables Quick Reference
**Generated**: 2025-11-09

## Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| **Total Tables** | 47 | All database tables |
| **Tables Needing RLS** | 44 | Multi-tenant tables |
| **Tables with RLS (Current)** | 7 | From existing migration |
| **Missing RLS Policies** | 37 | **Gap to address** |
| **Global Tables (No RLS)** | 3 | Reference data only |

---

## RLS Policy Patterns

### Pattern 1: Organization + Plant (Standard)
**Used by**: 35+ tables
```sql
-- Organization Policy
CREATE POLICY {table}_org_isolation ON {table}
FOR ALL USING (
    organization_id = current_setting('app.current_organization_id', true)::int
);

-- Plant Policy (allows NULL)
CREATE POLICY {table}_plant_isolation ON {table}
FOR ALL USING (
    plant_id IS NULL OR 
    plant_id = current_setting('app.current_plant_id', true)::int
);
```

### Pattern 2: Organization Only
**Used by**: material_category
```sql
CREATE POLICY {table}_org_isolation ON {table}
FOR ALL USING (
    organization_id = current_setting('app.current_organization_id', true)::int
);
```

### Pattern 3: Plant Only (Inherits Org via FK)
**Used by**: departments, lanes
```sql
CREATE POLICY {table}_plant_isolation ON {table}
FOR ALL USING (
    plant_id = current_setting('app.current_plant_id', true)::int
);
```

### Pattern 4: Self-Referential (Organizations)
```sql
CREATE POLICY organizations_self_isolation ON organizations
FOR ALL USING (
    id = current_setting('app.current_organization_id', true)::int
);
```

---

## Complete Table List with RLS Requirements

| # | Table Name | Organization ID | Plant ID | RLS Pattern | Priority | Notes |
|---|------------|----------------|----------|-------------|----------|-------|
| 1 | `users` | ❌ **MISSING** | ❌ **MISSING** | **SCHEMA FIX REQUIRED** | **CRITICAL** | Add org_id + plant_id |
| 2 | `organizations` | ✅ (self) | - | Self-referential | **HIGH** | Top-level tenant |
| 3 | `plants` | ✅ (FK) | ✅ | Organization filter | **HIGH** | Sub-tenant |
| 4 | `departments` | ✅ (FK) | ✅ | Plant filter | **HIGH** | Via plant FK |
| 5 | `material_category` | ✅ | - | Org only | **HIGH** | Shared categories |
| 6 | `unit_of_measure` | - | - | **NO RLS** | N/A | Global reference |
| 7 | `material` | ✅ | ✅ | Org + Plant | **HIGH** | Material master |
| 8 | `material_costing` | ✅ | ✅ | Org + Plant | **HIGH** | Costing data |
| 9 | `cost_layer` | ✅ | ✅ | Org + Plant | MEDIUM | FIFO/LIFO |
| 10 | `storage_location` | ✅ | ✅ | Org + Plant | **HIGH** | Warehouse locations |
| 11 | `inventory` | ✅ | ✅ | Org + Plant | **HIGH** | Stock levels |
| 12 | `inventory_transaction` | ✅ | ✅ | Org + Plant | **HIGH** | Audit trail |
| 13 | `work_center` | ✅ | ✅ | Org + Plant | **HIGH** | Production resources |
| 14 | `work_order` | ✅ | ✅ | Org + Plant | **HIGH** | Production orders |
| 15 | `work_order_operation` | ✅ | ✅ | Org + Plant | **HIGH** | Operations routing |
| 16 | `work_order_material` | ✅ (FK) | ✅ (FK) | Via work_order FK | MEDIUM | Material consumption |
| 17 | `rework_config` | ✅ | ✅ | Org + Plant | MEDIUM | Rework settings |
| 18 | `work_center_shift` | ✅ (FK) | ✅ (FK) | Via work_center FK | MEDIUM | Shift calendar |
| 19 | `operation_scheduling_config` | ✅ | ✅ | Org + Plant | MEDIUM | Scheduling config |
| 20 | `bom_header` | ✅ | ✅ | Org + Plant | **HIGH** | Bill of materials |
| 21 | `bom_line` | ✅ (FK) | ✅ (FK) | Via bom_header FK | **HIGH** | BOM components |
| 22 | `machine` | ✅ | ✅ | Org + Plant | **HIGH** | Equipment master |
| 23 | `machine_status_history` | ✅ (FK) | ✅ (FK) | Via machine FK | MEDIUM | Status tracking |
| 24 | `pm_schedule` | ✅ | ✅ | Org + Plant | **HIGH** | PM schedules |
| 25 | `pm_work_order` | ✅ | ✅ | Org + Plant | **HIGH** | PM tasks |
| 26 | `downtime_event` | ✅ | ✅ | Org + Plant | **HIGH** | Downtime tracking |
| 27 | `shift` | ✅ | ✅ | Org + Plant | **HIGH** | Shift patterns |
| 28 | `shift_handover` | ✅ | ✅ | Org + Plant | MEDIUM | Shift notes |
| 29 | `shift_performance` | ✅ | ✅ | Org + Plant | MEDIUM | Shift metrics |
| 30 | `ncr` | ✅ | ✅ | Org + Plant | **HIGH** | Quality NCRs |
| 31 | `inspection_plan` | ✅ | ✅ | Org + Plant | **HIGH** | Inspection config |
| 32 | `inspection_log` | ✅ | ✅ | Org + Plant | **HIGH** | Inspection results |
| 33 | `projects` | ✅ | ✅ | Org + Plant | **HIGH** | Project tracking |
| 34 | `lanes` | ✅ (FK) | ✅ | Via plant FK | MEDIUM | Production lanes |
| 35 | `lane_assignments` | ✅ | ✅ | Org + Plant | MEDIUM | Lane scheduling |
| 36 | `production_logs` | ✅ | ✅ | Org + Plant | **HIGH** | TimescaleDB hypertable |
| 37 | `rls_audit_log` | ✅ | ✅ | Org + Plant | MEDIUM | RLS audit trail |
| 38 | `currency` | - | - | **NO RLS** | N/A | Global reference |
| 39 | `exchange_rate` | - | - | **NO RLS** | N/A | Global reference |

---

## Multi-Tenancy Field Patterns

### Direct Columns (Explicit Fields)
**Tables with direct organization_id + plant_id columns**:
- material, material_costing, cost_layer
- storage_location, inventory, inventory_transaction
- work_center, work_order, work_order_operation
- rework_config, operation_scheduling_config
- bom_header, machine
- pm_schedule, pm_work_order, downtime_event
- shift, shift_handover, shift_performance
- ncr, inspection_plan, inspection_log
- projects, lane_assignments, production_logs
- rls_audit_log

**Total**: 25 tables

### Inherited via Foreign Key
**Tables that inherit tenant context through parent FK**:
- departments (via plants.id)
- lanes (via plants.id)
- work_order_material (via work_order.id)
- work_center_shift (via work_center.id)
- bom_line (via bom_header.id)
- machine_status_history (via machine.id)

**Total**: 6 tables

### Organization Only
**Tables with organization_id only**:
- material_category (categories shared across plants)

**Total**: 1 table

### Self-Referential
**Tables filtering on their own ID**:
- organizations (id = current_organization_id)
- plants (organization_id + id check)

**Total**: 2 tables

---

## Current vs Required Coverage

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ **Has RLS Policy** | 7 | 16% |
| ❌ **Missing RLS Policy** | 37 | 84% |
| **Total Requiring RLS** | 44 | 100% |

### Currently Covered (7 tables)
1. ✅ users (in migration but **schema missing fields**)
2. ✅ organizations
3. ✅ plants
4. ✅ materials (wrong name: should be `material`)
5. ✅ work_orders (wrong name: should be `work_order`)
6. ✅ production_lines (wrong name: should be `lanes` or `work_center`)
7. ✅ inventory_transactions (wrong name: should be `inventory_transaction`)

**Issues**: Table names don't match actual schema! Need to fix migration.

### High Priority Missing (18 tables)
- material (fix name from `materials`)
- work_order (fix name from `work_orders`)
- work_center
- work_order_operation
- bom_header, bom_line
- machine
- pm_schedule, pm_work_order, downtime_event
- shift
- ncr, inspection_plan, inspection_log
- projects
- storage_location, inventory
- inventory_transaction (fix name from `inventory_transactions`)
- production_logs

### Medium Priority Missing (14 tables)
- material_costing, cost_layer
- work_order_material, rework_config
- work_center_shift, operation_scheduling_config
- machine_status_history
- shift_handover, shift_performance
- departments, lanes, lane_assignments
- rls_audit_log
- material_category

---

## Session Variables Reference

| Variable | Type | Required | Usage | Example |
|----------|------|----------|-------|---------|
| `app.current_organization_id` | INTEGER | ✅ **Yes** | Primary tenant filter | `123` |
| `app.current_plant_id` | INTEGER | ❌ Optional | Sub-tenant filter | `456` or `NULL` |
| `app.current_user_id` | INTEGER | ❌ Optional | Audit trail | `789` |

**Setting Context**:
```python
db.execute(text("SET LOCAL app.current_organization_id = :org_id"), {"org_id": 123})
db.execute(text("SET LOCAL app.current_plant_id = :plant_id"), {"plant_id": 456})
db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": 789})
```

**Clearing Context**:
```python
db.execute(text("RESET app.current_organization_id"))
db.execute(text("RESET app.current_plant_id"))
db.execute(text("RESET app.current_user_id"))
```

---

## Implementation Priority Matrix

### Phase 1: Critical Foundation (Week 1)
**Must-Fix Items**:
1. Fix user table schema (add organization_id, plant_id)
2. Fix table names in existing migration
3. Add policies for: organizations, plants, users

**Deliverable**: Foundation tables have correct RLS

### Phase 2: Core Modules (Week 2-3)
**Production Core**:
4. work_order, work_order_operation, work_center
5. material, inventory, storage_location
6. bom_header, bom_line
7. production_logs (TimescaleDB)

**Deliverable**: Production planning module secured

### Phase 3: Equipment & Quality (Week 4)
**Equipment**:
8. machine, machine_status_history
9. pm_schedule, pm_work_order, downtime_event

**Quality**:
10. ncr, inspection_plan, inspection_log

**Deliverable**: Equipment and quality modules secured

### Phase 4: Operational Modules (Week 5)
**Shift & Scheduling**:
11. shift, shift_handover, shift_performance
12. lanes, lane_assignments

**Projects**:
13. projects

**Deliverable**: All operational modules secured

### Phase 5: Extended Features (Week 6)
**Costing & Inventory**:
14. material_costing, cost_layer
15. inventory_transaction

**Configuration**:
16. rework_config, operation_scheduling_config
17. work_center_shift

**Deliverable**: All extended features secured

### Phase 6: Testing & Verification (Week 7)
18. Integration tests for all RLS policies
19. Security testing (cross-tenant access attempts)
20. Performance testing (query plans with RLS)
21. Documentation and runbooks

**Deliverable**: Production-ready RLS implementation

---

## Quick Verification Queries

### Check RLS Status
```sql
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### Check Policies on a Table
```sql
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename = 'material'
ORDER BY policyname;
```

### Verify All Policies
```sql
SELECT * FROM verify_rls_policies();
```

### Test RLS Context
```sql
-- Set context
SET app.current_organization_id = 1;
SET app.current_plant_id = 10;

-- Verify context
SELECT 
    current_setting('app.current_organization_id', true) as org_id,
    current_setting('app.current_plant_id', true) as plant_id;

-- Test query with RLS
SELECT COUNT(*) FROM material;

-- Clear context
RESET app.current_organization_id;
RESET app.current_plant_id;
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**Companion Document**: RLS_IMPLEMENTATION_FINDINGS.md
