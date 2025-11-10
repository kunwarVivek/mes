# Frontend Debt Review & Implementation Plan
**Date**: 2025-11-10
**Branch**: `claude/frontend-debt-review-implementation-011CUz2s2sYnGckcEGDpDhN5`
**Approach**: Bottoms Up (Schema → Backend → Frontend)

---

## Executive Summary

**Critical Findings:**
1. **BLOCKER**: Missing API client (`src/lib/api-client.ts`) - entire frontend non-functional
2. **BLOCKER**: Missing utils file (`src/lib/utils.ts`) - components fail to compile
3. **BLOCKER**: Duplicate auth stores with incompatible schemas
4. **MAJOR GAP**: 8 features have backend services but no frontend UI routes
5. **MAJOR GAP**: Onboarding flow completely missing (schema + backend + frontend)
6. **MAJOR GAP**: Production Planning & Scheduling missing (schema + backend + frontend)

**Overall Status**: Frontend ~40% implemented, 0% functional due to blockers

**Total Effort**: ~176 hours (23 work days) organized in 5 phases

---

## Phase 1: Critical Blockers (MUST FIX FIRST)
**Duration**: 2 days | **Priority**: P0 | **Effort**: 13 hours

### 1.1 Create API Client Infrastructure
**File**: `/home/user/mes/frontend/src/lib/api-client.ts`

**Impact**: TOTAL SYSTEM FAILURE - All 17 services import this but it doesn't exist

**Implementation**:
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios'

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Request interceptor - JWT token + RLS context
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  const orgId = localStorage.getItem('current_organization_id')
  const plantId = localStorage.getItem('current_plant_id')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // RLS context for multi-tenancy
  if (orgId) {
    config.headers['X-Organization-ID'] = orgId
  }
  if (plantId) {
    config.headers['X-Plant-ID'] = plantId
  }

  return config
})

