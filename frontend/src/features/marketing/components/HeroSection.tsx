import { Link } from '@tanstack/react-router'
import { Button } from '../../../components/ui/button'
import { ArrowRight, CheckCircle2 } from 'lucide-react'

/**
 * Hero Section Component
 *
 * Primary landing page hero with compelling value proposition:
 * - Single Responsibility: Hero section with headline and CTAs
 * - Focus: Outcome-driven messaging for SME manufacturers
 * - CTAs: Free trial (primary), Pricing (secondary)
 */

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white py-20 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          {/* Badge */}
          <div className="mb-8 inline-flex items-center rounded-full border border-slate-200 bg-white px-4 py-1.5 text-sm font-medium text-slate-700 shadow-sm">
            <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
            Trusted by 100+ manufacturers across automotive, electronics & switchgear
          </div>

          {/* Headline - Outcome focused */}
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
            Configure Your Shop Floor in
            <span className="block text-blue-600">Hours, Not Months</span>
          </h1>

          {/* Value Proposition */}
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Manufacturing ERP that adapts to your process—not the other way around.
            <strong> Configure 80% through UI</strong>, replace Excel chaos, and get
            your team mobile-ready in days.
          </p>

          {/* Key Benefits List */}
          <div className="mt-8 flex flex-col items-center gap-3 text-left sm:flex-row sm:justify-center sm:gap-8">
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span>NCRs in 30 seconds (not 15 minutes)</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span>83% MES coverage out-of-box</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <span>1/10th the cost of SAP</span>
            </div>
          </div>

          {/* CTAs */}
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link to="/register">
              <Button size="lg" className="group w-full sm:w-auto">
                Start Free Trial
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                View Pricing
              </Button>
            </Link>
          </div>

          {/* Trust Signal */}
          <p className="mt-6 text-sm text-slate-500">
            No credit card required • Setup in under 2 hours • 14-day free trial
          </p>
        </div>

        {/* Hero Image/Visual Placeholder */}
        <div className="mt-16 flow-root sm:mt-24">
          <div className="relative -m-2 rounded-xl bg-slate-900/5 p-2 ring-1 ring-inset ring-slate-900/10 lg:-m-4 lg:rounded-2xl lg:p-4">
            <div className="aspect-[16/9] rounded-md bg-gradient-to-br from-blue-50 to-slate-100 shadow-2xl ring-1 ring-slate-900/10">
              {/* Placeholder for dashboard screenshot */}
              <div className="flex h-full items-center justify-center text-slate-400">
                <span className="text-sm">Dashboard Screenshot Placeholder</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
