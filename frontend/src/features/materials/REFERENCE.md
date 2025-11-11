# Materials Module - Reference Patterns Guide

## Purpose
This document provides copy-paste patterns from the MaterialsModule for building the remaining 9 CRUD modules.

---

## Quick Start Checklist

1. [ ] Create module directory structure
2. [ ] Define types matching backend DTOs
3. [ ] Create Zod validation schemas
4. [ ] Write service tests (RED)
5. [ ] Implement service (GREEN)
6. [ ] Write hook tests (RED)
7. [ ] Implement hooks (GREEN)
8. [ ] Write component tests (RED)
9. [ ] Implement components (GREEN)
10. [ ] Create pages
11. [ ] Export from index.ts
12. [ ] Run all tests
13. [ ] Add routes to app

---

## Directory Structure Template

```bash
mkdir -p /path/to/frontend/src/features/{entity-name}/{__tests__,components,hooks,pages,services,schemas,types}
```

Replace `{entity-name}` with: work-orders, boms, inventory, etc.

---

## Pattern 1: Types Definition

**File**: `types/{entity}.types.ts`

```typescript
/**
 * {Entity} Types
 *
 * TypeScript types matching backend {Entity} entity and DTOs
 */

// Main entity interface (matches backend response)
export interface {Entity} {
  id: number
  organization_id: number
  plant_id: number
  // ... add your fields here
  is_active: boolean
  created_at: string
  updated_at?: string
}

// Create DTO (matches backend create request)
export interface Create{Entity}DTO {
  organization_id: number
  plant_id: number
  // ... add required create fields
}

// Update DTO (matches backend update request - all optional)
export interface Update{Entity}DTO {
  // ... add updatable fields (all optional)
  is_active?: boolean
}

// List response with pagination
export interface {Entity}ListResponse {
  items: {Entity}[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Filters for list endpoint
export interface {Entity}Filters {
  search?: string
  // ... add filter fields
  is_active?: boolean
  page?: number
  page_size?: number
}
```

---

## Pattern 2: Zod Validation Schemas

**File**: `schemas/{entity}.schema.ts`

```typescript
/**
 * {Entity} Validation Schemas
 *
 * Zod schemas for form validation matching backend validation rules
 */
import { z } from 'zod'

export const create{Entity}Schema = z.object({
  organization_id: z.number().positive('Organization ID is required'),
  plant_id: z.number().positive('Plant ID is required'),
  // Add your fields with validation rules
  // Example:
  // name: z.string().min(1, 'Name is required').max(200),
  // status: z.enum(['PENDING', 'ACTIVE', 'COMPLETED']),
  // quantity: z.number().positive('Quantity must be positive'),
})

export const update{Entity}Schema = z.object({
  // Same fields as create but all optional
  // name: z.string().min(1).max(200).optional(),
  is_active: z.boolean().optional(),
})

export type Create{Entity}FormData = z.infer<typeof create{Entity}Schema>
export type Update{Entity}FormData = z.infer<typeof update{Entity}Schema>
```

---

## Pattern 3: Service Layer

**File**: `services/{entity}.service.ts`

```typescript
/**
 * {Entity} Service
 *
 * API client for {Entity} CRUD operations
 */
import axios from 'axios'
import type {
  {Entity},
  Create{Entity}DTO,
  Update{Entity}DTO,
  {Entity}ListResponse,
  {Entity}Filters,
} from '../types/{entity}.types'

const API_URL = '/api/v1/{entities}'  // Use plural form

export const {entity}Service = {
  getAll: async (filters?: {Entity}Filters): Promise<{Entity}ListResponse> => {
    const { data } = await axios.get(API_URL, { params: filters })
    return data
  },

  getById: async (id: number): Promise<{Entity}> => {
    const { data } = await axios.get(`${API_URL}/${id}`)
    return data
  },

  create: async ({entity}: Create{Entity}DTO): Promise<{Entity}> => {
    const { data } = await axios.post(API_URL, {entity})
    return data
  },

  update: async (id: number, {entity}: Update{Entity}DTO): Promise<{Entity}> => {
    const { data } = await axios.put(`${API_URL}/${id}`, {entity})
    return data
  },

  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_URL}/${id}`)
  },

  // Add custom methods if needed
  // search: async (query: string, limit: number = 20): Promise<{Entity}[]> => {
  //   const { data } = await axios.get(`${API_URL}/search`, {
  //     params: { q: query, limit },
  //   })
  //   return data
  // },
}
```

**Test File**: `__tests__/{entity}.service.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { {entity}Service } from '../services/{entity}.service'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('{entity}Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all {entities}', async () => {
      const mockResponse = { data: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 } }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await {entity}Service.getAll()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/{entities}', { params: undefined })
      expect(result).toEqual(mockResponse.data)
    })
  })

  // Add tests for: getById, create, update, delete
})
```

---

## Pattern 4: TanStack Query Hooks

**File**: `hooks/use{Entities}.ts`

```typescript
/**
 * use{Entities} Hook
 *
 * TanStack Query hook for fetching {entities} list
 */
