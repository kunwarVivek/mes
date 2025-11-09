# IMPLEMENTATION PLAN - Backend Debt Resolution
## Bottom-Up Approach: Schema → Backend → Testing

**Date**: 2025-11-09
**Scope**: Complete MVP-blocking gaps identified in gap analysis
**Approach**: Prioritized, bottom-up implementation (database schema first)

---

## EXECUTION STRATEGY

### Phase 1: Quick Wins & Foundation (Week 1)
**Goal**: Ship RBAC + enable parallel work on other modules

#### 1.1 RBAC System (5 days) ⚡ QUICK WIN
- **Schema**: Create migrations for `roles`, `user_roles`, `user_plant_access`
- **Models**: SQLAlchemy models with RLS
- **Repositories**: CRUD operations
- **Services**: Role assignment, permission checking
- **API**: Endpoints for role management
- **Testing**: RLS isolation tests

#### 1.2 PostgreSQL Extensions Setup (2 days)
- **pgmq**: Message queue setup
- **pg_search**: Full-text search indexes
- **pg_cron**: Scheduled task configuration
- **timescaledb**: Expand to all time-series tables
- **pg_duckdb**: Analytics query optimization

---

### Phase 2: Configuration Engine (Week 2)
**Goal**: Enable self-service customization (core differentiator)

#### 2.1 Custom Fields Infrastructure (8 days)
**Schema**:
- `custom_fields` - Field definitions per entity type
- `field_values` - JSONB storage for field values
- `type_lists` - Configurable taxonomies
- `type_list_values` - Type list items

**Backend**:
- Dynamic field validation service
- Custom field CRUD service
- Type list management service
- Entity mixin for custom field support

**API**:
- `/api/v1/custom-fields` - Field definition CRUD
- `/api/v1/type-lists` - Type list management
- Extend entity endpoints to include custom fields

---

### Phase 3: Workflow Engine (Week 3)
**Goal**: Enable approval workflows for NCR, drawings, change orders

#### 3.1 Workflow Infrastructure (10 days)
**Schema**:
- `workflows` - Workflow definitions
- `workflow_states` - State machine states
- `workflow_transitions` - Transition rules with conditions
- `approvals` - Approval instances and history

**Backend**:
- Workflow state machine engine
- Transition validation service
- Approval routing service
- Notification integration (PGMQ)

**API**:
- `/api/v1/workflows` - Workflow definition CRUD
- `/api/v1/approvals` - Approval actions
- Extend NCR/Project endpoints with workflow support

---

### Phase 4: Logistics & Tracking (Week 4)
**Goal**: Enable barcode/QR scanning and shipment tracking

#### 4.1 Logistics Module (8 days)
**Schema**:
- `shipments` - Shipment tracking
- `shipment_items` - Line items
- `qr_code_scans` - Scan events (timescaledb hypertable)
- `barcode_labels` - Generated label storage

**Backend**:
- Barcode generation service (async PGMQ)
- QR scanning service
- Shipment tracking service
- Label printing service

**API**:
- `/api/v1/shipments` - Shipment CRUD
- `/api/v1/barcodes/scan` - Scan endpoint
- `/api/v1/barcodes/generate` - Async generation

---

### Phase 5: Reporting & Dashboards (Week 5)
**Goal**: Enable KPI dashboards (OEE, OTD, FPY)

#### 5.1 Reporting Infrastructure (10 days)
**Schema**:
- `reports` - Report definitions
- `report_executions` - Execution history
- `dashboards` - Dashboard configurations

**Backend**:
- Report execution engine (pg_duckdb)
- Dashboard data aggregation service
- KPI calculation service (pg_cron)
- Export service (PDF/CSV via PGMQ)

**API**:
- `/api/v1/reports` - Report CRUD
- `/api/v1/reports/{id}/execute` - Async execution
- `/api/v1/dashboards` - Dashboard data

---

### Phase 6: Project Management (Week 6)
**Goal**: Complete project module with documents, milestones, RDA

#### 6.1 Project Enhancements (6 days)
**Schema**:
- `project_documents` - Document management
- `project_milestones` - Milestone tracking
- `rda_drawings` - Drawing approval workflow
- `project_bom` - Bill of Materials for projects

