import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Avatar, AvatarImage, AvatarFallback } from '../avatar'

describe('Avatar', () => {
  it('renders avatar container', () => {
    const { container } = render(
      <Avatar>
        <AvatarImage src="/test.jpg" alt="Test User" />
        <AvatarFallback>TU</AvatarFallback>
      </Avatar>
    )

    // Avatar renders with the correct classes
    const avatar = container.firstChild as HTMLElement
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveClass('relative', 'flex', 'rounded-full')
  })

  it('renders fallback when no image', () => {
    render(
      <Avatar>
        <AvatarFallback>AB</AvatarFallback>
      </Avatar>
    )

    expect(screen.getByText('AB')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <Avatar className="custom-avatar">
        <AvatarFallback>TC</AvatarFallback>
      </Avatar>
    )

    const avatar = container.querySelector('.custom-avatar')
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveClass('custom-avatar')
  })
})
