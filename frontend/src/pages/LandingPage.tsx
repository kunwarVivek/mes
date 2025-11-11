import { Link } from '@tanstack/react-router'
import { Button } from '../components/ui/button'
import { Factory } from 'lucide-react'
import { HeroSection } from '../features/marketing/components/HeroSection'
import { ValuePropositions } from '../features/marketing/components/ValuePropositions'
import { FeatureHighlights } from '../features/marketing/components/FeatureHighlights'
import { SocialProof } from '../features/marketing/components/SocialProof'
import { PricingTeaser } from '../features/marketing/components/PricingTeaser'
import { Footer } from '../features/marketing/components/Footer'

/**
 * Landing Page Component
 *
 * Public landing page for unauthenticated visitors:
 * - Single Responsibility: Main marketing page composition
 * - Target: SME discrete manufacturers (automotive, electronics, switchgear)
 * - Positioning: Configure 80% through UI, not code
 * - CTAs: Free trial, pricing, demo
 *
 * Marketing Copy Strategy:
 * - Focus on outcomes (time saved, cost reduced)
 * - Quantified benefits (30 sec NCRs, 83% MES coverage, 1/10th SAP cost)
 * - Address pain points (Excel chaos, expensive SAP, rigid custom software)
 * - Persona-specific messaging (Plant Manager, Supervisor, QC, Operator)
 */

export function LandingPage() {
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
            <a href="#features" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Features
            </a>
            <Link to="/pricing" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Pricing
            </Link>
            <a href="#testimonials" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Customers
            </a>
            <a href="#resources" className="text-sm font-semibold leading-6 text-slate-700 hover:text-slate-900">
              Resources
            </a>
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

      {/* Page Sections */}
      <main>
        {/* Hero Section */}
        <HeroSection />

        {/* Value Propositions by Persona */}
        <div id="features">
          <ValuePropositions />
        </div>

        {/* Feature Highlights */}
        <FeatureHighlights />

        {/* Social Proof / Testimonials */}
        <div id="testimonials">
          <SocialProof />
        </div>

        {/* Pricing Teaser */}
        <PricingTeaser />

        {/* Final CTA Section */}
        <section className="bg-blue-600 py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-6 text-center lg:px-8">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to Transform Your Shop Floor?
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-blue-100">
              Join 100+ manufacturers who've replaced Excel chaos and expensive ERPs with Unison.
              Setup in under 2 hours. See results in days, not months.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link to="/register">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                  Start Your Free Trial
                </Button>
              </Link>
              <Link to="#contact">
                <Button size="lg" variant="outline" className="w-full border-white text-white hover:bg-white/10 sm:w-auto">
                  Schedule a Demo
                </Button>
              </Link>
            </div>
            <p className="mt-6 text-sm text-blue-200">
              14-day free trial • No credit card required • Setup in 2 hours
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <div id="resources">
        <Footer />
      </div>
    </div>
  )
}