import { useQuery } from '@tanstack/react-query'
import { {entity}Service } from '../services/{entity}.service'
import type { {Entity}Filters } from '../types/{entity}.types'

export const {ENTITIES}_QUERY_KEY = '{entities}'

export function use{Entities}(filters?: {Entity}Filters) {
  return useQuery({
    queryKey: [{ENTITIES}_QUERY_KEY, filters],
    queryFn: () => {entity}Service.getAll(filters),
  })
}
```

**File**: `hooks/use{Entity}.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { {entity}Service } from '../services/{entity}.service'
import { {ENTITIES}_QUERY_KEY } from './use{Entities}'

export function use{Entity}(id: number) {
  return useQuery({
    queryKey: [{ENTITIES}_QUERY_KEY, id],
    queryFn: () => {entity}Service.getById(id),
    enabled: !!id,
  })
}
```

**File**: `hooks/useCreate{Entity}.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { {entity}Service } from '../services/{entity}.service'
import { {ENTITIES}_QUERY_KEY } from './use{Entities}'
import type { Create{Entity}DTO } from '../types/{entity}.types'

export function useCreate{Entity}() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Create{Entity}DTO) => {entity}Service.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [{ENTITIES}_QUERY_KEY] })
    },
  })
}
```

**File**: `hooks/useUpdate{Entity}.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { {entity}Service } from '../services/{entity}.service'
import { {ENTITIES}_QUERY_KEY } from './use{Entities}'
import type { Update{Entity}DTO } from '../types/{entity}.types'

export function useUpdate{Entity}() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Update{Entity}DTO }) =>
      {entity}Service.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [{ENTITIES}_QUERY_KEY] })
      queryClient.invalidateQueries({ queryKey: [{ENTITIES}_QUERY_KEY, variables.id] })
    },
  })
}
```

**File**: `hooks/useDelete{Entity}.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { {entity}Service } from '../services/{entity}.service'
import { {ENTITIES}_QUERY_KEY } from './use{Entities}'

export function useDelete{Entity}() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => {entity}Service.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [{ENTITIES}_QUERY_KEY] })
    },
  })
}
```

---

## Pattern 5: Table Component

**File**: `components/{Entities}Table.tsx`

```typescript
import { Button, Badge, Skeleton } from '@/design-system/atoms'
import { EmptyState } from '@/design-system/molecules'
import type { {Entity} } from '../types/{entity}.types'
import './{Entities}Table.css'

export interface {Entities}TableProps {
  {entities}: {Entity}[]
  isLoading?: boolean
  onEdit?: ({entity}: {Entity}) => void
  onDelete?: ({entity}: {Entity}) => void
  onRowClick?: ({entity}: {Entity}) => void
}

