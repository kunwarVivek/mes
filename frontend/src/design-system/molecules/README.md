# Domain-Specific Molecules

Manufacturing ERP molecules built on shadcn/ui atoms following atomic design principles.

## Components

### StatusBadge
Color-coded status indicators for machines, work orders, and quality checks.

```tsx
import { StatusBadge } from '@/design-system/molecules'

// Machine status
<StatusBadge status="running" withIcon withPulse />
<StatusBadge status="idle" />
<StatusBadge status="down" />

// Work order status
<StatusBadge status="in_progress" withPulse />
<StatusBadge status="completed" />

// Quality status
<StatusBadge status="pass" />
<StatusBadge status="fail" />
```

**Props:**
- `status`: Machine, work order, or quality status
- `withIcon?`: Show status icon
- `withPulse?`: Animate pulse for active statuses
- `size?`: 'sm' | 'md' | 'lg'
- `className?`: Additional CSS classes

---

### PriorityIndicator
Visual priority levels with icons.

```tsx
import { PriorityIndicator } from '@/design-system/molecules'

<PriorityIndicator priority="critical" withLabel />
<PriorityIndicator priority="high" withLabel />
<PriorityIndicator priority="medium" />
<PriorityIndicator priority="low" />
```

**Props:**
- `priority`: 'low' | 'medium' | 'high' | 'critical'
- `withLabel?`: Show priority text label
- `size?`: 'sm' | 'md' | 'lg'

---

### MetricCard
KPI display with trend indicators.

```tsx
import { MetricCard } from '@/design-system/molecules'
import { Activity } from 'lucide-react'

<MetricCard
  title="Total Orders"
  value={150}
  trend="up"
  trendValue="+15%"
  icon={<Activity />}
/>

<MetricCard
  title="Efficiency"
  value={95}
  unit="%"
  trend="down"
  trendValue="-2%"
/>
```

**Props:**
- `title`: Metric name
- `value`: Metric value (string or number)
- `unit?`: Unit of measurement
- `trend?`: 'up' | 'down' | 'neutral'
- `trendValue?`: Trend percentage or description
- `icon?`: React node icon
- `className?`: Additional CSS classes

---

### FilterGroup
Multi-select dropdown for filtering tables.

```tsx
import { FilterGroup } from '@/design-system/molecules'

const [selectedStatuses, setSelectedStatuses] = useState<string[]>([])

<FilterGroup
  label="Status"
  options={[
    { value: 'running', label: 'Running' },
    { value: 'idle', label: 'Idle' },
    { value: 'down', label: 'Down' },
  ]}
  value={selectedStatuses}
  onChange={setSelectedStatuses}
  placeholder="Filter by machine status"
/>
```

**Props:**
- `label`: Filter group label
- `options`: Array of { value, label } options
- `value`: Selected values array
- `onChange`: Selection change handler
- `placeholder?`: Custom placeholder text

---

### SearchBar
Search input with clear button.

```tsx
import { SearchBar } from '@/design-system/molecules'

const [query, setQuery] = useState('')

<SearchBar
  value={query}
  onChange={setQuery}
  onSearch={(q) => console.log('Searching for:', q)}
  placeholder="Search work orders..."
/>
```

**Props:**
- `value`: Current search value
- `onChange`: Value change handler
- `onSearch?`: Enter key / search handler
- `placeholder?`: Custom placeholder
- `className?`: Additional CSS classes

---

### Pagination
Table pagination controls.

```tsx
import { Pagination } from '@/design-system/molecules'

const [page, setPage] = useState(1)
const [pageSize, setPageSize] = useState(25)

<Pagination
  currentPage={page}
  totalPages={10}
  pageSize={pageSize}
  totalItems={250}
  onPageChange={setPage}
  onPageSizeChange={setPageSize}
  pageSizeOptions={[10, 25, 50, 100]}
/>
```

**Props:**
- `currentPage`: Current page number (1-indexed)
- `totalPages`: Total number of pages
- `pageSize`: Items per page
- `totalItems`: Total number of items
- `onPageChange`: Page change handler
- `onPageSizeChange`: Page size change handler
- `pageSizeOptions?`: Available page sizes (default: [10, 25, 50, 100])

---

### DateRangeFilter
Date range picker for filtering.

```tsx
import { DateRangeFilter } from '@/design-system/molecules'

const [from, setFrom] = useState<Date | null>(null)
const [to, setTo] = useState<Date | null>(null)

<DateRangeFilter
  from={from}
  to={to}
  onChange={(newFrom, newTo) => {
    setFrom(newFrom)
    setTo(newTo)
  }}
  label="Date Range"
/>
```

**Props:**
- `from`: Start date
- `to`: End date
- `onChange`: Date range change handler (from, to) => void
- `label?`: Label for the date range

---

### BreadcrumbNav
Page hierarchy navigation.

```tsx
import { BreadcrumbNav } from '@/design-system/molecules'

<BreadcrumbNav
  items={[
    { label: 'Dashboard', to: '/dashboard' },
    { label: 'Work Orders', to: '/work-orders' },
    { label: 'WO-001' }, // Current page (no link)
  ]}
/>
```

**Props:**
- `items`: Array of { label, to? } breadcrumb items
  - `label`: Display text
  - `to?`: Route path (omit for current page)

---

## Design Principles

### Atomic Design
Molecules compose shadcn atoms (Button, Badge, Card, Input, etc.) into domain-specific components.

### Accessibility
- ARIA labels and roles
- Keyboard navigation support
- Screen reader friendly

### Type Safety
All components are fully typed with TypeScript interfaces.

### Testing
All molecules have comprehensive test coverage (39 tests total).

## Dependencies

Built on:
- **shadcn/ui**: Base component primitives
- **Radix UI**: Accessible component primitives
- **Lucide React**: Icon library
- **TailwindCSS**: Styling

## Usage Pattern

```tsx
// Import molecules
import { StatusBadge, PriorityIndicator, MetricCard } from '@/design-system/molecules'

// Use in your components
function WorkOrderCard({ order }) {
  return (
    <Card>
      <StatusBadge status={order.status} withIcon />
      <PriorityIndicator priority={order.priority} withLabel />
      <MetricCard
        title="Completion"
        value={order.completion}
        unit="%"
        trend={order.trend}
        trendValue={order.trendValue}
      />
    </Card>
  )
}
```

## Contributing

When adding new molecules:
1. Write tests first (TDD)
2. Compose from existing atoms
3. Follow naming conventions
4. Document props and examples
5. Ensure accessibility
6. Export from index.ts
