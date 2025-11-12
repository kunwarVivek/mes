import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  billingService,
  Subscription,
  SubscriptionUsage,
  Invoice,
} from '@/services/billing.service'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/design-system/atoms/Button'
import { Progress } from '@/design-system/atoms/Progress'
import { Alert, AlertDescription } from '@/design-system/atoms/Alert'
import { Badge } from '@/design-system/atoms/Badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/design-system/atoms/Table'
import {
  CreditCard,
  Users,
  Building2,
  Database,
  Calendar,
  AlertCircle,
  CheckCircle,
  ArrowUpCircle,
  FileText,
  ExternalLink,
} from 'lucide-react'

/**
 * Billing Page
 *
 * Customer-facing billing dashboard:
 * - Current subscription and plan details
 * - Usage vs limits with progress bars
 * - Upgrade/downgrade options
 * - Invoice history
 * - Link to Stripe billing portal
 */

export function BillingPage() {
  const navigate = useNavigate()
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [usage, setUsage] = useState<SubscriptionUsage | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBillingData()
  }, [])

  const loadBillingData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [subData, usageData, invoiceData] = await Promise.all([
        billingService.getCurrentSubscription(),
        billingService.getUsage(),
        billingService.listInvoices({ limit: 10 }),
      ])

      setSubscription(subData)
      setUsage(usageData)
      setInvoices(invoiceData.invoices)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load billing information')
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = () => {
    navigate({ to: '/pricing' })
  }

  const handleManageBilling = async () => {
    try {
      const { url } = await billingService.getBillingPortalUrl()
      window.open(url, '_blank')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to open billing portal')
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading billing information...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error && !subscription) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!subscription) {
    return null
  }

  const trialDaysRemaining = subscription.trial_ends_at
    ? Math.ceil(
        (new Date(subscription.trial_ends_at).getTime() - Date.now()) /
          (1000 * 60 * 60 * 24)
      )
    : 0

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      trial: 'text-blue-600 bg-blue-50',
      active: 'text-green-600 bg-green-50',
      past_due: 'text-orange-600 bg-orange-50',
      suspended: 'text-red-600 bg-red-50',
      cancelled: 'text-gray-600 bg-gray-50',
    }

    return (
      <Badge className={colors[status] || 'text-gray-600 bg-gray-50'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    )
  }

  const getTierBadge = (tier: string) => {
    const colors: Record<string, string> = {
      starter: 'text-blue-700 bg-blue-100',
      professional: 'text-purple-700 bg-purple-100',
      enterprise: 'text-green-700 bg-green-100',
    }

    return (
      <Badge variant="outline" className={colors[tier]}>
        {tier.toUpperCase()}
      </Badge>
    )
  }

  const calculateUsagePercentage = (current: number, max?: number): number => {
    if (!max) return 0 // Unlimited
    return Math.min((current / max) * 100, 100)
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-gray-600 mt-1">Manage your subscription and usage</p>
        </div>
        {subscription.status === 'active' && (
          <Button onClick={handleManageBilling} variant="outline">
            <ExternalLink className="h-4 w-4 mr-2" />
            Manage Billing
          </Button>
        )}
      </div>

      {/* Trial Warning */}
      {subscription.status === 'trial' && (
        <Alert
          variant={trialDaysRemaining <= 3 ? 'destructive' : 'info'}
          className="border-l-4"
        >
          <Calendar className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <div>
                <strong>Your trial ends in {trialDaysRemaining} days</strong>
                <p className="text-sm mt-1">
                  Ends on {new Date(subscription.trial_ends_at!).toLocaleDateString()}
                </p>
              </div>
              <Button onClick={handleUpgrade} size="sm">
                Upgrade Now
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Past Due Warning */}
      {subscription.status === 'past_due' && (
        <Alert variant="destructive" className="border-l-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <div>
                <strong>Payment Required</strong>
                <p className="text-sm mt-1">
                  Your last payment failed. Please update your payment method.
                </p>
              </div>
              <Button onClick={handleManageBilling} size="sm" variant="destructive">
                Update Payment
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>Your subscription details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Tier</p>
                <div className="mt-1">{getTierBadge(subscription.tier)}</div>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <div className="mt-1">{getStatusBadge(subscription.status)}</div>
              </div>
              <div>
                <p className="text-sm text-gray-600">Billing Cycle</p>
                <p className="font-medium capitalize">{subscription.billing_cycle}</p>
              </div>
            </div>

            {subscription.status === 'active' && (
              <div className="flex flex-col justify-center">
                <Button onClick={handleUpgrade} className="w-full" size="lg">
                  <ArrowUpCircle className="h-4 w-4 mr-2" />
                  Upgrade Plan
                </Button>
              </div>
            )}

            {subscription.status === 'trial' && (
              <div className="flex flex-col justify-center space-y-3">
                <Button onClick={handleUpgrade} className="w-full" size="lg">
                  <CreditCard className="h-4 w-4 mr-2" />
                  Subscribe Now
                </Button>
                <p className="text-xs text-center text-gray-600">
                  Start at just $49/month
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Usage & Limits */}
      {usage && (
        <Card>
          <CardHeader>
            <CardTitle>Usage & Limits</CardTitle>
            <CardDescription>Current usage vs your plan limits</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Users */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <span className="font-medium">Users</span>
                </div>
                <span className="text-sm text-gray-600">
                  {usage.current_users}
                  {subscription.max_users ? ` / ${subscription.max_users}` : ' / Unlimited'}
                </span>
              </div>
              {subscription.max_users ? (
                <Progress
                  value={calculateUsagePercentage(
                    usage.current_users,
                    subscription.max_users
                  )}
                  className="h-2"
                />
              ) : (
                <div className="text-sm text-green-600">Unlimited users</div>
              )}
            </div>

            {/* Plants */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-purple-600" />
                  <span className="font-medium">Plants</span>
                </div>
                <span className="text-sm text-gray-600">
                  {usage.current_plants}
                  {subscription.max_plants ? ` / ${subscription.max_plants}` : ' / Unlimited'}
                </span>
              </div>
              {subscription.max_plants ? (
                <Progress
                  value={calculateUsagePercentage(
                    usage.current_plants,
                    subscription.max_plants
                  )}
                  className="h-2"
                />
              ) : (
                <div className="text-sm text-green-600">Unlimited plants</div>
              )}
            </div>

            {/* Storage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-green-600" />
                  <span className="font-medium">Storage</span>
                </div>
                <span className="text-sm text-gray-600">
                  {usage.storage_used_gb.toFixed(1)} GB
                  {subscription.storage_limit_gb
                    ? ` / ${subscription.storage_limit_gb} GB`
                    : ' / Unlimited'}
                </span>
              </div>
              {subscription.storage_limit_gb ? (
                <Progress
                  value={calculateUsagePercentage(
                    usage.storage_used_gb,
                    subscription.storage_limit_gb
                  )}
                  className="h-2"
                />
              ) : (
                <div className="text-sm text-green-600">Unlimited storage</div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Invoice History */}
      {invoices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Invoice History</CardTitle>
            <CardDescription>Your past invoices</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((invoice) => (
                  <TableRow key={invoice.id}>
                    <TableCell>
                      <code className="text-sm">{invoice.invoice_number}</code>
                    </TableCell>
                    <TableCell>
                      {new Date(invoice.invoice_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>${(invoice.amount_cents / 100).toFixed(2)}</TableCell>
                    <TableCell>
                      <Badge
                        variant={invoice.status === 'paid' ? 'default' : 'secondary'}
                        className={
                          invoice.status === 'paid'
                            ? 'text-green-600 bg-green-50'
                            : 'text-gray-600 bg-gray-50'
                        }
                      >
                        {invoice.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {invoice.status === 'paid' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            billingService
                              .downloadInvoice(invoice.id)
                              .then((blob) => {
                                const url = window.URL.createObjectURL(blob)
                                const a = document.createElement('a')
                                a.href = url
                                a.download = `invoice-${invoice.invoice_number}.pdf`
                                a.click()
                              })
                          }
                        >
                          <FileText className="h-4 w-4 mr-1" />
                          Download
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
