import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton } from '../skeleton'

describe('Skeleton', () => {
  it('renders with default styles', () => {
    const { container } = render(<Skeleton />)
    const skeleton = container.firstChild as HTMLElement
    expect(skeleton).toHaveClass('animate-pulse', 'rounded-md', 'bg-muted')
  })

  it('applies custom className', () => {
    const { container } = render(<Skeleton className="h-4 w-full" />)
    const skeleton = container.firstChild as HTMLElement
    expect(skeleton).toHaveClass('h-4', 'w-full', 'animate-pulse')
  })

  it('forwards HTML attributes', () => {
    const { container } = render(<Skeleton data-testid="skeleton" />)
    const skeleton = container.firstChild as HTMLElement
    expect(skeleton).toHaveAttribute('data-testid', 'skeleton')
  })
})
