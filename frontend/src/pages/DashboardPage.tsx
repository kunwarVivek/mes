/**
 * DashboardPage Component
 *
 * Executive Dashboard with KPIs and visualizations
 */
import React from 'react'
import { useDashboardMetrics } from '@/hooks/useDashboardMetrics'
import { MetricCard } from '@/design-system/molecules/MetricCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/design-system/atoms/Skeleton'
import { Button } from '@/design-system/atoms'
import { Package, ClipboardList, AlertTriangle } from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import type { OrderStatus } from '@/features/work-orders/schemas/work-order.schema'
import type { NCRStatus } from '@/features/quality/schemas/ncr.schema'

export const DashboardPage = () => {
  const { materials, workOrders, ncrs, isLoading, error, metrics } = useDashboardMetrics()

  // Loading state
  if (isLoading) {
    return (
      <div className="dashboard-page p-6">
        <h1 className="text-3xl font-bold mb-6">Executive Dashboard</h1>

        {/* KPI Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <Skeleton width={100} height={20} />
                <Skeleton variant="circular" width={24} height={24} />
              </CardHeader>
              <CardContent>
                <Skeleton width={60} height={32} />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton width={150} height={24} />
              </CardHeader>
              <CardContent>
                <Skeleton width="100%" height={300} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="dashboard-page p-6">
        <h1 className="text-3xl font-bold mb-6">Executive Dashboard</h1>

        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded mb-4">
          <p className="font-medium">Failed to load dashboard data</p>
          <p className="text-sm mt-1">{error.message}</p>
        </div>

        <Button
          onClick={() => window.location.reload()}
          variant="outline"
        >
          Retry
        </Button>
      </div>
    )
  }

  if (!metrics) {
    return null
  }

  // Prepare chart data
  const workOrderChartData = Object.entries(metrics.workOrdersByStatus).map(
    ([status, count]) => ({
      status,
      count,
    })
  )

  const ncrChartData = Object.entries(metrics.ncrsByStatus).map(([status, count]) => ({
    status,
    count,
  }))

  // Colors for work order statuses
  const workOrderColors: Record<OrderStatus, string> = {
    PLANNED: '#6b7280', // gray
    RELEASED: '#f59e0b', // yellow
    IN_PROGRESS: '#10b981', // green
    COMPLETED: '#059669', // dark green
    CANCELLED: '#ef4444', // red
  }

  // Colors for NCR statuses
  const ncrColors: Record<NCRStatus, string> = {
    OPEN: '#ef4444', // red
    IN_REVIEW: '#f59e0b', // yellow
    RESOLVED: '#10b981', // green
    CLOSED: '#6b7280', // gray
  }

  return (
    <div className="dashboard-page p-6">
      <h1 className="text-3xl font-bold mb-6">Executive Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <MetricCard
          title="Total Materials"
          value={metrics.totalMaterials}
          icon={<Package className="h-5 w-5 text-muted-foreground" />}
        />
        <MetricCard
          title="Total Work Orders"
          value={metrics.totalWorkOrders}
          icon={<ClipboardList className="h-5 w-5 text-muted-foreground" />}
        />
        <MetricCard
          title="Total NCRs"
          value={metrics.totalNCRs}
          icon={<AlertTriangle className="h-5 w-5 text-muted-foreground" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Work Orders Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Work Orders by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={workOrderChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="status" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8">
                  {workOrderChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={workOrderColors[entry.status as OrderStatus]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* NCRs Chart */}
        <Card>
          <CardHeader>
            <CardTitle>NCRs by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={ncrChartData}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label
                >
                  {ncrChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={ncrColors[entry.status as NCRStatus]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

DashboardPage.displayName = 'DashboardPage'
