# Materials UI Components - Quick Reference

## File Locations (Absolute Paths)

### Components
```
/Users/vivek/jet/unison/frontend/src/features/materials/components/MaterialForm.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/components/MaterialTable.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/components/__tests__/MaterialForm.test.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/components/__tests__/MaterialTable.test.tsx
```

### Pages
```
/Users/vivek/jet/unison/frontend/src/features/materials/pages/MaterialListPage.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/pages/MaterialFormPageNew.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/pages/__tests__/MaterialListPage.test.tsx
/Users/vivek/jet/unison/frontend/src/features/materials/pages/__tests__/MaterialFormPage.test.tsx
```

### Existing Data Layer (Already Implemented)
```
/Users/vivek/jet/unison/frontend/src/features/materials/schemas/material.schema.ts
/Users/vivek/jet/unison/frontend/src/features/materials/types/material.types.ts
/Users/vivek/jet/unison/frontend/src/features/materials/services/material.service.ts
/Users/vivek/jet/unison/frontend/src/features/materials/hooks/useMaterials.ts
/Users/vivek/jet/unison/frontend/src/features/materials/hooks/useMaterial.ts
/Users/vivek/jet/unison/frontend/src/features/materials/hooks/useMaterialMutations.ts
```

### Design System Dependencies
```
/Users/vivek/jet/unison/frontend/src/design-system/organisms/DataTable.tsx
/Users/vivek/jet/unison/frontend/src/design-system/molecules/SearchBar.tsx
/Users/vivek/jet/unison/frontend/src/design-system/molecules/FilterGroup.tsx
/Users/vivek/jet/unison/frontend/src/design-system/molecules/StatusBadge.tsx
```

### shadcn/ui Components Used
```
/Users/vivek/jet/unison/frontend/src/components/ui/button.tsx
/Users/vivek/jet/unison/frontend/src/components/ui/input.tsx
/Users/vivek/jet/unison/frontend/src/components/ui/label.tsx
/Users/vivek/jet/unison/frontend/src/components/ui/select.tsx
/Users/vivek/jet/unison/frontend/src/components/ui/badge.tsx
```

## Test Commands

### Run Individual Component Tests
```bash
cd /Users/vivek/jet/unison/frontend

# MaterialForm tests (13 tests)
npm test -- src/features/materials/components/__tests__/MaterialForm.test.tsx --run

# MaterialTable tests (21 tests)
npm test -- src/features/materials/components/__tests__/MaterialTable.test.tsx --run

# MaterialListPage tests (16 tests)
npm test -- src/features/materials/pages/__tests__/MaterialListPage.test.tsx --run
```

### Run All Materials UI Tests (50 tests)
```bash
cd /Users/vivek/jet/unison/frontend
npm test -- src/features/materials/components/__tests__/*.test.tsx src/features/materials/pages/__tests__/MaterialListPage.test.tsx --run
```

## Component Usage Examples

### MaterialForm
```tsx
import { MaterialForm } from '@/features/materials/components/MaterialForm'

// Create mode
<MaterialForm
  onSuccess={() => navigate('/materials')}
/>

// Edit mode
<MaterialForm
  materialId={1}
  defaultValues={material}
  onSuccess={() => navigate('/materials')}
/>
```

### MaterialTable
```tsx
import { MaterialTable } from '@/features/materials/components/MaterialTable'

<MaterialTable
  data={materials}
  loading={isLoading}
  onRowClick={(material) => navigate(`/materials/${material.id}`)}
/>
```

### MaterialListPage
```tsx
import { MaterialListPage } from '@/features/materials/pages/MaterialListPage'

// In your router
<Route path="/materials" element={<MaterialListPage />} />
```

### MaterialFormPage
```tsx
import { MaterialFormPage } from '@/features/materials/pages/MaterialFormPageNew'

// In your router
<Route path="/materials/create" element={<MaterialFormPage />} />
<Route path="/materials/:id/edit" element={<MaterialFormPage />} />
```

## Key Props and Interfaces

### MaterialForm Props
```typescript
interface MaterialFormProps {
  materialId?: number           // For edit mode
  onSuccess?: () => void       // Callback after successful submit
  defaultValues?: Partial<Material>  // Pre-populate form
}
```

### MaterialTable Props
```typescript
interface MaterialTableProps {
  data: Material[]             // Array of materials to display
  loading?: boolean           // Show loading skeleton
  onRowClick?: (material: Material) => void  // Row click handler
  emptyState?: ReactNode      // Custom empty state
}
```

## Validation Rules

### Material Number
- Required in create mode
- Max 10 characters
- Uppercase alphanumeric only (regex: `/^[A-Z0-9]+$/`)
- Disabled in edit mode

### Material Name
- Required
- Max 200 characters

### Description
- Optional
- Max 500 characters

### Numeric Fields
- safety_stock: non-negative (default: 0)
- reorder_point: non-negative (default: 0)
- lot_size: positive (default: 1)
- lead_time_days: non-negative (default: 0)

### Enums
- procurement_type: 'PURCHASE' | 'MANUFACTURE' | 'BOTH'
- mrp_type: 'MRP' | 'REORDER'

## Test Results (Latest Run)

```
Test Files  3 passed (3)
Tests       50 passed (50)
Duration    ~2-3 seconds
```

### Breakdown
- MaterialForm: 13/13 ✅
- MaterialTable: 21/21 ✅
- MaterialListPage: 16/16 ✅

## Common Issues & Solutions

### Issue: Tests fail with "Cannot find module"
**Solution:** Ensure you're in the frontend directory:
```bash
cd /Users/vivek/jet/unison/frontend
```

### Issue: Build errors about TypeScript
**Solution:** These are pre-existing issues unrelated to Materials UI. The components themselves compile correctly through Vite.

### Issue: Mock errors in tests
**Solution:** All required mocks are already set up in test files. If adding new tests, follow the existing mock patterns.

## Architecture Summary

```
Pages (Routes/Navigation)
  └── MaterialListPage
  └── MaterialFormPage
       │
       └── Organisms (Complex Components)
            └── MaterialTable (uses DataTable)
            └── MaterialForm
                 │
                 └── Molecules (Composed Components)
                      └── SearchBar
                      └── FilterGroup
                      └── StatusBadge
                           │
                           └── Atoms (shadcn/ui)
                                └── Button
                                └── Input
                                └── Select
                                └── Label
                                └── Badge
```

## Integration with Existing Code

The new UI components integrate seamlessly with:
1. **Existing hooks**: Uses useMaterials, useMaterialMutations, useMaterial
2. **Existing schemas**: Validates against createMaterialSchema, updateMaterialSchema
3. **Existing types**: Uses Material, CreateMaterialFormData, UpdateMaterialFormData
4. **Existing services**: Calls materialService methods

No changes required to existing data layer (59/59 tests still passing).
