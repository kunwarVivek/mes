import { BarChart } from '@/components/charts/BarChart'
import { LineChart } from '@/components/charts/LineChart'
import { PieChart } from '@/components/charts/PieChart'
import { MetricCard } from '@/components/metrics/MetricCard'
import { DashboardGrid } from '@/components/layouts/DashboardGrid'
import { z } from 'zod'

export interface ExecutiveDashboardProps {
  metrics: {
    revenue: { value: number; trend: 'up' | 'down' | 'neutral'; target: number }
    orders: { value: number; trend: 'up' | 'down' | 'neutral'; target: number }
    efficiency: { value: number; trend: 'up' | 'down' | 'neutral'; target: number }
    quality: { value: number; trend: 'up' | 'down' | 'neutral'; target: number }
  }
  revenueTrend: Array<{ name: string; value: number }>
  productDistribution: Array<{ name: string; value: number }>
  departmentPerformance: Array<{ name: string; value: number }>
}

// Input validation schema to prevent XSS and data injection
const MetricSchema = z.object({
  value: z.number().finite(),
  trend: z.enum(['up', 'down', 'neutral']),
  target: z.number().finite(),
})

const ChartDataPointSchema = z.object({
  name: z.string().max(100).trim(), // Limit length to prevent DoS
  value: z.number().finite(),
})

const ExecutiveDashboardPropsSchema = z.object({
  metrics: z.object({
    revenue: MetricSchema,
    orders: MetricSchema,
    efficiency: MetricSchema,
    quality: MetricSchema,
  }),
  revenueTrend: z.array(ChartDataPointSchema).max(1000), // Prevent memory exhaustion
  productDistribution: z.array(ChartDataPointSchema).max(1000),
  departmentPerformance: z.array(ChartDataPointSchema).max(1000),
})

// Chart configuration constants
const CHART_HEIGHT = 300
const CHART_COLORS = {
  revenue: '#1976d2',
  department: '#388e3c',
} as const

/**
 * ExecutiveDashboard Component
 *
 * Executive-level overview dashboard displaying key business metrics,
 * revenue trends, product distribution, and department performance.
 *
 * Layout:
 * - Row 1: 4 MetricCards (Revenue, Orders, Efficiency, Quality)
 * - Row 2: 2 Charts side-by-side (Revenue trend, Product distribution)
 * - Row 3: 1 full-width Chart (Department performance)
 *
 * Accessibility: WCAG 2.1 AA compliant with semantic HTML and ARIA labels
 */
export function ExecutiveDashboard(props: ExecutiveDashboardProps) {
  // Validate input data to prevent XSS and injection attacks
  const validated = ExecutiveDashboardPropsSchema.parse(props)
  const { metrics, revenueTrend, productDistribution, departmentPerformance } = validated

  return (
    <section
      role="region"
      aria-label="Executive Dashboard"
      data-testid="executive-dashboard"
    >
      <h2 className="text-2xl font-bold mb-6">Executive Dashboard</h2>

      {/* Row 1: Metric Cards */}
      <DashboardGrid columns={4} gap={1.5} data-testid="metrics-row">
        <MetricCard
          value={metrics.revenue.value}
          label="Revenue"
          trend={metrics.revenue.trend}
          target={metrics.revenue.target}
        />
        <MetricCard
          value={metrics.orders.value}
          label="Orders"
          trend={metrics.orders.trend}
          target={metrics.orders.target}
        />
        <MetricCard
          value={metrics.efficiency.value}
          label="Efficiency"
          trend={metrics.efficiency.trend}
          target={metrics.efficiency.target}
          unit="%"
        />
        <MetricCard
          value={metrics.quality.value}
          label="Quality"
          trend={metrics.quality.trend}
          target={metrics.quality.target}
          unit="%"
        />
      </DashboardGrid>

      {/* Row 2: Revenue Trend and Product Distribution Charts */}
      <DashboardGrid
        columns={2}
        gap={1.5}
        className="mt-6"
        data-testid="dashboard-row"
      >
        <div>
          <h3 className="text-lg font-semibold mb-3">Revenue Trend</h3>
          <LineChart
            data={revenueTrend}
            height={CHART_HEIGHT}
            color={CHART_COLORS.revenue}
            ariaLabel="Revenue trend over time"
          />
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-3">Product Distribution</h3>
          <PieChart
            data={productDistribution}
            height={CHART_HEIGHT}
            ariaLabel="Product distribution by category"
          />
        </div>
      </DashboardGrid>

      {/* Row 3: Department Performance Bar Chart */}
      <div className="mt-6" data-testid="full-width-row">
        <h3 className="text-lg font-semibold mb-3">Department Performance</h3>
        <BarChart
          data={departmentPerformance}
          height={CHART_HEIGHT}
          color={CHART_COLORS.department}
          ariaLabel="Department performance comparison"
        />
      </div>
    </section>
  )
}
