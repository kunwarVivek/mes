/**
 * ProductionSummaryCard Component Tests
 *
 * TDD: Testing summary card display with various states
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProductionSummaryCard } from '../components/ProductionSummaryCard'
import type { ProductionSummary } from '../types/productionLog.types'

describe('ProductionSummaryCard', () => {
  const mockSummary: ProductionSummary = {
    work_order_id: 10,
    total_produced: 500,
    total_scrapped: 25,
    total_reworked: 10,
    yield_rate: 93.46,
    log_count: 5,
    first_log: '2025-01-15T10:00:00Z',
    last_log: '2025-01-15T18:00:00Z',
  }

  describe('with data', () => {
    it('should display total produced', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={false} />)
      expect(screen.getByText('500')).toBeInTheDocument()
      expect(screen.getByText('Total Produced')).toBeInTheDocument()
    })

    it('should display total scrapped', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={false} />)
      expect(screen.getByText('25')).toBeInTheDocument()
      expect(screen.getByText('Total Scrapped')).toBeInTheDocument()
    })

    it('should display total reworked', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={false} />)
      expect(screen.getByText('10')).toBeInTheDocument()
      expect(screen.getByText('Total Reworked')).toBeInTheDocument()
    })

    it('should display yield rate as percentage', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={false} />)
      expect(screen.getByText('93.5%')).toBeInTheDocument()
      expect(screen.getByText('Yield Rate')).toBeInTheDocument()
    })

    it('should display log count', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={false} />)
      expect(screen.getByText(/5 log entries/i)).toBeInTheDocument()
    })

    it('should apply green color for high yield rate (>=95%)', () => {
      const highYieldSummary = { ...mockSummary, yield_rate: 96.5 }
      const { container } = render(<ProductionSummaryCard summary={highYieldSummary} isLoading={false} />)
      const yieldElement = screen.getByText('96.5%')
      expect(yieldElement.className).toContain('text-green')
    })

    it('should apply yellow color for medium yield rate (85-95%)', () => {
      const mediumYieldSummary = { ...mockSummary, yield_rate: 90.0 }
      const { container } = render(<ProductionSummaryCard summary={mediumYieldSummary} isLoading={false} />)
      const yieldElement = screen.getByText('90.0%')
      expect(yieldElement.className).toContain('text-yellow')
    })

    it('should apply red color for low yield rate (<85%)', () => {
      const lowYieldSummary = { ...mockSummary, yield_rate: 80.0 }
      const { container } = render(<ProductionSummaryCard summary={lowYieldSummary} isLoading={false} />)
      const yieldElement = screen.getByText('80.0%')
      expect(yieldElement.className).toContain('text-red')
    })
  })

  describe('loading state', () => {
    it('should show loading skeleton when isLoading is true', () => {
      const { container } = render(<ProductionSummaryCard summary={undefined} isLoading={true} />)
      const skeletons = container.querySelectorAll('.skeleton')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should not show data when loading', () => {
      render(<ProductionSummaryCard summary={mockSummary} isLoading={true} />)
      expect(screen.queryByText('500')).not.toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('should show message when no summary data', () => {
      render(<ProductionSummaryCard summary={undefined} isLoading={false} />)
      expect(screen.getByText(/no production data/i)).toBeInTheDocument()
    })
  })
})
