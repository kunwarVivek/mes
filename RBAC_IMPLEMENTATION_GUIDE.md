# RBAC Implementation Guide

**Date**: 2025-11-10
**Status**: Enhanced RBAC decorator implemented, ready for rollout
**Coverage**: 0/335 endpoints (94 critical endpoints identified for immediate implementation)

---

## Overview

The RBAC (Role-Based Access Control) enforcement decorator has been enhanced to properly integrate with the database-backed role system using PyCasbin. This guide provides instructions for systematically applying permission checks to all 335 API endpoints.

---

## Enhanced Decorator

**Location**: `/home/user/mes/backend/app/infrastructure/security/rbac_dependencies.py`

**Key Improvements**:
1. ✅ Queries actual user roles from `UserRole` table
2. ✅ Supports multiple roles per user
3. ✅ Integrates with Casbin policy enforcement
4. ✅ Superusers bypass all checks
5. ✅ Clear error messages (403 Forbidden with details)

---

## Usage Pattern

### Before (No Permission Check):
```python
@router.delete("/work-orders/{id}")
async def delete_work_order(
    id: int,
    current_user: User = Depends(get_current_user),  # Only authentication
    db: Session = Depends(get_db)
):
    # Any authenticated user can delete!
    return repo.delete(id)
```

### After (With RBAC):
```python
from app.infrastructure.security.rbac_dependencies import require_permission

@router.delete("/work-orders/{id}")
async def delete_work_order(
    id: int,
    current_user: User = Depends(require_permission("work_orders", "delete")),  # Auth + Authorization
    db: Session = Depends(get_db)
):
    # Only users with "work_orders:delete" permission can proceed
    return repo.delete(id)
```

**Key Change**: Replace `Depends(get_current_user)` with `Depends(require_permission(resource, action))`

---

## Standard Permissions by Resource

### Work Orders
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /work-orders | work_orders | view | All roles except Viewer (read-only) |
| POST /work-orders | work_orders | create | Plant Manager, Supervisor |
| PUT /work-orders/{id} | work_orders | update | Plant Manager, Supervisor |
| DELETE /work-orders/{id} | work_orders | delete | Plant Manager only |
| POST /work-orders/{id}/release | work_orders | release | Plant Manager, Supervisor |
| POST /work-orders/{id}/complete | work_orders | complete | Supervisor, Operator |

### Materials & Inventory
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /materials | materials | view | All roles |
| POST /materials | materials | create | Plant Manager, Organization Admin |
| PUT /materials/{id} | materials | update | Plant Manager, Organization Admin |
| DELETE /materials/{id} | materials | delete | Organization Admin only |
| POST /inventory/{id}/receive | inventory | receive | Supervisor, Operator |
| POST /inventory/{id}/issue | inventory | issue | Supervisor, Operator |
| POST /inventory/{id}/adjust | inventory | adjust | Plant Manager only |

### NCRs (Non-Conformance Reports)
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /ncrs | ncrs | view | All roles |
| POST /ncrs | ncrs | create | Quality Inspector, Supervisor, Operator |
| PUT /ncrs/{id} | ncrs | update | Quality Inspector, Plant Manager |
| DELETE /ncrs/{id} | ncrs | delete | Plant Manager only |
| POST /ncrs/{id}/disposition | ncrs | disposition | Plant Manager (>$10K: Organization Admin) |

### Machines & Equipment
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /machines | machines | view | All roles |
| POST /machines | machines | create | Plant Manager |
| PUT /machines/{id} | machines | update | Plant Manager, Supervisor |
| DELETE /machines/{id} | machines | delete | Organization Admin |
| POST /machines/{id}/status | machines | update_status | Operator, Supervisor |

### Scheduling & Lanes
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /scheduling/gantt | scheduling | view | Plant Manager, Supervisor |
| POST /scheduling/validate | scheduling | validate | Supervisor |
| PUT /scheduling/gantt/reschedule | scheduling | reschedule | Plant Manager, Supervisor |
| GET /scheduling/conflicts | scheduling | view | Plant Manager, Supervisor |

### Users & Roles (Admin Functions)
| Endpoint | Resource | Action | Roles Allowed |
|----------|----------|--------|---------------|
| GET /users | users | view | System Admin, Organization Admin |
| POST /users | users | create | System Admin, Organization Admin |
| PUT /users/{id} | users | update | System Admin, Organization Admin |
| DELETE /users/{id} | users | delete | System Admin only |
| POST /roles/assign | roles | assign | Organization Admin, System Admin |

