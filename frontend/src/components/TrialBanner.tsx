import { useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { billingService, Subscription } from '@/services/billing.service'
import { Button } from '@/design-system/atoms/Button'
import { AlertCircle, Clock, X } from 'lucide-react'

/**
 * Trial Countdown Banner
 *
 * Persistent banner shown to trial users:
 * - Shows days remaining in trial
 * - Color changes based on urgency (7+ days: blue, 3-6 days: orange, <3 days: red)
 * - CTA button to upgrade
 * - Dismissible (but persists across sessions until trial ends)
 *
 * Only shown when:
 * - Subscription status is 'trial'
 * - Trial end date is in the future
 */

export function TrialBanner() {
  const navigate = useNavigate()
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSubscription()

    // Check if banner was previously dismissed (session storage)
    const wasDismissed = sessionStorage.getItem('trialBannerDismissed')
    if (wasDismissed === 'true') {
      setDismissed(true)
    }
  }, [])

  const loadSubscription = async () => {
    try {
      const sub = await billingService.getCurrentSubscription()
      setSubscription(sub)
    } catch (err) {
      // Silently fail - banner just won't show
      console.error('Failed to load subscription for trial banner:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    sessionStorage.setItem('trialBannerDismissed', 'true')
  }

  const handleUpgrade = () => {
    navigate({ to: '/pricing' })
  }

  // Don't show banner if loading, dismissed, not trial, or trial expired
  if (
    loading ||
    dismissed ||
    !subscription ||
    subscription.status !== 'trial' ||
    !subscription.trial_ends_at
  ) {
    return null
  }

  const trialEndsAt = new Date(subscription.trial_ends_at)
  const now = new Date()
  const daysRemaining = Math.ceil(
    (trialEndsAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  )

  // Trial already expired
  if (daysRemaining <= 0) {
    return null
  }

  // Determine urgency color
  let bgColor = 'bg-blue-600' // 7+ days
  let icon = <Clock className="h-5 w-5" />

  if (daysRemaining <= 2) {
    bgColor = 'bg-red-600' // Critical
    icon = <AlertCircle className="h-5 w-5" />
  } else if (daysRemaining <= 6) {
    bgColor = 'bg-orange-600' // Warning
    icon = <AlertCircle className="h-5 w-5" />
  }

  return (
    <div className={`${bgColor} text-white py-3 px-4 shadow-lg`}>
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          {icon}
          <div>
            <p className="font-semibold">
              {daysRemaining === 1
                ? 'Your trial ends tomorrow!'
                : `Your trial ends in ${daysRemaining} days`}
            </p>
            <p className="text-sm opacity-90">
              Trial ends on {trialEndsAt.toLocaleDateString()} · Upgrade to keep your data
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={handleUpgrade}
            variant="outline"
            size="sm"
            className="bg-white text-gray-900 hover:bg-gray-100"
          >
            Upgrade Now
          </Button>
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            aria-label="Dismiss banner"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
