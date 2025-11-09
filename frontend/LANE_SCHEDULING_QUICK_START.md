# Lane Scheduling - Quick Start Guide

## Integration into Application

### 1. Add to Router

```typescript
// In your router configuration (src/router.tsx or similar)
import { LaneSchedulingPage } from '@/features/lanes/pages/LaneSchedulingPage'

// Add route
{
  path: '/lanes',
  element: <LaneSchedulingPage />
}
```

### 2. Add to Navigation

```typescript
// In your navigation component
<Link to="/lanes">Lane Scheduling</Link>
```

### 3. Component Usage Examples

#### Basic CalendarGrid

```typescript
import { CalendarGrid } from '@/features/lanes/components/CalendarGrid'
import { useLanes, useLaneAssignments } from '@/features/lanes/hooks/useLanes'

function MyComponent() {
  const [startDate, setStartDate] = useState(new Date())
  const { data: lanesData } = useLanes(plantId)
  const { data: assignmentsData } = useLaneAssignments({
    plant_id: plantId,
    start_date: '2025-01-15',
    end_date: '2025-01-22'
  })

  return (
    <CalendarGrid
      lanes={lanesData?.items || []}
      assignments={assignmentsData?.items || []}
      startDate={startDate}
      daysToShow={7}
      onDateChange={setStartDate}
      onCellClick={(laneId, date) => console.log('Cell clicked:', laneId, date)}
      isLoading={false}
    />
  )
}
```

#### Assignment Form

```typescript
import { AssignmentForm } from '@/features/lanes/components/AssignmentForm'
import { useCreateAssignment } from '@/features/lanes/hooks/useLanes'

function MyModal() {
  const createMutation = useCreateAssignment()

  const handleSubmit = async (data) => {
    await createMutation.mutateAsync(data)
  }

  return (
    <AssignmentForm
      preSelectedLane={1}
      preSelectedDate="2025-01-15"
      onSubmit={handleSubmit}
      onCancel={() => console.log('Cancelled')}
      isLoading={createMutation.isPending}
    />
  )
}
```

#### Assignment Card

```typescript
import { AssignmentCard } from '@/features/lanes/components/AssignmentCard'

function MyCalendar() {
  return (
    <AssignmentCard
      assignment={myAssignment}
      onClick={(assignment) => console.log('Edit:', assignment)}
      startDate={new Date('2025-01-15')}
      daysToShow={7}
    />
  )
}
```

## API Service Usage

### Direct Service Calls

```typescript
import { lanesService } from '@/features/lanes/services/lanes.service'

// List lanes
const lanes = await lanesService.listLanes({ plant_id: 100 })

// Get capacity
const capacity = await lanesService.getLaneCapacity(1, '2025-01-15')

// Create assignment
const newAssignment = await lanesService.createAssignment({
  organization_id: 1,
  plant_id: 100,
  lane_id: 1,
  work_order_id: 500,
  scheduled_start: '2025-01-15',
  scheduled_end: '2025-01-20',
  allocated_capacity: 500,
  priority: 1,
})

// Update assignment
const updated = await lanesService.updateAssignment(1, {
  allocated_capacity: 600,
  status: 'ACTIVE'
})

// Delete assignment
await lanesService.deleteAssignment(1)
```

### Using Hooks (Recommended)

```typescript
import {
  useLanes,
  useLaneAssignments,
  useCreateAssignment,
  useUpdateAssignment,
  useDeleteAssignment
} from '@/features/lanes/hooks/useLanes'

function MyComponent() {
  // Queries
  const { data: lanes, isLoading } = useLanes(plantId)
  const { data: assignments } = useLaneAssignments({
    lane_id: 1,
    start_date: '2025-01-15',
    end_date: '2025-01-22'
  })

  // Mutations
  const createMutation = useCreateAssignment()
  const updateMutation = useUpdateAssignment()
  const deleteMutation = useDeleteAssignment()

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      organization_id: 1,
      plant_id: 100,
      lane_id: 1,
      work_order_id: 500,
      scheduled_start: '2025-01-15',
      scheduled_end: '2025-01-20',
      allocated_capacity: 500,
      priority: 1,
    })
    // Cache is automatically invalidated
  }

  const handleUpdate = async (id: number) => {
    await updateMutation.mutateAsync({
      id,
      data: { allocated_capacity: 600 }
    })
  }

  const handleDelete = async (id: number) => {
    await deleteMutation.mutateAsync(id)
  }

  return (
    // Your component JSX
  )
}
```

## Date Formatting Utilities

```typescript
// Format date for API (YYYY-MM-DD)
const formatDateForAPI = (date: Date): string => {
  return date.toLocaleDateString('en-CA')
}

// Format date for display
const formatDateForDisplay = (date: Date): string => {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}

// Get day of week
const getDayOfWeek = (date: Date): string => {
  return date.toLocaleDateString('en-US', {
    weekday: 'short'
  })
}
```

## Capacity Calculation

```typescript
// Calculate utilization for a specific lane and date
function calculateUtilization(
  laneId: number,
  date: Date,
  lanes: Lane[],
  assignments: LaneAssignment[]
): number {
  const dateStr = formatDateForAPI(date)
  const lane = lanes.find(l => l.id === laneId)
  if (!lane) return 0

  const cellAssignments = assignments.filter(a => {
    return (
      a.lane_id === laneId &&
      dateStr >= a.scheduled_start &&
      dateStr <= a.scheduled_end
    )
  })

  const allocated = cellAssignments.reduce(
    (sum, a) => sum + a.allocated_capacity,
    0
  )

  return (allocated / lane.capacity_per_day) * 100
}

// Get color for utilization
function getUtilizationColor(utilization: number): string {
  if (utilization > 100) return 'bg-red-100 border-red-400'
  if (utilization >= 80) return 'bg-yellow-100 border-yellow-400'
  return 'bg-green-100 border-green-400'
}
```

