import { Link } from '@tanstack/react-router'
import { Button } from '../../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Check, ArrowRight, TrendingDown } from 'lucide-react'

/**
 * Pricing Teaser Component
 *
 * High-level pricing overview with CTA:
 * - Single Responsibility: Drive users to pricing page or trial
 * - Focus: Value-based pricing comparison (vs SAP, custom builds, Excel chaos)
 * - Design: Simple, transparent, emphasizes ROI
 */

const pricingHighlights = [
  '1/10th the cost of SAP or Oracle',
  'No per-module licensing fees',
  'Unlimited custom fields included',
  'Free mobile apps for all users',
  'Free updates and security patches',
  '14-day free trial, no credit card',
]

export function PricingTeaser() {
  return (
    <section className="bg-gradient-to-b from-slate-50 to-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-semibold leading-7 text-blue-600">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Enterprise Features Without Enterprise Prices
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Per-user pricing that scales with your team. No hidden fees, no per-module charges,
            no surprise invoices.
          </p>
        </div>

        {/* Pricing Card */}
        <div className="mx-auto mt-16 max-w-4xl">
          <Card className="border-2 border-blue-600 shadow-xl">
            <CardHeader className="bg-gradient-to-br from-blue-50 to-white pb-8 text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-green-100 px-4 py-1.5 text-sm font-medium text-green-700">
                <TrendingDown className="h-4 w-4" />
                90% lower TCO than traditional ERP
              </div>
              <CardTitle className="text-3xl">Starting at ₹999/user/month</CardTitle>
              <CardDescription className="mt-2 text-base">
                All modules included. Volume discounts available for 25+ users.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-8">
              {/* What's Included */}
              <div className="mb-8">
                <h3 className="mb-4 text-lg font-semibold text-slate-900">
                  Everything included:
                </h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {pricingHighlights.map((feature) => (
                    <div key={feature} className="flex items-start gap-3">
                      <Check className="h-5 w-5 flex-shrink-0 text-green-600" />
                      <span className="text-sm text-slate-700">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Comparison */}
              <div className="mb-8 rounded-lg bg-slate-50 p-6">
                <h4 className="mb-4 text-center font-semibold text-slate-900">
                  Cost Comparison (50 users, 3 years)
                </h4>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="text-center">
                    <p className="text-sm text-slate-600">SAP / Oracle</p>
                    <p className="mt-1 text-2xl font-bold text-slate-400 line-through">
                      ₹1.5Cr+
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-600">Custom Build</p>
                    <p className="mt-1 text-2xl font-bold text-slate-400 line-through">
                      ₹80L+
                    </p>
                  </div>
                  <div className="rounded-lg bg-blue-600 p-4 text-center">
                    <p className="text-sm font-medium text-blue-100">Unison MES</p>
                    <p className="mt-1 text-2xl font-bold text-white">₹18L</p>
                  </div>
                </div>
                <p className="mt-4 text-center text-xs text-slate-500">
                  * Includes implementation, training, and 3-year subscription
                </p>
              </div>

              {/* CTAs */}
              <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                <Link to="/register" className="flex-1 sm:flex-initial">
                  <Button size="lg" className="group w-full sm:w-auto">
                    Start Free Trial
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
                <Link to="/pricing" className="flex-1 sm:flex-initial">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto">
                    View Detailed Pricing
                  </Button>
                </Link>
              </div>

              {/* Trust Signal */}
              <p className="mt-6 text-center text-sm text-slate-500">
                No credit card required • Cancel anytime • 30-day money-back guarantee
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Bottom Note */}
        <div className="mx-auto mt-12 max-w-2xl text-center">
          <p className="text-sm text-slate-600">
            <strong>Need custom pricing?</strong> Contact us for enterprise plans with dedicated support,
            on-premise deployment, and custom SLAs.
          </p>
        </div>
      </div>
    </section>
  )
}
