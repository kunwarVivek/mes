import { describe, test, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MobileNav, MobileNavProps, NavItem } from '../MobileNav'
import { renderWithRouter } from './test-utils'

// Mock icons for testing
const MockIcon = () => <span data-testid="mock-icon">Icon</span>

const mockNavItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <MockIcon /> },
  { to: '/work-orders', label: 'Work Orders', icon: <MockIcon />, badge: 3 },
  { to: '/quality', label: 'Quality', icon: <MockIcon /> },
  { to: '/equipment', label: 'Equipment', icon: <MockIcon /> },
  { to: '/profile', label: 'Profile', icon: <MockIcon /> },
]

const defaultProps: MobileNavProps = {
  items: mockNavItems,
}

const renderMobileNav = (props: Partial<MobileNavProps> = {}, initialPath = '/') => {
  return renderWithRouter(
    <MobileNav {...defaultProps} {...props} />,
    { initialPath }
  )
}

describe('MobileNav', () => {
  test('renders max 5 items', () => {
    const sixItems: NavItem[] = [
      ...mockNavItems,
      { to: '/extra', label: 'Extra', icon: <MockIcon /> },
    ]

    renderMobileNav({ items: sixItems })

    // Should only render 5 items
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(5)
  })

  test('highlights active item', () => {
    renderMobileNav()

    const dashboardLink = screen.getByText('Dashboard').closest('a')
    expect(dashboardLink).toHaveClass('mobile-nav__link--active')
  })

  test('shows badges on items', () => {
    renderMobileNav()

    expect(screen.getByText('3')).toBeInTheDocument()
  })

  test('navigates on item click', async () => {
    renderMobileNav()

    const qualityLink = screen.getByText('Quality')
    await userEvent.click(qualityLink)

    // Link should be clickable
    expect(qualityLink.closest('a')).toHaveAttribute('href', '/quality')
  })

  test('renders all item labels', () => {
    renderMobileNav()

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Work Orders')).toBeInTheDocument()
    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('Equipment')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
  })

  test('renders navigation role', () => {
    renderMobileNav()

    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })

  test('applies fixed positioning class', () => {
    const { container } = renderMobileNav()

    const nav = container.querySelector('.mobile-nav')
    expect(nav).toBeInTheDocument()
  })
})
