import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { adminService, PlatformMetrics } from '@/services/admin.service'
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
  Users,
  Building2,
  DollarSign,
  Database,
  TrendingUp,
  AlertCircle,
  Clock,
  CheckCircle,
} from 'lucide-react'

/**
 * Platform Admin Dashboard
 *
 * Platform-wide KPIs and metrics:
 * - Total organizations, active subscriptions, MRR
 * - Organizations by tier and status
 * - Total users, plants, storage usage
 *
 * Access: Requires is_superuser=true
 */

export function PlatformDashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is superuser
    if (!user?.is_superuser) {
      navigate({ to: '/dashboard' })
      return
    }

    loadMetrics()
  }, [user, navigate])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminService.getMetrics()
      setMetrics(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load metrics')
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
            <p className="text-gray-600">Loading platform metrics...</p>
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

  if (!metrics) {
    return null
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Platform Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">Platform-wide metrics and KPIs</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => navigate({ to: '/admin/organizations' })}
          >
            <Building2 className="h-4 w-4 mr-2" />
            Organizations
          </Button>
          <Button variant="outline" onClick={() => navigate({ to: '/admin/audit-logs' })}>
            <AlertCircle className="h-4 w-4 mr-2" />
            Audit Logs
          </Button>
        </div>
      </div>

      {/* Top-level KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Organizations */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Organizations</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_organizations}</div>
            <p className="text-xs text-muted-foreground mt-1">
              All registered tenants
            </p>
          </CardContent>
        </Card>

        {/* Active Subscriptions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.active_subscriptions}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Paying customers
            </p>
          </CardContent>
        </Card>

        {/* Trial Subscriptions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trial Accounts</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.trial_subscriptions}</div>
            <p className="text-xs text-muted-foreground mt-1">
              14-day free trials
            </p>
          </CardContent>
        </Card>

        {/* MRR */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Recurring Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(metrics.monthly_recurring_revenue / 100).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Total MRR from active subs
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Organizations by Tier */}
      <Card>
        <CardHeader>
          <CardTitle>Organizations by Tier</CardTitle>
          <CardDescription>Distribution across pricing tiers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Starter</p>
                <p className="text-2xl font-bold">
                  {metrics.organizations_by_tier.starter}
                </p>
              </div>
              <div className="text-blue-600">
                <TrendingUp className="h-6 w-6" />
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Professional</p>
                <p className="text-2xl font-bold">
                  {metrics.organizations_by_tier.professional}
                </p>
              </div>
              <div className="text-purple-600">
                <TrendingUp className="h-6 w-6" />
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-600">Enterprise</p>
                <p className="text-2xl font-bold">
                  {metrics.organizations_by_tier.enterprise}
                </p>
              </div>
              <div className="text-green-600">
                <TrendingUp className="h-6 w-6" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Organizations by Status */}
      <Card>
        <CardHeader>
          <CardTitle>Organizations by Status</CardTitle>
          <CardDescription>Subscription lifecycle status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <p className="text-sm font-medium text-gray-600">Trial</p>
              <p className="text-2xl font-bold text-blue-600">
                {metrics.organizations_by_status.trial}
              </p>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <p className="text-sm font-medium text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {metrics.organizations_by_status.active}
              </p>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <p className="text-sm font-medium text-gray-600">Past Due</p>
              <p className="text-2xl font-bold text-orange-600">
                {metrics.organizations_by_status.past_due}
              </p>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <p className="text-sm font-medium text-gray-600">Suspended</p>
              <p className="text-2xl font-bold text-red-600">
                {metrics.organizations_by_status.suspended}
              </p>
            </div>

            <div className="text-center p-4 border rounded-lg">
              <p className="text-sm font-medium text-gray-600">Cancelled</p>
              <p className="text-2xl font-bold text-gray-600">
                {metrics.organizations_by_status.cancelled}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Users */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_users}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Across all organizations
            </p>
          </CardContent>
        </Card>

        {/* Total Plants */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Plants</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.total_plants}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Manufacturing facilities
            </p>
          </CardContent>
        </Card>

        {/* Total Storage */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Storage</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.total_storage_gb.toFixed(1)} GB
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Documents and attachments
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
