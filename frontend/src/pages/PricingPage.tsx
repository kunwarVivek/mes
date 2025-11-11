import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Factory } from 'lucide-react'
import { BillingToggle } from '@/features/pricing/components/BillingToggle'
import { PricingTier, PricingFeature } from '@/features/pricing/components/PricingTier'
import { FeatureMatrix } from '@/features/pricing/components/FeatureMatrix'
import { PricingFAQ } from '@/features/pricing/components/PricingFAQ'

/**
 * Pricing Page Component
 *
 * B2B SaaS pricing page with 3-tier model:
 * - Single Responsibility: Pricing presentation and comparison
 * - Target: SME discrete manufacturers
 * - Tiers: Starter, Professional, Enterprise
 * - Monthly/Annual billing toggle (10% discount on annual)
 * - Feature comparison matrix
 * - FAQ section
 *
 * Pricing Strategy:
 * - Starter: Entry-level for single plants ($499/month)
 * - Professional: Multi-plant operations ($1,499/month) - Most Popular
 * - Enterprise: Large-scale deployments (Custom pricing)
 */

export function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false)

  // Calculate prices based on billing period
  const calculatePrice = (monthlyPrice: number) => {
    if (isAnnual) {
      // 10% discount on annual
      return Math.round(monthlyPrice * 12 * 0.9)
    }
    return monthlyPrice
  }

  const calculatePriceINR = (monthlyPriceINR: number) => {
    if (isAnnual) {
      // 10% discount on annual
      return Math.round(monthlyPriceINR * 12 * 0.9)
    }
    return monthlyPriceINR
  }

  // Starter tier features
  const starterFeatures: PricingFeature[] = [
    { name: 'Material Management', included: true },
    { name: 'Work Orders', included: true },
    { name: 'Quality Management (NCRs)', included: true },
    { name: 'Production Logs', included: true },
    { name: 'Bill of Materials (BOM)', included: true },
    { name: 'Email Support', included: true },
    { name: 'Custom Fields', included: false },
    { name: 'Workflow Automation', included: false },
    { name: 'White-labeling', included: false },
  ]

  // Professional tier features
  const professionalFeatures: PricingFeature[] = [
    { name: 'Everything in Starter', included: true, highlight: true },
    { name: 'Custom Fields (unlimited)', included: true },
    { name: 'Workflow Automation', included: true },
    { name: 'Equipment & Maintenance', included: true },
    { name: 'Visual Gantt Scheduling', included: true },
    { name: 'Advanced Reporting', included: true },
    { name: 'Multi-plant Operations', included: true },
    { name: 'Priority Support (4-hour)', included: true },
    { name: 'Onboarding & Training', included: true },
  ]

  // Enterprise tier features
  const enterpriseFeatures: PricingFeature[] = [
    { name: 'Everything in Professional', included: true, highlight: true },
    { name: 'White-labeling & Branding', included: true },
    { name: 'SSO (SAML/OAuth)', included: true },
    { name: 'Dedicated Instance', included: true },
    { name: 'SAP Integration', included: true },
    { name: 'Dedicated Success Manager', included: true },
    { name: 'SLA Guarantee (99.9%)', included: true },
    { name: 'Custom Development', included: true },
    { name: '24/7 Emergency Support', included: true },
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
        <nav className="mx-auto flex max-w-7xl items-center justify-between p-6 lg:px-8" aria-label="Global">
          {/* Logo */}
          <div className="flex lg:flex-1">
            <Link to="/" className="-m-1.5 flex items-center gap-2 p-1.5">
              <Factory className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-slate-900">Unison MES</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex lg:gap-x-8">
            <Link to="/" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Home
            </Link>
            <a href="/#features" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Features
            </a>
            <Link to="/pricing" className="text-sm font-semibold leading-6 text-blue-600">
              Pricing
            </Link>
          </div>

          {/* CTA Buttons */}
          <div className="hidden lg:flex lg:flex-1 lg:justify-end lg:gap-x-4">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Log in
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm">
                Start Free Trial
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex lg:hidden">
            <Link to="/register">
              <Button size="sm">
                Get Started
              </Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Page Content */}
      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-b from-slate-50 to-white px-6 py-16 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              Simple, Transparent Pricing
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Choose the plan that fits your manufacturing needs. Start with a 14-day free trial,
              no credit card required. Scale as you grow.
            </p>

            {/* Billing Toggle */}
            <div className="mt-10">
              <BillingToggle isAnnual={isAnnual} onToggle={setIsAnnual} />
            </div>
          </div>
        </section>

        {/* Pricing Tiers */}
        <section className="px-6 py-16 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-8 lg:grid-cols-3">
              {/* Starter Tier */}
              <PricingTier
                name="Starter"
                description="Perfect for single-plant operations getting started with MES"
                price={isAnnual ? calculatePrice(499) : 499}
                priceINR={isAnnual ? calculatePriceINR(41583) : 41583}
                period={isAnnual ? 'year' : 'month'}
                limits={{
                  users: '10 users',
                  plants: '1 plant',
                  storage: '10GB',
                }}
                features={starterFeatures}
                cta={{
                  text: 'Start Free Trial',
                  href: '/register',
                }}
              />

              {/* Professional Tier */}
              <PricingTier
                name="Professional"
                description="For growing manufacturers with multiple plants and advanced needs"
                price={isAnnual ? calculatePrice(1499) : 1499}
                priceINR={isAnnual ? calculatePriceINR(124917) : 124917}
                period={isAnnual ? 'year' : 'month'}
                isPopular
                limits={{
                  users: '50 users',
                  plants: '5 plants',
                  storage: '50GB',
                }}
                features={professionalFeatures}
                cta={{
                  text: 'Start Free Trial',
                  href: '/register',
                }}
              />

              {/* Enterprise Tier */}
              <PricingTier
                name="Enterprise"
                description="Custom solutions for large-scale manufacturing operations"
                price="custom"
                priceINR="custom"
                period="month"
                limits={{
                  users: 'Unlimited',
                  plants: 'Unlimited',
                  storage: '500GB+',
                }}
                features={enterpriseFeatures}
                cta={{
                  text: 'Contact Sales',
                  href: '/register',
                }}
              />
            </div>
          </div>
        </section>

        {/* Volume Discounts & Add-ons */}
        <section className="bg-slate-50 px-6 py-16 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-12 lg:grid-cols-2">
              {/* Volume Discounts */}
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Volume Discounts</h2>
                <p className="mt-4 text-slate-600">
                  Save more as you scale. Volume discounts apply automatically based on user count.
                </p>
                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                    <span className="font-medium text-slate-900">11-25 users</span>
                    <span className="text-green-600 font-semibold">10% off</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                    <span className="font-medium text-slate-900">26-50 users</span>
                    <span className="text-green-600 font-semibold">15% off</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                    <span className="font-medium text-slate-900">51-100 users</span>
                    <span className="text-green-600 font-semibold">20% off</span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                    <span className="font-medium text-slate-900">100+ users</span>
                    <span className="text-blue-600 font-semibold">Custom pricing</span>
                  </div>
                </div>
              </div>

              {/* Add-ons */}
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Add-ons</h2>
                <p className="mt-4 text-slate-600">
                  Extend your plan with additional capacity as needed.
                </p>
                <div className="mt-6 space-y-4">
                  <div className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-900">Additional User</span>
                      <span className="text-slate-900 font-semibold">$30/month</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">Add more users to your account</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-900">Additional Plant</span>
                      <span className="text-slate-900 font-semibold">$200/month</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">Support for additional manufacturing locations</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-900">Extra Storage (10GB)</span>
                      <span className="text-slate-900 font-semibold">$50/month</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">Additional storage for documents and files</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Comparison Matrix */}
        <section className="px-6 py-16 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-slate-900">Compare Plans</h2>
              <p className="mt-4 text-lg text-slate-600">
                Detailed feature breakdown across all pricing tiers
              </p>
            </div>
            <div className="mt-12">
              <FeatureMatrix />
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="bg-slate-50 px-6 py-16 lg:px-8">
          <div className="mx-auto max-w-3xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-slate-900">Frequently Asked Questions</h2>
              <p className="mt-4 text-lg text-slate-600">
                Everything you need to know about our pricing
              </p>
            </div>
            <div className="mt-12">
              <PricingFAQ />
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-blue-600 px-6 py-16 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-7xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to Get Started?
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-blue-100">
              Start your 14-day free trial today. No credit card required.
              Setup in under 2 hours and see results in days.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link to="/register">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                  Start Your Free Trial
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="w-full border-white text-white hover:bg-white/10 sm:w-auto">
                  Contact Sales
                </Button>
              </Link>
            </div>
            <p className="mt-6 text-sm text-blue-200">
              14-day free trial • No credit card required • Cancel anytime
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-6 py-12 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <Factory className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-bold text-slate-900">Unison MES</span>
            </div>
            <p className="text-sm text-slate-600">
              © 2025 Unison Manufacturing ERP. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
