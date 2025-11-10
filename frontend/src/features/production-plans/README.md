# Production Plans Module Quick Start Guide

## Overview
Production Plans module for managing production schedules and material requirements over time periods.

## Module Structure
```
production-plans/
├── types/productionPlan.types.ts      - TypeScript definitions
├── schemas/productionPlan.schema.ts   - Zod validation
├── services/productionPlan.service.ts - API client
├── hooks/                             - TanStack Query hooks
│   ├── useProductionPlans.ts         - List query
│   ├── useProductionPlan.ts          - Single query
│   ├── useCreateProductionPlan.ts    - Create mutation
│   ├── useUpdateProductionPlan.ts    - Update mutation
│   └── useDeleteProductionPlan.ts    - Delete mutation
└── __tests__/                         - Test files (14 passing)
```

## Usage Examples

### List Production Plans
```typescript
import { useProductionPlans } from '@/features/production-plans'

function ProductionPlanList() {
  const { data, isLoading } = useProductionPlans({
    status: 'APPROVED',
    start_date: '2024-01-01',
    page: 1,
    page_size: 20,
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      {data?.items.map(plan => (
        <div key={plan.id}>
          {plan.plan_name} ({plan.status})
        </div>
      ))}
    </div>
  )
}
```

### Create Production Plan
```typescript
import { useCreateProductionPlan } from '@/features/production-plans'

function CreatePlanForm() {
  const createPlan = useCreateProductionPlan()

  const handleSubmit = (data: CreateProductionPlanDTO) => {
    createPlan.mutate(data, {
      onSuccess: () => console.log('Plan created!'),
      onError: (error) => console.error(error),
    })
  }

  return <form onSubmit={handleSubmit}>...</form>
}
```

### Get Single Plan with Items
```typescript
import { useProductionPlan } from '@/features/production-plans'

function PlanDetail({ id }: { id: number }) {
  const { data: plan, isLoading } = useProductionPlan(id)

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      <h1>{plan?.plan_name}</h1>
      <p>Status: {plan?.status}</p>
      <p>Period: {plan?.start_date} to {plan?.end_date}</p>

      {/* Plan Items */}
      {plan?.items?.map(item => (
        <div key={item.id}>
          Material: {item.material_id},
          Qty: {item.planned_quantity},
          Due: {item.target_completion_date}
        </div>
      ))}
    </div>
  )
}
```

### Update Plan Status
```typescript
import { useUpdateProductionPlan } from '@/features/production-plans'

function ApprovePlan({ id }: { id: number }) {
  const updatePlan = useUpdateProductionPlan()

  const handleApprove = () => {
    updatePlan.mutate({
      id,
      status: 'APPROVED',
    })
  }

  return <button onClick={handleApprove}>Approve Plan</button>
}
```

## Types

### Production Plan Entity
```typescript
interface ProductionPlan {
  id: number
  organization_id: number
  plant_id: number
  plan_code: string
  plan_name: string
  start_date: string
  end_date: string
  status: 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED'
  created_by_user_id: number
  approved_by_user_id?: number
  approval_date?: string
  created_at: string
  updated_at?: string
  items?: ProductionPlanItem[]
}
```

### Production Plan Item
```typescript
interface ProductionPlanItem {
  id: number
  production_plan_id: number
  material_id: number
  planned_quantity: number
  unit_of_measure_id: number
  target_completion_date: string
  created_at: string
  updated_at?: string
}
```

## Status Workflow

```
DRAFT ──→ APPROVED ──→ IN_PROGRESS ──→ COMPLETED
```

- **DRAFT**: Plan being created/edited
- **APPROVED**: Plan approved by manager
- **IN_PROGRESS**: Execution started
- **COMPLETED**: All items completed

## Validation

### Create Production Plan Schema
```typescript
createProductionPlanSchema = {
  plan_code: string (required, max 50 chars)
  plan_name: string (required, max 200 chars)
  start_date: string (required)
  end_date: string (required)
  status: 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED' (optional, default 'DRAFT')
}
```

### Update Schema
```typescript
updateProductionPlanSchema = {
  plan_name: string (optional, max 200 chars)
  start_date: string (optional)
  end_date: string (optional)
  status: 'DRAFT' | 'APPROVED' | 'IN_PROGRESS' | 'COMPLETED' (optional)
}
```

## Backend Integration

**API Endpoint**: `/api/v1/production-plans` (⚠️ Pending implementation)
**Backend Entity**: ✅ `/backend/app/domain/entities/production_plan.py`

### Required Backend Endpoints
```
GET    /api/v1/production-plans          - List plans with filters
GET    /api/v1/production-plans/:id      - Get single plan with items
POST   /api/v1/production-plans          - Create new plan
PUT    /api/v1/production-plans/:id      - Update plan
DELETE /api/v1/production-plans/:id      - Delete plan
```

## Testing

Run tests:
```bash
npm test -- src/features/production-plans/__tests__/
```

Expected: 14 tests passing (6 service + 8 hooks)

## Typical Use Cases

### 1. Quarterly Production Planning
```typescript
const plan = {
  plan_code: 'Q1-2024',
  plan_name: 'Q1 2024 Production Plan',
  start_date: '2024-01-01',
  end_date: '2024-03-31',
  status: 'DRAFT',
}
```

### 2. MRP-Driven Planning
- Create plan from MRP run results
- Add plan items for each required material
- Approve plan to generate work orders

### 3. Capacity Planning
- Filter plans by date range
- Sum planned quantities
- Compare against capacity

## Status

- ✅ Frontend: Complete and tested
- ✅ Types: Complete
- ✅ Validation: Complete
- ⏳ Backend API: Pending implementation
- ⏳ UI Components: To be built

## Next Steps

1. Implement backend API at `/api/v1/production-plans`
2. Build UI components (PlansTable, PlanForm, PlanFilters)
3. Create page components (PlansPage, PlanFormPage)
4. Add routing integration
5. Integrate with Work Orders for execution
