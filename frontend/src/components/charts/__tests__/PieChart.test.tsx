import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PieChart } from '../PieChart'

describe('PieChart', () => {
  const mockData = [
    { name: 'Category A', value: 400 },
    { name: 'Category B', value: 300 },
    { name: 'Category C', value: 200 },
  ]

  it('should render pie chart with data', () => {
    render(<PieChart data={mockData} />)

    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should apply custom aria label', () => {
    const customLabel = 'Market share distribution'
    render(<PieChart data={mockData} ariaLabel={customLabel} />)

    const chart = screen.getByRole('img', { name: customLabel })
    expect(chart).toBeInTheDocument()
  })

  it('should have default aria label', () => {
    render(<PieChart data={mockData} />)

    const chart = screen.getByRole('img', { name: 'Pie chart' })
    expect(chart).toBeInTheDocument()
  })

  it('should render with custom height', () => {
    const { container } = render(<PieChart data={mockData} height={350} />)

    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
  })

  it('should handle empty data array', () => {
    render(<PieChart data={[]} />)

    const chart = screen.getByRole('img')
    expect(chart).toBeInTheDocument()
  })

  it('should render chart container', () => {
    const { container } = render(<PieChart data={mockData} />)

    const rechartContainer = container.querySelector('.recharts-responsive-container')
    expect(rechartContainer).toBeInTheDocument()
  })

  it('should apply custom colors', () => {
    const customColors = ['#ff0000', '#00ff00', '#0000ff']
    const { container } = render(<PieChart data={mockData} colors={customColors} />)

    // Chart should render with custom colors prop accepted
    const rechartContainer = container.querySelector('.recharts-responsive-container')
    expect(rechartContainer).toBeInTheDocument()
  })
})
