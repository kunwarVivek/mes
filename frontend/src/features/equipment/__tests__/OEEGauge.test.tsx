/**
 * OEEGauge Component Tests
 *
 * Tests for OEE visualization component
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OEEGauge } from '../components/OEEGauge'
import type { OEEMetrics } from '../types/machine.types'

const mockOEEMetrics: OEEMetrics = {
  availability: 0.95,
  performance: 0.93,
  quality: 0.99,
  oee_score: 0.87,
}

describe('OEEGauge', () => {
  it('should render OEE score', () => {
    render(<OEEGauge metrics={mockOEEMetrics} />)

    expect(screen.getByText('87%')).toBeInTheDocument()
  })

  it('should render all OEE components', () => {
    render(<OEEGauge metrics={mockOEEMetrics} />)

    expect(screen.getByText('Availability')).toBeInTheDocument()
    expect(screen.getByText('95%')).toBeInTheDocument()

    expect(screen.getByText('Performance')).toBeInTheDocument()
    expect(screen.getByText('93%')).toBeInTheDocument()

    expect(screen.getByText('Quality')).toBeInTheDocument()
    expect(screen.getByText('99%')).toBeInTheDocument()
  })

  it('should display excellent status for OEE >= 85%', () => {
    render(<OEEGauge metrics={mockOEEMetrics} />)

    expect(screen.getByText('Excellent')).toBeInTheDocument()
    const gauge = screen.getByTestId('oee-gauge')
    expect(gauge).toHaveClass('oee-excellent')
  })

  it('should display good status for OEE >= 70% and < 85%', () => {
    const metrics = { ...mockOEEMetrics, oee_score: 0.75 }
    render(<OEEGauge metrics={metrics} />)

    expect(screen.getByText('Good')).toBeInTheDocument()
    const gauge = screen.getByTestId('oee-gauge')
    expect(gauge).toHaveClass('oee-good')
  })

  it('should display acceptable status for OEE >= 60% and < 70%', () => {
    const metrics = { ...mockOEEMetrics, oee_score: 0.65 }
    render(<OEEGauge metrics={metrics} />)

    expect(screen.getByText('Acceptable')).toBeInTheDocument()
    const gauge = screen.getByTestId('oee-gauge')
    expect(gauge).toHaveClass('oee-acceptable')
  })

  it('should display poor status for OEE < 60%', () => {
    const metrics = { ...mockOEEMetrics, oee_score: 0.45 }
    render(<OEEGauge metrics={metrics} />)

    expect(screen.getByText('Poor')).toBeInTheDocument()
    const gauge = screen.getByTestId('oee-gauge')
    expect(gauge).toHaveClass('oee-poor')
  })

  it('should handle zero OEE', () => {
    const metrics = {
      availability: 0,
      performance: 0,
      quality: 0,
      oee_score: 0,
    }
    render(<OEEGauge metrics={metrics} />)

    const scoreElement = screen.getAllByText('0%')[0] // First occurrence is the main score
    expect(scoreElement).toBeInTheDocument()
    expect(screen.getByText('Poor')).toBeInTheDocument()
  })

  it('should handle perfect OEE', () => {
    const metrics = {
      availability: 1.0,
      performance: 1.0,
      quality: 1.0,
      oee_score: 1.0,
    }
    render(<OEEGauge metrics={metrics} />)

    const scoreElements = screen.getAllByText('100%')
    expect(scoreElements.length).toBeGreaterThan(0) // Should appear multiple times (main score + components)
    expect(screen.getByText('Excellent')).toBeInTheDocument()
  })

  it('should render compact mode when specified', () => {
    render(<OEEGauge metrics={mockOEEMetrics} compact={true} />)

    const gauge = screen.getByTestId('oee-gauge')
    expect(gauge).toHaveClass('compact')

    // In compact mode, only show main OEE score
    expect(screen.queryByText('Availability')).not.toBeInTheDocument()
    expect(screen.queryByText('Performance')).not.toBeInTheDocument()
    expect(screen.queryByText('Quality')).not.toBeInTheDocument()
  })

  it('should show loading state when specified', () => {
    render(<OEEGauge metrics={mockOEEMetrics} isLoading={true} />)

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument()
  })

  it('should format percentages correctly', () => {
    const metrics = {
      availability: 0.8567,
      performance: 0.9234,
      quality: 0.9876,
      oee_score: 0.7812,
    }
    render(<OEEGauge metrics={metrics} />)

    // Should round to nearest integer
    expect(screen.getByText('86%')).toBeInTheDocument() // availability
    expect(screen.getByText('92%')).toBeInTheDocument() // performance
    expect(screen.getByText('99%')).toBeInTheDocument() // quality
    expect(screen.getByText('78%')).toBeInTheDocument() // OEE
  })

  it('should highlight low availability component', () => {
    const metrics = {
      availability: 0.55, // Low
      performance: 0.93,
      quality: 0.99,
      oee_score: 0.51,
    }
    render(<OEEGauge metrics={metrics} />)

    const availabilityBar = screen.getByTestId('availability-bar')
    expect(availabilityBar).toHaveClass('low-metric')
  })

  it('should highlight low performance component', () => {
    const metrics = {
      availability: 0.95,
      performance: 0.58, // Low
      quality: 0.99,
      oee_score: 0.55,
    }
    render(<OEEGauge metrics={metrics} />)

    const performanceBar = screen.getByTestId('performance-bar')
    expect(performanceBar).toHaveClass('low-metric')
  })

  it('should highlight low quality component', () => {
    const metrics = {
      availability: 0.95,
      performance: 0.93,
      quality: 0.55, // Low
      oee_score: 0.49,
    }
    render(<OEEGauge metrics={metrics} />)

    const qualityBar = screen.getByTestId('quality-bar')
    expect(qualityBar).toHaveClass('low-metric')
  })
})