---

## Implementation Priority

### Phase 1: Critical Security Endpoints (94 endpoints - Immediate)
**Estimated Time**: 1-2 days

Apply RBAC to endpoints that can:
- Modify financial data (costs, pricing)
- Delete data
- Change system configuration
- Affect production schedules

**Files to Update**:
1. `/backend/app/presentation/api/v1/work_orders.py` (DELETE, release, complete)
2. `/backend/app/presentation/api/v1/materials.py` (DELETE, CREATE, UPDATE)
3. `/backend/app/presentation/api/v1/quality.py` (NCR disposition, UPDATE, DELETE)
4. `/backend/app/presentation/api/v1/machines.py` (DELETE, CREATE, UPDATE)
5. `/backend/app/presentation/api/v1/inventory.py` (adjust, issue)
6. `/backend/app/presentation/api/v1/users.py` (ALL endpoints)
7. `/backend/app/presentation/api/v1/roles.py` (ALL endpoints)
8. `/backend/app/presentation/api/v1/scheduling.py` (reschedule)

### Phase 2: Production & Operations (102 endpoints - High Priority)
**Estimated Time**: 2-3 days

**Files**:
- production_logs.py
- shifts.py
- lanes.py
- maintenance.py
- projects.py

### Phase 3: Configuration & Supporting Features (139 endpoints - Medium Priority)
**Estimated Time**: 3-4 days

**Files**:
- custom_fields.py
- workflows.py
- bran ding.py
- logistics.py
- traceability.py
- project_management.py
- reporting.py
- infrastructure.py

---

## Example Implementations

### Example 1: Work Orders Delete Endpoint

**File**: `/backend/app/presentation/api/v1/work_orders.py`

```python
from app.infrastructure.security.rbac_dependencies import require_permission

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order(
    id: int,
    current_user: User = Depends(require_permission("work_orders", "delete")),  # CHANGED
    db: Session = Depends(get_db)
):
    """
    Delete a work order.

    **Permissions**: Requires work_orders:delete permission
    **Roles Allowed**: Plant Manager only

    ## Business Rules
    - Can only delete PLANNED or CANCELLED work orders
    - Cannot delete IN_PROGRESS or COMPLETED work orders

    ## Audit
    - Deletion is logged in audit_logs table
    """
    # Implementation...
```

### Example 2: NCR Disposition (Conditional Permission)

**File**: `/backend/app/presentation/api/v1/quality.py`

```python
@router.post("/{id}/disposition", response_model=NCRResponse)
async def disposition_ncr(
    id: int,
    request: NCRDispositionRequest,
    current_user: User = Depends(require_permission("ncrs", "disposition")),  # CHANGED
    db: Session = Depends(get_db)
):
    """
    Approve NCR disposition (Rework, Scrap, Use-as-is, Return to Supplier).

    **Permissions**: Requires ncrs:disposition permission
    **Roles Allowed**:
    - Plant Manager (all dispositions <$10K)
    - Organization Admin (all dispositions, required for >$10K)

    ## Business Logic
    - Cost >$10K requires Organization Admin approval
    - Critical defects automatically escalate to Plant Manager
    """
    # Additional cost-based check
    if request.estimated_cost > 10000:
        # Verify user is Organization Admin
        if not current_user.is_organization_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dispositions >$10K require Organization Admin approval"
            )

    # Implementation...
```

### Example 3: Inventory Adjustment (Financial Impact)

**File**: `/backend/app/presentation/api/v1/inventory.py`

```python
@router.post("/{material_id}/adjust", response_model=TransactionResponse)
async def adjust_inventory(
    material_id: int,
    request: AdjustInventoryRequest,
    current_user: User = Depends(require_permission("inventory", "adjust")),  # CHANGED
    db: Session = Depends(get_db)
):
    """
    Adjust inventory for physical count discrepancies.

    **Permissions**: Requires inventory:adjust permission
    **Roles Allowed**: Plant Manager only

    ## Business Rules
    - Creates ADJUSTMENT transaction
    - Affects material valuation (financial impact)
    - Requires reason_code and notes

    ## Audit
    - All adjustments logged with user_id and timestamp
    """
    # Implementation...
```

---

## Casbin Policy Configuration

**File**: `/backend/app/infrastructure/security/casbin_policy.csv`

Example policies to add:

