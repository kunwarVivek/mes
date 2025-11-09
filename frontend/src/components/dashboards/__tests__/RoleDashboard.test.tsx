/**
 * RoleDashboard Component Tests
 *
 * TDD: Testing role-specific dashboard layouts, metrics display, and accessibility
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RoleDashboard } from '../RoleDashboard'
import type { RoleDashboardProps } from '../RoleDashboard'

// Mock data factory
const createMockMetrics = () => ({
  primary: { value: 85, label: 'Primary Metric', trend: 'up' as const, target: 90, unit: '%' },
  secondary: { value: 72, label: 'Secondary Metric', trend: 'down' as const, target: 80, unit: '%' },
  tertiary: { value: 95, label: 'Tertiary Metric', trend: 'neutral' as const, target: 95, unit: '%' },
})

const createMockChartData = () => [
  { name: 'Item 1', value: 100 },
  { name: 'Item 2', value: 200 },
  { name: 'Item 3', value: 150 },
]

const createMockTrendData = () => [
  { name: 'Mon', value: 80 },
  { name: 'Tue', value: 85 },
  { name: 'Wed', value: 90 },
]

describe('RoleDashboard', () => {
  describe('Production Role', () => {
    const productionProps: RoleDashboardProps = {
      role: 'production',
      metrics: createMockMetrics(),
      chartData: createMockChartData(),
      trendData: createMockTrendData(),
    }

    it('should render production dashboard heading', () => {
      render(<RoleDashboard {...productionProps} />)

      expect(screen.getByRole('heading', { name: /production dashboard/i })).toBeInTheDocument()
    })

    it('should render all three metric cards', () => {
      render(<RoleDashboard {...productionProps} />)

      expect(screen.getByText('Primary Metric')).toBeInTheDocument()
      expect(screen.getByText('Secondary Metric')).toBeInTheDocument()
      expect(screen.getByText('Tertiary Metric')).toBeInTheDocument()
    })

    it('should render machine utilization chart with correct aria label', () => {
      render(<RoleDashboard {...productionProps} />)

      expect(screen.getByRole('img', { name: /machine utilization/i })).toBeInTheDocument()
    })

    it('should render work order status trend chart', () => {
      render(<RoleDashboard {...productionProps} />)

      expect(screen.getByRole('img', { name: /work order status/i })).toBeInTheDocument()
    })

    it('should have proper accessibility attributes', () => {
      render(<RoleDashboard {...productionProps} />)

      const dashboard = screen.getByRole('region', { name: /production dashboard/i })
      expect(dashboard).toBeInTheDocument()
    })
  })

  describe('Quality Role', () => {
    const qualityProps: RoleDashboardProps = {
      role: 'quality',
      metrics: createMockMetrics(),
      chartData: createMockChartData(),
      trendData: createMockTrendData(),
    }

    it('should render quality dashboard heading', () => {
      render(<RoleDashboard {...qualityProps} />)

      expect(screen.getByRole('heading', { name: /quality dashboard/i })).toBeInTheDocument()
    })

    it('should render inspection results chart', () => {
      render(<RoleDashboard {...qualityProps} />)

      expect(screen.getByRole('img', { name: /inspection results/i })).toBeInTheDocument()
    })

    it('should render NCR trend chart', () => {
      render(<RoleDashboard {...qualityProps} />)

      expect(screen.getByRole('img', { name: /ncr trend/i })).toBeInTheDocument()
    })

    it('should display all quality metrics', () => {
      render(<RoleDashboard {...qualityProps} />)

      expect(screen.getByText('Primary Metric')).toBeInTheDocument()
      expect(screen.getByText('Secondary Metric')).toBeInTheDocument()
      expect(screen.getByText('Tertiary Metric')).toBeInTheDocument()
    })
  })

  describe('Maintenance Role', () => {
    const maintenanceProps: RoleDashboardProps = {
      role: 'maintenance',
      metrics: createMockMetrics(),
      chartData: createMockChartData(),
      trendData: createMockTrendData(),
    }

    it('should render maintenance dashboard heading', () => {
      render(<RoleDashboard {...maintenanceProps} />)

      expect(screen.getByRole('heading', { name: /maintenance dashboard/i })).toBeInTheDocument()
    })

    it('should render equipment status chart', () => {
      render(<RoleDashboard {...maintenanceProps} />)

      expect(screen.getByRole('img', { name: /equipment status/i })).toBeInTheDocument()
    })

    it('should render maintenance schedule trend chart', () => {
      render(<RoleDashboard {...maintenanceProps} />)

      expect(screen.getByRole('img', { name: /maintenance schedule/i })).toBeInTheDocument()
    })

    it('should display all maintenance metrics', () => {
      render(<RoleDashboard {...maintenanceProps} />)

      expect(screen.getByText('Primary Metric')).toBeInTheDocument()
      expect(screen.getByText('Secondary Metric')).toBeInTheDocument()
      expect(screen.getByText('Tertiary Metric')).toBeInTheDocument()
    })
  })

  describe('Planning Role', () => {
    const planningProps: RoleDashboardProps = {
      role: 'planning',
      metrics: createMockMetrics(),
      chartData: createMockChartData(),
      trendData: createMockTrendData(),
    }

    it('should render planning dashboard heading', () => {
      render(<RoleDashboard {...planningProps} />)

      expect(screen.getByRole('heading', { name: /planning dashboard/i })).toBeInTheDocument()
    })

    it('should render capacity utilization chart', () => {
      render(<RoleDashboard {...planningProps} />)

      expect(screen.getByRole('img', { name: /capacity utilization/i })).toBeInTheDocument()
    })

    it('should render order backlog trend chart', () => {
      render(<RoleDashboard {...planningProps} />)

      expect(screen.getByRole('img', { name: /order backlog/i })).toBeInTheDocument()
    })

    it('should display all planning metrics', () => {
      render(<RoleDashboard {...planningProps} />)

      expect(screen.getByText('Primary Metric')).toBeInTheDocument()
      expect(screen.getByText('Secondary Metric')).toBeInTheDocument()
      expect(screen.getByText('Tertiary Metric')).toBeInTheDocument()
    })
  })

  describe('Data Display', () => {
    it('should display metric values correctly', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      expect(screen.getByText(/85\.0%/)).toBeInTheDocument()
      expect(screen.getByText(/72\.0%/)).toBeInTheDocument()
      expect(screen.getByText(/95\.0%/)).toBeInTheDocument()
    })

    it('should display trend indicators', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      expect(screen.getByText('↑')).toBeInTheDocument() // up trend
      expect(screen.getByText('↓')).toBeInTheDocument() // down trend
      expect(screen.getByText('→')).toBeInTheDocument() // neutral trend
    })

    it('should display target values', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      expect(screen.getByText('Target: 90%')).toBeInTheDocument()
      expect(screen.getByText('Target: 80%')).toBeInTheDocument()
      expect(screen.getByText('Target: 95%')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have semantic heading hierarchy', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      const mainHeading = screen.getByRole('heading', { level: 2 })
      expect(mainHeading).toBeInTheDocument()
    })

    it('should have role region with proper label', () => {
      const props: RoleDashboardProps = {
        role: 'quality',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      const region = screen.getByRole('region', { name: /quality dashboard/i })
      expect(region).toBeInTheDocument()
    })

    it('should have data-testid for testing', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      const { container } = render(<RoleDashboard {...props} />)

      expect(container.querySelector('[data-testid="role-dashboard"]')).toBeInTheDocument()
    })
  })

  describe('Responsive Behavior', () => {
    it('should use DashboardGrid for layout', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      const { container } = render(<RoleDashboard {...props} />)

      expect(container.querySelector('.dashboard-grid')).toBeInTheDocument()
    })

    it('should render 3-column grid for metrics', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      const { container } = render(<RoleDashboard {...props} />)

      const grid = container.querySelector('.dashboard-grid')
      expect(grid).toHaveStyle({ gridTemplateColumns: 'repeat(3, 1fr)' })
    })
  })

  describe('Edge Cases', () => {
    it('should handle metrics without units', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: {
          primary: { value: 100, label: 'Count', trend: 'up', target: 120 },
          secondary: { value: 50, label: 'Items', trend: 'down', target: 60 },
          tertiary: { value: 75, label: 'Total', trend: 'neutral', target: 75 },
        },
        chartData: createMockChartData(),
        trendData: createMockTrendData(),
      }

      render(<RoleDashboard {...props} />)

      expect(screen.getByText(/100\.0/)).toBeInTheDocument()
      expect(screen.getByText('Target: 120')).toBeInTheDocument()
    })

    it('should handle empty chart data gracefully', () => {
      const props: RoleDashboardProps = {
        role: 'production',
        metrics: createMockMetrics(),
        chartData: [],
        trendData: [],
      }

      render(<RoleDashboard {...props} />)

      expect(screen.getByRole('heading', { name: /production dashboard/i })).toBeInTheDocument()
    })
  })
})
