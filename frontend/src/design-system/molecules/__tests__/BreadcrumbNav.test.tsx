import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BreadcrumbNav } from '../BreadcrumbNav'

// Mock TanStack Router Link
vi.mock('@tanstack/react-router', () => ({
  Link: ({ to, children, className }: { to: string; children: React.ReactNode; className?: string }) => (
    <a href={to} className={className}>{children}</a>
  ),
}))

describe('BreadcrumbNav', () => {
  it('renders all breadcrumb items', () => {
    const items = [
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Work Orders', to: '/work-orders' },
      { label: 'WO-001' },
    ]

    render(<BreadcrumbNav items={items} />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Work Orders')).toBeInTheDocument()
    expect(screen.getByText('WO-001')).toBeInTheDocument()
  })

  it('shows separator between items', () => {
    const items = [
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Orders' },
    ]

    const { container } = render(<BreadcrumbNav items={items} />)
    const separators = container.querySelectorAll('svg')
    expect(separators.length).toBeGreaterThan(0)
  })

  it('last item is not a link', () => {
    const items = [
      { label: 'Dashboard', to: '/dashboard' },
      { label: 'Current Page' },
    ]

    render(<BreadcrumbNav items={items} />)

    const dashboardLink = screen.getByText('Dashboard')
    expect(dashboardLink.tagName).toBe('A')

    const currentPage = screen.getByText('Current Page')
    expect(currentPage.tagName).toBe('SPAN')
  })
})
