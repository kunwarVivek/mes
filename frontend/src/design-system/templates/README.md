# Layout Templates

Production-ready page layout templates built using Atomic Design principles and TDD methodology.

## Components

### 1. Sidebar

Navigation sidebar with responsive behavior.

```tsx
import { Sidebar } from '@/design-system/templates'

// Permanent variant (desktop)
<Sidebar isOpen={true} onClose={() => {}} variant="permanent">
  <nav>Navigation items</nav>
</Sidebar>

// Temporary variant (mobile drawer)
<Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} variant="temporary">
  <nav>Navigation items</nav>
</Sidebar>
```

**Features**:
- Permanent variant: Always visible on desktop
- Temporary variant: Mobile drawer with backdrop
- Keyboard navigation: Escape key closes drawer
- Accessibility: Proper ARIA roles and labels

### 2. Navbar

Top navigation bar with menu toggle and actions.

```tsx
import { Navbar } from '@/design-system/templates'

<Navbar
  title="Dashboard"
  showMenuButton
  onMenuClick={() => toggleSidebar()}
  actions={
    <>
      <IconButton icon={<Bell />} aria-label="Notifications" />
      <IconButton icon={<User />} aria-label="User menu" />
    </>
  }
/>
```

**Features**:
- Optional title display
- Menu button for mobile
- Custom actions slot
- Sticky positioning

### 3. AppLayout

Main application shell combining sidebar, navbar, and content area.

```tsx
import { AppLayout } from '@/design-system/templates'

// With default sidebar and navbar
<AppLayout>
  <YourPageContent />
</AppLayout>

// With custom sidebar and navbar
<AppLayout
  sidebar={<CustomSidebar />}
  navbar={<CustomNavbar />}
>
  <YourPageContent />
</AppLayout>
```

**Features**:
- Responsive layout grid
- Default sidebar and navbar included
- Custom component overrides
- Automatic sidebar toggle on mobile

### 4. AuthLayout

Centered card layout for authentication pages.

```tsx
import { AuthLayout } from '@/design-system/templates'

<AuthLayout
  logo={<YourLogo />}
  title="Sign In"
  subtitle="Welcome back to your account"
>
  <LoginForm />
</AuthLayout>
```

**Features**:
- Centered card design
- Optional logo, title, subtitle
- Responsive: Full-width on mobile, card on desktop
- Background gradient

## Usage Example

### Complete App with Layouts

```tsx
import { AppLayout, AuthLayout } from '@/design-system/templates'
import { Sidebar, Navbar } from '@/design-system/templates'

// Dashboard page
function DashboardPage() {
  return (
    <AppLayout>
      <h1>Dashboard</h1>
      <YourContent />
    </AppLayout>
  )
}

// Login page
function LoginPage() {
  return (
    <AuthLayout
      title="Sign In"
      subtitle="Enter your credentials"
    >
      <LoginForm />
    </AuthLayout>
  )
}
```

## Responsive Breakpoints

- **Mobile**: < 768px (sidebar becomes drawer)
- **Tablet**: 768px - 1024px (sidebar collapsible)
- **Desktop**: > 1024px (sidebar permanent)

## Accessibility

All templates follow WCAG 2.1 Level AA guidelines:

- Semantic HTML (`nav`, `main`, `aside`, `header`)
- Proper ARIA roles and labels
- Keyboard navigation support
- Focus management in mobile drawer
- Screen reader friendly

## Testing

Comprehensive test coverage with 29 tests:
- Sidebar: 10 tests (variants, states, keyboard)
- Navbar: 7 tests (title, menu, actions)
- AppLayout: 6 tests (composition, responsiveness)
- AuthLayout: 6 tests (layout, content)

Run tests:
```bash
npm test -- src/design-system/__tests__/LayoutTemplates.test.tsx
```

## File Structure

```
templates/
├── Sidebar.tsx          # Sidebar component
├── Sidebar.css          # Sidebar styles
├── Navbar.tsx           # Navbar component
├── Navbar.css           # Navbar styles
├── AppLayout.tsx        # App layout component
├── AppLayout.css        # App layout styles
├── AuthLayout.tsx       # Auth layout component
├── AuthLayout.css       # Auth layout styles
├── index.ts             # Exports
└── README.md            # This file
```

## Dependencies

Built using existing atoms:
- IconButton (for close/menu buttons)
- Uses ThemeProvider for theming
- Lucide React icons (Menu, X)

## Design Principles

1. **Single Responsibility**: Each template has one clear purpose
2. **Composition over Configuration**: Use children and slots
3. **Progressive Enhancement**: Works without JavaScript for core functionality
4. **Mobile First**: Responsive by default
5. **Accessibility First**: ARIA and keyboard navigation built-in
