import { describe, test, expect, vi } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar, SidebarProps, NavItem } from '../Sidebar'
import { renderWithRouter } from './test-utils'

// Mock icons for testing
const MockIcon = () => <span data-testid="mock-icon">Icon</span>

const mockNavItems: NavItem[] = [
  {
    to: '/',
    label: 'Dashboard',
    icon: <MockIcon />,
  },
  {
    to: '/materials',
    label: 'Materials',
    icon: <MockIcon />,
    badge: 3,
  },
  {
    to: '/work-orders',
    label: 'Work Orders',
    icon: <MockIcon />,
    children: [
      { to: '/work-orders/planned', label: 'Planned', icon: <MockIcon /> },
      { to: '/work-orders/active', label: 'Active', icon: <MockIcon /> },
    ],
  },
]

const defaultProps: SidebarProps = {
  open: true,
  onClose: vi.fn(),
  items: mockNavItems,
  collapsed: false,
}

const renderSidebar = (props: Partial<SidebarProps> = {}, initialPath = '/') => {
  return renderWithRouter(
    <Sidebar {...defaultProps} {...props} />,
    { initialPath }
  )
}

describe('Sidebar', () => {
  test('renders navigation items', async () => {
    renderSidebar()

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
    expect(screen.getByText('Materials')).toBeInTheDocument()
    expect(screen.getByText('Work Orders')).toBeInTheDocument()
  })

  test('highlights active link', async () => {
    renderSidebar()

    await waitFor(() => {
      const dashboardLink = screen.getByText('Dashboard').closest('a')
      expect(dashboardLink).toHaveClass('sidebar__link--active')
    })
  })

  test('closes on Escape key', async () => {
    const onClose = vi.fn()
    renderSidebar({ onClose, open: true })

    fireEvent.keyDown(window, { key: 'Escape' })

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    })
  })

  test('closes on backdrop click', async () => {
    const onClose = vi.fn()
    renderSidebar({ onClose, open: true })

    const backdrop = screen.getByRole('presentation', { hidden: true })
    fireEvent.click(backdrop)

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled()
    })
  })

  test('collapses to icon-only mode', () => {
    renderSidebar({ collapsed: true })

    // Labels should not be visible when collapsed
    const dashboardLabel = screen.queryByText('Dashboard')
    expect(dashboardLabel).not.toBeInTheDocument()

    // Icons should still be visible
    const icons = screen.getAllByTestId('mock-icon')
    expect(icons.length).toBeGreaterThan(0)
  })

  test('renders nested navigation items', async () => {
    renderSidebar({ collapsed: false })

    await waitFor(() => {
      expect(screen.getByText('Planned')).toBeInTheDocument()
    })
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  test('shows notification badges', async () => {
    renderSidebar()

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  test('does not render backdrop when closed', () => {
    renderSidebar({ open: false })

    const backdrop = screen.queryByRole('presentation', { hidden: true })
    expect(backdrop).not.toBeInTheDocument()
  })

  test('calls onToggleCollapse when toggle button is clicked', async () => {
    const onToggleCollapse = vi.fn()
    renderSidebar({ onToggleCollapse, collapsed: false })

    const toggleButton = await screen.findByLabelText('Collapse sidebar')
    await userEvent.click(toggleButton)

    expect(onToggleCollapse).toHaveBeenCalled()
  })

  test('applies open class when open prop is true', async () => {
    renderSidebar({ open: true })

    await waitFor(() => {
      const sidebar = document.querySelector('.sidebar')
      expect(sidebar).toHaveClass('sidebar--open')
    })
  })

  test('applies collapsed class when collapsed prop is true', async () => {
    renderSidebar({ collapsed: true })

    await waitFor(() => {
      const sidebar = document.querySelector('.sidebar')
      expect(sidebar).toHaveClass('sidebar--collapsed')
    })
  })

  test('hides nested items when collapsed', () => {
    renderSidebar({ collapsed: true })

    // Nested items should not be visible when sidebar is collapsed
    expect(screen.queryByText('Planned')).not.toBeInTheDocument()
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  test('closes sidebar when link is clicked', async () => {
    const onClose = vi.fn()
    renderSidebar({ onClose, open: true })

    const materialsLink = await screen.findByText('Materials')
    await userEvent.click(materialsLink)

    expect(onClose).toHaveBeenCalled()
  })
})
