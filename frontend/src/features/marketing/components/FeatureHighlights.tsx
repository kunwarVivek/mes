import {
  Settings,
  Shield,
  Zap,
  Database,
  GitBranch,
  Boxes
} from 'lucide-react'

/**
 * Feature Highlights Component
 *
 * Key technical features and differentiators:
 * - Single Responsibility: Display 6 core platform capabilities
 * - Focus: Technical advantages with quantified benefits
 * - Positioning: Configuration over customization
 */

interface Feature {
  icon: React.ElementType
  title: string
  description: string
  metric: string
  iconColor: string
  iconBg: string
}

const features: Feature[] = [
  {
    icon: Settings,
    title: 'UI-First Configuration',
    description: 'Configure 80% of your processes through intuitive UI—no code required. Custom fields, workflows, and reports in minutes.',
    metric: '80% no-code configuration',
    iconColor: 'text-blue-600',
    iconBg: 'bg-blue-50',
  },
  {
    icon: Shield,
    title: 'Multi-Tenant Security',
    description: 'Enterprise-grade isolation between tenants. Your data stays yours with row-level security and encrypted storage.',
    metric: 'ISO 27001 compliant',
    iconColor: 'text-green-600',
    iconBg: 'bg-green-50',
  },
  {
    icon: Zap,
    title: 'High-Performance Queues',
    description: 'Redis-backed job processing at 300x faster than traditional systems. Real-time updates without refresh.',
    metric: '300x faster job processing',
    iconColor: 'text-yellow-600',
    iconBg: 'bg-yellow-50',
  },
  {
    icon: Database,
    title: 'Smart Data Compression',
    description: 'PostgreSQL with TOAST compression reduces storage costs by 75%. Handle millions of records without bloat.',
    metric: '75% storage reduction',
    iconColor: 'text-purple-600',
    iconBg: 'bg-purple-50',
  },
  {
    icon: GitBranch,
    title: 'MES Coverage Out-of-Box',
    description: 'ISA-95 compliant with 83%+ MES coverage. Production tracking, quality, maintenance, and inventory ready day one.',
    metric: '83% MES coverage',
    iconColor: 'text-indigo-600',
    iconBg: 'bg-indigo-50',
  },
  {
    icon: Boxes,
    title: 'Flexible Data Model',
    description: 'Multi-level BOMs, routing variants, and custom attributes without schema changes. Adapt as your business evolves.',
    metric: 'Unlimited custom fields',
    iconColor: 'text-pink-600',
    iconBg: 'bg-pink-50',
  },
]

export function FeatureHighlights() {
  return (
    <section className="bg-slate-50 py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-semibold leading-7 text-blue-600">
            Powerful Platform
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Enterprise Features, SME Pricing
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Built on modern architecture that scales from 10 to 10,000 users.
            Get enterprise-grade capabilities without enterprise-grade complexity.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="mx-auto mt-16 max-w-7xl sm:mt-20">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <div
                  key={feature.title}
                  className="group relative rounded-2xl border border-slate-200 bg-white p-8 shadow-sm transition-all hover:shadow-md"
                >
                  {/* Icon */}
                  <div className={`mb-6 inline-flex h-14 w-14 items-center justify-center rounded-xl ${feature.iconBg}`}>
                    <Icon className={`h-7 w-7 ${feature.iconColor}`} />
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-semibold text-slate-900">
                    {feature.title}
                  </h3>

                  {/* Description */}
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {feature.description}
                  </p>

                  {/* Metric Badge */}
                  <div className="mt-6">
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                      {feature.metric}
                    </span>
                  </div>

                  {/* Hover Effect */}
                  <div className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-inset ring-slate-900/5 group-hover:ring-slate-900/10" />
                </div>
              )
            })}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <p className="text-sm font-medium text-slate-900">
            Replace Excel, SAP, or your custom-built system
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Modern architecture. Lower TCO. Faster deployment.
          </p>
        </div>
      </div>
    </section>
  )
}
