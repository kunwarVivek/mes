import {
  BarChart3,
  Smartphone,
  ClipboardCheck,
  Scan
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'

/**
 * Value Propositions Component
 *
 * Persona-based benefits section:
 * - Single Responsibility: Display 4 key personas with outcome-driven messaging
 * - Target: Plant Manager, Supervisor, Quality Inspector, Operator
 * - Focus: Specific time savings and productivity gains
 */

interface Persona {
  icon: React.ElementType
  title: string
  role: string
  problem: string
  solution: string
  outcome: string
  iconColor: string
  iconBg: string
}

const personas: Persona[] = [
  {
    icon: BarChart3,
    title: 'Real-Time Shop Floor Visibility',
    role: 'For Plant Managers',
    problem: 'Spending hours chasing data across Excel sheets and whiteboard notes',
    solution: 'Live dashboards with production, quality, and inventory metrics',
    outcome: '3+ hours saved daily on manual reporting',
    iconColor: 'text-blue-600',
    iconBg: 'bg-blue-100',
  },
  {
    icon: Smartphone,
    title: 'Mobile Work Order Management',
    role: 'For Supervisors',
    problem: 'Running back to the office to update work orders and check schedules',
    solution: 'Complete work order lifecycle from your phone—no desktop required',
    outcome: '40% faster work order updates',
    iconColor: 'text-green-600',
    iconBg: 'bg-green-100',
  },
  {
    icon: ClipboardCheck,
    title: 'Lightning-Fast NCR Creation',
    role: 'For Quality Inspectors',
    problem: 'NCR paperwork taking 15+ minutes, delaying corrective actions',
    solution: 'Mobile NCR creation with photo capture and instant notifications',
    outcome: 'NCRs logged in 30 seconds, not 15 minutes',
    iconColor: 'text-purple-600',
    iconBg: 'bg-purple-100',
  },
  {
    icon: Scan,
    title: 'Simple Barcode Operations',
    role: 'For Operators',
    problem: 'Manual data entry errors causing rework and production delays',
    solution: 'Barcode scanning for material tracking, job logging, and inventory',
    outcome: '95% reduction in data entry errors',
    iconColor: 'text-orange-600',
    iconBg: 'bg-orange-100',
  },
]

export function ValuePropositions() {
  return (
    <section className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-semibold leading-7 text-blue-600">
            Built for Every Role
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            From Shop Floor to Top Floor
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Purpose-built workflows for plant managers, supervisors, quality teams, and operators.
            Everyone gets what they need, when they need it.
          </p>
        </div>

        {/* Persona Cards */}
        <div className="mx-auto mt-16 grid max-w-7xl grid-cols-1 gap-8 sm:mt-20 md:grid-cols-2 lg:grid-cols-4">
          {personas.map((persona) => {
            const Icon = persona.icon
            return (
              <Card key={persona.title} className="border-slate-200 transition-shadow hover:shadow-lg">
                <CardHeader>
                  <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg ${persona.iconBg}`}>
                    <Icon className={`h-6 w-6 ${persona.iconColor}`} />
                  </div>
                  <CardTitle className="text-lg">{persona.title}</CardTitle>
                  <CardDescription className="font-medium text-slate-900">
                    {persona.role}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-slate-600">
                      <span className="font-medium text-slate-700">Problem:</span> {persona.problem}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">
                      <span className="font-medium text-slate-700">Solution:</span> {persona.solution}
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-sm font-semibold text-slate-900">
                      {persona.outcome}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </section>
  )
}
