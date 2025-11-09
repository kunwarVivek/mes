# DataTable Organism

## Overview
Production-ready, accessible data table component with sorting, filtering, pagination, and row selection. Built using strict TDD methodology (RED → GREEN → REFACTOR).

## Features
- **Data Display**: Render rows and columns from data array
- **Sorting**: Click column headers to sort ascending/descending
- **Filtering**: Text input filters per column
- **Pagination**: Configurable page size (10/25/50/100), navigation controls
- **Row Selection**: Individual and "select all" checkboxes
- **Empty State**: Custom message when no data
- **Loading State**: Skeleton rows during data fetch
- **Responsive**: Horizontal scroll on mobile, sticky header
- **Accessibility**: Full ARIA support, keyboard navigation

## Usage

### Basic Example
```tsx
import { DataTable, Column } from '@/design-system/organisms'

interface Material {
  id: number
  material_code: string
  name: string
  category: 'raw_material' | 'wip' | 'finished_good'
  stock_quantity: number
  unit_of_measure: string
}

const columns: Column<Material>[] = [
  {
    header: 'Material Code',
    accessor: 'material_code',
    sortable: true,
    filterable: true,
  },
  {
    header: 'Name',
    accessor: 'name',
    sortable: true,
    filterable: true,
  },
  {
    header: 'Category',
    accessor: 'category',
    sortable: true,
  },
  {
    header: 'Stock',
    accessor: 'stock_quantity',
    sortable: true,
    render: (value, row) => `${value} ${row.unit_of_measure}`
  },
]

function MaterialListPage() {
  const { data, isLoading } = useMaterials()

  return (
    <DataTable
      data={data}
      columns={columns}
      loading={isLoading}
      onRowClick={(row) => navigate(`/materials/${row.id}`)}
      emptyState={<p>No materials found. Create your first material.</p>}
    />
  )
}
```

### Advanced Example: Custom Rendering
```tsx
const columns: Column<WorkOrder>[] = [
  {
    header: 'Status',
    accessor: 'status',
    render: (value) => (
      <Badge variant={value === 'completed' ? 'success' : 'warning'}>
        {value}
      </Badge>
    ),
  },
  {
    header: 'Priority',
    accessor: row => row.priority_level, // Function accessor
    sortable: true,
    render: (value) => <PriorityIndicator level={value} />,
  },
  {
    header: 'Actions',
    accessor: () => null, // Computed column
    render: (_, row) => (
      <div>
        <IconButton onClick={() => editRow(row)} icon="edit" />
        <IconButton onClick={() => deleteRow(row)} icon="delete" />
      </div>
    ),
  },
]
```

## API

### DataTableProps<T>

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `T[]` | Required | Array of data objects to display |
| `columns` | `Column<T>[]` | Required | Column definitions |
| `loading` | `boolean` | `false` | Show loading skeleton |
| `pagination` | `boolean` | `true` | Enable pagination |
| `pageSize` | `number` | `25` | Initial rows per page |
| `pageSizeOptions` | `number[]` | `[10,25,50,100]` | Page size dropdown options |
| `onRowClick` | `(row: T) => void` | - | Row click handler |
| `emptyState` | `ReactNode` | `'No data found.'` | Custom empty state |
| `stickyHeader` | `boolean` | `true` | Sticky table header |
| `rowKey` | `keyof T \| (row: T) => string \| number` | `'id'` | Unique row identifier |

### Column<T>

| Property | Type | Description |
|----------|------|-------------|
| `header` | `string` | Column display name |
| `accessor` | `keyof T \| (row: T) => any` | Field key or accessor function |
| `sortable` | `boolean` | Enable column sorting |
| `filterable` | `boolean` | Enable column filtering |
| `render` | `(value: any, row: T) => ReactNode` | Custom cell renderer |
| `width` | `string` | Column width (e.g., "200px", "20%") |

## Accessibility

### ARIA Support
- `role="grid"` on table
- `role="columnheader"` on headers
- `role="row"` on rows
- `role="gridcell"` on cells
- `aria-sort` on sortable columns
- `aria-label` on all interactive elements
- `aria-selected` on selected rows

