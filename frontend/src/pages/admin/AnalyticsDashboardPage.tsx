import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  analyticsService,
  AnalyticsDashboardSummary,
  MRRGrowthDataPoint,
} from '@/services/analytics.service'
import { useAuthStore } from '@/stores/auth.store'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/design-system/atoms/Card'
import { Button } from '@/design-system/atoms/Button'
import { Alert, AlertDescription } from '@/design-system/atoms/Alert'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  AlertCircle,
  ArrowLeft,
  BarChart3,
  PieChart,
} from 'lucide-react'

/**
 * Analytics Dashboard Page
 *
 * Business intelligence dashboard for platform admins:
 * - MRR/ARR tracking with growth charts
 * - Trial conversion funnel
 * - Churn analysis
 * - Revenue forecasting
 * - Cohort retention (future)
 *
 * Access: Requires is_superuser=true
 */

export function AnalyticsDashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [data, setData] = useState<AnalyticsDashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is superuser
    if (!user?.is_superuser) {
      navigate({ to: '/dashboard' })
      return
    }

    loadAnalytics()
  }, [user, navigate])

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)
      const summary = await analyticsService.getDashboardSummary()
      setData(summary)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading analytics...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data) {
    return null
  }

  // Calculate growth metrics
  const currentMRR = data.mrr.total_mrr
  const lastMonthMRR = data.growth.length > 0 ? data.growth[data.growth.length - 1].mrr : currentMRR
  const mrrGrowth = lastMonthMRR > 0 ? ((currentMRR - lastMonthMRR) / lastMonthMRR) * 100 : 0

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/admin/dashboard' })}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
            <p className="text-gray-600 mt-1">Business intelligence and revenue metrics</p>
          </div>
        </div>
        <Button onClick={loadAnalytics} variant="outline">
          <BarChart3 className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* MRR */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Recurring Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${currentMRR.toLocaleString()}</div>
            <div className="flex items-center mt-1">
              {mrrGrowth >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
              )}
              <p
                className={`text-xs ${
                  mrrGrowth >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {mrrGrowth >= 0 ? '+' : ''}
                {mrrGrowth.toFixed(1)}% from last month
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ARR */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual Recurring Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(currentMRR * 12).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              MRR × 12
            </p>
          </CardContent>
        </Card>

        {/* ARPU */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Revenue Per User</CardTitle>
            <Users className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${data.mrr.arpu.toFixed(0)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.mrr.customer_count} paying customers
            </p>
          </CardContent>
        </Card>

        {/* Trial Conversion */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trial Conversion Rate</CardTitle>
            <PieChart className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.trials.conversion_rate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.trials.converted_trials} of {data.trials.total_trials} converted
            </p>
          </CardContent>
        </Card>
      </div>

      {/* MRR Growth Chart */}
      <Card>
        <CardHeader>
          <CardTitle>MRR Growth (Last 6 Months)</CardTitle>
          <CardDescription>Monthly recurring revenue trend</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <MRRGrowthChart data={data.growth} />
          </div>
        </CardContent>
      </Card>

      {/* MRR Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* By Tier */}
        <Card>
          <CardHeader>
            <CardTitle>MRR by Tier</CardTitle>
            <CardDescription>Revenue distribution across pricing tiers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium">Starter</span>
                </div>
                <div className="text-sm font-bold">
                  ${data.mrr.mrr_by_tier.starter.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{
                    width: `${(data.mrr.mrr_by_tier.starter / currentMRR) * 100}%`,
                  }}
                ></div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-sm font-medium">Professional</span>
                </div>
                <div className="text-sm font-bold">
                  ${data.mrr.mrr_by_tier.professional.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full"
                  style={{
                    width: `${(data.mrr.mrr_by_tier.professional / currentMRR) * 100}%`,
                  }}
                ></div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm font-medium">Enterprise</span>
                </div>
                <div className="text-sm font-bold">
                  ${data.mrr.mrr_by_tier.enterprise.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{
                    width: `${(data.mrr.mrr_by_tier.enterprise / currentMRR) * 100}%`,
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* By Billing Cycle */}
        <Card>
          <CardHeader>
            <CardTitle>MRR by Billing Cycle</CardTitle>
            <CardDescription>Monthly vs annual subscriptions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium">Monthly</span>
                </div>
                <div className="text-sm font-bold">
                  ${data.mrr.mrr_by_cycle.monthly.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{
                    width: `${(data.mrr.mrr_by_cycle.monthly / currentMRR) * 100}%`,
                  }}
                ></div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm font-medium">Annual (10% discount)</span>
                </div>
                <div className="text-sm font-bold">
                  ${data.mrr.mrr_by_cycle.annual.toLocaleString()}
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{
                    width: `${(data.mrr.mrr_by_cycle.annual / currentMRR) * 100}%`,
                  }}
                ></div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-gray-600">
                  Annual subscriptions provide more predictable revenue and reduce churn
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trial & Churn Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Trial Conversion Funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Trial Conversion Funnel</CardTitle>
            <CardDescription>Trial to paid conversion metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Total Trials Created</span>
              <span className="font-bold">{data.trials.total_trials}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Converted to Paid</span>
              <span className="font-bold text-green-600">
                {data.trials.converted_trials}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Currently Active Trials</span>
              <span className="font-bold text-blue-600">{data.trials.active_trials}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Expired Without Converting</span>
              <span className="font-bold text-red-600">{data.trials.expired_trials}</span>
            </div>

            <div className="pt-4 mt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Conversion Rate</span>
                <span className="text-2xl font-bold text-green-600">
                  {data.trials.conversion_rate}%
                </span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-600">Avg. Days to Convert</span>
                <span className="text-sm font-medium">
                  {data.trials.avg_days_to_convert} days
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Churn Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Churn Analysis (30 Days)</CardTitle>
            <CardDescription>Customer and revenue churn</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Customers at Start</span>
              <span className="font-bold">{data.churn.customers_start}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Churned Customers</span>
              <span className="font-bold text-red-600">{data.churn.churned_count}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">MRR Churned</span>
              <span className="font-bold text-red-600">
                ${data.churn.mrr_churned.toLocaleString()}
              </span>
            </div>

            <div className="pt-4 mt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Customer Churn Rate</span>
                <span
                  className={`text-2xl font-bold ${
                    data.churn.churn_rate < 5 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {data.churn.churn_rate}%
                </span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-600">MRR Churn Rate</span>
                <span className="text-sm font-medium">
                  {data.churn.mrr_churn_rate}%
                </span>
              </div>
            </div>

            {data.churn.churn_rate >= 5 && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Churn rate is above healthy threshold (5%). Consider retention campaigns.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Revenue Forecast */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Forecast (Next 6 Months)</CardTitle>
          <CardDescription>
            Projected MRR based on current growth trends (
            {data.forecast[0]?.growth_rate?.toFixed(1)}% monthly growth)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.forecast.map((forecast, index) => (
              <div key={forecast.date} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{forecast.date}</span>
                <div className="flex items-center gap-4">
                  <span className="text-sm font-medium">
                    MRR: ${forecast.forecasted_mrr.toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-500">
                    ARR: ${forecast.forecasted_arr.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Simple MRR Growth Chart Component
function MRRGrowthChart({ data }: { data: MRRGrowthDataPoint[] }) {
  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-full text-gray-400">No data</div>
  }

  const maxMRR = Math.max(...data.map((d) => d.mrr))
  const minMRR = Math.min(...data.map((d) => d.mrr))
  const range = maxMRR - minMRR

  return (
    <div className="w-full h-full flex items-end justify-between gap-2 px-4 pb-8">
      {data.map((point, index) => {
        const heightPercent = range > 0 ? ((point.mrr - minMRR) / range) * 100 : 50
        return (
          <div key={point.date} className="flex-1 flex flex-col items-center gap-2">
            <div
              className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer relative group"
              style={{ height: `${Math.max(heightPercent, 5)}%` }}
            >
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                ${point.mrr.toLocaleString()}
                <br />
                +{point.new_customers} / -{point.churned_customers}
              </div>
            </div>
            <span className="text-xs text-gray-500 transform -rotate-45 origin-top-left">
              {point.date}
            </span>
          </div>
        )
      })}
    </div>
  )
}
