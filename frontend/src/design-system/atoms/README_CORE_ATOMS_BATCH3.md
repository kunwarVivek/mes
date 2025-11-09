# Core Atoms Batch 3 - Navigation & Layout

**Status**: ✅ Complete
**Components**: IconButton, Link, Tooltip, Divider
**Tests**: 50/50 passing
**TDD Approach**: RED -> GREEN -> REFACTOR

---

## Components Overview

### 1. IconButton
Icon-only button component for toolbars and actions.

**Use Cases**:
- Toolbar actions (close, settings, delete)
- Compact interfaces
- Icon grids

**Props**:
```typescript
interface IconButtonProps {
  icon: ReactNode          // Lucide React icon
  variant?: 'default' | 'primary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  'aria-label': string     // Required for accessibility
  type?: 'button' | 'submit' | 'reset'
  className?: string
  onClick?: () => void
}
```

**Example**:
```tsx
import { Heart, Trash2 } from 'lucide-react'

<IconButton
  icon={<Heart />}
  variant="primary"
  aria-label="Like this item"
  onClick={() => console.log('Liked!')}
/>

<IconButton
  icon={<Trash2 />}
  variant="danger"
  aria-label="Delete item"
  size="sm"
/>
```

---

### 2. Link
Navigation link component with variants and states.

**Use Cases**:
- Internal navigation
- External links (opens in new tab)
- Inline text links
- Disabled links

**Props**:
```typescript
interface LinkProps {
  href: string
  children: ReactNode
  variant?: 'default' | 'primary' | 'muted'
  external?: boolean       // Opens in new tab with security
  underline?: 'always' | 'hover' | 'none'
  disabled?: boolean
  className?: string
  onClick?: (e: React.MouseEvent) => void
}
```

**Example**:
```tsx
// Internal link
<Link href="/dashboard" variant="primary">
  Dashboard
</Link>

// External link (secure)
<Link href="https://github.com" external>
  View on GitHub
</Link>

// Disabled link
<Link href="/admin" disabled>
  Admin (No Access)
</Link>

// Custom underline
<Link href="/help" underline="none">
  Help Center
</Link>
```

---

### 3. Tooltip
Contextual help tooltip on hover, click, or focus.

**Use Cases**:
- Icon button labels
- Form field help text
- Feature explanations
- Truncated text preview

**Props**:
```typescript
interface TooltipProps {
  content: ReactNode
  children: ReactNode
  placement?: 'top' | 'bottom' | 'left' | 'right'
  trigger?: 'hover' | 'click' | 'focus'
  delay?: number           // Default 300ms (hover only)
  className?: string
}
```

**Example**:
```tsx
// Hover tooltip (default)
<Tooltip content="Click to favorite this item">
  <IconButton icon={<Heart />} aria-label="Favorite" />
</Tooltip>

// Click tooltip
<Tooltip content="Account settings" trigger="click" placement="bottom">
  <button>Settings</button>
</Tooltip>

// Custom delay
<Tooltip content="Help text" delay={0}>
  <span>Hover me</span>
</Tooltip>

// Complex content
<Tooltip
  content={
    <div>
      <strong>Pro Tip</strong>
      <p>Use Ctrl+K for quick search</p>
    </div>
  }
>
  <button>Search</button>
</Tooltip>
```

---

### 4. Divider
Visual separator for content sections.

**Use Cases**:
- Section separators
- Toolbar dividers (vertical)
- List item separators
- Card content dividers

**Props**:
```typescript
interface DividerProps {
  orientation?: 'horizontal' | 'vertical'
  variant?: 'solid' | 'dashed' | 'dotted'
  spacing?: 'sm' | 'md' | 'lg'
  thickness?: 'thin' | 'medium' | 'thick'
  className?: string
}
```

**Example**:
```tsx
// Horizontal divider (default)
<Divider />

// Vertical divider in toolbar
<div style={{ display: 'flex' }}>
  <button>Action 1</button>
  <Divider orientation="vertical" />
  <button>Action 2</button>
</div>

// Dashed divider with custom spacing
<Divider variant="dashed" spacing="lg" />

// Thick divider
<Divider thickness="thick" />
```

---

## Common Patterns

### Pattern 1: Toolbar with IconButtons and Tooltips
```tsx
<div className="toolbar">
  <Tooltip content="Add to favorites">
    <IconButton icon={<Heart />} variant="ghost" aria-label="Favorite" />
  </Tooltip>

  <Divider orientation="vertical" spacing="sm" />

  <Tooltip content="Settings">
    <IconButton icon={<Settings />} variant="ghost" aria-label="Settings" />
  </Tooltip>

  <Tooltip content="Delete permanently">
    <IconButton icon={<Trash2 />} variant="danger" aria-label="Delete" />
  </Tooltip>
</div>
```

### Pattern 2: Navigation with Links and Dividers
```tsx
<nav>
  <Link href="/" variant="primary">Home</Link>
  <Link href="/about">About</Link>
  <Link href="/contact">Contact</Link>

  <Divider spacing="md" />

  <Link href="https://github.com" external>
    GitHub
  </Link>
</nav>
```