**Backend**:
- Document versioning service
- Milestone tracking service
- RDA approval workflow (uses workflow engine)
- Project BOM service

**API**:
- `/api/v1/projects/{id}/documents` - Document management
- `/api/v1/projects/{id}/milestones` - Milestone tracking
- `/api/v1/projects/{id}/rda` - Drawing approvals

---

### Phase 7: Quality Management Enhancements (Week 7)
**Goal**: Complete quality module with SPC and inspection plans

#### 7.1 Inspection Details (6 days)
**Schema**:
- `inspection_plans` - Plan definitions
- `inspection_points` - Checkpoint definitions
- `inspection_characteristics` - Measurable characteristics
- `inspection_measurements` - SPC measurements (timescaledb)

**Backend**:
- Inspection plan service
- SPC calculation service (Cp, Cpk, control charts)
- First Pass Yield (FPY) service
- Quality trend analysis (pg_duckdb)

**API**:
- `/api/v1/inspection-plans` - Plan CRUD
- `/api/v1/inspections/{id}/measurements` - SPC data
- `/api/v1/quality/spc-charts` - Control chart data

---

### Phase 8: Traceability (Week 8)
**Goal**: Enable lot/serial tracking and genealogy

#### 8.1 Traceability Infrastructure (8 days)
**Schema**:
- `lot_numbers` - Lot tracking
- `serial_numbers` - Serial number tracking
- `genealogy_records` - Forward/backward genealogy

**Backend**:
- Lot assignment service
- Serial number generation service
- Genealogy traversal service
- Recall simulation service

**API**:
- `/api/v1/lots` - Lot tracking
- `/api/v1/serial-numbers` - Serial tracking
- `/api/v1/traceability/genealogy` - Genealogy queries

---

### Phase 9: White-Label Branding (Week 9)
**Goal**: Enable custom branding per organization

#### 9.1 Branding Infrastructure (5 days)
**Schema**:
- `organization_branding` - Branding configuration
- `branding_configs` - Logo, colors, fonts, custom domain

**Backend**:
- Branding service
- Custom domain routing
- Logo upload service (MinIO)
- Theme generation service

**API**:
- `/api/v1/organizations/{id}/branding` - Branding CRUD
- `/api/v1/branding/theme` - Theme data for frontend

---

### Phase 10: Infrastructure & Polish (Week 10)
**Goal**: Complete remaining infrastructure

#### 10.1 Missing Infrastructure (4 days)
**Schema**:
- `audit_logs` - Comprehensive audit trail
- `notifications` - In-app notifications
- `system_settings` - Organization-level config
- `file_uploads` - File tracking
- `sap_sync_logs` - SAP integration logs
- `sap_mappings` - Entity mappings

**Backend**:
- Audit logging service (automatic via middleware)
- Notification service (PGMQ + WebSocket)
- System settings service
- SAP integration enhancement

#### 10.2 Missing Columns (2 days)
- Add missing columns to existing tables
- Create migration for column additions

#### 10.3 RLS & Indexes (2 days)
- Create RLS policies for all new tables
- Add composite indexes for performance
- Add pg_search BM25 indexes

---

## TECHNICAL IMPLEMENTATION DETAILS

### Migration Naming Convention
```
{timestamp}_{descriptive_name}.py
```

Example:
```
2025_11_09_123456_add_rbac_tables.py
2025_11_09_134567_add_custom_fields_tables.py
```

### Model Structure
```python
# Example: app/models/role.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    role_name = Column(String(100), nullable=False)
    role_code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)
    permissions = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")

    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'role_code',
                        name='uq_role_code_per_org'),
        Index('idx_role_org', 'organization_id'),
        {'postgresql_rls': True}  # Enable RLS
    )
```

### Repository Pattern
```python
# Example: app/infrastructure/repositories/role_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.role import Role
from app.application.dtos.role_dto import RoleCreateDTO, RoleUpdateDTO

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: RoleCreateDTO) -> Role:
        role = Role(**dto.dict())
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_by_id(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def list(self, organization_id: int, skip: int = 0, limit: int = 100) -> List[Role]:
        # RLS automatically filters by organization_id
        return self.db.query(Role).offset(skip).limit(limit).all()
```

