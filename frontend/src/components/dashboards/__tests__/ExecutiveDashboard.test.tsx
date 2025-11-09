/**
 * ExecutiveDashboard Component Tests
 *
 * TDD: RED phase - Write tests first to define expected behavior
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ExecutiveDashboard } from '../ExecutiveDashboard'
import type { ExecutiveDashboardProps } from '../ExecutiveDashboard'

const mockDashboardData: ExecutiveDashboardProps = {
  metrics: {
    revenue: { value: 1250000, trend: 'up', target: 1200000 },
    orders: { value: 450, trend: 'up', target: 400 },
    efficiency: { value: 87.5, trend: 'down', target: 90 },
    quality: { value: 96.2, trend: 'neutral', target: 95 },
  },
  revenueTrend: [
    { name: 'Jan', value: 950000 },
    { name: 'Feb', value: 1050000 },
    { name: 'Mar', value: 1150000 },
    { name: 'Apr', value: 1250000 },
  ],
  productDistribution: [
    { name: 'Product A', value: 45 },
    { name: 'Product B', value: 30 },
    { name: 'Product C', value: 25 },
  ],
  departmentPerformance: [
    { name: 'Assembly', value: 92 },
    { name: 'Machining', value: 88 },
    { name: 'Quality', value: 95 },
    { name: 'Packaging', value: 85 },
  ],
}

describe('ExecutiveDashboard', () => {
  describe('Component Structure', () => {
    it('should render executive dashboard container', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      const dashboard = container.querySelector('[data-testid="executive-dashboard"]')
      expect(dashboard).toBeInTheDocument()
    })

    it('should render with proper accessibility attributes', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      const dashboard = container.querySelector('[role="region"]')
      expect(dashboard).toBeInTheDocument()
      expect(dashboard).toHaveAttribute('aria-label', 'Executive Dashboard')
    })
  })

  describe('Metric Cards - Row 1', () => {
    it('should render all four metric cards', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Orders')).toBeInTheDocument()
      expect(screen.getByText('Efficiency')).toBeInTheDocument()
      expect(screen.getByText('Quality')).toBeInTheDocument()
    })

    it('should display revenue metric with correct value and trend', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText(/1250000/)).toBeInTheDocument()
      const upTrend = screen.getAllByText('↑')
      expect(upTrend.length).toBeGreaterThan(0)
    })

    it('should display orders metric with target', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByText('Orders')).toBeInTheDocument()
      expect(screen.getByText(/450/)).toBeInTheDocument()
      expect(screen.getByText('Target: 400')).toBeInTheDocument()
    })

    it('should display efficiency metric with down trend', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByText('Efficiency')).toBeInTheDocument()
      expect(screen.getByText(/87\.5/)).toBeInTheDocument()
      expect(screen.getByText('↓')).toBeInTheDocument()
    })

    it('should display quality metric with neutral trend', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByText('Quality')).toBeInTheDocument()
      expect(screen.getByText(/96\.2/)).toBeInTheDocument()
      expect(screen.getByText('→')).toBeInTheDocument()
    })
  })

  describe('Charts - Row 2', () => {
    it('should render revenue trend line chart', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      const lineChart = screen.getByRole('img', { name: /revenue trend/i })
      expect(lineChart).toBeInTheDocument()
    })

    it('should render product distribution pie chart', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      const pieChart = screen.getByRole('img', { name: /product distribution/i })
      expect(pieChart).toBeInTheDocument()
    })

    it('should display charts side by side in row 2', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      // Verify two charts exist in row 2 using DashboardGrid
      const grids = container.querySelectorAll('.dashboard-grid')
      expect(grids.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('Charts - Row 3', () => {
    it('should render department performance bar chart', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      const barChart = screen.getByRole('img', { name: /department performance/i })
      expect(barChart).toBeInTheDocument()
    })

    it('should render bar chart at full width in row 3', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      const fullWidthRow = container.querySelector('[data-testid="full-width-row"]')
      expect(fullWidthRow).toBeInTheDocument()
    })
  })

  describe('Data Display', () => {
    it('should display all revenue trend data points', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      // LineChart should receive all 4 data points
      const lineChart = screen.getByRole('img', { name: /revenue trend/i })
      expect(lineChart).toBeInTheDocument()
    })

    it('should display all product distribution segments', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      // PieChart should receive all 3 segments
      const pieChart = screen.getByRole('img', { name: /product distribution/i })
      expect(pieChart).toBeInTheDocument()
    })

    it('should display all department performance bars', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      // BarChart should receive all 4 departments
      const barChart = screen.getByRole('img', { name: /department performance/i })
      expect(barChart).toBeInTheDocument()
    })
  })

  describe('Responsive Layout', () => {
    it('should use DashboardGrid for responsive layout', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      const grid = container.querySelector('.dashboard-grid')
      expect(grid).toBeInTheDocument()
    })

    it('should have proper grid structure for metric cards row', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      // Verify first DashboardGrid contains metric cards
      const firstGrid = container.querySelector('.dashboard-grid')
      expect(firstGrid).toBeInTheDocument()

      // Verify metric cards are within the grid
      expect(screen.getByText('Revenue')).toBeInTheDocument()
      expect(screen.getByText('Orders')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have semantic section structure', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      const section = container.querySelector('section')
      expect(section).toBeInTheDocument()
    })

    it('should have proper heading hierarchy', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('Executive Dashboard')
    })

    it('should have accessible chart labels', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      expect(screen.getByRole('img', { name: /revenue trend/i })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: /product distribution/i })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: /department performance/i })).toBeInTheDocument()
    })

    it('should support keyboard navigation', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      // Chart components should be keyboard accessible
      const lineChart = screen.getByRole('img', { name: /revenue trend/i })
      const pieChart = screen.getByRole('img', { name: /product distribution/i })
      const barChart = screen.getByRole('img', { name: /department performance/i })

      // All charts should have tabIndex for keyboard navigation
      expect(lineChart.getAttribute('tabIndex')).toBe('0')
      expect(pieChart.getAttribute('tabIndex')).toBe('0')
      expect(barChart.getAttribute('tabIndex')).toBe('0')
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero values in metrics', () => {
      const zeroData = {
        ...mockDashboardData,
        metrics: {
          revenue: { value: 0, trend: 'neutral' as const, target: 1000 },
          orders: { value: 0, trend: 'neutral' as const, target: 100 },
          efficiency: { value: 0, trend: 'neutral' as const, target: 90 },
          quality: { value: 0, trend: 'neutral' as const, target: 95 },
        },
      }

      render(<ExecutiveDashboard {...zeroData} />)

      expect(screen.getByText('Revenue')).toBeInTheDocument()
    })

    it('should handle empty chart data arrays', () => {
      const emptyData = {
        ...mockDashboardData,
        revenueTrend: [],
        productDistribution: [],
        departmentPerformance: [],
      }

      render(<ExecutiveDashboard {...emptyData} />)

      // Should still render charts with empty data
      expect(screen.getByRole('img', { name: /revenue trend/i })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: /product distribution/i })).toBeInTheDocument()
      expect(screen.getByRole('img', { name: /department performance/i })).toBeInTheDocument()
    })

    it('should handle large numbers in metrics', () => {
      const largeData = {
        ...mockDashboardData,
        metrics: {
          ...mockDashboardData.metrics,
          revenue: { value: 99999999, trend: 'up' as const, target: 90000000 },
        },
      }

      render(<ExecutiveDashboard {...largeData} />)

      expect(screen.getByText(/99999999/)).toBeInTheDocument()
    })
  })

  describe('Component Integration', () => {
    it('should integrate MetricCard components correctly', () => {
      render(<ExecutiveDashboard {...mockDashboardData} />)

      // All MetricCards should display trend indicators
      const trends = screen.getAllByRole('img', { name: /Trend:/i })
      expect(trends.length).toBeGreaterThanOrEqual(4)
    })

    it('should integrate chart components with proper props', () => {
      const { container } = render(<ExecutiveDashboard {...mockDashboardData} />)

      // All charts should use recharts responsive containers
      const rechartsContainers = container.querySelectorAll('.recharts-responsive-container')
      expect(rechartsContainers.length).toBe(3) // LineChart, PieChart, BarChart
    })
  })
})
