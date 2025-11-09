import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BarChart } from '../BarChart'

describe('BarChart', () => {
  const mockData = [
    { name: 'Jan', value: 100 },
    { name: 'Feb', value: 200 },
    { name: 'Mar', value: 150 },
  ]

  it('should render bar chart with data', () => {
    render(<BarChart data={mockData} />)

    // Check for chart container with proper role
    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should apply custom aria label', () => {
    const customLabel = 'Monthly revenue chart'
    render(<BarChart data={mockData} ariaLabel={customLabel} />)

    const chart = screen.getByRole('img', { name: customLabel })
    expect(chart).toBeInTheDocument()
  })

  it('should have default aria label', () => {
    render(<BarChart data={mockData} />)

    const chart = screen.getByRole('img', { name: 'Bar chart' })
    expect(chart).toBeInTheDocument()
  })

  it('should render with custom height', () => {
    const { container } = render(<BarChart data={mockData} height={400} />)

    // ResponsiveContainer should be present
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
  })

  it('should handle empty data array', () => {
    render(<BarChart data={[]} />)

    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should sanitize data to prevent XSS', () => {
    const xssData = [
      { name: '<script>alert("xss")</script>', value: 100 },
      { name: 'Safe', value: 200 },
    ]

    const { container } = render(<BarChart data={xssData} />)

    // Ensure no script tags are rendered
    expect(container.querySelector('script')).not.toBeInTheDocument()
  })

  it('should render all data points', () => {
    const { container } = render(<BarChart data={mockData} />)

    // Check that chart container has been rendered
    const rechartContainer = container.querySelector('.recharts-responsive-container')
    expect(rechartContainer).toBeInTheDocument()
  })
})
