# Equipment Module - Quick Start Guide

## Installation
The Equipment module is ready to use. Import from `@/features/equipment`.

## Basic Usage

### 1. Fetch Machines List

```typescript
import { useMachines, MachinesTable } from '@/features/equipment'

function MachinesPage() {
  const { data, isLoading, error } = useMachines({
    status: 'RUNNING',
    plant_id: 1,
  })

  if (error) return <div>Error: {error.message}</div>

  return (
    <MachinesTable
      machines={data?.items ?? []}
      isLoading={isLoading}
      onEdit={handleEdit}
      onDelete={handleDelete}
      onStatusChange={handleStatusChange}
    />
  )
}
```

### 2. Create a Machine

```typescript
import { useCreateMachine, MachineForm } from '@/features/equipment'

function CreateMachinePage() {
  const createMachine = useCreateMachine({
    onSuccess: (machine) => {
      console.log('Machine created:', machine)
      navigate('/equipment')
    },
    onError: (error) => {
      console.error('Failed to create machine:', error)
    },
  })

  const handleSubmit = async (data) => {
    createMachine.mutate(data)
  }

  return (
    <MachineForm
      onSubmit={handleSubmit}
      isSubmitting={createMachine.isPending}
      error={createMachine.error?.message}
    />
  )
}
```

### 3. Update Machine Status

```typescript
import { useUpdateMachineStatus } from '@/features/equipment'

function StatusControls({ machine }) {
  const updateStatus = useUpdateMachineStatus({
    onSuccess: () => {
      toast.success('Status updated successfully')
    },
  })

  const handleStartProduction = () => {
    updateStatus.mutate({
      id: machine.id,
      data: {
        status: 'RUNNING',
        notes: 'Production started',
      },
    })
  }

  return (
    <button onClick={handleStartProduction}>
      Start Production
    </button>
  )
}
```

### 4. Display Machine Status Card

```typescript
import { MachineStatusCard } from '@/features/equipment'

function Dashboard() {
  const { data } = useMachines({ plant_id: 1 })

  return (
    <div className="grid">
      {data?.items.map((machine) => (
        <MachineStatusCard
          key={machine.id}
          machine={machine}
          onClick={() => navigate(`/machines/${machine.id}`)}
          onStatusChange={handleStatusChange}
        />
      ))}
    </div>
  )
}
```

### 5. Display OEE Metrics

```typescript
import { useMachineOEE, OEEGauge } from '@/features/equipment'

function MachineOEEDisplay({ machineId }) {
  const { data, isLoading } = useMachineOEE({
    machineId,
    startDate: '2024-01-01T00:00:00Z',
    endDate: '2024-01-01T08:00:00Z',
    idealCycleTime: 0.5,
    totalPieces: 900,
    defectPieces: 10,
  })

  if (isLoading) return <div>Loading OEE...</div>

  return <OEEGauge metrics={data} />
}
```

## API Reference

### Hooks

#### Query Hooks
- `useMachines(filters?)` - Fetch machines list with optional filters
- `useMachine(id)` - Fetch single machine by ID
- `useMachineOEE(params)` - Fetch OEE metrics for a machine

#### Mutation Hooks
- `useCreateMachine(options?)` - Create new machine
- `useUpdateMachine(options?)` - Update machine details
- `useDeleteMachine(options?)` - Delete machine (soft delete)
- `useUpdateMachineStatus(options?)` - Update machine status

### Components

#### MachinesTable
```typescript
interface MachinesTableProps {
  machines: Machine[]
  isLoading?: boolean
  onEdit?: (machine: Machine) => void
  onDelete?: (machine: Machine) => void
  onRowClick?: (machine: Machine) => void
  onStatusChange?: (machine: Machine) => void
}
```

#### MachineForm
```typescript
interface MachineFormProps {
  initialData?: Machine
  onSubmit: (data: CreateMachineDTO | UpdateMachineDTO) => void
  onCancel?: () => void
  isSubmitting?: boolean
  error?: string
}
```

#### MachineStatusCard
```typescript
interface MachineStatusCardProps {
  machine: Machine
  onClick?: (machine: Machine) => void
  onStatusChange?: (machine: Machine) => void
  compact?: boolean
  isLoading?: boolean
}
```

#### OEEGauge
```typescript
interface OEEGaugeProps {
  metrics: OEEMetrics
  compact?: boolean
  isLoading?: boolean
}
```

### Types

#### Machine
```typescript
interface Machine {
  id: number
  organization_id: number
  plant_id: number
  machine_code: string
  machine_name: string
  description: string
  work_center_id: number
  status: MachineStatus
  is_active: boolean
  created_at: string
  updated_at?: string
}
```

#### MachineStatus
```typescript
type MachineStatus =
  | 'AVAILABLE'
  | 'RUNNING'
  | 'IDLE'
  | 'DOWN'
  | 'SETUP'
  | 'MAINTENANCE'
```

