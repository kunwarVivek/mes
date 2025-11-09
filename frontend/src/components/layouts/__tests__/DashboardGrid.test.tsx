/**
 * DashboardGrid Component Tests
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DashboardGrid } from '../DashboardGrid'

describe('DashboardGrid', () => {
  it('should render children in grid container', () => {
    render(
      <DashboardGrid>
        <div data-testid="widget-1">Widget 1</div>
        <div data-testid="widget-2">Widget 2</div>
        <div data-testid="widget-3">Widget 3</div>
      </DashboardGrid>
    )

    expect(screen.getByTestId('widget-1')).toBeInTheDocument()
    expect(screen.getByTestId('widget-2')).toBeInTheDocument()
    expect(screen.getByTestId('widget-3')).toBeInTheDocument()
  })

  it('should apply dashboard-grid class', () => {
    const { container } = render(
      <DashboardGrid>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid')
    expect(gridElement).toBeInTheDocument()
  })

  it('should use default 3 columns', () => {
    const { container } = render(
      <DashboardGrid>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid') as HTMLElement
    expect(gridElement).toHaveStyle({ gridTemplateColumns: 'repeat(3, 1fr)' })
  })

  it('should accept custom column count', () => {
    const { container } = render(
      <DashboardGrid columns={4}>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid') as HTMLElement
    expect(gridElement).toHaveStyle({ gridTemplateColumns: 'repeat(4, 1fr)' })
  })

  it('should use default 1.5rem gap', () => {
    const { container } = render(
      <DashboardGrid>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid') as HTMLElement
    expect(gridElement).toHaveStyle({ gap: '1.5rem' })
  })

  it('should accept custom gap size', () => {
    const { container } = render(
      <DashboardGrid gap={2}>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid') as HTMLElement
    expect(gridElement).toHaveStyle({ gap: '2rem' })
  })

  it('should accept custom className', () => {
    const { container } = render(
      <DashboardGrid className="custom-grid">
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid')
    expect(gridElement).toHaveClass('dashboard-grid', 'custom-grid')
  })

  it('should render as a div with grid class', () => {
    const { container } = render(
      <DashboardGrid>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid')
    expect(gridElement?.tagName).toBe('DIV')
    expect(gridElement).toHaveClass('dashboard-grid')
  })

  it('should render multiple children correctly', () => {
    render(
      <DashboardGrid>
        <div data-testid="widget-1">Widget 1</div>
        <div data-testid="widget-2">Widget 2</div>
        <div data-testid="widget-3">Widget 3</div>
        <div data-testid="widget-4">Widget 4</div>
        <div data-testid="widget-5">Widget 5</div>
        <div data-testid="widget-6">Widget 6</div>
      </DashboardGrid>
    )

    expect(screen.getByTestId('widget-1')).toBeInTheDocument()
    expect(screen.getByTestId('widget-2')).toBeInTheDocument()
    expect(screen.getByTestId('widget-3')).toBeInTheDocument()
    expect(screen.getByTestId('widget-4')).toBeInTheDocument()
    expect(screen.getByTestId('widget-5')).toBeInTheDocument()
    expect(screen.getByTestId('widget-6')).toBeInTheDocument()
  })

  it('should handle zero gap', () => {
    const { container } = render(
      <DashboardGrid gap={0}>
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid') as HTMLElement
    expect(gridElement).toHaveStyle({ gap: '0rem' })
  })

  it('should combine classNames correctly', () => {
    const { container } = render(
      <DashboardGrid className="custom-1 custom-2">
        <div>Widget</div>
      </DashboardGrid>
    )

    const gridElement = container.querySelector('.dashboard-grid')
    expect(gridElement).toHaveClass('dashboard-grid')
    expect(gridElement).toHaveClass('custom-1')
    expect(gridElement).toHaveClass('custom-2')
  })
})
