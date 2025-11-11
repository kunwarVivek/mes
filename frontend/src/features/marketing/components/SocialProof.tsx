import { Star, Quote } from 'lucide-react'
import { Card, CardContent } from '../../../components/ui/card'
import { Avatar, AvatarFallback } from '../../../components/ui/avatar'

/**
 * Social Proof Component
 *
 * Customer testimonials and trust indicators:
 * - Single Responsibility: Build credibility through customer stories
 * - Focus: Real outcomes from target industries (automotive, electronics, switchgear)
 * - Design: Professional B2B aesthetic with quantified results
 */

interface Testimonial {
  quote: string
  author: string
  role: string
  company: string
  industry: string
  metric: string
  initials: string
}

const testimonials: Testimonial[] = [
  {
    quote: "We went from 15-minute NCR paperwork to 30 seconds on the shop floor. Quality issues get addressed immediately instead of sitting in a pile on someone's desk.",
    author: 'Amit Sharma',
    role: 'Quality Manager',
    company: 'Precision Auto Components',
    industry: 'Automotive',
    metric: '30x faster NCR creation',
    initials: 'AS',
  },
  {
    quote: "Our supervisors used to run back to the office 20 times a day to check schedules. Now everything is on their phones. Work order updates happen in real-time.",
    author: 'Priya Desai',
    role: 'Production Head',
    company: 'Excel Electronics Pvt Ltd',
    industry: 'Electronics',
    metric: '3 hours saved daily per supervisor',
    initials: 'PD',
  },
  {
    quote: "We replaced a custom system that took 18 months and ₹50L to build. Unison was configured in 3 weeks and costs 1/10th to maintain. Best ROI decision we made.",
    author: 'Rajesh Kumar',
    role: 'Plant Manager',
    company: 'Switchgear Solutions India',
    industry: 'Switchgear',
    metric: '6x faster deployment, 90% cost reduction',
    initials: 'RK',
  },
]

const trustedByLogos = [
  'Automotive Co.',
  'Electronics Ltd.',
  'Precision Mfg.',
  'Industrial Systems',
  'Component Works',
  'Manufacturing Inc.',
]

export function SocialProof() {
  return (
    <section className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-semibold leading-7 text-blue-600">
            Customer Success Stories
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Trusted by Manufacturers Like You
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Join 100+ discrete manufacturers who've transformed their operations with Unison.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="mx-auto mt-16 grid max-w-7xl grid-cols-1 gap-8 sm:mt-20 lg:grid-cols-3">
          {testimonials.map((testimonial) => (
            <Card key={testimonial.author} className="border-slate-200 bg-slate-50">
              <CardContent className="p-8">
                {/* Quote Icon */}
                <Quote className="h-8 w-8 text-blue-600 opacity-50" />

                {/* Star Rating */}
                <div className="mt-4 flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>

                {/* Quote */}
                <blockquote className="mt-6 text-sm leading-6 text-slate-700">
                  "{testimonial.quote}"
                </blockquote>

                {/* Metric Highlight */}
                <div className="mt-6 rounded-lg bg-white p-3 shadow-sm">
                  <p className="text-sm font-semibold text-blue-600">
                    {testimonial.metric}
                  </p>
                </div>

                {/* Author */}
                <div className="mt-6 flex items-center gap-4">
                  <Avatar className="h-12 w-12 border-2 border-white shadow-sm">
                    <AvatarFallback className="bg-blue-600 text-white">
                      {testimonial.initials}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-semibold text-slate-900">{testimonial.author}</p>
                    <p className="text-sm text-slate-600">{testimonial.role}</p>
                    <p className="text-xs text-slate-500">
                      {testimonial.company} • {testimonial.industry}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Trusted By Logos */}
        <div className="mx-auto mt-20 max-w-7xl">
          <p className="text-center text-sm font-semibold text-slate-500">
            TRUSTED BY LEADING MANUFACTURERS
          </p>
          <div className="mt-8 grid grid-cols-2 gap-8 md:grid-cols-3 lg:grid-cols-6">
            {trustedByLogos.map((logo) => (
              <div
                key={logo}
                className="flex items-center justify-center rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
              >
                <span className="text-sm font-medium text-slate-400">{logo}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats Bar */}
        <div className="mx-auto mt-20 max-w-4xl">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            <div className="text-center">
              <p className="text-4xl font-bold text-slate-900">100+</p>
              <p className="mt-2 text-sm text-slate-600">Active Manufacturers</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-slate-900">50,000+</p>
              <p className="mt-2 text-sm text-slate-600">Work Orders Monthly</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-slate-900">99.9%</p>
              <p className="mt-2 text-sm text-slate-600">Uptime SLA</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
