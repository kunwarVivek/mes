# Work Orders Module - Usage Examples

## Import the Module

```typescript
import {
  // Schemas & Types
  WorkOrder,
  CreateWorkOrderFormData,
  OrderType,
  OrderStatus,

  // Hooks
  useWorkOrders,
  useWorkOrder,
  useWorkOrderMutations,

  // Components
  WorkOrderForm,

  // Service (if needed)
  workOrderService,
} from '@/features/work-orders'
```

---

## Example 1: List Work Orders with Filtering

```typescript
import { useWorkOrders } from '@/features/work-orders'

function WorkOrdersList() {
  const { data, isLoading, error } = useWorkOrders({
    page: 1,
    page_size: 10,
    status: 'PLANNED',
    priority: 8,
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      <h2>Work Orders ({data?.total})</h2>
      <ul>
        {data?.items.map((wo) => (
          <li key={wo.id}>
            {wo.work_order_number} - {wo.order_status} - Priority: {wo.priority}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

---

## Example 2: Get Single Work Order

```typescript
import { useWorkOrder } from '@/features/work-orders'

function WorkOrderDetail({ id }: { id: number }) {
  const { data: workOrder, isLoading } = useWorkOrder(id)

  if (isLoading) return <div>Loading...</div>
  if (!workOrder) return <div>Work order not found</div>

  return (
    <div>
      <h2>{workOrder.work_order_number}</h2>
      <p>Status: {workOrder.order_status}</p>
      <p>Material ID: {workOrder.material_id}</p>
      <p>Planned Quantity: {workOrder.planned_quantity}</p>
      <p>Priority: {workOrder.priority}</p>

      <h3>Operations ({workOrder.operations.length})</h3>
      <ul>
        {workOrder.operations.map((op) => (
          <li key={op.id}>
            {op.operation_sequence}: {op.operation_name} - {op.status}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

---

## Example 3: Create Work Order Form

```typescript
import { WorkOrderForm } from '@/features/work-orders'
import { useNavigate } from '@tanstack/react-router'

function CreateWorkOrderPage() {
  const navigate = useNavigate()

  const handleSuccess = () => {
    navigate({ to: '/work-orders' })
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">Create Work Order</h1>
      <WorkOrderForm onSuccess={handleSuccess} />
    </div>
  )
}
```

---

## Example 4: Edit Work Order Form

```typescript
import { WorkOrderForm, useWorkOrder } from '@/features/work-orders'
import { useNavigate } from '@tanstack/react-router'

function EditWorkOrderPage({ id }: { id: number }) {
  const navigate = useNavigate()
  const { data: workOrder, isLoading } = useWorkOrder(id)

  const handleSuccess = () => {
    navigate({ to: '/work-orders' })
  }

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">Edit Work Order</h1>
      <WorkOrderForm
        workOrderId={id}
        defaultValues={workOrder}
        onSuccess={handleSuccess}
      />
    </div>
  )
}
```

---

## Example 5: State Transitions (Release, Start, Complete)

```typescript
import { useWorkOrderMutations, useWorkOrder } from '@/features/work-orders'
import { Button } from '@/components/ui/button'

function WorkOrderActions({ id }: { id: number }) {
  const { data: workOrder } = useWorkOrder(id)
  const { releaseWorkOrder, startWorkOrder, completeWorkOrder } = useWorkOrderMutations()

  if (!workOrder) return null

  const canRelease = workOrder.order_status === 'PLANNED'
  const canStart = workOrder.order_status === 'RELEASED'
  const canComplete = workOrder.order_status === 'IN_PROGRESS'

  return (
    <div className="flex gap-2">
      {canRelease && (
        <Button onClick={() => releaseWorkOrder.mutate(id)}>
          Release Work Order
        </Button>
      )}
      {canStart && (
        <Button onClick={() => startWorkOrder.mutate(id)}>
          Start Work Order
        </Button>
      )}
      {canComplete && (
        <Button onClick={() => completeWorkOrder.mutate(id)}>
          Complete Work Order
        </Button>
      )}
    </div>
  )
}
```

---

## Example 6: Manual Mutations (Create, Update, Cancel)

```typescript
import { useWorkOrderMutations } from '@/features/work-orders'
import { Button } from '@/components/ui/button'

function WorkOrderManagement() {
  const { createWorkOrder, updateWorkOrder, cancelWorkOrder } = useWorkOrderMutations()

  const handleCreate = () => {
    createWorkOrder.mutate({
      material_id: 1,
      order_type: 'PRODUCTION',
      planned_quantity: 100,
      priority: 7,
      start_date_planned: new Date('2025-01-15'),
    })
  }

  const handleUpdate = (id: number) => {
    updateWorkOrder.mutate({
      id,
      data: {
        planned_quantity: 150,
        priority: 9,
      },
    })
  }

  const handleCancel = (id: number) => {
    cancelWorkOrder.mutate(id)
  }

  return (
    <div>
      <Button onClick={handleCreate}>Create Work Order</Button>
      <Button onClick={() => handleUpdate(1)}>Update WO 1</Button>
      <Button onClick={() => handleCancel(1)}>Cancel WO 1</Button>
    </div>
  )
}
```

---

## Example 7: Using StatusBadge and PriorityIndicator (Molecules)

```typescript
import { useWorkOrders } from '@/features/work-orders'
import { StatusBadge, PriorityIndicator } from '@/design-system/molecules'

function WorkOrdersTable() {
  const { data } = useWorkOrders()

  return (
    <table>
      <thead>
        <tr>
          <th>WO Number</th>
          <th>Status</th>
          <th>Priority</th>
          <th>Planned Qty</th>
        </tr>
      </thead>
      <tbody>
        {data?.items.map((wo) => (
          <tr key={wo.id}>
            <td>{wo.work_order_number}</td>
            <td>
              <StatusBadge
                status={wo.order_status.toLowerCase() as any}
                withIcon
              />
            </td>
            <td>
              <PriorityIndicator
                priority={wo.priority <= 3 ? 'low' : wo.priority <= 7 ? 'medium' : 'high'}
                withLabel
              />
            </td>
            <td>{wo.planned_quantity}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

---

## Example 8: Direct Service Usage (Advanced)

```typescript
import { workOrderService } from '@/features/work-orders'

async function directServiceExample() {
  try {
    // List work orders
    const list = await workOrderService.list({
      page: 1,
      page_size: 20,
      status: 'IN_PROGRESS',
    })
    console.log('Work Orders:', list.items)

    // Get single work order
    const wo = await workOrderService.get(1)
    console.log('Work Order:', wo)

    // Create work order
    const newWo = await workOrderService.create({
      material_id: 1,
      order_type: 'PRODUCTION',
      planned_quantity: 100,
      priority: 5,
    })
    console.log('Created:', newWo)

    // State transitions
    await workOrderService.release(newWo.id)
    await workOrderService.start(newWo.id)
    await workOrderService.complete(newWo.id)

    // Add operation
    await workOrderService.addOperation(newWo.id, {
      operation_sequence: 10,
      operation_name: 'Cutting',
      setup_time_minutes: 30,
      run_time_minutes: 120,
    })

    // Add material
    await workOrderService.addMaterial(newWo.id, {
      material_id: 2,
      required_quantity: 50,
    })
  } catch (error) {
    console.error('Service error:', error)
  }
}
```

---

## Type Examples

```typescript
import type {
  WorkOrder,
  CreateWorkOrderFormData,
  UpdateWorkOrderFormData,
  OrderType,
  OrderStatus,
  OperationStatus,
  WorkOrderOperation,
  WorkOrderMaterial,
} from '@/features/work-orders'

// Create work order data
const createData: CreateWorkOrderFormData = {
  material_id: 1,
  order_type: 'PRODUCTION', // OrderType
  planned_quantity: 100,
  start_date_planned: new Date('2025-01-15'),
  end_date_planned: new Date('2025-01-20'),
  priority: 7, // 1-10
}

// Update work order data
const updateData: UpdateWorkOrderFormData = {
  planned_quantity: 150,
  priority: 9,
}

// Full work order response
const workOrder: WorkOrder = {
  id: 1,
  organization_id: 1,
  plant_id: 1,
  work_order_number: 'WO-2025-001',
  material_id: 1,
  order_type: 'PRODUCTION',
  order_status: 'PLANNED', // OrderStatus
  planned_quantity: 100,
  actual_quantity: 0,
  priority: 7,
  created_by_user_id: 1,
  created_at: new Date(),
  operations: [],
  materials: [],
}
```

---

## State Machine Flow

```
PLANNED
   ↓ (release)
RELEASED
   ↓ (start)
IN_PROGRESS
   ↓ (complete)
COMPLETED

(cancel from any state → CANCELLED)
```

Mutations enforce valid transitions via backend API.

---

## Validation Rules

- `material_id`: Required, must be > 0
- `order_type`: PRODUCTION | REWORK | ASSEMBLY (default: PRODUCTION)
- `planned_quantity`: Required, must be > 0 (accepts decimals)
- `priority`: 1-10 (default: 5)
- `start_date_planned`: Optional date
- `end_date_planned`: Optional date

All validation handled by Zod schema with proper error messages.