### Keyboard Navigation
- **Tab**: Navigate through interactive elements
- **Enter/Space**: Activate buttons, toggle checkboxes
- **Arrow Keys**: Navigate cells (future enhancement)

### Screen Reader Support
- All controls have descriptive labels
- Sort state announced
- Filter inputs labeled by column
- Page info announced
- Loading state indicated

## Styling

### CSS Variables
```css
--color-background: Background color
--color-neutral-50 to --color-neutral-900: Neutral colors
--color-primary-50 to --color-primary-600: Primary colors
--font-size-xs to --font-size-base: Typography sizes
--font-weight-medium to --font-weight-semibold: Font weights
--border-radius-sm to --border-radius-md: Border radius
--shadow-sm: Shadow
--transition-fast: Transition speed
```

### Customization
Override CSS classes:
- `.data-table-container`: Main container
- `.data-table`: Table element
- `.data-table__sort-button`: Sort buttons
- `.data-table__filter-input`: Filter inputs
- `.data-table__pagination`: Pagination controls
- `.data-table--sticky-header`: Sticky header variant

## Performance

### Optimizations
- **useMemo**: Filtered and paginated data cached
- **Skeleton Loading**: Prevents layout shift
- **Virtual Scrolling**: Future enhancement for 1000+ rows
- **Debounced Filters**: Future enhancement for expensive filters

### Best Practices
- Use `rowKey` for stable row identity
- Memoize `columns` array to prevent re-renders
- Keep `render` functions pure
- Paginate large datasets (>100 rows)

## Testing

### Test Coverage: 21/21 Tests Passing ✓

**Rendering Tests (3)**
- Renders table with data rows
- Renders column headers
- Renders custom cell content with render function

**Sorting Tests (3)**
- Sorts column ascending on first click
- Sorts column descending on second click
- Shows sort indicator icon

**Filtering Tests (2)**
- Filters rows by column value
- Shows no results when filter matches nothing

**Pagination Tests (4)**
- Paginates data with correct page size
- Changes page size when selector changed
- Navigates to next/previous page
- Shows correct page info (Showing 1-25 of 100)

**Selection Tests (2)**
- Selects individual row with checkbox
- Selects all rows with header checkbox

**State Tests (2)**
- Shows empty state when no data
- Shows loading skeleton when loading

**Accessibility Tests (2)**
- Has proper ARIA labels on interactive elements
- Keyboard navigation works (Tab, Enter)

**Other Tests (3)**
- Calls onRowClick when row is clicked
- Applies sticky header class when stickyHeader is true
- Uses custom rowKey function

## Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Migration Guide

### From Legacy Table
```diff
- <table>
-   <thead>
-     <tr><th>Name</th></tr>
-   </thead>
-   <tbody>
-     {data.map(row => <tr><td>{row.name}</td></tr>)}
-   </tbody>
- </table>
+ <DataTable
+   data={data}
+   columns={[
+     { header: 'Name', accessor: 'name', sortable: true }
+   ]}
+ />
```

### Benefits of Migration
- Instant sorting/filtering/pagination
- Accessibility built-in
- Consistent styling
- Responsive out of the box
- Loading states handled
- Selection management included

## Future Enhancements
- [ ] Column resizing
- [ ] Column reordering (drag-and-drop)
- [ ] Virtual scrolling for 1000+ rows
- [ ] Export to CSV/Excel
- [ ] Advanced filters (date range, multi-select)
- [ ] Column visibility toggle
- [ ] Saved table configurations
- [ ] Inline editing
- [ ] Expandable rows
- [ ] Grouping/aggregation

## Component Status
**Status**: Production Ready ✓
**Version**: 1.0.0
**TDD Evidence**: All 21 tests passing
**Accessibility**: WCAG 2.1 AA compliant
**Browser Tested**: Chrome, Firefox, Safari
**Mobile Tested**: iOS Safari, Chrome Android
**Critical Dependency**: Blocks all CRUD list pages
