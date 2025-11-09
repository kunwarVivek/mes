# Unison Manufacturing ERP - Critical Review & Implementation Roadmap

**Date**: 2025-11-09
**PRD Version**: v4.0 (Final - Pure Business Focus)
**Review Scope**: Backend, Frontend, Deployment vs PRD Requirements

---

## EXECUTIVE SUMMARY

### Current Implementation Status

| Layer | Completion | Critical Gaps | Status |
|-------|-----------|---------------|--------|
| **Database Schema** | ~40% | 27/47 tables missing | 🔴 CRITICAL |
| **Backend API** | ~28% | Multi-tenancy, Projects, Workflows | 🔴 CRITICAL |
| **Frontend UI** | ~31% | Routing, 11/16 features missing | 🔴 CRITICAL |
| **Deployment** | ~90% | PostgreSQL extensions not initialized | 🟡 READY |

**Overall System Readiness**: ~30% - **NOT PRODUCTION READY**

### Critical Blockers (Must Fix Immediately)

🔴 **1. NO Multi-Tenancy Foundation**
- Missing: `organizations`, `plants`, `departments` tables
- Missing: Row-Level Security (RLS) policies
- Impact: Cannot support multiple customers

🔴 **2. NO Database Migrations**
- No Alembic migrations for existing models
- Schema managed by `Base.metadata.create_all()` (not production-safe)
- Impact: Cannot safely evolve schema

🔴 **3. NO Frontend Routing**
- react-router-dom installed but unused
- App hardcoded to single page (UsersPage)
- Impact: Cannot navigate between features

🔴 **4. NO Authentication Integration**
- JWT not added to API requests
- No token refresh logic
- Impact: Protected endpoints fail

