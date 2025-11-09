/**
 * MetricCard Component Tests
 *
 * TDD: Testing metric card display, formatting, trends, and color coding
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MetricCard } from '../MetricCard'

describe('MetricCard', () => {
  describe('Basic Rendering', () => {
    it('should render metric value and label', () => {
      render(<MetricCard value={85.5} label="OEE" />)

      expect(screen.getByText('OEE')).toBeInTheDocument()
      expect(screen.getByText(/85\.5/)).toBeInTheDocument()
    })

    it('should render string values', () => {
      render(<MetricCard value="N/A" label="MTBF" />)

      expect(screen.getByText('MTBF')).toBeInTheDocument()
      expect(screen.getByText('N/A')).toBeInTheDocument()
    })

    it('should format numeric values to 1 decimal place', () => {
      render(<MetricCard value={92.678} label="FPY" />)

      expect(screen.getByText(/92\.7/)).toBeInTheDocument()
    })
  })

  describe('Units', () => {
    it('should display unit when provided', () => {
      render(<MetricCard value={85} label="OEE" unit="%" />)

      expect(screen.getByText(/85\.0%/)).toBeInTheDocument()
    })

    it('should handle hours unit', () => {
      render(<MetricCard value={48.5} label="MTBF" unit=" hrs" />)

      expect(screen.getByText(/48\.5 hrs/)).toBeInTheDocument()
    })

    it('should not display unit when omitted', () => {
      render(<MetricCard value={150} label="Count" />)

      const element = screen.getByText(/150\.0/)
      expect(element.textContent).toBe('150.0')
    })
  })

  describe('Trend Indicators', () => {
    it('should display up trend with green color', () => {
      render(<MetricCard value={90} label="OEE" trend="up" unit="%" />)

      const trendElement = screen.getByText('↑')
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-green-600')
    })

    it('should display down trend with red color', () => {
      render(<MetricCard value={75} label="OEE" trend="down" unit="%" />)

      const trendElement = screen.getByText('↓')
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-red-600')
    })

    it('should display neutral trend with gray color', () => {
      render(<MetricCard value={85} label="OEE" trend="neutral" unit="%" />)

      const trendElement = screen.getByText('→')
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-gray-600')
    })

    it('should not display trend when omitted', () => {
      render(<MetricCard value={85} label="OEE" unit="%" />)

      expect(screen.queryByText('↑')).not.toBeInTheDocument()
      expect(screen.queryByText('↓')).not.toBeInTheDocument()
      expect(screen.queryByText('→')).not.toBeInTheDocument()
    })
  })

  describe('Target Display', () => {
    it('should display target when provided', () => {
      render(<MetricCard value={85} label="OEE" target={90} unit="%" />)

      expect(screen.getByText('Target: 90%')).toBeInTheDocument()
    })

    it('should display target without unit when unit is omitted', () => {
      render(<MetricCard value={150} label="Count" target={200} />)

      expect(screen.getByText('Target: 200')).toBeInTheDocument()
    })

    it('should not display target when omitted', () => {
      render(<MetricCard value={85} label="OEE" unit="%" />)

      expect(screen.queryByText(/Target:/)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper semantic structure', () => {
      const { container } = render(
        <MetricCard value={85} label="OEE" trend="up" unit="%" />
      )

      const card = container.firstChild
      expect(card).toBeInTheDocument()
    })

    it('should support custom className', () => {
      const { container } = render(
        <MetricCard value={85} label="OEE" className="custom-class" />
      )

      const card = container.querySelector('.custom-class')
      expect(card).toBeInTheDocument()
    })

    it('should have aria-label for trend indicator', () => {
      render(<MetricCard value={90} label="OEE" trend="up" unit="%" />)

      const trendElement = screen.getByLabelText('Trend: increasing')
      expect(trendElement).toBeInTheDocument()
    })

    it('should have aria-label for down trend', () => {
      render(<MetricCard value={75} label="OEE" trend="down" unit="%" />)

      const trendElement = screen.getByLabelText('Trend: decreasing')
      expect(trendElement).toBeInTheDocument()
    })

    it('should have aria-label for neutral trend', () => {
      render(<MetricCard value={85} label="OEE" trend="neutral" unit="%" />)

      const trendElement = screen.getByLabelText('Trend: stable')
      expect(trendElement).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero values', () => {
      render(<MetricCard value={0} label="Defects" />)

      expect(screen.getByText(/0\.0/)).toBeInTheDocument()
    })

    it('should handle large numbers', () => {
      render(<MetricCard value={99999.99} label="Production" />)

      expect(screen.getByText(/100000\.0/)).toBeInTheDocument()
    })

    it('should handle negative numbers', () => {
      render(<MetricCard value={-5.5} label="Variance" unit="%" />)

      expect(screen.getByText(/-5\.5%/)).toBeInTheDocument()
    })

    it('should handle NaN values gracefully', () => {
      render(<MetricCard value={NaN} label="Invalid" />)

      expect(screen.getByText('Invalid value')).toBeInTheDocument()
    })

    it('should handle Infinity values gracefully', () => {
      render(<MetricCard value={Infinity} label="Invalid" />)

      expect(screen.getByText('Invalid value')).toBeInTheDocument()
    })
  })

  describe('Security', () => {
    it('should sanitize label to prevent XSS', () => {
      const maliciousLabel = '<script>alert("xss")</script>OEE'
      const { container } = render(
        <MetricCard value={85} label={maliciousLabel} />
      )

      expect(container.querySelector('script')).not.toBeInTheDocument()
      expect(screen.getByText(maliciousLabel)).toBeInTheDocument()
    })

    it('should sanitize unit to prevent XSS', () => {
      const maliciousUnit = '<img src=x onerror=alert("xss")>%'
      const { container } = render(
        <MetricCard value={85} label="OEE" unit={maliciousUnit} />
      )

      expect(container.querySelector('img')).not.toBeInTheDocument()
    })
  })
})
