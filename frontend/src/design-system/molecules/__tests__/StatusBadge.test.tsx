import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../StatusBadge'

describe('StatusBadge', () => {
  it('renders correct variant for each status', () => {
    const { rerender } = render(<StatusBadge status="running" />)
    expect(screen.getByText('Running')).toBeInTheDocument()

    rerender(<StatusBadge status="idle" />)
    expect(screen.getByText('Idle')).toBeInTheDocument()

    rerender(<StatusBadge status="down" />)
    expect(screen.getByText('Down')).toBeInTheDocument()

    rerender(<StatusBadge status="completed" />)
    expect(screen.getByText('Completed')).toBeInTheDocument()

    rerender(<StatusBadge status="pass" />)
    expect(screen.getByText('Pass')).toBeInTheDocument()
  })

  it('shows icon when withIcon=true', () => {
    const { container } = render(<StatusBadge status="running" withIcon />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('does not show icon when withIcon=false', () => {
    const { container } = render(<StatusBadge status="running" />)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeInTheDocument()
  })

  it('applies pulse animation when withPulse=true and status supports it', () => {
    const { container } = render(<StatusBadge status="running" withIcon withPulse />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('animate-pulse')
  })

  it('merges className prop', () => {
    const { container } = render(<StatusBadge status="running" className="custom-class" />)
    const badge = container.firstChild
    expect(badge).toHaveClass('custom-class')
  })
})