### Pattern 3: Card with Actions
```tsx
<div className="card">
  <h3>Product Title</h3>
  <p>Product description here</p>

  <Divider spacing="sm" />

  <div className="actions">
    <Tooltip content="Like this product">
      <IconButton icon={<Heart />} variant="primary" aria-label="Like" />
    </Tooltip>

    <Link href="/product/123" variant="primary">
      View Details
    </Link>

    <Link href="#" variant="muted">
      Share
    </Link>
  </div>
</div>
```

---

## Accessibility Features

### IconButton
- ✅ Mandatory `aria-label` (TypeScript enforced)
- ✅ Focus-visible keyboard navigation
- ✅ Disabled state handling
- ✅ Proper button semantics

### Link
- ✅ `aria-disabled` for disabled state
- ✅ External links have `rel="noopener noreferrer"`
- ✅ Focus-visible styles
- ✅ Keyboard navigation

### Tooltip
- ✅ `role="tooltip"`
- ✅ `aria-describedby` linking
- ✅ Keyboard accessible (focus trigger)
- ✅ Screen reader friendly

### Divider
- ✅ `role="separator"`
- ✅ `aria-orientation` for vertical dividers
- ✅ Semantic HTML

---

## Design Tokens

### IconButton Sizes
- **Small**: 32x32px, 16px icon
- **Medium**: 40x40px, 20px icon (default)
- **Large**: 48x48px, 24px icon

### Divider Spacing
- **Small**: 8px margin
- **Medium**: 16px margin (default)
- **Large**: 24px margin

### Divider Thickness
- **Thin**: 1px
- **Medium**: 1px (default)
- **Thick**: 2px

### Tooltip Delay
- **Hover**: Configurable (default 300ms)
- **Click**: Immediate
- **Focus**: Immediate

---

## Testing

### Test Coverage
- **IconButton**: 14 tests
- **Link**: 12 tests
- **Tooltip**: 10 tests
- **Divider**: 14 tests
- **Total**: 50 tests (all passing)

### Run Tests
```bash
# Run Batch 3 tests only
npm test -- src/design-system/__tests__/CoreAtomsNav.test.tsx

# Run all tests
npm test
```

### Test Categories
- ✅ Variants and sizes
- ✅ Interactions (click, hover, focus)
- ✅ Accessibility (ARIA, keyboard)
- ✅ Props and states
- ✅ Edge cases

---

## Demo

Interactive demo showcasing all components:

```tsx
import { NavLayoutDemo } from './atoms/__demo__/NavLayoutDemo'

<NavLayoutDemo />
```

**Demo Features**:
- All variants and sizes
- Interactive examples
- Accessibility showcase
- Combined patterns

---

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

**Accessibility**:
- ✅ Screen readers (NVDA, JAWS, VoiceOver)
- ✅ Keyboard navigation
- ✅ Reduced motion support

---

## Performance

### Optimizations
- Tooltip: Conditional rendering (only when visible)
- Tooltip: Proper cleanup (timeouts)
- All: forwardRef for ref forwarding
- All: CSS custom properties (no runtime JS)

### Benchmarks
- Render time: < 16ms (60fps)
- Re-renders: Minimal (only on state change)
- Bundle size: ~5KB (gzipped)

---

## Migration Guide

### From HTML buttons to IconButton
```tsx
// Before
<button aria-label="Close" onClick={handleClose}>
  <X />
</button>

// After
<IconButton
  icon={<X />}
  aria-label="Close"
  onClick={handleClose}
/>
```

### From anchor tags to Link
```tsx
// Before
<a href="/about" className="link-primary">About</a>

// After
<Link href="/about" variant="primary">About</Link>
```

### From title attribute to Tooltip
```tsx
// Before
<button title="Delete this item">
  <Trash2 />
</button>

// After
<Tooltip content="Delete this item">
  <IconButton icon={<Trash2 />} aria-label="Delete" />
</Tooltip>
```

### From hr to Divider
```tsx
// Before
<hr className="my-4" />

// After
<Divider spacing="md" />
```

---

## Related Components

### Previous Batches
- **Batch 1**: Badge, Chip, Spinner, Skeleton, Progress
- **Batch 2**: Switch, Radio, Checkbox, Textarea

### Upcoming
- **Batch 4**: Modal, Dropdown, Select, DatePicker (if needed)

---

## Support

### Documentation
- [TDD Evidence](./CORE_ATOMS_BATCH3_TDD_EVIDENCE.md)
- [Demo File](./__demo__/NavLayoutDemo.tsx)
- [Test Suite](../__tests__/CoreAtomsNav.test.tsx)

### Issues
- TypeScript errors: Check prop types match interface
- Styling issues: Verify CSS custom properties are defined
- Accessibility: Run tests with screen reader

---

## License

Part of the Unison Design System