### API Endpoint Pattern
```python
# Example: app/presentation/api/v1/roles.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.infrastructure.repositories.role_repository import RoleRepository
from app.application.dtos.role_dto import RoleCreateDTO, RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("/", response_model=RoleResponse, status_code=201)
async def create_role(
    dto: RoleCreateDTO,
    db: Session = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    repo = RoleRepository(db)
    role = repo.create(dto)
    return RoleResponse.from_orm(role)

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    repo = RoleRepository(db)
    role = repo.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleResponse.from_orm(role)
```

---

## TESTING STRATEGY

### 1. Unit Tests
- Domain entity validation
- Service business logic
- Repository operations (mocked DB)

### 2. Integration Tests
- Repository with real database
- RLS policy enforcement
- API endpoint contracts

### 3. Security Tests
- JWT token validation
- RLS isolation between organizations
- SQL injection prevention
- Input validation

### 4. Performance Tests
- Query optimization with EXPLAIN ANALYZE
- Index usage verification
- pg_search performance vs LIKE
- pg_duckdb analytics performance

---

## SUCCESS CRITERIA

### Phase 1 (RBAC)
- [ ] 3 new tables created with migrations
- [ ] RLS policies applied
- [ ] API endpoints functional
- [ ] Security tests pass (organization isolation)
- [ ] Casbin integration works with new roles table

### Phase 2 (Configuration Engine)
- [ ] 4 new tables created
- [ ] Custom fields work on materials, work_orders, projects, NCRs
- [ ] Type lists configurable via UI
- [ ] API supports dynamic field queries

### Phase 3 (Workflow Engine)
- [ ] 4 new tables created
- [ ] State machine works for NCR workflow
- [ ] Approval routing functional
- [ ] Email notifications sent via PGMQ

### Phase 4 (Logistics)
- [ ] 4 new tables created
- [ ] Barcode generation async (PGMQ)
- [ ] QR scanning records in timescaledb
- [ ] Shipment tracking functional

### Phase 5 (Reporting)
- [ ] 3 new tables created
- [ ] Dashboard KPI calculations use pg_duckdb
- [ ] Report execution async (PGMQ)
- [ ] PDF/CSV export works

---

## RISK MITIGATION

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Run full test suite before/after each phase
- Use feature flags for new features
- Database migrations with rollback scripts

### Risk 2: Performance Degradation
**Mitigation**:
- EXPLAIN ANALYZE on all new queries
- Add indexes proactively
- Use pg_duckdb for analytics

### Risk 3: RLS Policy Gaps
**Mitigation**:
- Security test suite for every new table
- Automated RLS verification script
- Peer review on all migrations

---

## TIMELINE SUMMARY

| Phase | Duration | Effort (days) | Deliverable |
|-------|----------|---------------|-------------|
| Phase 1: RBAC + Extensions | Week 1 | 7 | RBAC system + PostgreSQL setup |
| Phase 2: Configuration Engine | Week 2 | 8 | Custom fields + type lists |
| Phase 3: Workflow Engine | Week 3 | 10 | Approval workflows |
| Phase 4: Logistics | Week 4 | 8 | Barcode/QR tracking |
| Phase 5: Reporting | Week 5 | 10 | Dashboards + KPIs |
| Phase 6: Project Mgmt | Week 6 | 6 | Documents + milestones |
| Phase 7: Quality | Week 7 | 6 | SPC + inspection plans |
| Phase 8: Traceability | Week 8 | 8 | Lot/serial tracking |
| Phase 9: Branding | Week 9 | 5 | White-label support |
| Phase 10: Infrastructure | Week 10 | 8 | Audit, notifications, polish |
| **TOTAL** | **10 weeks** | **76 days** | **MVP-complete backend** |

---

## NEXT IMMEDIATE ACTIONS

1. ✅ Review this implementation plan
2. 🚀 **START: Phase 1.1 - RBAC System**
   - Create migration for `roles` table
   - Create migration for `user_roles` table
   - Create migration for `user_plant_access` table
3. Build models, repositories, services, API endpoints
4. Test RLS isolation
5. Commit and push Phase 1.1

**Estimated MVP Completion: 10 weeks from start**
