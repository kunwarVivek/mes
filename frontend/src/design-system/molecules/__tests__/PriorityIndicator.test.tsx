import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PriorityIndicator } from '../PriorityIndicator'

describe('PriorityIndicator', () => {
  it('renders correct icon for each priority', () => {
    const { container, rerender } = render(<PriorityIndicator priority="low" withLabel />)
    expect(screen.getByText('Low')).toBeInTheDocument()
    let svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()

    rerender(<PriorityIndicator priority="medium" withLabel />)
    expect(screen.getByText('Medium')).toBeInTheDocument()

    rerender(<PriorityIndicator priority="high" withLabel />)
    expect(screen.getByText('High')).toBeInTheDocument()

    rerender(<PriorityIndicator priority="critical" withLabel />)
    expect(screen.getByText('Critical')).toBeInTheDocument()
  })

  it('shows label when withLabel=true', () => {
    render(<PriorityIndicator priority="high" withLabel />)
    expect(screen.getByText('High')).toBeInTheDocument()
  })

  it('does not show label when withLabel=false', () => {
    render(<PriorityIndicator priority="high" />)
    expect(screen.queryByText('High')).not.toBeInTheDocument()
  })

  it('handles all priority values', () => {
    const priorities = ['low', 'medium', 'high', 'critical'] as const
    priorities.forEach(priority => {
      const { container } = render(<PriorityIndicator priority={priority} />)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })
})
