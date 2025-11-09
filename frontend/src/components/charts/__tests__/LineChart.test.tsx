import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LineChart } from '../LineChart'

describe('LineChart', () => {
  const mockData = [
    { name: 'Jan', value: 100 },
    { name: 'Feb', value: 200 },
    { name: 'Mar', value: 150 },
    { name: 'Apr', value: 300 },
  ]

  it('should render line chart with data', () => {
    render(<LineChart data={mockData} />)

    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should apply custom aria label', () => {
    const customLabel = 'Temperature trend chart'
    render(<LineChart data={mockData} ariaLabel={customLabel} />)

    const chart = screen.getByRole('img', { name: customLabel })
    expect(chart).toBeInTheDocument()
  })

  it('should have default aria label', () => {
    render(<LineChart data={mockData} />)

    const chart = screen.getByRole('img', { name: 'Line chart' })
    expect(chart).toBeInTheDocument()
  })

  it('should render with custom height', () => {
    const { container } = render(<LineChart data={mockData} height={500} />)

    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
  })

  it('should handle empty data array', () => {
    render(<LineChart data={[]} />)

    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should render chart container', () => {
    const { container } = render(<LineChart data={mockData} />)

    const rechartContainer = container.querySelector('.recharts-responsive-container')
    expect(rechartContainer).toBeInTheDocument()
  })
})
