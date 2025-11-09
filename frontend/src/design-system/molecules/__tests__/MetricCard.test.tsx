import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MetricCard } from '../MetricCard'
import { Activity } from 'lucide-react'

describe('MetricCard', () => {
  it('renders title and value', () => {
    render(<MetricCard title="Total Orders" value={150} />)
    expect(screen.getByText('Total Orders')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('shows unit when provided', () => {
    render(<MetricCard title="Efficiency" value={95} unit="%" />)
    expect(screen.getByText('95')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('shows trend indicator', () => {
    const { container, rerender } = render(
      <MetricCard title="Sales" value={100} trend="up" trendValue="+15%" />
    )
    expect(screen.getByText('+15%')).toBeInTheDocument()
    let svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()

    rerender(<MetricCard title="Sales" value={100} trend="down" trendValue="-5%" />)
    expect(screen.getByText('-5%')).toBeInTheDocument()
  })

  it('shows icon when provided', () => {
    const { container } = render(
      <MetricCard title="Activity" value={42} icon={<Activity data-testid="icon" />} />
    )
    expect(container.querySelector('[data-testid="icon"]')).toBeInTheDocument()
  })

  it('applies className', () => {
    const { container } = render(
      <MetricCard title="Test" value={1} className="custom-metric" />
    )
    const card = container.firstChild
    expect(card).toHaveClass('custom-metric')
  })
})
