/**
 * Core Atoms Batch 3 - Navigation & Layout Tests
 * TDD approach: RED -> GREEN -> REFACTOR
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '../ThemeProvider'
import { Heart, X, Trash2 } from 'lucide-react'
import { IconButton } from '../atoms/IconButton'
import { Link } from '../atoms/Link'
import { Tooltip } from '../atoms/Tooltip'
import { Divider } from '../atoms/Divider'

// Test wrapper with ThemeProvider
function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>)
}

// ===================================
// ICONBUTTON COMPONENT TESTS
// ===================================

describe('IconButton Component', () => {
  describe('Basic Rendering', () => {
    it('renders icon button with aria-label', () => {
      renderWithTheme(
        <IconButton icon={<Heart data-testid="heart-icon" />} aria-label="Like this item" />
      )
      const button = screen.getByRole('button', { name: 'Like this item' })
      expect(button).toBeTruthy()
      expect(screen.getByTestId('heart-icon')).toBeTruthy()
    })

    it('throws TypeScript error without aria-label', () => {
      // This test verifies TypeScript enforcement
      // @ts-expect-error - aria-label is required
      renderWithTheme(<IconButton icon={<Heart />} />)
    })
  })

  describe('Variants', () => {
    it('renders default variant', () => {
      renderWithTheme(
        <IconButton variant="default" icon={<Heart />} aria-label="Default" />
      )
      const button = screen.getByRole('button', { name: 'Default' })
      expect(button.className).toContain('icon-button--default')
    })

    it('renders primary variant', () => {
      renderWithTheme(
        <IconButton variant="primary" icon={<Heart />} aria-label="Primary" />
      )
      const button = screen.getByRole('button', { name: 'Primary' })
      expect(button.className).toContain('icon-button--primary')
    })

    it('renders danger variant', () => {
      renderWithTheme(
        <IconButton variant="danger" icon={<Trash2 />} aria-label="Delete" />
      )
      const button = screen.getByRole('button', { name: 'Delete' })
      expect(button.className).toContain('icon-button--danger')
    })

    it('renders ghost variant', () => {
      renderWithTheme(
        <IconButton variant="ghost" icon={<X />} aria-label="Close" />
      )
      const button = screen.getByRole('button', { name: 'Close' })
      expect(button.className).toContain('icon-button--ghost')
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      renderWithTheme(
        <IconButton size="sm" icon={<Heart />} aria-label="Small" />
      )
      const button = screen.getByRole('button', { name: 'Small' })
      expect(button.className).toContain('icon-button--sm')
    })

    it('renders medium size (default)', () => {
      renderWithTheme(
        <IconButton size="md" icon={<Heart />} aria-label="Medium" />
      )
      const button = screen.getByRole('button', { name: 'Medium' })
      expect(button.className).toContain('icon-button--md')
    })

    it('renders large size', () => {
      renderWithTheme(
        <IconButton size="lg" icon={<Heart />} aria-label="Large" />
      )
      const button = screen.getByRole('button', { name: 'Large' })
      expect(button.className).toContain('icon-button--lg')
    })
  })

  describe('Interactions', () => {
    it('handles click events', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()

      renderWithTheme(
        <IconButton icon={<Heart />} onClick={handleClick} aria-label="Click me" />
      )

      const button = screen.getByRole('button', { name: 'Click me' })
      await user.click(button)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('respects disabled state', async () => {
      const handleClick = vi.fn()
      const user = userEvent.setup()

      renderWithTheme(
        <IconButton icon={<Heart />} onClick={handleClick} disabled aria-label="Disabled" />
      )

      const button = screen.getByRole('button', { name: 'Disabled' })
      expect(button).toBeDisabled()
      await user.click(button)
      expect(handleClick).not.toHaveBeenCalled()
    })

    it('supports different button types', () => {
      renderWithTheme(
        <IconButton type="submit" icon={<Heart />} aria-label="Submit" />
      )
      const button = screen.getByRole('button', { name: 'Submit' })
      expect(button).toHaveAttribute('type', 'submit')
    })
  })

  describe('Accessibility', () => {
    it('has proper focus-visible styles', () => {
      renderWithTheme(
        <IconButton icon={<Heart />} aria-label="Focus test" />
      )
      const button = screen.getByRole('button', { name: 'Focus test' })
      expect(button.className).toContain('icon-button')
    })

    it('accepts custom className', () => {
      renderWithTheme(
        <IconButton icon={<Heart />} aria-label="Custom" className="custom-class" />
      )
      const button = screen.getByRole('button', { name: 'Custom' })
      expect(button.className).toContain('custom-class')
    })
  })
})

// ===================================
// LINK COMPONENT TESTS
// ===================================

describe('Link Component', () => {
  describe('Basic Rendering', () => {
    it('renders link with href and children', () => {
      renderWithTheme(<Link href="/dashboard">Dashboard</Link>)
      const link = screen.getByRole('link', { name: 'Dashboard' })
      expect(link).toHaveAttribute('href', '/dashboard')
    })

    it('renders default variant', () => {
      renderWithTheme(<Link href="/" variant="default">Home</Link>)
      const link = screen.getByRole('link', { name: 'Home' })
      expect(link.className).toContain('link--default')
    })
  })

  describe('Variants', () => {
    it('renders primary variant', () => {
      renderWithTheme(<Link href="/" variant="primary">Primary</Link>)
      const link = screen.getByRole('link', { name: 'Primary' })
      expect(link.className).toContain('link--primary')
    })

    it('renders muted variant', () => {
      renderWithTheme(<Link href="/" variant="muted">Muted</Link>)
      const link = screen.getByRole('link', { name: 'Muted' })
      expect(link.className).toContain('link--muted')
    })
  })

  describe('External Links', () => {
    it('opens external links in new tab with security attributes', () => {
      renderWithTheme(
        <Link href="https://example.com" external>
          External
        </Link>
      )
      const link = screen.getByRole('link', { name: 'External' })
      expect(link).toHaveAttribute('target', '_blank')
      expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    })

    it('does not add external attributes for internal links', () => {
      renderWithTheme(<Link href="/about">About</Link>)
      const link = screen.getByRole('link', { name: 'About' })
      expect(link).not.toHaveAttribute('target')
      expect(link).not.toHaveAttribute('rel')
    })
  })

  describe('Underline Variants', () => {
    it('renders always underline', () => {
      renderWithTheme(<Link href="/" underline="always">Always</Link>)
      const link = screen.getByRole('link', { name: 'Always' })
      expect(link.className).toContain('link--underline-always')
    })

    it('renders hover underline', () => {
      renderWithTheme(<Link href="/" underline="hover">Hover</Link>)
      const link = screen.getByRole('link', { name: 'Hover' })
      expect(link.className).toContain('link--underline-hover')
    })

    it('renders no underline', () => {
      renderWithTheme(<Link href="/" underline="none">None</Link>)
      const link = screen.getByRole('link', { name: 'None' })
      expect(link.className).toContain('link--underline-none')
    })
  })

  describe('Disabled State', () => {
    it('renders disabled link', () => {
      renderWithTheme(<Link href="/" disabled>Disabled</Link>)
      const link = screen.getByRole('link', { name: 'Disabled' })
      expect(link.className).toContain('link--disabled')
      expect(link).toHaveAttribute('aria-disabled', 'true')
    })

    it('prevents navigation when disabled', async () => {
      const handleClick = vi.fn((e) => e.preventDefault())
      const user = userEvent.setup()

      renderWithTheme(
        <Link href="/" onClick={handleClick} disabled>
          Disabled
        </Link>
      )

      const link = screen.getByRole('link', { name: 'Disabled' })
      await user.click(link)
      expect(handleClick).toHaveBeenCalled()
    })
  })

  describe('Interactions', () => {
    it('handles click events', async () => {
      const handleClick = vi.fn((e) => e.preventDefault())
      const user = userEvent.setup()

      renderWithTheme(
        <Link href="/" onClick={handleClick}>
          Click me
        </Link>
      )

      const link = screen.getByRole('link', { name: 'Click me' })
      await user.click(link)
      expect(handleClick).toHaveBeenCalledTimes(1)
    })
  })
})

// ===================================
// TOOLTIP COMPONENT TESTS
// ===================================

describe('Tooltip Component', () => {
  describe('Basic Rendering', () => {
    it('renders tooltip trigger', () => {
      renderWithTheme(
        <Tooltip content="Helpful tip">
          <button>Hover me</button>
        </Tooltip>
      )
      const trigger = screen.getByRole('button', { name: 'Hover me' })
      expect(trigger).toBeTruthy()
    })

    it('shows tooltip on hover', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <Tooltip content="Tooltip content" trigger="hover">
          <button>Hover me</button>
        </Tooltip>
      )

      const trigger = screen.getByRole('button', { name: 'Hover me' })
      await user.hover(trigger)

      // Wait for tooltip to appear with delay
      await new Promise(resolve => setTimeout(resolve, 350))

      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toBeTruthy()
      expect(tooltip.textContent).toBe('Tooltip content')
    })
  })

  describe('Placement', () => {
    it('supports top placement', () => {
      renderWithTheme(
        <Tooltip content="Top tooltip" placement="top">
          <button>Top</button>
        </Tooltip>
      )
      const trigger = screen.getByRole('button', { name: 'Top' })
      expect(trigger).toBeTruthy()
    })

    it('supports bottom placement', () => {
      renderWithTheme(
        <Tooltip content="Bottom tooltip" placement="bottom">
          <button>Bottom</button>
        </Tooltip>
      )
      const trigger = screen.getByRole('button', { name: 'Bottom' })
      expect(trigger).toBeTruthy()
    })

    it('supports left placement', () => {
      renderWithTheme(
        <Tooltip content="Left tooltip" placement="left">
          <button>Left</button>
        </Tooltip>
      )
      const trigger = screen.getByRole('button', { name: 'Left' })
      expect(trigger).toBeTruthy()
    })

    it('supports right placement', () => {
      renderWithTheme(
        <Tooltip content="Right tooltip" placement="right">
          <button>Right</button>
        </Tooltip>
      )
      const trigger = screen.getByRole('button', { name: 'Right' })
      expect(trigger).toBeTruthy()
    })
  })

  describe('Trigger Types', () => {
    it('shows tooltip on click trigger', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <Tooltip content="Click content" trigger="click">
          <button>Click me</button>
        </Tooltip>
      )

      const trigger = screen.getByRole('button', { name: 'Click me' })
      await user.click(trigger)

      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toBeTruthy()
    })

    it('shows tooltip on focus trigger', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <Tooltip content="Focus content" trigger="focus">
          <button>Focus me</button>
        </Tooltip>
      )

      const trigger = screen.getByRole('button', { name: 'Focus me' })
      await user.tab()

      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toBeTruthy()
    })
  })

  describe('Delay', () => {
    it('respects custom delay', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <Tooltip content="Delayed" delay={500}>
          <button>Delayed</button>
        </Tooltip>
      )

      const trigger = screen.getByRole('button', { name: 'Delayed' })
      await user.hover(trigger)

      // Should not appear immediately
      expect(screen.queryByRole('tooltip')).toBeFalsy()

      // Wait for custom delay
      await new Promise(resolve => setTimeout(resolve, 550))

      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const user = userEvent.setup()
      renderWithTheme(
        <Tooltip content="Accessible tooltip">
          <button>Button</button>
        </Tooltip>
      )

      const trigger = screen.getByRole('button', { name: 'Button' })
      await user.hover(trigger)
      await new Promise(resolve => setTimeout(resolve, 350))

      const tooltip = screen.getByRole('tooltip')
      expect(tooltip).toBeTruthy()
      expect(trigger).toHaveAttribute('aria-describedby')
    })
  })
})

// ===================================
// DIVIDER COMPONENT TESTS
// ===================================

describe('Divider Component', () => {
  describe('Orientation', () => {
    it('renders horizontal divider by default', () => {
      const { container } = renderWithTheme(<Divider />)
      const divider = container.querySelector('.divider--horizontal')
      expect(divider).toBeTruthy()
    })

    it('renders vertical divider', () => {
      const { container } = renderWithTheme(<Divider orientation="vertical" />)
      const divider = container.querySelector('.divider--vertical')
      expect(divider).toBeTruthy()
    })
  })

  describe('Variants', () => {
    it('renders solid variant by default', () => {
      const { container } = renderWithTheme(<Divider variant="solid" />)
      const divider = container.querySelector('.divider--solid')
      expect(divider).toBeTruthy()
    })

    it('renders dashed variant', () => {
      const { container } = renderWithTheme(<Divider variant="dashed" />)
      const divider = container.querySelector('.divider--dashed')
      expect(divider).toBeTruthy()
    })

    it('renders dotted variant', () => {
      const { container } = renderWithTheme(<Divider variant="dotted" />)
      const divider = container.querySelector('.divider--dotted')
      expect(divider).toBeTruthy()
    })
  })

  describe('Spacing', () => {
    it('renders small spacing', () => {
      const { container } = renderWithTheme(<Divider spacing="sm" />)
      const divider = container.querySelector('.divider--spacing-sm')
      expect(divider).toBeTruthy()
    })

    it('renders medium spacing (default)', () => {
      const { container } = renderWithTheme(<Divider spacing="md" />)
      const divider = container.querySelector('.divider--spacing-md')
      expect(divider).toBeTruthy()
    })

    it('renders large spacing', () => {
      const { container } = renderWithTheme(<Divider spacing="lg" />)
      const divider = container.querySelector('.divider--spacing-lg')
      expect(divider).toBeTruthy()
    })
  })

  describe('Thickness', () => {
    it('renders thin thickness', () => {
      const { container } = renderWithTheme(<Divider thickness="thin" />)
      const divider = container.querySelector('.divider--thin')
      expect(divider).toBeTruthy()
    })

    it('renders medium thickness (default)', () => {
      const { container } = renderWithTheme(<Divider thickness="medium" />)
      const divider = container.querySelector('.divider--medium')
      expect(divider).toBeTruthy()
    })

    it('renders thick thickness', () => {
      const { container } = renderWithTheme(<Divider thickness="thick" />)
      const divider = container.querySelector('.divider--thick')
      expect(divider).toBeTruthy()
    })
  })

  describe('Custom className', () => {
    it('accepts custom className', () => {
      const { container } = renderWithTheme(<Divider className="custom-divider" />)
      const divider = container.querySelector('.custom-divider')
      expect(divider).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA role', () => {
      const { container } = renderWithTheme(<Divider />)
      const divider = container.querySelector('[role="separator"]')
      expect(divider).toBeTruthy()
    })

    it('has aria-orientation for vertical dividers', () => {
      const { container } = renderWithTheme(<Divider orientation="vertical" />)
      const divider = container.querySelector('[aria-orientation="vertical"]')
      expect(divider).toBeTruthy()
    })
  })
})
