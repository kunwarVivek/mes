/**
 * Core Atoms Batch 1 - Status & Indicators Tests
 * TDD approach: RED -> GREEN -> REFACTOR
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '../ThemeProvider'
import { Badge } from '../atoms/Badge'
import { Chip } from '../atoms/Chip'
import { Spinner } from '../atoms/Spinner'
import { Skeleton } from '../atoms/Skeleton'
import { Progress } from '../atoms/Progress'

// Test wrapper with ThemeProvider
function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>)
}

describe('Badge Component', () => {
  describe('Variants', () => {
    it('renders success variant with correct styles', () => {
      renderWithTheme(<Badge variant="success">Passed</Badge>)
      const badge = screen.getByText('Passed')
      expect(badge).toBeTruthy()
      expect(badge.className).toContain('badge--success')
    })

    it('renders warning variant with correct styles', () => {
      renderWithTheme(<Badge variant="warning">Pending</Badge>)
      const badge = screen.getByText('Pending')
      expect(badge.className).toContain('badge--warning')
    })

    it('renders error variant with correct styles', () => {
      renderWithTheme(<Badge variant="error">Failed</Badge>)
      const badge = screen.getByText('Failed')
      expect(badge.className).toContain('badge--error')
    })

    it('renders info variant with correct styles', () => {
      renderWithTheme(<Badge variant="info">Info</Badge>)
      const badge = screen.getByText('Info')
      expect(badge.className).toContain('badge--info')
    })

    it('renders neutral variant with correct styles', () => {
      renderWithTheme(<Badge variant="neutral">Neutral</Badge>)
      const badge = screen.getByText('Neutral')
      expect(badge.className).toContain('badge--neutral')
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      renderWithTheme(<Badge variant="success" size="sm">Small</Badge>)
      const badge = screen.getByText('Small')
      expect(badge.className).toContain('badge--sm')
    })

    it('renders medium size (default)', () => {
      renderWithTheme(<Badge variant="success">Medium</Badge>)
      const badge = screen.getByText('Medium')
      expect(badge.className).toContain('badge--md')
    })

    it('renders large size', () => {
      renderWithTheme(<Badge variant="success" size="lg">Large</Badge>)
      const badge = screen.getByText('Large')
      expect(badge.className).toContain('badge--lg')
    })
  })

  describe('Dot Indicator', () => {
    it('shows dot when dot prop is true', () => {
      const { container } = renderWithTheme(
        <Badge variant="success" dot>Active</Badge>
      )
      const dot = container.querySelector('.badge__dot')
      expect(dot).toBeTruthy()
    })

    it('hides dot when dot prop is false', () => {
      const { container } = renderWithTheme(
        <Badge variant="success">Inactive</Badge>
      )
      const dot = container.querySelector('.badge__dot')
      expect(dot).toBeFalsy()
    })
  })
})

describe('Chip Component', () => {
  describe('Basic Rendering', () => {
    it('renders label correctly', () => {
      renderWithTheme(<Chip label="Test Tag" />)
      expect(screen.getByText('Test Tag')).toBeTruthy()
    })

    it('renders with filled variant by default', () => {
      const { container } = renderWithTheme(<Chip label="Tag" />)
      const chip = container.querySelector('.chip')
      expect(chip?.className).toContain('chip--filled')
    })

    it('renders with outlined variant', () => {
      const { container } = renderWithTheme(<Chip label="Tag" variant="outlined" />)
      const chip = container.querySelector('.chip')
      expect(chip?.className).toContain('chip--outlined')
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<Chip label="Tag" size="sm" />)
      const chip = container.querySelector('.chip')
      expect(chip?.className).toContain('chip--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(<Chip label="Tag" />)
      const chip = container.querySelector('.chip')
      expect(chip?.className).toContain('chip--md')
    })
  })

  describe('Delete Functionality', () => {
    it('shows delete button when onDelete is provided', () => {
      const onDelete = vi.fn()
      renderWithTheme(<Chip label="Tag" onDelete={onDelete} />)
      const deleteButton = screen.getByRole('button')
      expect(deleteButton).toBeTruthy()
    })

    it('hides delete button when onDelete is not provided', () => {
      renderWithTheme(<Chip label="Tag" />)
      const deleteButton = screen.queryByRole('button')
      expect(deleteButton).toBeFalsy()
    })

    it('calls onDelete when delete button is clicked', async () => {
      const user = userEvent.setup()
      const onDelete = vi.fn()
      renderWithTheme(<Chip label="Tag" onDelete={onDelete} />)

      const deleteButton = screen.getByRole('button')
      await user.click(deleteButton)

      expect(onDelete).toHaveBeenCalledTimes(1)
    })
  })

  describe('Icon Support', () => {
    it('renders leading icon when provided', () => {
      renderWithTheme(
        <Chip label="Tag" icon={<span data-testid="icon">★</span>} />
      )
      expect(screen.getByTestId('icon')).toBeTruthy()
    })
  })
})

describe('Spinner Component', () => {
  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<Spinner size="sm" />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(<Spinner />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--md')
    })

    it('renders large size', () => {
      const { container } = renderWithTheme(<Spinner size="lg" />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--lg')
    })

    it('renders extra large size', () => {
      const { container } = renderWithTheme(<Spinner size="xl" />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--xl')
    })
  })

  describe('Colors', () => {
    it('renders primary color (default)', () => {
      const { container } = renderWithTheme(<Spinner />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--primary')
    })

    it('renders secondary color', () => {
      const { container } = renderWithTheme(<Spinner color="secondary" />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--secondary')
    })

    it('renders neutral color', () => {
      const { container } = renderWithTheme(<Spinner color="neutral" />)
      const spinner = container.querySelector('.spinner')
      expect(spinner?.className).toContain('spinner--neutral')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA role', () => {
      const { container } = renderWithTheme(<Spinner />)
      const spinner = container.querySelector('[role="status"]')
      expect(spinner).toBeTruthy()
    })

    it('includes visually hidden label by default', () => {
      const { container } = renderWithTheme(<Spinner />)
      const label = container.querySelector('.spinner__label')
      expect(label?.textContent).toBe('Loading...')
    })

    it('uses custom label when provided', () => {
      const { container } = renderWithTheme(<Spinner label="Processing data..." />)
      const label = container.querySelector('.spinner__label')
      expect(label?.textContent).toBe('Processing data...')
    })
  })
})

describe('Skeleton Component', () => {
  describe('Variants', () => {
    it('renders text variant (default)', () => {
      const { container } = renderWithTheme(<Skeleton />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).toContain('skeleton--text')
    })

    it('renders circular variant', () => {
      const { container } = renderWithTheme(<Skeleton variant="circular" />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).toContain('skeleton--circular')
    })

    it('renders rectangular variant', () => {
      const { container } = renderWithTheme(<Skeleton variant="rectangular" />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).toContain('skeleton--rectangular')
    })
  })

  describe('Dimensions', () => {
    it('applies custom width as number', () => {
      const { container } = renderWithTheme(<Skeleton width={200} />)
      const skeleton = container.querySelector('.skeleton') as HTMLElement
      expect(skeleton?.style.width).toBe('200px')
    })

    it('applies custom width as string', () => {
      const { container } = renderWithTheme(<Skeleton width="50%" />)
      const skeleton = container.querySelector('.skeleton') as HTMLElement
      expect(skeleton?.style.width).toBe('50%')
    })

    it('applies custom height as number', () => {
      const { container } = renderWithTheme(<Skeleton height={100} />)
      const skeleton = container.querySelector('.skeleton') as HTMLElement
      expect(skeleton?.style.height).toBe('100px')
    })

    it('applies custom height as string', () => {
      const { container } = renderWithTheme(<Skeleton height="2rem" />)
      const skeleton = container.querySelector('.skeleton') as HTMLElement
      expect(skeleton?.style.height).toBe('2rem')
    })
  })

  describe('Animation', () => {
    it('uses pulse animation by default', () => {
      const { container } = renderWithTheme(<Skeleton />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).toContain('skeleton--pulse')
    })

    it('uses wave animation', () => {
      const { container } = renderWithTheme(<Skeleton animation="wave" />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).toContain('skeleton--wave')
    })

    it('disables animation', () => {
      const { container } = renderWithTheme(<Skeleton animation="none" />)
      const skeleton = container.querySelector('.skeleton')
      expect(skeleton?.className).not.toContain('skeleton--pulse')
      expect(skeleton?.className).not.toContain('skeleton--wave')
    })
  })
})

describe('Progress Component', () => {
  describe('Value Display', () => {
    it('renders progress with correct value', () => {
      const { container } = renderWithTheme(<Progress value={50} />)
      const progressBar = container.querySelector('.progress__bar') as HTMLElement
      expect(progressBar?.style.width).toBe('50%')
    })

    it('handles 0% progress', () => {
      const { container } = renderWithTheme(<Progress value={0} />)
      const progressBar = container.querySelector('.progress__bar') as HTMLElement
      expect(progressBar?.style.width).toBe('0%')
    })

    it('handles 100% progress', () => {
      const { container } = renderWithTheme(<Progress value={100} />)
      const progressBar = container.querySelector('.progress__bar') as HTMLElement
      expect(progressBar?.style.width).toBe('100%')
    })

    it('clamps value above 100', () => {
      const { container } = renderWithTheme(<Progress value={150} />)
      const progressBar = container.querySelector('.progress__bar') as HTMLElement
      expect(progressBar?.style.width).toBe('100%')
    })

    it('clamps value below 0', () => {
      const { container } = renderWithTheme(<Progress value={-10} />)
      const progressBar = container.querySelector('.progress__bar') as HTMLElement
      expect(progressBar?.style.width).toBe('0%')
    })
  })

  describe('Sizes', () => {
    it('renders small size', () => {
      const { container } = renderWithTheme(<Progress value={50} size="sm" />)
      const progress = container.querySelector('.progress')
      expect(progress?.className).toContain('progress--sm')
    })

    it('renders medium size (default)', () => {
      const { container } = renderWithTheme(<Progress value={50} />)
      const progress = container.querySelector('.progress')
      expect(progress?.className).toContain('progress--md')
    })

    it('renders large size', () => {
      const { container } = renderWithTheme(<Progress value={50} size="lg" />)
      const progress = container.querySelector('.progress')
      expect(progress?.className).toContain('progress--lg')
    })
  })

  describe('Variants', () => {
    it('renders default variant', () => {
      const { container } = renderWithTheme(<Progress value={50} />)
      const progressBar = container.querySelector('.progress__bar')
      expect(progressBar?.className).toContain('progress__bar--default')
    })

    it('renders success variant', () => {
      const { container } = renderWithTheme(<Progress value={50} variant="success" />)
      const progressBar = container.querySelector('.progress__bar')
      expect(progressBar?.className).toContain('progress__bar--success')
    })

    it('renders warning variant', () => {
      const { container } = renderWithTheme(<Progress value={50} variant="warning" />)
      const progressBar = container.querySelector('.progress__bar')
      expect(progressBar?.className).toContain('progress__bar--warning')
    })

    it('renders error variant', () => {
      const { container } = renderWithTheme(<Progress value={50} variant="error" />)
      const progressBar = container.querySelector('.progress__bar')
      expect(progressBar?.className).toContain('progress__bar--error')
    })
  })

  describe('Label Display', () => {
    it('hides label by default', () => {
      renderWithTheme(<Progress value={50} />)
      expect(screen.queryByText('50%')).toBeFalsy()
    })

    it('shows label when showLabel is true', () => {
      renderWithTheme(<Progress value={75} showLabel />)
      expect(screen.getByText('75%')).toBeTruthy()
    })

    it('displays correct percentage', () => {
      renderWithTheme(<Progress value={33} showLabel />)
      expect(screen.getByText('33%')).toBeTruthy()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      const { container } = renderWithTheme(<Progress value={60} />)
      const progress = container.querySelector('[role="progressbar"]')
      expect(progress).toBeTruthy()
      expect(progress?.getAttribute('aria-valuenow')).toBe('60')
      expect(progress?.getAttribute('aria-valuemin')).toBe('0')
      expect(progress?.getAttribute('aria-valuemax')).toBe('100')
    })
  })
})
