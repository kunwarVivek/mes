# BOM Module Quick Start Guide

## Overview
Bill of Materials (BOM) module for managing component requirements for finished goods production.

## Module Structure
```
bom/
├── types/bom.types.ts           - TypeScript definitions
├── schemas/bom.schema.ts        - Zod validation
├── services/bom.service.ts      - API client
├── hooks/                       - TanStack Query hooks
│   ├── useBOMs.ts              - List query
│   ├── useBOM.ts               - Single query
│   ├── useCreateBOM.ts         - Create mutation
│   ├── useUpdateBOM.ts         - Update mutation
│   └── useDeleteBOM.ts         - Delete mutation
└── __tests__/                   - Test files (14 passing)
```

## Usage Examples

### List BOMs
```typescript
import { useBOMs } from '@/features/bom'

function BOMList() {
  const { data, isLoading } = useBOMs({
    material_id: 1,
    bom_type: 'PRODUCTION',
    page: 1,
    page_size: 20,
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      {data?.items.map(bom => (
        <div key={bom.id}>{bom.bom_name}</div>
      ))}
    </div>
  )
}
```

### Create BOM
```typescript
import { useCreateBOM } from '@/features/bom'

function CreateBOMForm() {
  const createBOM = useCreateBOM()

  const handleSubmit = (data: CreateBOMDTO) => {
    createBOM.mutate(data, {
      onSuccess: () => console.log('BOM created!'),
      onError: (error) => console.error(error),
    })
  }

  return <form onSubmit={handleSubmit}>...</form>
}
```

### Get Single BOM
```typescript
import { useBOM } from '@/features/bom'

function BOMDetail({ id }: { id: number }) {
  const { data: bom, isLoading } = useBOM(id)

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      <h1>{bom?.bom_name}</h1>
      <p>Version: {bom?.bom_version}</p>
      <p>Base Quantity: {bom?.base_quantity}</p>

      {/* BOM Lines */}
      {bom?.bom_lines?.map(line => (
        <div key={line.id}>
          Component: {line.component_material_id}, Qty: {line.quantity}
        </div>
      ))}
    </div>
  )
}
```

## Types

### BOM Entity
```typescript
interface BOM {
  id: number
  organization_id: number
  plant_id: number
  bom_number: string
  material_id: number          // Finished good
  bom_version: number
  bom_name: string
  bom_type: 'PRODUCTION' | 'ENGINEERING' | 'PLANNING'
  base_quantity: number
  unit_of_measure_id: number
  effective_start_date?: string
  effective_end_date?: string
  is_active: boolean
  created_by_user_id: number
  created_at: string
  updated_at?: string
  bom_lines?: BOMLine[]       // Child components
}
```

### BOM Line
```typescript
interface BOMLine {
  id: number
  bom_header_id: number
  line_number: number
  component_material_id: number  // Component material
  quantity: number
  unit_of_measure_id: number
  scrap_factor: number
  operation_number?: number
  is_phantom: boolean
  backflush: boolean
  created_at: string
  updated_at?: string
}
```

## Validation

### Create BOM Schema
```typescript
createBOMSchema = {
  bom_number: string (required, max 50 chars)
  material_id: number (required, positive)
  bom_name: string (required, max 200 chars)
  bom_type: 'PRODUCTION' | 'ENGINEERING' | 'PLANNING'
  base_quantity: number (required, positive)
  unit_of_measure_id: number (required, positive)
  effective_start_date: string (optional)
  effective_end_date: string (optional)
  bom_version: number (optional, default 1, min 1)
}
```

## Backend Integration

**API Endpoint**: `/api/v1/boms` (⚠️ Pending implementation)
**Backend Models**: ✅ `/backend/app/models/bom.py`

### Required Backend Endpoints
```
GET    /api/v1/boms          - List BOMs with filters
GET    /api/v1/boms/:id      - Get single BOM with lines
POST   /api/v1/boms          - Create new BOM
PUT    /api/v1/boms/:id      - Update BOM
DELETE /api/v1/boms/:id      - Delete BOM
```

## Testing

Run tests:
```bash
npm test -- src/features/bom/__tests__/
```

Expected: 14 tests passing (6 service + 8 hooks)

## Status

- ✅ Frontend: Complete and tested
- ✅ Types: Complete
- ✅ Validation: Complete
- ⏳ Backend API: Pending implementation
- ⏳ UI Components: To be built

## Next Steps

1. Implement backend API at `/api/v1/boms`
2. Build UI components (BOMsTable, BOMForm, BOMFilters)
3. Create page components (BOMsPage, BOMFormPage)
4. Add routing integration