#### OEEMetrics
```typescript
interface OEEMetrics {
  availability: number    // 0-1
  performance: number     // 0-1
  quality: number        // 0-1
  oee_score: number     // 0-1
}
```

### Filters

```typescript
interface MachineFilters {
  search?: string
  status?: MachineStatus
  work_center_id?: number
  plant_id?: number
  is_active?: boolean
  page?: number
  page_size?: number
}
```

## Common Patterns

### Filter Machines by Status

```typescript
const { data } = useMachines({ status: 'RUNNING' })
```

### Search Machines

```typescript
const { data } = useMachines({ search: 'CNC' })
```

### Paginate Results

```typescript
const [page, setPage] = useState(1)
const { data } = useMachines({ page, page_size: 20 })
```

### Update and Refetch

```typescript
const queryClient = useQueryClient()

const updateMachine = useUpdateMachine({
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['machines'] })
  },
})
```

## Status Badge Colors

| Status | Color | Animation |
|--------|-------|-----------|
| AVAILABLE | Green | None |
| RUNNING | Blue | Pulse |
| IDLE | Gray | None |
| DOWN | Red | None |
| SETUP | Gray | None |
| MAINTENANCE | Yellow | None |

## OEE Status Indicators

| OEE Score | Status | Color |
|-----------|--------|-------|
| >= 85% | Excellent | Green |
| >= 70% | Good | Blue |
| >= 60% | Acceptable | Yellow |
| < 60% | Poor | Red |

## Best Practices

1. **Always handle loading states**
   ```typescript
   if (isLoading) return <Spinner />
   ```

2. **Handle errors gracefully**
   ```typescript
   if (error) return <ErrorMessage error={error} />
   ```

3. **Use optimistic updates for better UX**
   ```typescript
   const updateStatus = useUpdateMachineStatus({
     onMutate: async (variables) => {
       // Optimistically update UI
     },
   })
   ```

4. **Invalidate queries after mutations**
   ```typescript
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ['machines'] })
   }
   ```

5. **Use compact mode for dashboards**
   ```typescript
   <MachineStatusCard machine={machine} compact />
   <OEEGauge metrics={metrics} compact />
   ```

## Validation Rules

### Machine Code
- Required
- 1-20 characters
- Uppercase alphanumeric only (A-Z, 0-9)

### Machine Name
- Required
- 1-200 characters

### Description
- Optional
- Max 500 characters

### Status
- Must be one of: AVAILABLE, RUNNING, IDLE, DOWN, SETUP, MAINTENANCE

## Examples

### Complete CRUD Example

```typescript
import {
  useMachines,
  useCreateMachine,
  useUpdateMachine,
  useDeleteMachine,
  MachinesTable,
  MachineForm,
} from '@/features/equipment'

function MachinesManagement() {
  const [mode, setMode] = useState<'list' | 'create' | 'edit'>('list')
  const [selectedMachine, setSelectedMachine] = useState<Machine | null>(null)

  const { data, isLoading } = useMachines()

  const createMachine = useCreateMachine({
    onSuccess: () => setMode('list'),
  })

  const updateMachine = useUpdateMachine({
    onSuccess: () => setMode('list'),
  })

  const deleteMachine = useDeleteMachine({
    onSuccess: () => console.log('Deleted'),
  })

  if (mode === 'create') {
    return (
      <MachineForm
        onSubmit={(data) => createMachine.mutate(data)}
        onCancel={() => setMode('list')}
      />
    )
  }

  if (mode === 'edit' && selectedMachine) {
    return (
      <MachineForm
        initialData={selectedMachine}
        onSubmit={(data) => updateMachine.mutate({
          id: selectedMachine.id,
          data,
        })}
        onCancel={() => setMode('list')}
      />
    )
  }

  return (
    <div>
      <button onClick={() => setMode('create')}>
        Create Machine
      </button>
      <MachinesTable
        machines={data?.items ?? []}
        isLoading={isLoading}
        onEdit={(machine) => {
          setSelectedMachine(machine)
          setMode('edit')
        }}
        onDelete={(machine) => {
          if (confirm('Delete?')) {
            deleteMachine.mutate(machine.id)
          }
        }}
      />
    </div>
  )
}
```

## Testing

The module includes comprehensive tests. Run tests with:

```bash
npm test -- src/features/equipment/__tests__/
```

81 tests covering:
- Service layer (17 tests)
- React Query hooks (15 tests)
- UI components (49 tests)

## Further Reading

- [TDD_EVIDENCE.md](./TDD_EVIDENCE.md) - TDD methodology and test details
- [VERIFICATION_SUMMARY.md](./VERIFICATION_SUMMARY.md) - Complete verification checklist
- Backend API: `/backend/app/presentation/api/v1/machines.py`
- Backend Entity: `/backend/app/domain/entities/machine.py`
