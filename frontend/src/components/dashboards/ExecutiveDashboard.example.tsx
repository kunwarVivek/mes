import { ExecutiveDashboard } from './ExecutiveDashboard'
import type { ExecutiveDashboardProps } from './ExecutiveDashboard'

/**
 * ExecutiveDashboard Component Example
 *
 * Demonstrates usage of the ExecutiveDashboard component with sample data.
 */
export function ExecutiveDashboardExample() {
  const mockData: ExecutiveDashboardProps = {
    metrics: {
      revenue: {
        value: 1250000,
        trend: 'up',
        target: 1200000,
      },
      orders: {
        value: 450,
        trend: 'up',
        target: 400,
      },
      efficiency: {
        value: 87.5,
        trend: 'down',
        target: 90,
      },
      quality: {
        value: 96.2,
        trend: 'neutral',
        target: 95,
      },
    },
    revenueTrend: [
      { name: 'Jan', value: 950000 },
      { name: 'Feb', value: 1050000 },
      { name: 'Mar', value: 1150000 },
      { name: 'Apr', value: 1250000 },
      { name: 'May', value: 1300000 },
      { name: 'Jun', value: 1450000 },
    ],
    productDistribution: [
      { name: 'Product A', value: 45 },
      { name: 'Product B', value: 30 },
      { name: 'Product C', value: 25 },
    ],
    departmentPerformance: [
      { name: 'Assembly', value: 92 },
      { name: 'Machining', value: 88 },
      { name: 'Quality Control', value: 95 },
      { name: 'Packaging', value: 85 },
      { name: 'Logistics', value: 90 },
    ],
  }

  return (
    <div className="p-8">
      <ExecutiveDashboard {...mockData} />
    </div>
  )
}

export default ExecutiveDashboardExample
