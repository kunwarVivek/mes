import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Separator } from '../separator'

describe('Separator', () => {
  it('renders horizontal separator by default', () => {
    const { container } = render(<Separator />)
    const separator = container.firstChild as HTMLElement
    expect(separator).toHaveClass('h-[1px]', 'w-full')
  })

  it('renders vertical separator', () => {
    const { container } = render(<Separator orientation="vertical" />)
    const separator = container.firstChild as HTMLElement
    expect(separator).toHaveClass('h-full', 'w-[1px]')
  })

  it('applies custom className', () => {
    const { container } = render(<Separator className="my-4" />)
    const separator = container.firstChild as HTMLElement
    expect(separator).toHaveClass('my-4')
  })

  it('supports decorative prop', () => {
    const { container } = render(<Separator decorative />)
    const separator = container.firstChild as HTMLElement
    expect(separator).toBeInTheDocument()
  })
})