export const {Entities}Table = ({
  {entities},
  isLoading,
  onEdit,
  onDelete,
  onRowClick,
}: {Entities}TableProps) => {
  if (isLoading) {
    return (
      <div className="{entities}-table-skeleton">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} height="48px" />
        ))}
      </div>
    )
  }

  if ({entities}.length === 0) {
    return (
      <EmptyState
        title="No {entities} found"
        description="No {entities} match your filters."
      />
    )
  }

  return (
    <div className="{entities}-table-container">
      <table className="{entities}-table">
        <thead>
          <tr>
            <th>ID</th>
            {/* Add your column headers */}
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {{entities}.map(({entity}) => (
            <tr
              key={{entity}.id}
              onClick={() => onRowClick?.({entity})}
              className={onRowClick ? '{entities}-table-row-clickable' : ''}
            >
              <td>{{entity}.id}</td>
              {/* Add your columns */}
              <td>
                <Badge variant={{entity}.is_active ? 'success' : 'danger'} size="sm">
                  {{entity}.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </td>
              <td className="{entities}-table-actions">
                <Button variant="secondary" size="sm" onClick={(e) => {
                  e.stopPropagation()
                  onEdit?.({entity})
                }}>
                  Edit
                </Button>
                <Button variant="danger" size="sm" onClick={(e) => {
                  e.stopPropagation()
                  onDelete?.({entity})
                }}>
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## Pattern 6: Form Component

**File**: `components/{Entity}Form.tsx`

```typescript
import { useState, FormEvent } from 'react'
import { Card, Button } from '@/design-system/atoms'
import { FormField } from '@/design-system/molecules'
import { create{Entity}Schema, update{Entity}Schema } from '../schemas/{entity}.schema'
import type { Create{Entity}DTO, Update{Entity}DTO, {Entity} } from '../types/{entity}.types'
import { ZodError } from 'zod'

export interface {Entity}FormProps {
  mode: 'create' | 'edit'
  initialData?: {Entity}
  defaultOrgId?: number
  defaultPlantId?: number
  onSubmit: (data: Create{Entity}DTO | Update{Entity}DTO) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
  error?: string
}

export const {Entity}Form = ({
  mode,
  initialData,
  defaultOrgId = 1,
  defaultPlantId = 1,
  onSubmit,
  onCancel,
  isLoading,
  error,
}: {Entity}FormProps) => {
  const [formData, setFormData] = useState<Partial<Create{Entity}DTO>>({
    organization_id: initialData?.organization_id ?? defaultOrgId,
    plant_id: initialData?.plant_id ?? defaultPlantId,
    // Initialize your fields here
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = (): boolean => {
    try {
      const schema = mode === 'create' ? create{Entity}Schema : update{Entity}Schema
      schema.parse(formData)
      setErrors({})
      return true
    } catch (e) {
      if (e instanceof ZodError) {
        const newErrors: Record<string, string> = {}
        e.errors.forEach((err) => {
          const path = err.path.join('.')
          newErrors[path] = err.message
        })
        setErrors(newErrors)
      }
      return false
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    if (mode === 'create') {
      await onSubmit(formData as Create{Entity}DTO)
    } else {
      // Build update DTO with only changed fields
      const updateData: Update{Entity}DTO = {}
      // Add changed field detection here
      await onSubmit(updateData)
    }
  }

  const handleChange = (field: keyof Create{Entity}DTO) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <Card variant="elevated" padding="lg">
      <form onSubmit={handleSubmit}>
        {/* Add your form fields using FormField component */}

        {error && (
          <div className="{entity}-form__error-message" role="alert">
            {error}
          </div>
        )}

        <div className="{entity}-form__actions">
          <Button type="submit" variant="primary" isLoading={isLoading} fullWidth>
            {mode === 'create' ? 'Create {Entity}' : 'Update {Entity}'}
          </Button>
          {onCancel && (
            <Button type="button" variant="ghost" onClick={onCancel} disabled={isLoading} fullWidth>
              Cancel
            </Button>
          )}
        </div>
      </form>
    </Card>
  )
}
```

---

## Pattern 7: List Page

**File**: `pages/{Entities}Page.tsx`

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/design-system/templates'
import { Button, Heading1 } from '@/design-system/atoms'
import { {Entities}Table } from '../components/{Entities}Table'
import { use{Entities} } from '../hooks/use{Entities}'
import { useDelete{Entity} } from '../hooks/useDelete{Entity}'
import type { {Entity}Filters, {Entity} } from '../types/{entity}.types'

export const {Entities}Page = () => {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<{Entity}Filters>({})

  const { data, isLoading, error } = use{Entities}(filters)
  const deleteMutation = useDelete{Entity}()

  const handleCreate = () => {
    navigate('/{entities}/create')
  }

  const handleEdit = ({entity}: {Entity}) => {
    navigate(`/{entities}/${{entity}.id}/edit`)
  }

  const handleDelete = async ({entity}: {Entity}) => {
    if (window.confirm(`Delete {entity} ${{entity}.id}?`)) {
      await deleteMutation.mutateAsync({entity}.id)
    }
  }

  return (
    <AppLayout>
      <div className="{entities}-page">
        <div className="{entities}-page__header">
          <Heading1>{Entities}</Heading1>
          <Button variant="primary" onClick={handleCreate}>
            Add {Entity}
          </Button>
        </div>

        {error && (
          <div className="{entities}-page__error" role="alert">
            Error: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        )}

        <{Entities}Table
          {entities}={data?.items ?? []}
          isLoading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>
    </AppLayout>
  )
}
```

---

## Pattern 8: Form Page

**File**: `pages/{Entity}FormPage.tsx`

```typescript
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AppLayout } from '@/design-system/templates'
import { Heading1, Button } from '@/design-system/atoms'
import { {Entity}Form } from '../components/{Entity}Form'
import { use{Entity} } from '../hooks/use{Entity}'
import { useCreate{Entity} } from '../hooks/useCreate{Entity}'
import { useUpdate{Entity} } from '../hooks/useUpdate{Entity}'
import type { Create{Entity}DTO, Update{Entity}DTO } from '../types/{entity}.types'

export const {Entity}FormPage = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEditMode = !!id

  const { data: {entity}, isLoading: isFetching } = use{Entity}(id ? parseInt(id) : 0)
  const createMutation = useCreate{Entity}()
  const updateMutation = useUpdate{Entity}()

  const isLoading = createMutation.isPending || updateMutation.isPending
  const error = createMutation.error instanceof Error
    ? createMutation.error.message
    : updateMutation.error instanceof Error
      ? updateMutation.error.message
      : undefined

  useEffect(() => {
    if (createMutation.isSuccess || updateMutation.isSuccess) {
      navigate('/{entities}')
    }
  }, [createMutation.isSuccess, updateMutation.isSuccess, navigate])

  const handleSubmit = async (data: Create{Entity}DTO | Update{Entity}DTO) => {
    if (isEditMode && id) {
      await updateMutation.mutateAsync({ id: parseInt(id), data: data as Update{Entity}DTO })
    } else {
      await createMutation.mutateAsync(data as Create{Entity}DTO)
    }
  }

  const handleCancel = () => {
    navigate('/{entities}')
  }

  if (isFetching && isEditMode) {
    return <AppLayout><div>Loading...</div></AppLayout>
  }

  return (
    <AppLayout>
      <div className="{entity}-form-page">
        <Heading1>{isEditMode ? 'Edit' : 'Create'} {Entity}</Heading1>
        <{Entity}Form
          mode={isEditMode ? 'edit' : 'create'}
          initialData={{entity}}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </AppLayout>
  )
}
```

---

## Pattern 9: Module Index

**File**: `index.ts`

```typescript
// Types
export type * from './types/{entity}.types'

// Schemas
export * from './schemas/{entity}.schema'

// Hooks
export { use{Entities}, {ENTITIES}_QUERY_KEY } from './hooks/use{Entities}'
export { use{Entity} } from './hooks/use{Entity}'
export { useCreate{Entity} } from './hooks/useCreate{Entity}'
export { useUpdate{Entity} } from './hooks/useUpdate{Entity}'
export { useDelete{Entity} } from './hooks/useDelete{Entity}'

// Components
export { {Entities}Table } from './components/{Entities}Table'
export { {Entity}Form } from './components/{Entity}Form'

// Pages
export { {Entities}Page } from './pages/{Entities}Page'
export { {Entity}FormPage } from './pages/{Entity}FormPage'

// Service
export { {entity}Service } from './services/{entity}.service'
```

---

## TDD Workflow

1. **Write Service Test** → Run (RED) → **Implement Service** → Run (GREEN)
2. **Write Hook Tests** → Run (RED) → **Implement Hooks** → Run (GREEN)
3. **Write Component Tests** → Run (RED) → **Implement Components** → Run (GREEN)
4. **Create Pages** → **Manual testing**
5. **Run all tests** → Ensure 100% pass rate

---

## Naming Conventions

| Pattern | Example |
|---------|---------|
| Entity (singular) | Material, WorkOrder, BOM |
| Entities (plural) | Materials, WorkOrders, BOMs |
| Type file | material.types.ts |
| Service file | material.service.ts |
| Hook file | useMaterials.ts |
| Component file | MaterialsTable.tsx |
| Test file | material.service.test.ts |
| Query key constant | MATERIALS_QUERY_KEY |

---

## Common Replacements

When copying patterns, replace:
- `{Entity}` → Your entity name (singular, PascalCase): `WorkOrder`
- `{entity}` → Your entity name (singular, camelCase): `workOrder`
- `{Entities}` → Plural PascalCase: `WorkOrders`
- `{entities}` → Plural camelCase: `workOrders`
- `{ENTITIES}` → Plural SCREAMING_SNAKE_CASE: `WORK_ORDERS`

---

## Testing Commands

```bash
# Run all tests for your module
npm test -- src/features/{entity-name}/__tests__/

# Run specific test file
npm test -- src/features/{entity-name}/__tests__/{entity}.service.test.ts

# Watch mode
npm test:watch -- src/features/{entity-name}/__tests__/
```

---

## Final Checklist

- [ ] All types defined matching backend
- [ ] Zod schemas created with proper validation
- [ ] Service layer implemented with all CRUD methods
- [ ] All 5 hooks created (list, single, create, update, delete)
- [ ] Table component with loading/empty states
- [ ] Form component with validation
- [ ] List page with actions
- [ ] Form page for create/edit
- [ ] Module index exports everything
- [ ] All tests passing (minimum 30+ tests)
- [ ] Routes added to app router
- [ ] Manual smoke test completed

---

**Reference Implementation**: `/src/features/materials/`
**Total Test Count**: 34 tests
**Success Rate**: 100%
