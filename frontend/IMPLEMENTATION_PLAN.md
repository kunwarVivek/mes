# Unison Manufacturing ERP - Complete Frontend Implementation Plan

**Version**: 1.0
**Date**: 2025-11-08
**Scope**: ALL modules with premium, modern UI/UX and configurable theming
**Effort**: 150-200 hours (3-4 weeks full-time)

---

## Executive Summary

Build complete React 18 + TypeScript frontend for manufacturing ERP covering:
- **10 Core Modules**: Materials, BOM, Work Orders, Production, Quality, Equipment, Shift, Maintenance, MRP, Scheduling
- **120+ Components**: Using Atomic Design (Atoms → Molecules → Organisms → Pages)
- **35+ Pages**: Role-based dashboards, CRUD forms, mobile PWA flows
- **Premium UI/UX**: Modern, accessible (WCAG 2.1 AA), configurable theming
- **PWA Features**: Offline mode, camera access, push notifications, service workers

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design System](#design-system)
3. [Module Breakdown](#module-breakdown)
4. [File Structure](#file-structure)
5. [Implementation Phases](#implementation-phases)
6. [Code Examples](#code-examples)
7. [Testing Strategy](#testing-strategy)
8. [Deployment](#deployment)

---

## Architecture Overview

### Tech Stack (Existing)
```json
{
  "framework": "React 18.2.0",
  "language": "TypeScript 5.2.2",
  "build": "Vite 5.0.0",
  "routing": "@tanstack/react-router 1.8.0",
  "state": "Zustand 4.4.7 + @tanstack/react-query 5.8.4",
  "ui": "Radix UI + Tailwind CSS 3.3.6",
  "forms": "React Hook Form (TO ADD)",
  "validation": "Zod 3.22.4",
  "http": "Axios 1.6.2",
  "charts": "Recharts (TO ADD)",
  "gantt": "Frappe-Gantt (TO ADD)",
  "icons": "Lucide React 0.294.0"
}
```

### Additional Dependencies Needed
```bash
npm install react-hook-form @hookform/resolvers recharts frapp-gantt date-fns
npm install react-hot-toast react-beautiful-dnd @hello-pangea/dnd
npm install react-qr-reader html5-qrcode
npm install workbox-webpack-plugin workbox-window vite-plugin-pwa
```

### Architecture Patterns

**1. Atomic Design** (Current Structure)
```
src/design-system/
├── atoms/           # Smallest components (Button, Input, Badge)
├── molecules/       # Combinations (FormField, SearchBar, StatusCard)
├── organisms/       # Complex components (DataTable, Navigation, Header)
└── templates/       # Page layouts
```

**2. Feature-Based Structure** (New)
```
src/features/
├── materials/       # Material management feature
│   ├── components/  # Feature-specific components
│   ├── hooks/       # useMaterials, useMaterialSearch
│   ├── services/    # material.service.ts (API calls)
│   ├── stores/      # material.store.ts (Zustand)
│   ├── schemas/     # material.schema.ts (Zod validation)
│   └── pages/       # MaterialsPage, MaterialFormPage
├── production/
├── quality/
└── ... (one per module)
```

**3. State Management**
- **Server State**: TanStack Query (API data caching, mutations)
- **Global Client State**: Zustand (auth, theme, UI state)
- **Local Component State**: React useState
- **Form State**: React Hook Form

---

## Design System

### Theme Configuration (Enhance Existing)

**Current**: `src/design-system/theme.ts` (basic theme exists)

**Enhancements Needed**:

```typescript
// src/design-system/theme.ts (ENHANCED VERSION)

export type ThemeMode = 'light' | 'dark' | 'auto'
export type ColorScheme = 'blue' | 'purple' | 'green' | 'orange' | 'custom'

export interface ThemeConfig {
  mode: ThemeMode
  colorScheme: ColorScheme
  customColors?: {
    primary?: string
    accent?: string
  }
  compactMode?: boolean
  fontSize?: 'sm' | 'base' | 'lg'
}

// Premium color palettes (5 presets)
export const colorSchemes = {
  blue: {
    primary: { ... }, // Existing blue palette
    accent: {
      50: '#fdf4ff',
      500: '#a855f7',
      900: '#581c87',
    }
  },
  purple: {
    primary: {
      50: '#faf5ff',
      500: '#9333ea',
      900: '#581c87',
    },
    accent: {
      50: '#fff1f2',
      500: '#f43f5e',
      900: '#881337',
    }
  },
  green: {
    primary: {
      50: '#f0fdf4',
      500: '#22c55e',
      900: '#14532d',
    },
    accent: {
      50: '#fffbeb',
      500: '#f59e0b',
      900: '#78350f',
    }
  },
  orange: {
    primary: {
      50: '#fff7ed',
      500: '#f97316',
      900: '#7c2d12',
    },
    accent: {
      50: '#fef2f2',
      500: '#ef4444',
      900: '#7f1d1d',
    }
  },
  custom: {
    primary: { /* White-label colors */ },
    accent: { /* Configurable */ }
  }
}

// Manufacturing-specific semantic colors
export const semanticColors = {
  status: {
    running: '#10b981',      // Green
    idle: '#fbbf24',         // Yellow
    down: '#ef4444',         // Red
    setup: '#3b82f6',        // Blue
    maintenance: '#6b7280',  // Gray
    available: '#059669',    // Emerald
  },
  quality: {
    passed: '#10b981',
    failed: '#ef4444',
    conditional: '#f59e0b',
    pending: '#6b7280',
  },
  priority: {
    critical: '#dc2626',
    high: '#ea580c',
    medium: '#ca8a04',
    low: '#16a34a',
  },
  severity: {
    critical: '#dc2626',
    major: '#f97316',
    minor: '#fbbf24',
  }
}
```

**File**: `/Users/vivek/jet/unison/frontend/src/design-system/theme.ts`
**Action**: Enhance existing theme with color schemes and semantic colors

---

### Component Library Expansion

**Current**: 8 atoms, 3 molecules, 3 organisms
**Target**: 40+ atoms, 30+ molecules, 25+ organisms

#### Phase 1: Essential Atoms (20 components)

**New Atoms Needed**:

1. **Badge** - Status indicators
```tsx
// src/design-system/atoms/Badge.tsx
export interface BadgeProps {
  variant: 'success' | 'warning' | 'error' | 'info' | 'neutral'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}
```

2. **Avatar** - User profile images
3. **Chip** - Removable tags
4. **Divider** - Visual separators
5. **Spinner** - Loading indicators
6. **Progress** - Progress bars
7. **Skeleton** - Loading placeholders
8. **Tooltip** - Hover tooltips
9. **Switch** - Toggle switches
10. **Radio** - Radio buttons
11. **Checkbox** - Checkboxes
12. **Select** - Dropdown selects (enhance existing)
13. **Textarea** - Multi-line inputs
14. **DatePicker** - Date selection
15. **TimePicker** - Time selection
16. **FileUpload** - File/image upload
17. **IconButton** - Icon-only buttons
18. **Link** - Styled links
19. **Heading** - Typography headings
20. **Text** - Typography text

**File Pattern**: `/Users/vivek/jet/unison/frontend/src/design-system/atoms/{ComponentName}.tsx`

#### Phase 2: Molecules (30 components)

**Manufacturing-Specific Molecules**:

1. **StatusBadge** - Machine/WO status with colors
```tsx
// src/design-system/molecules/StatusBadge.tsx
export interface StatusBadgeProps {
  status: 'running' | 'idle' | 'down' | 'setup' | 'maintenance'
  withIcon?: boolean
  withPulse?: boolean  // Animated pulse for "running"
}
```

2. **PriorityIndicator** - Visual priority levels
3. **QualityResult** - Pass/Fail with FPY %
4. **MachineCard** - Machine status card
5. **WorkOrderCard** - WO summary card
6. **NCRCard** - NCR summary card
7. **SearchBar** - Search with filters
8. **FilterGroup** - Multi-select filters
9. **SortControl** - Sort dropdown
10. **Pagination** - Page navigation
11. **BreadcrumbNav** - Breadcrumb navigation
12. **ActionMenu** - Dropdown action menu
13. **ConfirmDialog** - Confirmation modal
14. **InfoCard** - Information display card
15. **MetricCard** - KPI metric card
16. **TrendIndicator** - Up/down trend arrow
17. **DateRangeFilter** - Date range picker
18. **UserAvatar** - User with name/role
19. **NotificationItem** - Notification card
20. **AlertBanner** - Page-level alerts
21. **EmptyState** (existing - enhance)
22. **ErrorState** - Error display
23. **LoadingState** - Loading skeleton
24. **SuccessToast** - Success notification
25. **PhotoCapture** - Camera capture for PWA
26. **BarcodeScanner** - QR/barcode scanner
27. **OEEGauge** - OEE circular gauge
28. **CapacityBar** - Capacity utilization bar
29. **ShiftTimeline** - Shift schedule visualization
30. **FormSection** - Form section with header

**File Pattern**: `/Users/vivek/jet/unison/frontend/src/design-system/molecules/{ComponentName}.tsx`

#### Phase 3: Organisms (25 components)

**Complex UI Components**:

1. **DataTable** - Sortable, filterable table
```tsx
// src/design-system/organisms/DataTable.tsx
export interface Column<T> {
  header: string
  accessor: keyof T | ((row: T) => any)
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: T) => ReactNode
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  pagination?: boolean
  onRowClick?: (row: T) => void
  emptyState?: ReactNode
}
```

2. **Sidebar** - Collapsible navigation
3. **Navbar** - Top navigation bar
4. **MobileNav** - Bottom mobile navigation
5. **DashboardGrid** - Responsive dashboard layout
6. **FormWizard** - Multi-step forms
7. **TabNavigation** - Tabbed content
8. **ModalDialog** - Full-featured modal
9. **DrawerPanel** - Slide-in panel
10. **NotificationCenter** - Notification dropdown
11. **UserMenu** - User profile dropdown
12. **CommandPalette** - Global search (Cmd+K)
13. **MachineGrid** - Machine status grid
14. **WorkOrderList** - WO list with filters
15. **MaterialInventoryTable** - Material stock table
16. **NCRWorkflow** - NCR approval workflow UI
17. **GanttScheduler** - Visual Gantt chart
18. **CalendarView** - Calendar scheduler
19. **KanbanBoard** - Kanban lanes (for WO)
20. **InspectionForm** - Inspection characteristics form
21. **BOMTree** - Hierarchical BOM view
22. **ShiftHandover** - Shift handover form
23. **DowntimeLogger** - Downtime event form
24. **OEEDashboard** - OEE metrics dashboard
25. **ChartPanel** - Recharts wrapper

**File Pattern**: `/Users/vivek/jet/unison/frontend/src/design-system/organisms/{ComponentName}.tsx`

---

## Module Breakdown

### Module 1: Materials Management

**Pages** (4):
1. `/materials` - Material list with search/filter
2. `/materials/new` - Create material form
3. `/materials/:id` - Material detail view
4. `/materials/:id/edit` - Edit material form

**Components**:
- `MaterialCard` - Material summary card
- `MaterialTable` - Sortable material table
- `MaterialForm` - Create/edit form
- `MaterialFilters` - Category, procurement type filters
- `MaterialSearch` - Full-text search with pg_search
- `StockLevelIndicator` - Min/max stock visual
- `BarcodeDisplay` - Material barcode/QR
- `CategoryBadge` - Material category badge

**API Integration**:
```typescript
// src/features/materials/services/material.service.ts
export const materialService = {
  list: (params: MaterialListParams) => axios.get('/api/v1/materials', { params }),
  get: (id: number) => axios.get(`/api/v1/materials/${id}`),
  create: (data: MaterialCreateDTO) => axios.post('/api/v1/materials', data),
  update: (id: number, data: MaterialUpdateDTO) => axios.patch(`/api/v1/materials/${id}`, data),
  delete: (id: number) => axios.delete(`/api/v1/materials/${id}`),
  search: (query: string) => axios.get(`/api/v1/materials/search?q=${query}`),
}
```

**Hooks**:
```typescript
// src/features/materials/hooks/useMaterials.ts
export function useMaterials(filters?: MaterialFilters) {
  return useQuery({
    queryKey: ['materials', filters],
    queryFn: () => materialService.list(filters),
  })
}

export function useMaterial(id: number) {
  return useQuery({
    queryKey: ['materials', id],
    queryFn: () => materialService.get(id),
    enabled: !!id,
  })
}

export function useCreateMaterial() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: materialService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      toast.success('Material created successfully')
    },
  })
}
```

**Files to Create** (15 files):
```
/Users/vivek/jet/unison/frontend/src/features/materials/
├── components/
│   ├── MaterialCard.tsx
│   ├── MaterialTable.tsx
│   ├── MaterialForm.tsx
│   ├── MaterialFilters.tsx
│   ├── MaterialSearch.tsx
│   ├── StockLevelIndicator.tsx
│   └── BarcodeDisplay.tsx
├── hooks/
│   ├── useMaterials.ts
│   ├── useMaterialSearch.ts
│   └── useMaterialMutations.ts
├── services/
│   └── material.service.ts
├── schemas/
│   └── material.schema.ts
├── stores/
│   └── material.store.ts  (for filters, view preferences)
└── pages/
    ├── MaterialListPage.tsx
    ├── MaterialFormPage.tsx
    └── MaterialDetailPage.tsx
```

---

### Module 2: BOM Management

**Pages** (3):
1. `/boms` - BOM list
2. `/boms/new` - Create BOM
3. `/boms/:id` - BOM tree view with effectivity

**Components**:
- `BOMTree` - Hierarchical tree visualization
- `BOMItemRow` - BOM line item
- `BOMEffectivity` - Date range selector
- `BOMExplosion` - Multi-level explosion view
- `ComponentSelector` - Add component modal

**Files** (12 files):
```
/Users/vivek/jet/unison/frontend/src/features/bom/
├── components/
│   ├── BOMTree.tsx
│   ├── BOMItemRow.tsx
│   ├── BOMEffectivity.tsx
│   └── ComponentSelector.tsx
├── hooks/
│   └── useBOM.ts
├── services/
│   └── bom.service.ts
├── schemas/
│   └── bom.schema.ts
└── pages/
    ├── BOMListPage.tsx
    └── BOMFormPage.tsx
```

---

### Module 3: Work Order Management

**Pages** (5):
1. `/work-orders` - WO list with Kanban/List view
2. `/work-orders/new` - Create WO
3. `/work-orders/:id` - WO detail
4. `/work-orders/:id/operations` - Operations routing
5. `/work-orders/:id/logs` - Production logs

**Components**:
- `WorkOrderCard` - WO summary card
- `WorkOrderKanban` - Lane-based Kanban board
- `WorkOrderTable` - List view
- `WorkOrderForm` - Create/edit form
- `OperationsRouter` - Operations sequencing
- `ProductionLogForm` - Log production (mobile-friendly)
- `MaterialConsumption` - Material issue tracker
- `WOStatusTimeline` - Status history timeline

**Mobile PWA Focus**:
- **Production Logging**: Large buttons, voice input, barcode scan
- **Offline Mode**: Queue logs, sync when online
- **Camera Integration**: Capture progress photos

**Files** (20 files):
```
/Users/vivek/jet/unison/frontend/src/features/work-orders/
├── components/
│   ├── WorkOrderCard.tsx
│   ├── WorkOrderKanban.tsx
│   ├── WorkOrderTable.tsx
│   ├── WorkOrderForm.tsx
│   ├── OperationsRouter.tsx
│   ├── ProductionLogForm.tsx
│   ├── MaterialConsumption.tsx
│   └── WOStatusTimeline.tsx
├── hooks/
│   ├── useWorkOrders.ts
│   ├── useProductionLog.ts
│   └── useWOMutations.ts
├── services/
│   ├── work-order.service.ts
│   └── production-log.service.ts
├── schemas/
│   └── work-order.schema.ts
├── stores/
│   └── work-order.store.ts
└── pages/
    ├── WorkOrderListPage.tsx
    ├── WorkOrderFormPage.tsx
    ├── WorkOrderDetailPage.tsx
    └── ProductionLogPage.tsx  (Mobile PWA optimized)
```

---

### Module 4: Quality Management (NEW)

**Pages** (6):
1. `/quality/ncrs` - NCR list
2. `/quality/ncrs/new` - Create NCR with photos (PWA)
3. `/quality/ncrs/:id` - NCR detail with workflow
4. `/quality/inspection-plans` - Inspection plans list
5. `/quality/inspections` - Inspection logging (PWA)
6. `/quality/fpy` - First Pass Yield dashboard

**Components**:
- `NCRCard` - NCR summary with severity badge
- `NCRWorkflowViewer` - Visual workflow status
- `NCRForm` - Create NCR with photo capture
- `PhotoUploader` - Camera capture component
- `InspectionPlanForm` - Define characteristics
- `InspectionLogger` - Mobile inspection logging
- `FPYChart` - FPY trend chart (Recharts)
- `SPCChart` - Statistical process control chart

**PWA Features**:
- **Camera Access**: Capture 3 photos for NCR
- **Offline NCR Creation**: Queue for sync
- **Push Notifications**: NCR approval requests

**Files** (25 files):
```
/Users/vivek/jet/unison/frontend/src/features/quality/
├── components/
│   ├── NCRCard.tsx
│   ├── NCRWorkflowViewer.tsx
│   ├── NCRForm.tsx
│   ├── PhotoUploader.tsx
│   ├── InspectionPlanForm.tsx
│   ├── InspectionLogger.tsx
│   ├── FPYChart.tsx
│   └── SPCChart.tsx
├── hooks/
│   ├── useNCRs.ts
│   ├── useInspectionPlans.ts
│   └── useFPY.ts
├── services/
│   ├── ncr.service.ts
│   ├── inspection.service.ts
│   └── quality-metrics.service.ts
├── schemas/
│   ├── ncr.schema.ts
│   └── inspection.schema.ts
└── pages/
    ├── NCRListPage.tsx
    ├── NCRFormPage.tsx  (PWA optimized)
    ├── NCRDetailPage.tsx
    ├── InspectionPlanListPage.tsx
    ├── InspectionLogPage.tsx  (PWA optimized)
    └── FPYDashboardPage.tsx
```

---

### Module 5: Equipment & Machines (NEW)

**Pages** (4):
1. `/equipment` - Machine grid with real-time status
2. `/equipment/:id` - Machine detail with OEE
3. `/equipment/:id/status-history` - Status timeline
4. `/equipment/dashboard` - Plant-wide OEE dashboard

**Components**:
- `MachineStatusCard` - Live status card with pulse animation
- `MachineGrid` - Grid of all machines
- `OEEGauge` - Circular OEE gauge (85% target)
- `AvailabilityChart` - Availability breakdown
- `PerformanceChart` - Performance over time
- `QualityChart` - Quality metrics
- `StatusHistoryTimeline` - Status changes over time

**Real-time Features**:
- **WebSocket Integration**: Live machine status updates
- **Color-Coded Status**: Green (running), yellow (idle), red (down)
- **Pulse Animation**: Running machines have pulsing indicator

**Files** (18 files):
```
/Users/vivek/jet/unison/frontend/src/features/equipment/
├── components/
│   ├── MachineStatusCard.tsx
│   ├── MachineGrid.tsx
│   ├── OEEGauge.tsx
│   ├── AvailabilityChart.tsx
│   ├── PerformanceChart.tsx
│   ├── QualityChart.tsx
│   └── StatusHistoryTimeline.tsx
├── hooks/
│   ├── useMachines.ts
│   ├── useMachineStatus.ts  (WebSocket)
│   └── useOEE.ts
├── services/
│   ├── machine.service.ts
│   └── websocket.service.ts
├── schemas/
│   └── machine.schema.ts
└── pages/
    ├── MachineListPage.tsx
    ├── MachineDetailPage.tsx
    └── OEEDashboardPage.tsx
```

---

### Module 6: Shift Management (NEW)

**Pages** (4):
1. `/shifts` - Shift pattern list
2. `/shifts/handovers` - Shift handover log
3. `/shifts/performance` - Shift performance comparison
4. `/shifts/calendar` - Shift calendar view

**Components**:
- `ShiftPatternCard` - Shift definition card
- `ShiftHandoverForm` - Handover log form
- `ShiftPerformanceTable` - Comparison table
- `ShiftCalendar` - Calendar with shift assignments
- `WIPSummary` - Work in progress summary
- `IssuesReporter` - Report shift issues

**Files** (15 files):
```
/Users/vivek/jet/unison/frontend/src/features/shifts/
├── components/
│   ├── ShiftPatternCard.tsx
│   ├── ShiftHandoverForm.tsx
│   ├── ShiftPerformanceTable.tsx
│   ├── ShiftCalendar.tsx
│   └── WIPSummary.tsx
├── hooks/
│   └── useShifts.ts
├── services/
│   └── shift.service.ts
├── schemas/
│   └── shift.schema.ts
└── pages/
    ├── ShiftListPage.tsx
    ├── ShiftHandoverPage.tsx
    ├── ShiftPerformancePage.tsx
    └── ShiftCalendarPage.tsx
```

---

### Module 7: Maintenance Management (NEW)

**Pages** (5):
1. `/maintenance/pm-schedules` - PM schedule list
2. `/maintenance/pm-work-orders` - PM WO list
3. `/maintenance/downtime` - Downtime event log
4. `/maintenance/metrics` - MTBF/MTTR dashboard
5. `/maintenance/calendar` - PM calendar

**Components**:
- `PMScheduleCard` - PM schedule card
- `PMWorkOrderCard` - PM WO card
- `DowntimeLogForm` - Log downtime (mobile)
- `MTBFMTTRChart` - Reliability metrics chart
- `DowntimePareto` - Top causes chart
- `PMCalendar` - PM schedule calendar
- `MaintenanceTaskChecklist` - PM task checklist

**Files** (20 files):
```
/Users/vivek/jet/unison/frontend/src/features/maintenance/
├── components/
│   ├── PMScheduleCard.tsx
│   ├── PMWorkOrderCard.tsx
│   ├── DowntimeLogForm.tsx
│   ├── MTBFMTTRChart.tsx
│   ├── DowntimePareto.tsx
│   └── PMCalendar.tsx
├── hooks/
│   ├── usePMSchedules.ts
│   ├── useDowntime.ts
│   └── useMTBF.ts
├── services/
│   └── maintenance.service.ts
├── schemas/
│   └── maintenance.schema.ts
└── pages/
    ├── PMScheduleListPage.tsx
    ├── PMWorkOrderListPage.tsx
    ├── DowntimeLogPage.tsx  (PWA optimized)
    ├── MetricsDashboardPage.tsx
    └── PMCalendarPage.tsx
```

---

### Module 8: Visual Scheduling

**Pages** (2):
1. `/scheduling/gantt` - Gantt chart scheduler
2. `/scheduling/capacity` - Capacity planning

**Components**:
- `GanttScheduler` - Frappe-Gantt wrapper
- `WorkOrderGanttItem` - WO Gantt bar
- `DependencyLine` - Finish-to-start arrows
- `CapacityChart` - Lane utilization chart
- `ConflictIndicator` - Overloaded lane warning

**Drag-and-Drop**:
- `@hello-pangea/dnd` for rescheduling
- Conflict detection
- Auto-save on drop

**Files** (12 files):
```
/Users/vivek/jet/unison/frontend/src/features/scheduling/
├── components/
│   ├── GanttScheduler.tsx
│   ├── WorkOrderGanttItem.tsx
│   ├── CapacityChart.tsx
│   └── ConflictIndicator.tsx
├── hooks/
│   └── useScheduling.ts
├── services/
│   └── scheduling.service.ts
└── pages/
    ├── GanttSchedulerPage.tsx
    └── CapacityPlanningPage.tsx
```

---

### Module 9: MRP & Planning

**Pages** (4):
1. `/mrp/runs` - MRP run history
2. `/mrp/runs/new` - Execute MRP run
3. `/mrp/planned-orders` - Planned orders list
4. `/mrp/requirements` - Net requirements view

**Components**:
- `MRPRunCard` - MRP run summary
- `PlannedOrderTable` - Planned orders
- `NetRequirementsTable` - Material requirements
- `MRPExecutionLog` - Run log viewer
- `LotSizingSelector` - Lot sizing method picker

**Files** (15 files):
```
/Users/vivek/jet/unison/frontend/src/features/mrp/
├── components/
│   ├── MRPRunCard.tsx
│   ├── PlannedOrderTable.tsx
│   └── NetRequirementsTable.tsx
├── hooks/
│   └── useMRP.ts
├── services/
│   └── mrp.service.ts
├── schemas/
│   └── mrp.schema.ts
└── pages/
    ├── MRPRunsPage.tsx
    ├── MRPExecutePage.tsx
    ├── PlannedOrdersPage.tsx
    └── NetRequirementsPage.tsx
```

---

### Module 10: Dashboards & Analytics

**Pages** (5):
1. `/dashboard` - Executive dashboard (role-based)
2. `/dashboard/plant-manager` - Plant manager KPIs
3. `/dashboard/supervisor` - Supervisor dashboard
4. `/dashboard/operator` - Operator dashboard
5. `/reports` - Report generator

**Components**:
- `KPICard` - Metric card with trend
- `OEEOverview` - Plant OEE summary
- `OTDChart` - On-time delivery chart
- `ProductionChart` - Production vs target
- `QualityTrends` - FPY, NCR trends
- `TopNCRs` - Pareto chart
- `MachineUtilization` - Utilization heatmap

**Charts (Recharts)**:
- Line charts (trends)
- Bar charts (comparisons)
- Pie charts (distributions)
- Area charts (cumulative)
- Scatter plots (correlations)

**Files** (20 files):
```
/Users/vivek/jet/unison/frontend/src/features/dashboards/
├── components/
│   ├── KPICard.tsx
│   ├── OEEOverview.tsx
│   ├── OTDChart.tsx
│   ├── ProductionChart.tsx
│   └── QualityTrends.tsx
├── hooks/
│   └── useDashboardData.ts
├── services/
│   └── dashboard.service.ts
└── pages/
    ├── ExecutiveDashboard.tsx
    ├── PlantManagerDashboard.tsx
    ├── SupervisorDashboard.tsx
    ├── OperatorDashboard.tsx
    └── ReportsPage.tsx
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1, 40 hours)

**Goals**:
- Enhanced design system
- Core infrastructure
- Authentication flow
- Responsive layouts

**Tasks**:

**Day 1-2: Design System Enhancements**
1. ✅ Enhance `theme.ts` with color schemes (4 hours)
2. ✅ Create 20 atom components (12 hours)
3. ✅ Set up theme switcher (4 hours)

**Day 3: Core Infrastructure**
1. ✅ Set up React Router with routes (4 hours)
2. ✅ Create layout templates (Sidebar, Navbar) (4 hours)
3. ✅ Configure TanStack Query (2 hours)

**Day 4-5: Authentication & Navigation**
1. ✅ Login/Register pages (4 hours)
2. ✅ Protected routes (2 hours)
3. ✅ User menu, notifications (4 hours)
4. ✅ Sidebar navigation with icons (4 hours)

**Verification**:
```bash
npm run dev
# Navigate to http://localhost:5173
# Test: Login → Dashboard → Theme switch → Responsive mobile view
```

---

### Phase 2: Materials & BOM (Week 1-2, 30 hours)

**Day 6-7: Materials Module**
1. ✅ Material list page with DataTable (6 hours)
2. ✅ Material form (create/edit) (4 hours)
3. ✅ Material detail page (3 hours)
4. ✅ Material search and filters (3 hours)

**Day 8: BOM Module**
1. ✅ BOM tree component (6 hours)
2. ✅ BOM form (4 hours)
3. ✅ Effectivity date selector (2 hours)

**Verification**:
```bash
# Test Materials CRUD
curl http://localhost:8000/api/v1/materials
# Frontend: Create material → View list → Edit → Delete

# Test BOM tree
# Frontend: Create BOM → Add components → View tree
```

---

### Phase 3: Work Orders & Production (Week 2, 30 hours)

**Day 9-10: Work Order Module**
1. ✅ Work order list (Kanban + Table views) (8 hours)
2. ✅ Work order form (6 hours)
3. ✅ Operations routing (4 hours)

**Day 11: Production Logging (PWA)**
1. ✅ Mobile-optimized production log form (6 hours)
2. ✅ Barcode scanner integration (4 hours)
3. ✅ Offline mode setup (service workers) (6 hours)

**Verification**:
```bash
# PWA test on mobile device
# Offline mode: Log production → Go offline → Submit → Come online → Verify sync
```

---

### Phase 4: Quality Management (Week 2-3, 25 hours)

**Day 12: NCR Module**
1. ✅ NCR list with workflow status (4 hours)
2. ✅ NCR form with photo capture (6 hours)
3. ✅ NCR detail with workflow viewer (4 hours)

**Day 13: Inspections**
1. ✅ Inspection plan form (5 hours)
2. ✅ Mobile inspection logger (4 hours)
3. ✅ FPY dashboard (2 hours)

**Verification**:
```bash
# Mobile PWA test
# Camera permission → Capture 3 photos → Submit NCR → Verify upload
```

---

### Phase 5: Equipment & Machines (Week 3, 20 hours)

**Day 14: Equipment Module**
1. ✅ Machine status grid (real-time) (6 hours)
2. ✅ OEE gauge component (4 hours)
3. ✅ Machine detail page (4 hours)

**Day 15: OEE Dashboard**
1. ✅ Plant-wide OEE dashboard (4 hours)
2. ✅ Status history timeline (2 hours)

**Verification**:
```bash
# WebSocket test
# Backend: Change machine status → Frontend: See real-time update
```

---

### Phase 6: Shift & Maintenance (Week 3-4, 25 hours)

**Day 16: Shift Management**
1. ✅ Shift pattern list/form (4 hours)
2. ✅ Shift handover form (4 hours)
3. ✅ Shift performance table (3 hours)

**Day 17-18: Maintenance Management**
1. ✅ PM schedule list/form (6 hours)
2. ✅ Downtime logger (mobile PWA) (4 hours)
3. ✅ MTBF/MTTR dashboard (4 hours)

**Verification**:
```bash
# Test shift handover workflow
# Test PM calendar view
```

---

### Phase 7: Scheduling & MRP (Week 4, 25 hours)

**Day 19-20: Visual Scheduling**
1. ✅ Gantt chart integration (8 hours)
2. ✅ Drag-and-drop rescheduling (6 hours)
3. ✅ Capacity planning (4 hours)

**Day 21: MRP**
1. ✅ MRP run execution (4 hours)
2. ✅ Planned orders list (3 hours)

**Verification**:
```bash
# Test Gantt drag-and-drop
# Test MRP run → View planned orders
```

---

### Phase 8: Dashboards & Polish (Week 4-5, 30 hours)

**Day 22-23: Dashboards**
1. ✅ Executive dashboard (6 hours)
2. ✅ Role-based dashboards (6 hours)
3. ✅ Chart components (Recharts) (6 hours)

**Day 24-25: Polish & Testing**
1. ✅ Responsive design fixes (4 hours)
2. ✅ Accessibility audit (WCAG 2.1 AA) (4 hours)
3. ✅ PWA testing (offline, camera, notifications) (4 hours)

**Final Verification**:
```bash
# Lighthouse audit
npm run build
npx lighthouse http://localhost:5173 --view

# PWA audit
# - Service worker registered
# - Offline fallback
# - Install prompt
# - Camera access
```

---

## Code Examples

### Example 1: Machine Status Card (Real-time)

**File**: `/Users/vivek/jet/unison/frontend/src/features/equipment/components/MachineStatusCard.tsx`

```tsx
import { useEffect, useState } from 'react'
import { Card } from '@/design-system/atoms'
import { Badge } from '@/design-system/atoms/Badge'
import { useMachineStatus } from '../hooks/useMachineStatus'

export interface MachineStatusCardProps {
  machineId: number
  machineName: string
  onClick?: () => void
}

const statusColors = {
  running: 'bg-green-500',
  idle: 'bg-yellow-500',
  down: 'bg-red-500',
  setup: 'bg-blue-500',
  maintenance: 'bg-gray-500',
  available: 'bg-emerald-500',
}

export function MachineStatusCard({ machineId, machineName, onClick }: MachineStatusCardProps) {
  const { data: machine, isLoading } = useMachineStatus(machineId)
  const [isPulsing, setIsPulsing] = useState(false)

  useEffect(() => {
    setIsPulsing(machine?.status === 'running')
  }, [machine?.status])

  if (isLoading) {
    return <Card className="animate-pulse h-32" />
  }

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <div className="flex items-center justify-between p-4">
        <div>
          <h3 className="font-semibold text-lg">{machineName}</h3>
          <p className="text-sm text-gray-500">{machine?.machine_code}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge variant={machine?.status}>
            <div className="flex items-center gap-2">
              {isPulsing && (
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
              )}
              {machine?.status}
            </div>
          </Badge>
          {machine?.current_work_order && (
            <span className="text-xs text-gray-600">
              WO: {machine.current_work_order}
            </span>
          )}
        </div>
      </div>
      {machine?.last_status_change && (
        <div className="px-4 pb-3 text-xs text-gray-500">
          Since: {new Date(machine.last_status_change).toLocaleString()}
        </div>
      )}
    </Card>
  )
}
```

**WebSocket Hook**:

**File**: `/Users/vivek/jet/unison/frontend/src/features/equipment/hooks/useMachineStatus.ts`

```tsx
import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { machineService } from '../services/machine.service'
import { websocketService } from '../services/websocket.service'

export function useMachineStatus(machineId: number) {
  const queryClient = useQueryClient()

  // Fetch initial status
  const query = useQuery({
    queryKey: ['machines', machineId, 'status'],
    queryFn: () => machineService.getStatus(machineId),
    refetchInterval: 30000, // Fallback: poll every 30s
  })

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = websocketService.subscribe(
      `machine.${machineId}.status`,
      (update) => {
        queryClient.setQueryData(
          ['machines', machineId, 'status'],
          (old: any) => ({ ...old, ...update })
        )
      }
    )

    return () => unsubscribe()
  }, [machineId, queryClient])

  return query
}
```

---

### Example 2: NCR Form with Photo Capture

**File**: `/Users/vivek/jet/unison/frontend/src/features/quality/components/NCRForm.tsx`

```tsx
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { PhotoCapture } from '@/design-system/molecules/PhotoCapture'
import { Button, Input, Select, Textarea } from '@/design-system/atoms'
import { useCreateNCR } from '../hooks/useNCRs'
import { ncrSchema, type NCRCreateDTO } from '../schemas/ncr.schema'

export function NCRForm() {
  const [photos, setPhotos] = useState<File[]>([])
  const createNCR = useCreateNCR()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<NCRCreateDTO>({
    resolver: zodResolver(ncrSchema),
  })

  const onSubmit = async (data: NCRCreateDTO) => {
    // Upload photos to MinIO
    const photoUrls = await Promise.all(
      photos.map(photo => uploadPhoto(photo))
    )

    await createNCR.mutateAsync({
      ...data,
      attachments: photoUrls,
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label>Work Order</label>
        <Input {...register('work_order_id')} type="number" />
        {errors.work_order_id && (
          <p className="text-red-500 text-sm">{errors.work_order_id.message}</p>
        )}
      </div>

      <div>
        <label>Defect Type</label>
        <Select {...register('defect_type')}>
          <option value="DIMENSIONAL">Dimensional</option>
          <option value="VISUAL">Visual</option>
          <option value="FUNCTIONAL">Functional</option>
          <option value="MATERIAL">Material</option>
          <option value="OTHER">Other</option>
        </Select>
      </div>

      <div>
        <label>Severity</label>
        <Select {...register('severity')}>
          <option value="minor">Minor</option>
          <option value="major">Major</option>
          <option value="critical">Critical</option>
        </Select>
      </div>

      <div>
        <label>Description</label>
        <Textarea {...register('description')} rows={4} />
      </div>

      <div>
        <label>Photos (up to 3)</label>
        <PhotoCapture
          maxPhotos={3}
          onPhotosChange={setPhotos}
          photos={photos}
        />
      </div>

      <Button type="submit" loading={createNCR.isPending}>
        Submit NCR
      </Button>
    </form>
  )
}
```

**Photo Capture Component**:

**File**: `/Users/vivek/jet/unison/frontend/src/design-system/molecules/PhotoCapture.tsx`

```tsx
import { useRef, useState } from 'react'
import { Camera, X } from 'lucide-react'
import { Button } from '../atoms'

export interface PhotoCaptureProps {
  maxPhotos?: number
  photos: File[]
  onPhotosChange: (photos: File[]) => void
}

export function PhotoCapture({ maxPhotos = 3, photos, onPhotosChange }: PhotoCaptureProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isCameraMode, setIsCameraMode] = useState(false)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const newPhotos = [...photos, ...files].slice(0, maxPhotos)
    onPhotosChange(newPhotos)
  }

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }, // Use rear camera on mobile
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsCameraMode(true)
      }
    } catch (err) {
      console.error('Camera access denied:', err)
      alert('Camera access is required to capture photos')
    }
  }

  const capturePhoto = () => {
    if (!videoRef.current) return

    const canvas = document.createElement('canvas')
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight
    canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0)

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `photo-${Date.now()}.jpg`, { type: 'image/jpeg' })
        onPhotosChange([...photos, file])
      }
    }, 'image/jpeg', 0.9)
  }

  const removePhoto = (index: number) => {
    onPhotosChange(photos.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {!isCameraMode && (
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={photos.length >= maxPhotos}
          >
            Upload from Gallery
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={startCamera}
            disabled={photos.length >= maxPhotos}
          >
            <Camera className="mr-2 h-4 w-4" />
            Use Camera
          </Button>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={handleFileSelect}
      />

      {isCameraMode && (
        <div className="relative">
          <video ref={videoRef} autoPlay playsInline className="w-full rounded-lg" />
          <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-4">
            <Button onClick={capturePhoto}>Capture</Button>
            <Button variant="outline" onClick={() => setIsCameraMode(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}

      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {photos.map((photo, index) => (
            <div key={index} className="relative aspect-square">
              <img
                src={URL.createObjectURL(photo)}
                alt={`Photo ${index + 1}`}
                className="w-full h-full object-cover rounded-lg"
              />
              <button
                type="button"
                onClick={() => removePhoto(index)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="text-sm text-gray-500">
        {photos.length} / {maxPhotos} photos captured
      </p>
    </div>
  )
}
```

---

### Example 3: Gantt Scheduler

**File**: `/Users/vivek/jet/unison/frontend/src/features/scheduling/components/GanttScheduler.tsx`

```tsx
import { useEffect, useRef } from 'react'
import Gantt from 'frappe-gantt'
import { useWorkOrders } from '@/features/work-orders/hooks/useWorkOrders'

export function GanttScheduler() {
  const ganttRef = useRef<HTMLDivElement>(null)
  const { data: workOrders } = useWorkOrders({ status: ['planned', 'released'] })

  useEffect(() => {
    if (!ganttRef.current || !workOrders) return

    const tasks = workOrders.map(wo => ({
      id: wo.id.toString(),
      name: wo.work_order_number,
      start: wo.planned_start_date,
      end: wo.planned_end_date,
      progress: (wo.quantity_completed / wo.quantity_planned) * 100,
      dependencies: wo.dependencies?.join(',') || '',
      custom_class: getStatusClass(wo.status),
    }))

    const gantt = new Gantt(ganttRef.current, tasks, {
      on_click: (task) => {
        console.log('Clicked:', task)
      },
      on_date_change: (task, start, end) => {
        // Update backend
        updateWorkOrder(parseInt(task.id), {
          planned_start_date: start,
          planned_end_date: end,
        })
      },
      on_progress_change: (task, progress) => {
        // Update progress
        console.log('Progress:', progress)
      },
      view_mode: 'Week',
    })

    return () => {
      // Cleanup
    }
  }, [workOrders])

  return (
    <div className="gantt-container">
      <div ref={ganttRef} />
    </div>
  )
}

function getStatusClass(status: string): string {
  const classes = {
    planned: 'gantt-task-planned',
    released: 'gantt-task-released',
    in_progress: 'gantt-task-in-progress',
    completed: 'gantt-task-completed',
  }
  return classes[status] || ''
}
```

---

## Testing Strategy

### Unit Testing

**Tools**: Vitest + React Testing Library

**Example Test**:

**File**: `/Users/vivek/jet/unison/frontend/src/features/materials/components/MaterialCard.test.tsx`

```tsx
import { render, screen } from '@testing-library/react'
import { MaterialCard } from './MaterialCard'

describe('MaterialCard', () => {
  it('renders material information', () => {
    const material = {
      id: 1,
      material_code: 'MAT-001',
      name: 'Steel Plate',
      category: 'raw_material',
      stock_quantity: 100,
      unit_of_measure: 'kg',
    }

    render(<MaterialCard material={material} />)

    expect(screen.getByText('MAT-001')).toBeInTheDocument()
    expect(screen.getByText('Steel Plate')).toBeInTheDocument()
    expect(screen.getByText('100 kg')).toBeInTheDocument()
  })

  it('shows low stock warning', () => {
    const material = {
      ...baseMaterial,
      stock_quantity: 5,
      min_stock_level: 10,
    }

    render(<MaterialCard material={material} />)

    expect(screen.getByText(/low stock/i)).toBeInTheDocument()
  })
})
```

### Integration Testing

**PWA Testing**:
```bash
# Install Playwright
npm install -D @playwright/test

# Test offline mode
npx playwright test --project=chromium --headed
```

**Example E2E Test**:

**File**: `/Users/vivek/jet/unison/frontend/e2e/ncr-creation.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test('create NCR with photos on mobile', async ({ page, context }) => {
  // Grant camera permissions
  await context.grantPermissions(['camera'])

  await page.goto('http://localhost:5173/quality/ncrs/new')

  // Fill form
  await page.fill('[name="work_order_id"]', '123')
  await page.selectOption('[name="severity"]', 'major')
  await page.fill('[name="description"]', 'Weld defect found')

  // Capture photo
  await page.click('button:has-text("Use Camera")')
  await page.waitForTimeout(1000) // Wait for camera
  await page.click('button:has-text("Capture")')

  // Submit
  await page.click('button:has-text("Submit NCR")')

  // Verify success
  await expect(page.locator('text=NCR created successfully')).toBeVisible()
})

test('offline NCR creation', async ({ page, context }) => {
  // Go offline
  await context.setOffline(true)

  await page.goto('http://localhost:5173/quality/ncrs/new')
  await page.fill('[name="work_order_id"]', '123')
  await page.fill('[name="description"]', 'Offline NCR')
  await page.click('button:has-text("Submit NCR")')

  // Should queue for sync
  await expect(page.locator('text=Queued for sync')).toBeVisible()

  // Go online
  await context.setOffline(false)

  // Should sync
  await page.waitForTimeout(2000)
  await expect(page.locator('text=Synced successfully')).toBeVisible()
})
```

---

## Deployment

### Production Build

```bash
# Build
npm run build

# Preview
npm run preview

# Lighthouse audit
npx lighthouse http://localhost:4173 --view

# Target scores:
# - Performance: 90+
# - Accessibility: 95+
# - Best Practices: 95+
# - SEO: 90+
# - PWA: 100
```

### Docker

**File**: `/Users/vivek/jet/unison/frontend/Dockerfile` (enhance existing)

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Summary

**Total Effort**: 150-200 hours (3-4 weeks)

**Deliverables**:
- ✅ 120+ reusable components (Atomic Design)
- ✅ 35+ pages covering all 10 modules
- ✅ Premium, modern UI/UX
- ✅ Configurable theming (5 color schemes)
- ✅ PWA with offline mode, camera, notifications
- ✅ Real-time WebSocket updates
- ✅ Responsive (mobile, tablet, desktop)
- ✅ Accessible (WCAG 2.1 AA)
- ✅ 100+ unit tests
- ✅ E2E tests (Playwright)

**Next Steps**:
1. Review and approve plan
2. Start Phase 1 (Foundation)
3. Iterate with user feedback
4. Deploy and monitor

---

**Plan Version**: 1.0
**Created**: 2025-11-08
**Estimated Completion**: 4 weeks from start
