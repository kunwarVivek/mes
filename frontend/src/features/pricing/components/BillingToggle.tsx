import { Label } from '@/components/ui/label'

/**
 * Billing Toggle Component
 *
 * Toggle between monthly and annual billing:
 * - Single Responsibility: Billing period selection
 * - Shows annual discount (10% off)
 * - Clear visual toggle with labels
 */

interface BillingToggleProps {
  isAnnual: boolean
  onToggle: (isAnnual: boolean) => void
}

export function BillingToggle({ isAnnual, onToggle }: BillingToggleProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      <Label
        htmlFor="billing-toggle"
        className={`cursor-pointer text-base font-medium transition-colors ${
          !isAnnual ? 'text-slate-900' : 'text-slate-500'
        }`}
      >
        Monthly
      </Label>

      <button
        id="billing-toggle"
        role="switch"
        aria-checked={isAnnual}
        onClick={() => onToggle(!isAnnual)}
        className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
          isAnnual ? 'bg-blue-600' : 'bg-slate-300'
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform ${
            isAnnual ? 'translate-x-8' : 'translate-x-1'
          }`}
        />
      </button>

      <div className="flex items-center gap-2">
        <Label
          htmlFor="billing-toggle"
          className={`cursor-pointer text-base font-medium transition-colors ${
            isAnnual ? 'text-slate-900' : 'text-slate-500'
          }`}
        >
          Annual
        </Label>
        <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">
          Save 10%
        </span>
      </div>
    </div>
  )
}
