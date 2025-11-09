import { BarChart } from '@/components/charts/BarChart'
import { LineChart } from '@/components/charts/LineChart'
import { MetricCard } from '@/components/metrics/MetricCard'
import { DashboardGrid } from '@/components/layouts/DashboardGrid'
import { z } from 'zod'

export interface RoleDashboardProps {
  role: 'production' | 'quality' | 'maintenance' | 'planning'
  metrics: {
    primary: {
      value: number
      label: string
      trend: 'up' | 'down' | 'neutral'
      target: number
      unit?: string
    }
    secondary: {
      value: number
      label: string
      trend: 'up' | 'down' | 'neutral'
      target: number
      unit?: string
    }
    tertiary: {
      value: number
      label: string
      trend: 'up' | 'down' | 'neutral'
      target: number
      unit?: string
    }
  }
  chartData: Array<{ name: string; value: number }>
  trendData: Array<{ name: string; value: number }>
}

// Input validation schema to prevent XSS and data injection
const RoleMetricSchema = z.object({
  value: z.number().finite(),
  label: z.string().max(100).trim(), // Limit length to prevent DoS
  trend: z.enum(['up', 'down', 'neutral']),
  target: z.number().finite(),
  unit: z.string().max(20).trim().optional(), // Limit unit string length
})

const ChartDataPointSchema = z.object({
  name: z.string().max(100).trim(),
  value: z.number().finite(),
})

const RoleDashboardPropsSchema = z.object({
  role: z.enum(['production', 'quality', 'maintenance', 'planning']),
  metrics: z.object({
    primary: RoleMetricSchema,
    secondary: RoleMetricSchema,
    tertiary: RoleMetricSchema,
  }),
  chartData: z.array(ChartDataPointSchema).max(1000), // Prevent memory exhaustion
  trendData: z.array(ChartDataPointSchema).max(1000),
})

// Role configuration mapping
const ROLE_CONFIG = {
  production: {
    title: 'Production Dashboard',
    chartLabel: 'Machine Utilization',
    trendLabel: 'Work Order Status',
  },
  quality: {
    title: 'Quality Dashboard',
    chartLabel: 'Inspection Results',
    trendLabel: 'NCR Trend',
  },
  maintenance: {
    title: 'Maintenance Dashboard',
    chartLabel: 'Equipment Status',
    trendLabel: 'Maintenance Schedule',
  },
  planning: {
    title: 'Planning Dashboard',
    chartLabel: 'Capacity Utilization',
    trendLabel: 'Order Backlog',
  },
} as const

// Chart configuration constants
const CHART_HEIGHT = 300
const CHART_COLORS = {
  bar: '#1976d2',
  line: '#388e3c',
} as const

/**
 * RoleDashboard Component
 *
 * Role-specific dashboard that adapts layout and metrics based on user role.
 * Supports production, quality, maintenance, and planning roles.
 *
 * Layout:
 * - Row 1: 3 MetricCards (Primary, Secondary, Tertiary)
 * - Row 2: 2 Charts side-by-side (BarChart for main data, LineChart for trends)
 *
 * Accessibility: WCAG 2.1 AA compliant with role-based headings and ARIA labels
 */
export function RoleDashboard(props: RoleDashboardProps) {
  // Validate input data to prevent XSS and injection attacks
  const validated = RoleDashboardPropsSchema.parse(props)
  const { role, metrics, chartData, trendData } = validated

  const config = ROLE_CONFIG[role]

  return (
    <section
      role="region"
      aria-label={config.title}
      data-testid="role-dashboard"
    >
      <h2 className="text-2xl font-bold mb-6">{config.title}</h2>

      {/* Row 1: Metric Cards */}
      <DashboardGrid columns={3} gap={1.5}>
        <MetricCard
          value={metrics.primary.value}
          label={metrics.primary.label}
          trend={metrics.primary.trend}
          target={metrics.primary.target}
          unit={metrics.primary.unit}
        />
        <MetricCard
          value={metrics.secondary.value}
          label={metrics.secondary.label}
          trend={metrics.secondary.trend}
          target={metrics.secondary.target}
          unit={metrics.secondary.unit}
        />
        <MetricCard
          value={metrics.tertiary.value}
          label={metrics.tertiary.label}
          trend={metrics.tertiary.trend}
          target={metrics.tertiary.target}
          unit={metrics.tertiary.unit}
        />
      </DashboardGrid>

      {/* Row 2: Charts - BarChart and LineChart side-by-side */}
      <DashboardGrid columns={2} gap={1.5} className="mt-6">
        <div>
          <h3 className="text-lg font-semibold mb-3">{config.chartLabel}</h3>
          <BarChart
            data={chartData}
            height={CHART_HEIGHT}
            color={CHART_COLORS.bar}
            ariaLabel={config.chartLabel}
          />
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-3">{config.trendLabel}</h3>
          <LineChart
            data={trendData}
            height={CHART_HEIGHT}
            color={CHART_COLORS.line}
            ariaLabel={config.trendLabel}
          />
        </div>
      </DashboardGrid>
    </section>
  )
}