// Response interceptor - token refresh + error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any

    // Handle 401 - refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })

        localStorage.setItem('access_token', data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`

        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed - logout
        localStorage.clear()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
```

**Testing**: Verify all 17 services compile and can make API calls

**Effort**: 4 hours

---

### 1.2 Create Utils File
**File**: `/home/user/mes/frontend/src/lib/utils.ts`

**Impact**: Multiple components fail to compile

**Implementation**:
```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Effort**: 15 minutes

---

### 1.3 Consolidate Auth Stores
**Files**:
- DELETE: `/home/user/mes/frontend/src/features/auth/stores/authStore.ts`
- KEEP: `/home/user/mes/frontend/src/stores/auth.store.ts`

**Impact**: Authentication state inconsistency

**Implementation Steps**:
1. Search for all imports from `features/auth/stores/authStore`
2. Replace with imports from `stores/auth.store`
3. Update User interface to match API response:
   ```typescript
   interface User {
     id: number                    // Not string!
     email: string
     full_name: string
     username: string
     organization_id: number       // Required for RLS
     plant_ids: number[]           // Required for plant switching
     roles: string[]
     is_active: boolean
     is_superuser: boolean
   }
   ```
4. Delete duplicate auth store file
5. Test login flow end-to-end

**Effort**: 3 hours

---

### 1.4 Fix Hardcoded Tenant IDs (from BUILD_REPORT)
**Files**:
- `frontend/src/features/materials/components/MaterialForm.tsx:53-54`
- `frontend/src/features/quality/components/NCRForm.tsx:52`
- `frontend/src/features/equipment/components/MachineForm.tsx:28-29`

**Impact**: CRITICAL - Multi-tenant system fails for orgs other than ID 1

**Implementation**:
```typescript
// Before:
organization_id: 1,  // ❌ Hardcoded
plant_id: 1,         // ❌ Hardcoded
reported_by_user_id: 1,  // ❌ Hardcoded

// After:
import { useAuthStore } from '@/stores/auth.store'

const { currentOrg, currentPlant, user } = useAuthStore()

organization_id: currentOrg?.id,
plant_id: currentPlant?.id,
reported_by_user_id: user?.id,
```

**Effort**: 2 hours

---

### 1.5 End-to-End Testing
**Test Flow**: Login → Dashboard → Materials List → Create Material

**Verification**:
- ✅ API client attaches JWT token
- ✅ RLS headers set correctly
- ✅ Token refresh works on 401
- ✅ All services can communicate with backend

**Effort**: 2 hours

**Total Phase 1**: 13 hours (2 days)

---

## Phase 2: Quick Wins - Add Missing Routes
**Duration**: 1 day | **Priority**: P1 | **Effort**: 4 hours

### 2.1 Add Routes for Existing Pages
8 features have complete implementations but no routes!

**Implementation**:

1. **Projects** - `frontend/src/routes/projects.tsx`
   ```typescript
   import { createRoute } from '@tanstack/react-router'
   import { authenticatedRoute } from './_authenticated'
   import { ProjectsPage } from '@/features/projects/pages/ProjectsPage'

   export const projectsRoute = createRoute({
     getParentRoute: () => authenticatedRoute,
     path: '/projects',
     component: ProjectsPage,
   })
   ```

2. **Maintenance** - `frontend/src/routes/maintenance.tsx`
3. **Shifts** - `frontend/src/routes/shifts.tsx`
4. **Lanes** - `frontend/src/routes/lanes.tsx`
5. **Production** - `frontend/src/routes/production.tsx`
6. **Production Plans** - `frontend/src/routes/production-plans.tsx`
7. **MRP** - `frontend/src/routes/mrp.tsx`
8. **Scheduling** - `frontend/src/routes/scheduling.tsx`

**Update Router**:
```typescript
// frontend/src/router.tsx
import { projectsRoute } from './routes/projects'
import { maintenanceRoute } from './routes/maintenance'
// ... import all 8 routes

authenticatedRoute.addChildren([
  dashboardRoute,
  materialsRoute,
  workOrdersRoute,
  qualityRoute,
  projectsRoute,        // ← Add all 8
  maintenanceRoute,
  shiftsRoute,
  lanesRoute,
  productionRoute,
  productionPlansRoute,
  mrpRoute,
  schedulingRoute,
])
```

**Update Sidebar Navigation**:
```typescript
// frontend/src/components/layouts/Sidebar.tsx
const navItems = [
  { path: '/projects', label: 'Projects', icon: FolderIcon },
  { path: '/maintenance', label: 'Maintenance', icon: WrenchIcon },
  { path: '/shifts', label: 'Shifts', icon: ClockIcon },
  { path: '/lanes', label: 'Lanes', icon: LayoutIcon },
  { path: '/production', label: 'Production', icon: FactoryIcon },
  { path: '/production-plans', label: 'Planning', icon: CalendarIcon },
  { path: '/mrp', label: 'MRP', icon: PackageIcon },
  { path: '/scheduling', label: 'Scheduling', icon: GanttChartIcon },
]
```

**Effort**: 4 hours (30 mins per route)

**Total Phase 2**: 4 hours (1 day)

---

## Phase 3: High-Value Features
**Duration**: 8 days | **Priority**: P1 | **Effort**: 61 hours

### 3.1 Complete BOM Page UI
**File**: `frontend/src/features/bom/pages/BOMPage.tsx`

**Current State**: Placeholder only

**Requirements** (from PRD 4.6 & API_DESIGN.md):
- BOM hierarchy tree view (parent-child relationships)
- Multi-level BOM support (Level 0 → Level 3+)
- BOM explosion calculations
- Material requirements display
- CSV import/export

**Implementation**:
1. Create `BOMTree.tsx` component with react-arborist or similar
2. Create `BOMExplosion.tsx` component for calculations
3. Integrate with existing `BOMForm.tsx`, `BOMTreeView.tsx`, `BOMsTable.tsx`
4. Add CSV import/export with Papa Parse
5. Write comprehensive tests

**Effort**: 16 hours (2 days)

---

### 3.2 Complete Equipment Page UI
**File**: `frontend/src/features/equipment/pages/EquipmentPage.tsx`

**Current State**: Placeholder only

**Requirements** (from PRD 4.11 & API_DESIGN.md):
- Machine master data table
- Real-time status tracking (Running, Idle, Down, Setup)
- Utilization metrics (OEE calculation)
- Machine history/timeline
- Capacity planning view

**Implementation**:
1. Create `MachineTable.tsx` with status badges
2. Create `MachineStatusCard.tsx` for real-time status
3. Create `OEEMetricsCard.tsx` for utilization
4. Create `MachineHistoryTimeline.tsx` for history
5. Integrate with existing hooks (`useMachines`, `useMachineOEE`)
6. Write comprehensive tests

**Effort**: 12 hours (1.5 days)

---

### 3.3 Integrate Real Dashboard APIs
**File**: `frontend/src/hooks/useDashboardMetrics.ts`

**Current State**: Uses hardcoded limit=100 for all queries

**Issues**:
1. Dashboard only shows first 100 items
2. Metrics may be inaccurate for large datasets
3. No dedicated metrics aggregation endpoint

**Implementation**:
1. Remove `limit: 100` from queries
2. Use backend `/api/v1/reports/production-summary` endpoint
3. Use backend `/api/v1/reports/otd-tracking` endpoint
4. Use backend `/api/v1/reports/ncr-analysis` endpoint
5. Update dashboard page to use real data
6. Remove mock data from `ExecutiveDashboard.tsx`

**Effort**: 12 hours (1.5 days)

---

### 3.4 Implement Onboarding Wizard (Frontend Only)
**Files**: New directory `frontend/src/features/onboarding/`

**NOTE**: Backend endpoints are missing, so this is frontend-only prep

**Requirements** (from API_DESIGN.md):
- 4-step wizard (Signup → Organization → Plant → Invite Users)
- Progress indicator
- Validation at each step
- Sample data option

**Implementation**:
1. Create `OnboardingWizard.tsx` with step indicator
2. Create `SignupStep.tsx` (Step 1)
3. Create `OrganizationStep.tsx` (Step 2)
4. Create `PlantStep.tsx` (Step 3)
5. Create `InviteUsersStep.tsx` (Step 4)
6. Create `onboarding.service.ts` (API calls will fail until backend implemented)
7. Create routes for onboarding flow
8. Write comprehensive tests

**Effort**: 20 hours (2.5 days)

---

**Total Phase 3**: 61 hours (8 days)

---

## Phase 4: Complex Features
**Duration**: 9 days | **Priority**: P1-P2 | **Effort**: 70 hours

### 4.1 Install & Integrate Frappe-Gantt
**Missing Dependency**: `frappe-gantt` not installed

**Requirements** (from PRD 4.13 & API_DESIGN.md):
- Visual Gantt chart for production scheduling
- Drag-and-drop rescheduling
- Lane assignment
- Conflict detection
- Auto-schedule

**Implementation**:
1. Install dependencies:
   ```bash
   npm install frappe-gantt @types/frappe-gantt
   ```

2. Create `GanttChart.tsx` wrapper component
3. Create `SchedulingPage.tsx` with Gantt integration
4. Integrate with scheduling service
5. Add drag-and-drop handlers
6. Add conflict detection UI
7. Write comprehensive tests

**NOTE**: Backend `/api/v1/schedule/gantt` endpoint is missing!

**Effort**: 24 hours (3 days)

---

### 4.2 Add Production-Related UI
**Missing UI for**:
- Lanes (route added, need UI components)
- Production (route added, need UI components)
- Production Plans (route added, need UI components)
- MRP (route added, need UI components)

**Implementation**:
1. **Lanes**: Create LaneBoard.tsx (Kanban-style), LaneAssignmentDialog.tsx
2. **Production**: Create ProductionLogTable.tsx, ProductionMetrics.tsx
3. **Production Plans**: Create ProductionPlanTable.tsx, ProductionPlanForm.tsx
4. **MRP**: Create MRPRunTable.tsx, PlannedOrdersTable.tsx

**Effort**: 30 hours (4 days)

---

### 4.3 Complete Project Management UI
**Missing Endpoints** (Backend):
- `/api/v1/projects/{id}/documents`
- `/api/v1/projects/{id}/bom`
- `/api/v1/rda-drawings/*`

**Frontend Implementation** (prep for when backend is ready):
1. Create `ProjectDocumentsTab.tsx`
2. Create `ProjectBOMTab.tsx`
3. Create `RDADrawingWorkflow.tsx`
4. Integrate with MinIO for file uploads
5. Write comprehensive tests

**Effort**: 16 hours (2 days)

---

**Total Phase 4**: 70 hours (9 days)

---

## Phase 5: Technical Excellence & Polish
**Duration**: 4 days | **Priority**: P2 | **Effort**: 32 hours

### 5.1 Configure PWA Properly
**File**: `frontend/vite.config.ts`

**Current State**: `vite-plugin-pwa` installed but not configured

**Implementation**:
```typescript
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Unison Manufacturing ERP',
        short_name: 'Unison',
        theme_color: '#1976d2',
        icons: [
          { src: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512x512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^\/api\/.*/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: { maxEntries: 50, maxAgeSeconds: 300 },
            },
          },
        ],
      },
    }),
  ],
})
```

**Effort**: 6 hours

---

### 5.2 Implement Error Handling Strategy
**Current State**: Inconsistent error handling across services

**Implementation**:
1. Create `AppError` class for structured errors
2. Update API client interceptor to transform errors
3. Create error boundary component
4. Add toast notifications with actual error messages
5. Remove generic "Something went wrong" messages

**Effort**: 6 hours

---

### 5.3 Validation Schema Audit
**Issue**: Zod schemas don't match API response fields

**Example**:
```typescript
// API returns:
{ material_code: "STL-304", name: "Steel", standard_cost: 125.50 }

