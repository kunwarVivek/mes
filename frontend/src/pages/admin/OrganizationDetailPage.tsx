import { useEffect, useState } from 'react'
import { useNavigate, useParams } from '@tanstack/react-router'
import {
  adminService,
  Organization,
  Subscription,
  SubscriptionUsage,
  AdminActionResponse,
} from '@/services/admin.service'
import { useAuthStore } from '@/stores/auth.store'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/design-system/atoms/Card'
import { Button } from '@/design-system/atoms/Button'
import { Input } from '@/design-system/atoms/Input'
import { Alert, AlertDescription } from '@/design-system/atoms/Alert'
import { Badge } from '@/design-system/atoms/Badge'
import {
  Building2,
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Clock,
  Users,
  Database,
  Calendar,
} from 'lucide-react'

/**
 * Organization Detail Page
 *
 * Admin view of single organization:
 * - Organization details
 * - Subscription status and limits
 * - Usage metrics
 * - Admin actions (extend trial, suspend, override tier, etc.)
 *
 * Access: Requires is_superuser=true
 */

export function OrganizationDetailPage() {
  const navigate = useNavigate()
  const params = useParams({ from: '/admin/organizations/$orgId' })
  const { user } = useAuthStore()

  const [organization, setOrganization] = useState<Organization | null>(null)
  const [usage, setUsage] = useState<SubscriptionUsage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  // Action form states
  const [extendDays, setExtendDays] = useState('14')
  const [reason, setReason] = useState('')

  useEffect(() => {
    // Check if user is superuser
    if (!user?.is_superuser) {
      navigate({ to: '/dashboard' })
      return
    }

    if (params.orgId) {
      loadOrganizationData(parseInt(params.orgId))
    }
  }, [user, navigate, params.orgId])

  const loadOrganizationData = async (orgId: number) => {
    try {
      setLoading(true)
      setError(null)

      const [orgData, usageData] = await Promise.all([
        adminService.getOrganization(orgId),
        adminService.getSubscriptionUsage(orgId).catch(() => null), // Usage might not exist yet
      ])

      setOrganization(orgData)
      setUsage(usageData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load organization data')
    } finally {
      setLoading(false)
    }
  }

  const handleExtendTrial = async () => {
    if (!organization?.subscription?.id) return

    try {
      setActionLoading(true)
      setActionSuccess(null)
      setError(null)

      await adminService.extendTrial(
        organization.subscription.id,
        parseInt(extendDays),
        reason
      )

      setActionSuccess(`Trial extended by ${extendDays} days`)
      setReason('')

      // Reload data
      loadOrganizationData(organization.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extend trial')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSuspend = async () => {
    if (!organization?.subscription?.id) return
    if (!confirm('Are you sure you want to suspend this subscription?')) return

    try {
      setActionLoading(true)
      setActionSuccess(null)
      setError(null)

      await adminService.suspendSubscription(organization.subscription.id, reason)

      setActionSuccess('Subscription suspended')
      setReason('')

      // Reload data
      loadOrganizationData(organization.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to suspend subscription')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReactivate = async () => {
    if (!organization?.subscription?.id) return

    try {
      setActionLoading(true)
      setActionSuccess(null)
      setError(null)

      await adminService.reactivateSubscription(organization.subscription.id, reason)

      setActionSuccess('Subscription reactivated')
      setReason('')

      // Reload data
      loadOrganizationData(organization.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reactivate subscription')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading organization...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!organization) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Organization not found</AlertDescription>
        </Alert>
      </div>
    )
  }

  const subscription = organization.subscription
  const trialDaysRemaining = subscription?.trial_ends_at
    ? Math.ceil(
        (new Date(subscription.trial_ends_at).getTime() - Date.now()) /
          (1000 * 60 * 60 * 24)
      )
    : 0

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate({ to: '/admin/organizations' })}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Organizations
          </Button>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Building2 className="h-8 w-8" />
              {organization.org_name}
            </h1>
            <p className="text-gray-600 mt-1">
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                {organization.org_code}
              </code>
            </p>
          </div>
        </div>
      </div>

      {/* Action Feedback */}
      {actionSuccess && (
        <Alert variant="success">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>{actionSuccess}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Organization Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle>Organization Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Organization ID</p>
              <p className="font-medium">{organization.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Created At</p>
              <p className="font-medium">
                {new Date(organization.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <Badge variant={organization.is_active ? 'default' : 'destructive'}>
                {organization.is_active ? 'ACTIVE' : 'INACTIVE'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Subscription Info */}
        {subscription && (
          <Card>
            <CardHeader>
              <CardTitle>Subscription</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Tier</p>
                <Badge
                  variant="outline"
                  className={
                    subscription.tier === 'enterprise'
                      ? 'text-green-700 bg-green-100'
                      : subscription.tier === 'professional'
                        ? 'text-purple-700 bg-purple-100'
                        : 'text-blue-700 bg-blue-100'
                  }
                >
                  {subscription.tier.toUpperCase()}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <Badge
                  className={
                    subscription.status === 'active'
                      ? 'text-green-600 bg-green-50'
                      : subscription.status === 'trial'
                        ? 'text-blue-600 bg-blue-50'
                        : 'text-red-600 bg-red-50'
                  }
                >
                  {subscription.status.toUpperCase()}
                </Badge>
              </div>
              {subscription.status === 'trial' && subscription.trial_ends_at && (
                <div>
                  <p className="text-sm text-gray-600">Trial Ends</p>
                  <p className="font-medium flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    {new Date(subscription.trial_ends_at).toLocaleDateString()} (
                    {trialDaysRemaining} days)
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600">Billing Cycle</p>
                <p className="font-medium">{subscription.billing_cycle}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Usage Metrics */}
      {usage && subscription && (
        <Card>
          <CardHeader>
            <CardTitle>Usage & Limits</CardTitle>
            <CardDescription>Current usage vs subscription limits</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Users */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Users</p>
                  <p className="text-2xl font-bold">
                    {usage.current_users}
                    {subscription.max_users && ` / ${subscription.max_users}`}
                  </p>
                </div>
                <Users className="h-6 w-6 text-blue-600" />
              </div>

              {/* Plants */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Plants</p>
                  <p className="text-2xl font-bold">
                    {usage.current_plants}
                    {subscription.max_plants && ` / ${subscription.max_plants}`}
                  </p>
                </div>
                <Building2 className="h-6 w-6 text-purple-600" />
              </div>

              {/* Storage */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Storage</p>
                  <p className="text-2xl font-bold">
                    {usage.storage_used_gb.toFixed(1)} GB
                    {subscription.storage_limit_gb && ` / ${subscription.storage_limit_gb} GB`}
                  </p>
                </div>
                <Database className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Admin Actions */}
      {subscription && (
        <Card>
          <CardHeader>
            <CardTitle>Admin Actions</CardTitle>
            <CardDescription>Modify subscription and access</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Extend Trial */}
            {subscription.status === 'trial' && (
              <div className="p-4 border rounded-lg space-y-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Extend Trial
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Input
                    type="number"
                    placeholder="Days (1-90)"
                    value={extendDays}
                    onChange={(e) => setExtendDays(e.target.value)}
                    min="1"
                    max="90"
                  />
                  <Input
                    placeholder="Reason (required)"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="md:col-span-2"
                  />
                </div>
                <Button
                  onClick={handleExtendTrial}
                  disabled={actionLoading || !reason.trim() || !extendDays}
                >
                  {actionLoading ? 'Processing...' : 'Extend Trial'}
                </Button>
              </div>
            )}

            {/* Suspend/Reactivate */}
            <div className="p-4 border rounded-lg space-y-3">
              <h3 className="font-semibold flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {subscription.status === 'suspended' ? 'Reactivate' : 'Suspend'} Subscription
              </h3>
              <Input
                placeholder="Reason (required)"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              {subscription.status === 'suspended' ? (
                <Button
                  onClick={handleReactivate}
                  disabled={actionLoading || !reason.trim()}
                  variant="default"
                >
                  {actionLoading ? 'Processing...' : 'Reactivate Subscription'}
                </Button>
              ) : (
                <Button
                  onClick={handleSuspend}
                  disabled={actionLoading || !reason.trim()}
                  variant="destructive"
                >
                  {actionLoading ? 'Processing...' : 'Suspend Subscription'}
                </Button>
              )}
            </div>

            {/* Impersonate (placeholder for now) */}
            <div className="p-4 border rounded-lg space-y-3">
              <h3 className="font-semibold flex items-center gap-2">
                <Users className="h-4 w-4" />
                Customer Support
              </h3>
              <p className="text-sm text-gray-600">
                Impersonation feature will be available in next release
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
