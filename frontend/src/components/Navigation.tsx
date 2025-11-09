import { Link } from '@tanstack/react-router'
import {
  Home,
  Package,
  Users,
  ClipboardList,
  FileText,
  CheckSquare,
  Wrench,
} from 'lucide-react'
import './Navigation.css'

/**
 * Navigation Component
 *
 * Main application navigation menu:
 * - Single Responsibility: Navigation menu
 * - Uses TanStack Router Link for type-safe navigation
 * - Active link highlighting
 * - Icon-based navigation items
 */

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <Home /> },
  { to: '/materials', label: 'Materials', icon: <Package /> },
  { to: '/work-orders', label: 'Work Orders', icon: <ClipboardList /> },
  { to: '/bom', label: 'BOM', icon: <FileText /> },
  { to: '/quality', label: 'Quality', icon: <CheckSquare /> },
  { to: '/equipment', label: 'Equipment', icon: <Wrench /> },
  { to: '/users', label: 'Users', icon: <Users /> },
]

export const Navigation = () => {
  return (
    <nav className="navigation" aria-label="Main navigation">
      <ul className="navigation__list">
        {navItems.map((item) => (
          <li key={item.to} className="navigation__item">
            <Link
              to={item.to}
              className="navigation__link"
              activeProps={{ className: 'navigation__link--active' }}
            >
              <span className="navigation__icon">{item.icon}</span>
              <span className="navigation__label">{item.label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}

Navigation.displayName = 'Navigation'