```csv
# Role, Resource, Action
p, system_admin, *, *
p, organization_admin, users, *
p, organization_admin, roles, *
p, organization_admin, materials, *
p, organization_admin, plants, *
p, plant_manager, work_orders, *
p, plant_manager, materials, view
p, plant_manager, materials, update
p, plant_manager, machines, *
p, plant_manager, scheduling, *
p, plant_manager, ncrs, *
p, plant_manager, inventory, adjust
p, supervisor, work_orders, view
p, supervisor, work_orders, create
p, supervisor, work_orders, update
p, supervisor, work_orders, release
p, supervisor, production_logs, *
p, supervisor, inventory, receive
p, supervisor, inventory, issue
p, operator, work_orders, view
p, operator, work_orders, complete
p, operator, production_logs, create
p, operator, production_logs, update
p, operator, machines, update_status
p, quality_inspector, ncrs, *
p, quality_inspector, inspection, *
p, viewer, work_orders, view
p, viewer, materials, view
p, viewer, machines, view
p, viewer, ncrs, view
```

---

## Testing RBAC

### Manual Testing
```bash
# 1. Create test users with different roles
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"username": "test_operator", "email": "op@test.com", "password": "test123"}'

# 2. Assign role
curl -X POST http://localhost:8000/api/v1/roles/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"user_id": 123, "role_id": 5}'  # Operator role

# 3. Login as test user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d '{"username": "test_operator", "password": "test123"}'

# 4. Test forbidden action (should return 403)
curl -X DELETE http://localhost:8000/api/v1/work-orders/1 \
  -H "Authorization: Bearer $OPERATOR_TOKEN"

# Expected: 403 Forbidden "Insufficient permissions to delete work_orders"

# 5. Test allowed action (should succeed)
curl -X POST http://localhost:8000/api/v1/production-logs \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -d '{"work_order_id": 1, "quantity_produced": 10}'

# Expected: 201 Created
```

### Automated Testing
```python
def test_rbac_work_order_delete_as_operator_forbidden():
    """Operators cannot delete work orders"""
    client = TestClient(app)

    # Login as operator
    response = client.post("/api/v1/auth/login", json={
        "username": "operator_user",
        "password": "test123"
    })
    token = response.json()["access_token"]

    # Attempt to delete work order
    response = client.delete(
        "/api/v1/work-orders/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_rbac_work_order_delete_as_plant_manager_allowed():
    """Plant Managers can delete work orders"""
    client = TestClient(app)

    # Login as plant manager
    response = client.post("/api/v1/auth/login", json={
        "username": "plant_manager",
        "password": "test123"
    })
    token = response.json()["access_token"]

    # Delete work order
    response = client.delete(
        "/api/v1/work-orders/1",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204
```

---

## Rollout Plan

### Week 1: Critical Security (Immediate)
- [ ] Update 94 critical endpoints (delete, adjust, admin functions)
- [ ] Add Casbin policies for 7 standard roles
- [ ] Test each role's permissions

### Week 2: Production & Operations
- [ ] Update 102 production endpoints
- [ ] Validate work order lifecycle permissions
- [ ] Test shift handover permissions

### Week 3: Configuration & Supporting
- [ ] Update 139 remaining endpoints
- [ ] Document any custom permission requirements
- [ ] Final integration testing

### Week 4: Validation & Deployment
- [ ] Penetration testing for permission bypass
- [ ] Performance testing (RBAC adds ~5-10ms per request)
- [ ] Deploy to staging
- [ ] Production deployment

---

## Monitoring & Audit

### Audit Logging
All permission denials should be logged:

```python
# Add to rbac_dependencies.py
if not has_permission:
    # Log permission denial
    audit_log = AuditLog(
        user_id=current_user.id,
        action=f"PERMISSION_DENIED: {action} {resource}",
        resource_type=resource,
        timestamp=datetime.now()
    )
    db.add(audit_log)
    db.commit()

    raise HTTPException(...)
```

### Metrics to Track
- Permission denial rate by endpoint
- Most frequently denied actions
- Users with highest denial rates (potential misconfigurations)
- Average RBAC check latency

---

## References

- **PRD Section 4.2**: Role-Based Access Control
- **FRD Section 6.1**: RBAC Standard Roles
- **Casbin Documentation**: https://casbin.org/docs/overview
- **Enhanced Decorator**: `/backend/app/infrastructure/security/rbac_dependencies.py`
- **Policy File**: `/backend/app/infrastructure/security/casbin_policy.csv`

---

**Next Steps**:
1. Add Casbin policies for all resources
2. Apply decorator to 94 critical endpoints (Phase 1)
3. Create automated test suite for permission matrix
4. Deploy to development environment for team testing