## Assignment Positioning

```typescript
// Calculate assignment position on calendar
function calculateAssignmentPosition(
  assignment: LaneAssignment,
  startDate: Date,
  daysToShow: number
): { left: string; width: string } {
  const assignmentStart = new Date(assignment.scheduled_start)
  const assignmentEnd = new Date(assignment.scheduled_end)

  // Day offset from calendar start
  const dayOffset = Math.floor(
    (assignmentStart.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
  )

  // Width in days
  const widthInDays = Math.floor(
    (assignmentEnd.getTime() - assignmentStart.getTime()) / (1000 * 60 * 60 * 24)
  ) + 1

  const dayPercentage = 100 / daysToShow

  return {
    left: `${dayOffset * dayPercentage}%`,
    width: `${widthInDays * dayPercentage}%`,
  }
}
```

## Type Definitions

```typescript
import type {
  Lane,
  LaneAssignment,
  LaneCapacity,
  LaneAssignmentStatus,
  LaneListResponse,
  LaneAssignmentListResponse,
  LaneAssignmentCreateRequest,
  LaneAssignmentUpdateRequest
} from '@/features/lanes/types/lane.types'

// Status enum values
const status: LaneAssignmentStatus = 'PLANNED' // or 'ACTIVE', 'COMPLETED', 'CANCELLED'

// Create request example
const createRequest: LaneAssignmentCreateRequest = {
  organization_id: 1,
  plant_id: 100,
  lane_id: 1,
  work_order_id: 500,
  scheduled_start: '2025-01-15',
  scheduled_end: '2025-01-20',
  allocated_capacity: 500,
  priority: 1,
  notes: 'Optional notes',
  project_id: 10, // optional
}

// Update request example
const updateRequest: LaneAssignmentUpdateRequest = {
  scheduled_start: '2025-01-16',
  allocated_capacity: 600,
  status: 'ACTIVE',
}
```

## Testing

### Run Tests

```bash
# Run all lane feature tests
npm test -- src/features/lanes/__tests__/

# Run specific test file
npm test -- src/features/lanes/__tests__/CalendarGrid.test.tsx

# Run tests in watch mode
npm test -- --watch src/features/lanes/
```

### Test Coverage

All critical functionality is tested:
- Types validation (6 tests)
- Service API methods (9 tests)
- Hooks queries and mutations (8 tests)
- CalendarGrid rendering and interactions (6 tests)
- AssignmentCard display and clicks (3 tests)

Total: 32 tests passing

## Common Patterns

### Loading States

```typescript
const { data, isLoading, error } = useLanes(plantId)

if (isLoading) return <Spinner size="lg" />
if (error) return <div>Error loading lanes</div>
if (!data) return null

return <CalendarGrid lanes={data.items} ... />
```

### Error Handling

```typescript
const createMutation = useCreateAssignment()

const handleSubmit = async (data) => {
  try {
    await createMutation.mutateAsync(data)
    toast.success('Assignment created')
  } catch (error) {
    toast.error('Failed to create assignment')
    console.error(error)
  }
}
```

### Optimistic Updates

```typescript
const updateMutation = useUpdateAssignment()

updateMutation.mutate(
  { id: 1, data: { status: 'ACTIVE' } },
  {
    onSuccess: () => {
      queryClient.invalidateQueries(['lane-assignments'])
    },
    onError: (error) => {
      console.error('Update failed:', error)
    }
  }
)
```

## Troubleshooting

### Calendar not displaying dates correctly
- Ensure startDate is a valid Date object
- Check timezone: use `new Date()` and `.setHours(0, 0, 0, 0)` to reset time
- Date format for API must be YYYY-MM-DD (use `toLocaleDateString('en-CA')`)

### Assignments not showing on calendar
- Verify assignment dates are within calendar date range
- Check that lane_id matches between assignment and lane
- Ensure date strings are in correct format (YYYY-MM-DD)

### Capacity calculation incorrect
- Check that lane.capacity_per_day is set correctly
- Verify assignment.allocated_capacity values
- Ensure date range filtering includes all relevant assignments

### Form validation errors
- End date must be >= start date
- Allocated capacity must be > 0
- Required fields: lane_id, work_order_id, scheduled_start, scheduled_end

## Performance Tips

1. **Use Query Filters**: Only fetch assignments for visible date range
2. **Cache Configuration**: TanStack Query automatically caches results
3. **Pagination**: For large lane lists, use page/page_size parameters
4. **Debounce**: Debounce date navigation to reduce API calls
5. **Memoization**: Memoize expensive calculations in large calendars

## Accessibility

- All interactive elements have proper ARIA labels
- Keyboard navigation supported
- Screen reader friendly
- Color coding supplemented with text
- Form errors announced to assistive technologies

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ JavaScript required
- Date API support required
- CSS Grid and Flexbox support required

## Further Reading

- TanStack Query Documentation: https://tanstack.com/query/latest
- Design System Atoms: `/src/design-system/atoms/`
- Backend API Documentation: Check backend OpenAPI/Swagger docs
- Testing Guide: `/src/test/setup.ts`