// Frontend schema expects:
{ material_number: string, material_name: string }
```

**Implementation**:
1. Read API_DESIGN.md for all endpoint responses
2. Audit all Zod schemas against API specs
3. Fix field name mismatches
4. Add missing fields (standard_cost, reorder_point, etc.)

**Effort**: 12 hours

---

### 5.4 Naming Convention Cleanup
**Issue**: Mixing snake_case and camelCase

**Implementation**:
1. Create response transformer at API client boundary
2. Convert snake_case → camelCase automatically
3. Update all interfaces to use camelCase
4. Standardize on one convention

**Effort**: 8 hours

---

**Total Phase 5**: 32 hours (4 days)

---

## Technical Debt Fixes (from BUILD_REPORT)

### Additional Critical Fixes
1. **Console.log statements** - Remove or wrap in `import.meta.env.DEV`
   - Files: `src/lib/api-client.ts:91`, `src/components/ui/use-toast.ts:9`
   - Effort: 30 minutes

2. **Input sanitization** - Add DOMPurify
   - Files: All components displaying user content
   - Effort: 2 hours

3. **Type safety** - Replace `any` types (20+ instances)
   - Effort: 4 hours

4. **React.memo optimization** - Add to heavy components
   - Files: DataTable, forms, tables (0 components using memo currently)
   - Effort: 4 hours

5. **Error boundary** - Implement for graceful error handling
   - Effort: 2 hours

---

## Backend Prerequisites (BLOCKING)

**These backend items MUST be implemented before corresponding frontend:**

### Backend Phase 1: Onboarding (10 days)
1. Create `onboarding_progress` and `user_invitations` tables
2. Implement all 8 onboarding endpoints
3. Create `OnboardingService`
4. Create sample data generation with PGMQ

### Backend Phase 2: Production Planning & Scheduling (15 days)
1. Create database models:
   - `production_plans`
   - `schedules`
   - `scheduled_operations`
   - `planned_orders`
   - `mrp_runs`
2. Implement API endpoints:
   - `/api/v1/production-plans/*` (6 endpoints)
   - `/api/v1/schedule/gantt`
   - `/api/v1/schedule/validate`
   - `/api/v1/schedule/auto-schedule`
   - `/api/v1/mrp/*` (5 endpoints)

### Backend Phase 3: Infrastructure (8 days)
1. Enable PostgreSQL extensions: `pgmq`, `pg_search`, `pg_duckdb`, `pg_cron`
2. Set up PGMQ queues
3. Create LISTEN/NOTIFY triggers
4. Implement WebSocket `/ws` endpoint

### Backend Phase 4: Project Management (6 days)
1. Implement document endpoints: `/api/v1/projects/{id}/documents`
2. Implement BOM endpoints: `/api/v1/projects/{id}/bom`
3. Set up MinIO integration

**Total Backend Effort**: 44 days (9 weeks)

---

## Summary & Timeline

### Frontend Effort Breakdown
| Phase | Duration | Effort | Priority | Dependencies |
|-------|----------|--------|----------|--------------|
| **Phase 1: Blockers** | 2 days | 13h | P0 | None |
| **Phase 2: Quick Wins** | 1 day | 4h | P1 | Phase 1 |
| **Phase 3: High-Value** | 8 days | 61h | P1 | Phase 1 |
| **Phase 4: Complex** | 9 days | 70h | P1-P2 | Phase 1 + Backend |
| **Phase 5: Polish** | 4 days | 32h | P2 | Phase 1-3 |
| **TOTAL** | **23 days** | **176h** | - | - |

### Backend Effort (for reference)
| Phase | Duration | Effort | Priority |
|-------|----------|--------|----------|
| **Onboarding** | 10 days | 80h | P0 |
| **Production Planning** | 15 days | 120h | P0 |
| **Infrastructure** | 8 days | 64h | P0 |
| **Project Management** | 6 days | 48h | P1 |
| **TOTAL** | **44 days** | **312h** | - |

---

## Implementation Order (Bottoms Up)

### Week 1-2: Critical Path (Frontend + Backend Parallel)
- **Frontend**: Phase 1 (Blockers) + Phase 2 (Routes)
- **Backend**: Start Onboarding implementation

### Week 3-4: High-Value Features
- **Frontend**: Phase 3 (BOM, Equipment, Dashboard, Onboarding UI)
- **Backend**: Complete Onboarding + Start Production Planning

### Week 5-7: Complex Features
- **Frontend**: Phase 4 (Gantt, Production UI, Project Management)
- **Backend**: Complete Production Planning + Infrastructure

### Week 8-9: Polish & Integration
- **Frontend**: Phase 5 (PWA, Error Handling, Validation)
- **Backend**: Complete Project Management

### Week 10: Testing & Deployment
- End-to-end testing
- Performance optimization
- Production deployment

---

## Acceptance Criteria

### Phase 1 (Blockers)
- ✅ API client exists and all services compile
- ✅ Login → Dashboard → Materials list works end-to-end
- ✅ JWT token attached to requests
- ✅ RLS headers set correctly
- ✅ Single auth store (duplicate removed)
- ✅ No hardcoded tenant IDs

### Phase 2 (Routes)
- ✅ All 8 missing routes added
- ✅ Navigation menu updated
- ✅ All pages accessible via routes

### Phase 3 (High-Value)
- ✅ BOM page fully functional with tree view
- ✅ Equipment page shows machines and OEE
- ✅ Dashboard uses real API data (no mocks)
- ✅ Onboarding wizard UI complete

### Phase 4 (Complex)
- ✅ Gantt chart renders and allows drag-and-drop
- ✅ Production-related pages have functional UI
- ✅ Project management tabs complete

### Phase 5 (Polish)
- ✅ PWA installable
- ✅ Error handling consistent
- ✅ Validation schemas match API
- ✅ Naming conventions standardized

---

## Risk Assessment

### High Risk
1. **Frappe-Gantt Integration** - May not meet requirements (20-40h instead of 24h)
2. **Backend Delays** - Production planning backend may delay frontend work
3. **Multi-tenant Testing** - Hard to test without multiple organizations

### Medium Risk
1. **PWA Offline Mode** - Complex to test and debug
2. **Real-time Updates** - WebSocket implementation requires backend support
3. **MinIO Integration** - File upload/download may have edge cases

### Low Risk
1. **Route Addition** - Straightforward, low complexity
2. **BOM UI** - Components already exist, just need integration
3. **Dashboard API Integration** - Endpoints already exist

---

## Success Metrics

1. **Functionality**: All 16 PRD modules accessible via frontend
2. **Test Coverage**: Maintain 392+ passing tests, add ~200 more
3. **Performance**: < 3s initial load, < 500ms page navigation
4. **Accessibility**: WCAG 2.1 AA compliance
5. **Production Readiness**: 0 critical issues, < 5 important issues

---

## Next Steps

1. **Immediate**: Start Phase 1 (API client, utils, auth consolidation)
2. **Parallel Track**: Backend team starts onboarding implementation
3. **After Phase 1**: Add routes (Phase 2) while backend continues
4. **After Phase 2**: Start high-value features (Phase 3)
5. **Coordinate**: Sync with backend team on API availability

---

**Plan Created**: 2025-11-10
**Estimated Completion**: 2025-12-20 (6 weeks frontend + backend coordination)
**Review Date**: Every Friday for progress check