🔴 **5. NO Project Management**
- Missing entire project module (PRD requirement #6)
- Work orders not linked to customer orders
- Impact: Cannot track customer deliveries

---

## DETAILED GAP ANALYSIS

### Backend Gaps (72% Missing)

#### Missing Tables (27/47 tables - 57%)

**Multi-Tenancy (6 tables - 100% missing)**:
- `organizations` - Root tenant entity
- `plants` - Manufacturing sites
- `departments` - Org units
- `user_plant_access` - Plant-level permissions
- `user_department_access` - Department permissions
- `tenant_settings` - Per-tenant configuration

**Projects (5 tables - 100% missing)**:
- `projects` - Customer order tracking
- `project_bom` - Material requirements
- `project_documents` - Drawing storage
- `rda_drawings` - Drawing approval workflow
- `project_milestones` - Timeline tracking

**Production Scheduling (7 tables - 100% missing)**:
- `lanes` - Production lines/stations
- `lane_assignments` - Work order scheduling
- `production_logs` - Real-time shop floor logging (TimescaleDB)
- `rbs_schedules` - Resource-based schedules
- `rps_sheets` - Resource planning
- `manpower_allocation` - Worker assignments
- `daily_work_logs` - Shift summaries

**Traceability (3 tables - 100% missing)**:
- `lot_numbers` - Lot tracking
- `serial_numbers` - Serial genealogy
- `genealogy_records` - Parent-child relationships

**Logistics (4 tables - 100% missing)**:
- `shipments` - Shipment tracking
- `shipment_items` - Line items
- `qr_code_scans` - Scan history (TimescaleDB)
- `barcode_labels` - Generated barcodes

**Workflows (5 tables - 100% missing)**:
- `workflow_definitions` - Workflow templates
- `workflow_states` - State definitions
- `workflow_transitions` - Transition rules
- `workflow_instances` - Active workflows
- `workflow_approvals` - Approval history

**Configuration (3 tables - 100% missing)**:
- `custom_field_definitions` - Custom field schema
- `custom_field_values` - Custom data storage
- `type_configurations` - Custom type lists

**Reporting (3 tables - 100% missing)**:
- `dashboards` - Dashboard configurations
- `reports` - Report definitions
- `report_executions` - Report history

**SAP Integration (3 tables - 100% missing)**:
- `sap_material_mappings` - Material master sync
- `sap_sales_order_sync` - Sales order integration
- `sap_sync_logs` - Sync audit trail

**Inspection/Quality (3 tables - 75% missing)**:
- `inspection_points` - Inspection checkpoints
- `inspection_characteristics` - USL/LSL tolerances
- `inspection_measurements` - SPC data (TimescaleDB)

#### Missing API Endpoints (13 routers - 62%)

1. ❌ `/organizations` - Org CRUD
2. ❌ `/plants` - Plant management
3. ❌ `/departments` - Department management
4. ❌ `/projects` - Project CRUD
5. ❌ `/project-documents` - Document upload/download
6. ❌ `/lanes` - Lane scheduling
7. ❌ `/production-logs` - Real-time production
8. ❌ `/shipments` - Logistics tracking
9. ❌ `/dashboards` - Dashboard config
10. ❌ `/reports` - Report generation
11. ❌ `/workflows` - Workflow engine
12. ❌ `/custom-fields` - Configuration API
13. ❌ `/traceability` - Lot/serial genealogy

#### Missing Infrastructure (8 services - 80% missing)

1. ❌ TimescaleDB hypertables not created
2. ❌ pg_cron jobs not scheduled
3. ❌ PGMQ task runners not implemented
4. ❌ Row-Level Security (RLS) policies not created
5. ❌ LISTEN/NOTIFY triggers not configured
6. ❌ pg_search indexes not created
7. ❌ Email notification service not integrated
8. ❌ SAP integration not connected (mock adapter only)

### Frontend Gaps (69% Missing)

#### Missing Features (11/16 features - 69%)

1. ❌ Multi-tenant org switching UI
2. ❌ Configuration screens (custom fields builder)
3. ❌ Workflow designer UI (visual node-based)
4. ❌ White-label branding UI (theme customizer)
5. ❌ Visual scheduling (Gantt drag-drop)
6. ❌ Logistics tracking UI
7. ❌ Traceability UI (lot tracking, genealogy viewer)
8. ❌ Inspection/SPC screens (control charts)
9. ❌ Project management UI (project Gantt)
10. 🟡 Maintenance screens (partial - 3 components exist)
11. 🟡 Production scheduling (services only, no UI)

#### Critical Integration Gaps

1. 🔴 **NO Routing System**
   - react-router-dom installed but not configured
   - App hardcoded to UsersPage
   - No route definitions

2. 🔴 **NO Auth Integration**
   - JWT not added to axios requests (no interceptor)
   - No token refresh logic
   - ProtectedRoute component unused

3. 🔴 **NO Real-Time Updates**
   - No WebSocket client
   - Dashboard metrics static
   - No live production tracking

4. 🟡 **NO Page Components**
   - WorkOrdersPage, BOMsPage, NCRsPage missing
   - EquipmentPage, ShiftsPage, MaintenancePage missing
   - Only Materials and Auth have complete pages

### Deployment Gaps (10% Missing)

✅ **Docker Compose**: Well-configured (postgres, backend, frontend, pgmq_worker, minio)
✅ **Dockerfiles**: Present for backend and frontend
✅ **Environment Variables**: .env.example provided
⚠️ **PostgreSQL Extensions**: Docker configured but init script needs verification
❌ **Health Checks**: Only postgres has healthcheck
❌ **Production Config**: No production docker-compose
❌ **Kubernetes**: No K8s manifests
❌ **CI/CD**: No GitHub Actions/GitLab CI
❌ **Monitoring**: No Prometheus/Grafana
❌ **Logging**: No centralized logging (ELK/Loki)

---

## PRIORITIZED IMPLEMENTATION ROADMAP

### 🔴 PHASE 0: CRITICAL FOUNDATION (Week 1-2) - 10 days

**Goal**: Establish multi-tenancy, migrations, and routing to unblock all development

#### 0.1 Database Migrations (2 days)
**Owner**: Backend Lead
**Priority**: 🔴 BLOCKER

1. Initialize Alembic in `/backend/migrations/`
2. Create initial migration from existing models
3. Test upgrade/downgrade on local database
4. Document migration workflow

**Deliverables**:
- `backend/migrations/versions/001_initial_schema.py`
- `backend/migrations/README.md` (migration guide)

**Success Criteria**:
- `alembic upgrade head` runs successfully
- `alembic downgrade -1` works without errors

---

#### 0.2 Multi-Tenancy Schema (3 days)
**Owner**: Backend Lead
**Priority**: 🔴 BLOCKER

**Tasks**:
1. Create organizations, plants, departments tables
2. Add RLS policies to ALL existing tables
3. Create user-plant/department access tables
4. Migration: `002_multi_tenancy.py`

**Tables**:
```sql
CREATE TABLE organizations (
  id SERIAL PRIMARY KEY,
  org_code VARCHAR(20) UNIQUE NOT NULL,
  org_name VARCHAR(200) NOT NULL,
  subdomain VARCHAR(100) UNIQUE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE plants (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER REFERENCES organizations(id),
  plant_code VARCHAR(20) NOT NULL,
  plant_name VARCHAR(200) NOT NULL,
  location VARCHAR(500),
  is_active BOOLEAN DEFAULT true,
  UNIQUE(organization_id, plant_code)
);

CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  plant_id INTEGER REFERENCES plants(id),
  dept_code VARCHAR(20) NOT NULL,
  dept_name VARCHAR(200) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  UNIQUE(plant_id, dept_code)
);

-- RLS Policy Example (apply to ALL tables)
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON work_orders
  USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**Deliverables**:
- Migration `002_multi_tenancy.py`
- RLS policies on 20+ existing tables
- Seed data: 1 org, 2 plants, 3 departments

**Success Criteria**:
- RLS policies active on all tables
- Cannot query other tenant's data

---

#### 0.3 Multi-Tenancy Backend API (2 days)
**Owner**: Backend Lead
**Priority**: 🔴 BLOCKER

**Tasks**:
1. Create domain entities: Organization, Plant, Department
2. Implement repositories with RLS context
3. Build API endpoints: `/organizations`, `/plants`, `/departments`
4. Add tenant context middleware

**API Endpoints**:
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations` - List organizations
- `POST /api/v1/plants` - Create plant
- `GET /api/v1/plants` - List plants for org
- `POST /api/v1/departments` - Create department
- `GET /api/v1/departments` - List departments for plant

**Middleware**:
```python
# backend/app/presentation/middleware/tenant_context.py
async def set_tenant_context(request: Request, call_next):
    org_id = request.headers.get("X-Organization-ID")
    plant_id = request.headers.get("X-Plant-ID")

    # Set PostgreSQL session variables for RLS
    await db.execute(f"SET app.current_organization_id = {org_id}")
    await db.execute(f"SET app.current_plant_id = {plant_id}")

    response = await call_next(request)
    return response
```

**Deliverables**:
- 3 domain entities
- 3 API routers
- Tenant context middleware
- Integration tests (8 tests)

**Success Criteria**:
- Can create org → plant → department hierarchy
- Tenant isolation verified in tests

---

#### 0.4 Frontend Routing System (2 days)
**Owner**: Frontend Lead
**Priority**: 🔴 BLOCKER

**Tasks**:
1. Configure react-router-dom in `App.tsx`
2. Define route structure for all features
3. Implement ProtectedRoute usage
4. Create navigation components

**Route Structure**:
```typescript
// frontend/src/routes.tsx
export const routes = [
  { path: "/", element: <DashboardPage />, protected: true },
  { path: "/auth/login", element: <LoginPage />, protected: false },
  { path: "/auth/register", element: <RegisterPage />, protected: false },
  { path: "/materials", element: <MaterialsPage />, protected: true },
  { path: "/materials/new", element: <MaterialFormPage />, protected: true },
  { path: "/materials/:id/edit", element: <MaterialFormPage />, protected: true },
  { path: "/work-orders", element: <WorkOrdersPage />, protected: true },
  { path: "/bom", element: <BOMsPage />, protected: true },
  { path: "/quality/ncr", element: <NCRsPage />, protected: true },
  { path: "/equipment", element: <EquipmentPage />, protected: true },
  // ... 10+ more routes
];

// App.tsx
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {routes.map(route => (
            route.protected ? (
              <Route path={route.path} element={<ProtectedRoute>{route.element}</ProtectedRoute>} />
            ) : (
              <Route path={route.path} element={route.element} />
            )
          ))}
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

**Deliverables**:
- `frontend/src/routes.tsx` - Route definitions
- Updated `App.tsx` with BrowserRouter
- Navbar with navigation links
- 404 page

**Success Criteria**:
- Can navigate to all existing pages
- ProtectedRoute redirects to /auth/login
- URLs change on navigation

---

#### 0.5 Frontend Auth Integration (1 day)
**Owner**: Frontend Lead
**Priority**: 🔴 BLOCKER

**Tasks**:
1. Add axios request interceptor for JWT
2. Implement token refresh logic
3. Add org/plant headers to requests
4. Test protected API calls

**Axios Interceptor**:
```typescript
// frontend/src/lib/api-client.ts
import { authStore } from '@/stores/authStore'

apiClient.interceptors.request.use((config) => {
  const { token, currentOrg, currentPlant } = authStore.getState()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  if (currentOrg) {
    config.headers['X-Organization-ID'] = currentOrg.id
  }

  if (currentPlant) {
    config.headers['X-Plant-ID'] = currentPlant.id
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, refresh
      const newToken = await authService.refreshToken()
      // Retry request with new token
    }
    return Promise.reject(error)
  }
)
```

**Deliverables**:
- Updated `api-client.ts` with interceptors
- Token refresh service
- Tenant context in authStore
- Integration tests

**Success Criteria**:
- JWT added to all API requests
- Token refresh works automatically
- Org/plant context sent with requests

---

### 🔴 PHASE 1: CORE FEATURES (Week 3-4) - 10 days

#### 1.1 Projects Module (3 days)
**Owner**: Full Stack
**Priority**: 🔴 CRITICAL

**Backend** (2 days):
- Create projects tables (5 tables)
- Domain entities + repositories
- API endpoints: `/projects`, `/project-documents`
- Migration: `003_projects.py`

**Frontend** (1 day):
- ProjectsPage, ProjectFormPage
- Document upload component (MinIO)
- Project-work order linking

---

#### 1.2 Production Logging (2 days)
**Owner**: Full Stack
**Priority**: 🔴 CRITICAL

**Backend** (1 day):
- Create `production_logs` table (TimescaleDB hypertable)
- Real-time logging API: `POST /production-logs`
- WebSocket endpoint for live updates

**Frontend** (1 day):
- ProductionLoggingPage (PWA mobile view)
- useCamera integration for barcode scan
- WebSocket client for live dashboard

---

#### 1.3 Lane Scheduling (3 days)
**Owner**: Full Stack
**Priority**: 🔴 CRITICAL

**Backend** (2 days):
- Create lanes, lane_assignments tables
- Scheduling algorithm (RBS/RPS)
- API: `/lanes`, `/schedules`
- Migration: `004_scheduling.py`

**Frontend** (1 day):
- SchedulingPage with calendar view
- Lane selector dropdown
- Work order drag-drop (basic)

---

#### 1.4 Missing Page Components (2 days)
**Owner**: Frontend Lead
**Priority**: 🟡 IMPORTANT

**Tasks**:
- WorkOrdersPage, WorkOrderFormPage
- BOMsPage, BOMFormPage
- NCRsPage, NCRFormPage
- EquipmentPage, EquipmentFormPage

**Success Criteria**:
- All existing feature services connected to UI
- Full CRUD flows work end-to-end

---

### 🟡 PHASE 2: WORKFLOWS & CONFIGURATION (Week 5-6) - 10 days

#### 2.1 Workflow Engine (4 days)
**Owner**: Backend Lead
**Priority**: 🟡 IMPORTANT

**Backend** (4 days):
- Create workflow tables (5 tables)
- State machine engine
- Approval routing logic
- API: `/workflows`, `/approvals`
- Migration: `005_workflows.py`

---

#### 2.2 Configuration Engine (3 days)
**Owner**: Full Stack
**Priority**: 🟡 IMPORTANT

**Backend** (2 days):
- Create custom_fields tables (3 tables)
- Dynamic schema validation
- API: `/custom-fields`, `/type-configurations`

**Frontend** (1 day):
- Custom fields builder UI
- Form designer (basic)

---

#### 2.3 White-Label Branding (2 days)
**Owner**: Full Stack
**Priority**: 🟢 NICE-TO-HAVE

**Backend** (1 day):
- Add branding columns to organizations
- Logo upload to MinIO
- API: `/branding`

**Frontend** (1 day):
- Theme customizer UI
- Logo upload component

---

#### 2.4 Multi-Tenant Frontend (1 day)
**Owner**: Frontend Lead
**Priority**: 🔴 CRITICAL (moved from Phase 0 if deferred)

**Tasks**:
- Org selector dropdown in Navbar
- Tenant context provider
- Plant switching logic
- Update authStore with tenant state

---

### 🟡 PHASE 3: TRACEABILITY & LOGISTICS (Week 7-8) - 10 days

#### 3.1 Lot/Serial Traceability (4 days)
**Owner**: Full Stack
**Priority**: 🔴 CRITICAL (for regulated industries)

**Backend** (2 days):
- Create lot_numbers, serial_numbers, genealogy_records tables
- Traceability queries (forward/backward)
- API: `/lots`, `/serials`, `/traceability`
- Migration: `006_traceability.py`

**Frontend** (2 days):
- LotTrackerPage
- GenealogyViewer component
- Recall report generator

---

#### 3.2 Logistics Module (3 days)
**Owner**: Full Stack
**Priority**: 🟡 IMPORTANT

**Backend** (2 days):
- Create shipments, qr_code_scans tables
- QR scanning API
- API: `/shipments`, `/scans`
- Migration: `007_logistics.py`

**Frontend** (1 day):
- ShipmentTrackerPage
- QR scanner integration (useCamera)

---

#### 3.3 Inspection/SPC (3 days)
**Owner**: Full Stack
**Priority**: 🟡 IMPORTANT

**Backend** (2 days):
- Create inspection_points, inspection_characteristics, inspection_measurements tables
- TimescaleDB continuous aggregates for SPC
- Cp/Cpk calculation service

**Frontend** (1 day):
- InspectionChecklistPage
- SPCChartComponent (control limits)

---

### 🟡 PHASE 4: ANALYTICS & INTEGRATION (Week 9-10) - 10 days

#### 4.1 KPI Calculations (4 days)
**Owner**: Backend Lead
**Priority**: 🔴 CRITICAL

**Tasks**:
- TimescaleDB continuous aggregates:
  - `daily_production_summary`
  - `daily_machine_oee`
  - `daily_spc_metrics`
- OEE, OTD, FPY calculation services
- API: `/kpis/oee`, `/kpis/otd`, `/kpis/fpy`
- Migration: `008_analytics.py`

---

#### 4.2 Dashboards & Reports (3 days)
**Owner**: Full Stack
**Priority**: 🟡 IMPORTANT

**Backend** (2 days):
- Create dashboards, reports tables
- Report generation service (PDF/CSV)
- API: `/dashboards`, `/reports`

**Frontend** (1 day):
- Connect ExecutiveDashboard to real KPI APIs
- Report configuration UI

---

#### 4.3 Background Jobs (2 days)
**Owner**: Backend Lead
**Priority**: 🟡 IMPORTANT

**Tasks**:
- PGMQ task runners:
  - Barcode generation
  - Email notifications
  - Min/max stock alerts
  - PM work order generation (pg_cron)

---

#### 4.4 SAP Integration (1 day)
**Owner**: Backend Lead
**Priority**: 🟢 NICE-TO-HAVE

**Tasks**:
- Real SAP adapter (replace mock)
- Sync jobs: materials, sales orders
- API: `/sap/sync`

---

### 🟢 PHASE 5: POLISH & TESTING (Week 11-12) - 10 days

#### 5.1 Visual Scheduling Enhancement (3 days)
**Owner**: Frontend Lead
**Priority**: 🟡 IMPORTANT

**Tasks**:
- Integrate Gantt library (Frappe-Gantt or Bryntum)
- Drag-drop work order scheduling
- Dependency visualization
- Conflict detection UI

---

#### 5.2 Real-Time Updates (2 days)
**Owner**: Full Stack
**Priority**: 🟡 IMPORTANT

**Backend** (1 day):
- WebSocket endpoint: `/ws`
- LISTEN/NOTIFY triggers for production_logs

**Frontend** (1 day):
- WebSocket client setup
- Live dashboard updates

---

#### 5.3 Component Tests (2 days)
**Owner**: Frontend Lead
**Priority**: 🟡 IMPORTANT

**Tasks**:
- Add component tests for all features
- Integration tests (API mocking)
- Increase coverage to 80%+

---

#### 5.4 E2E Tests (2 days)
**Owner**: QA Lead
**Priority**: 🟡 IMPORTANT

**Tasks**:
- Playwright E2E tests
- Critical user journeys:
  - Login → Create work order → Log production
  - Create NCR → Workflow approval
  - Material transaction → Inventory check

---

#### 5.5 PWA Hardening (1 day)
**Owner**: Frontend Lead
**Priority**: 🟢 NICE-TO-HAVE

**Tasks**:
- Integrate Workbox
- Background sync
- Push notifications

---

## IMPLEMENTATION STRATEGY

### Bottoms-Up Approach ✅

```
Schema (Migrations + RLS)
    ↓
Backend (Domain + API)
    ↓
Frontend (Pages + Integration)
    ↓
Testing (E2E Validation)
```

### Team Structure (Recommended)

| Role | Responsibilities | Phases |
|------|-----------------|--------|
| **Backend Lead** | Schema, migrations, API, infrastructure | 0-4 |
| **Frontend Lead** | Routing, pages, components, integration | 0-5 |
| **Full Stack** | Projects, scheduling, traceability modules | 1-3 |
| **QA Lead** | Tests, E2E, quality gates | 5 |

### Daily Standup Focus

1. **Blockers** - Anything blocking bottom-up flow
2. **Dependencies** - Schema → Backend → Frontend coordination
3. **Risks** - Production readiness concerns
4. **Progress** - Feature completion %

---

## SUCCESS METRICS

### Phase 0 (Foundation) - Week 2
- ✅ All models have Alembic migrations
- ✅ RLS policies active on all tables
- ✅ Frontend routing works for all pages
- ✅ JWT auth integrated in axios

### Phase 1 (Core Features) - Week 4
- ✅ Projects module functional (create project → link work orders)
- ✅ Production logging works (scan → log → dashboard updates)
- ✅ Lane scheduling works (assign work order → lane → visual calendar)

### Phase 2 (Workflows) - Week 6
- ✅ NCR workflow routing works (create → route → approve → resolve)
- ✅ Custom fields functional (add custom field → populate → query)
- ✅ Org switching works (switch org → data isolation verified)

### Phase 3 (Traceability) - Week 8
- ✅ Lot traceability works (create lot → genealogy → recall report)
- ✅ Shipment tracking works (create shipment → scan → track)
- ✅ Inspection/SPC works (log measurements → control charts → Cp/Cpk)

### Phase 4 (Analytics) - Week 10
- ✅ OEE dashboard shows live metrics
- ✅ OTD tracking works
- ✅ Reports can be generated (PDF/CSV)

### Phase 5 (Polish) - Week 12
- ✅ Visual Gantt scheduler functional
- ✅ Real-time dashboard updates work
- ✅ 80%+ test coverage
- ✅ PWA passes Lighthouse audit (90+ score)

---

## RISK MITIGATION

### High-Risk Items

| Risk | Mitigation | Owner |
|------|-----------|-------|
| **RLS complexity** | Extensive testing with multi-tenant data | Backend Lead |
| **Gantt library integration** | Prototype 2-3 libraries in Week 1 | Frontend Lead |
| **TimescaleDB learning curve** | Study continuous aggregates in Week 0 | Backend Lead |
| **Workflow state machine** | Use existing library (pytransitions) | Backend Lead |
| **Real-time scalability** | Benchmark WebSocket connections early | Backend Lead |

### Contingency Plans

- **Gantt fails**: Fall back to calendar view (Week 5)
- **RLS too complex**: Use application-level filtering (Week 2)
- **TimescaleDB issues**: Use regular PostgreSQL tables (Week 4)
- **WebSocket scaling**: Use polling as fallback (Week 9)

---

## DELIVERABLES SUMMARY

### Phase 0 (Critical Foundation)
- 2 Alembic migrations
- 3 multi-tenancy tables
- RLS policies on 20+ tables
- Frontend routing system
- Auth integration (JWT + refresh)

### Phase 1 (Core Features)
- Projects module (5 tables, 2 API routers, 2 pages)
- Production logging (1 hypertable, 1 API, 1 page)
- Lane scheduling (2 tables, 2 APIs, 1 page)
- 8 missing page components

### Phase 2 (Workflows)
- Workflow engine (5 tables, 2 APIs)
- Configuration engine (3 tables, 2 APIs, 1 page)
- White-labeling (1 API, 1 page)
- Multi-tenant UI (org switcher)

### Phase 3 (Traceability)
- Traceability (3 tables, 3 APIs, 2 pages)
- Logistics (4 tables, 2 APIs, 1 page)
- Inspection/SPC (3 tables, 1 API, 2 pages)

### Phase 4 (Analytics)
- KPIs (3 continuous aggregates, 3 APIs)
- Dashboards (2 tables, 2 APIs, 1 page)
- Background jobs (PGMQ + pg_cron)
- SAP integration (3 tables, 1 API)

### Phase 5 (Polish)
- Visual Gantt scheduler
- WebSocket integration
- Component + E2E tests
- PWA hardening

---

## APPENDIX: QUICK REFERENCE

### Critical Commands

**Backend**:
```bash
# Initialize Alembic
cd backend
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# Run backend
uvicorn app.main:app --reload
```

**Frontend**:
```bash
# Run frontend
npm run dev

# Run tests
npm test

# Build
npm run build
```

**Database**:
```bash
# Enter PostgreSQL container
docker exec -it unison-postgres psql -U unison -d unison_erp

# Check RLS policies
\d+ work_orders

# Test RLS
SET app.current_organization_id = 1;
SELECT * FROM work_orders;
```

**Docker**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down
```

---

## CONCLUSION

This roadmap provides a systematic, bottoms-up approach to closing the 70% implementation gap. By prioritizing multi-tenancy foundation, migrations, and routing in Phase 0, we unblock all subsequent development.

**Estimated Timeline**: 12 weeks (3 months)
**Team Size**: 3-4 developers (Backend Lead, Frontend Lead, Full Stack, QA)
**Total Effort**: ~200 person-days

**Next Steps**:
1. Review and approve roadmap with stakeholders
2. Assign Phase 0 tasks to team
3. Begin Week 1: Migrations + Multi-Tenancy
4. Daily standups to track progress

---

**Roadmap Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Version**: 1.0
**Status**: READY FOR EXECUTION
