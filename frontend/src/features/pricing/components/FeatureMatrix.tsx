import { Check, X } from 'lucide-react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/**
 * Feature Matrix Component
 *
 * Detailed feature comparison table:
 * - Single Responsibility: Compare features across tiers
 * - Mobile-responsive
 * - Clear visual indicators for included features
 * - Organized by feature categories
 */

interface FeatureMatrixProps {
  className?: string
}

export function FeatureMatrix({ className }: FeatureMatrixProps) {
  const featureCategories = [
    {
      category: 'Core Features',
      features: [
        { name: 'Material Management', starter: true, professional: true, enterprise: true },
        { name: 'Work Orders', starter: true, professional: true, enterprise: true },
        { name: 'Quality Management (NCRs)', starter: true, professional: true, enterprise: true },
        { name: 'Production Logs', starter: true, professional: true, enterprise: true },
        { name: 'Bill of Materials (BOM)', starter: true, professional: true, enterprise: true },
      ],
    },
    {
      category: 'Advanced Features',
      features: [
        { name: 'Custom Fields (unlimited)', starter: false, professional: true, enterprise: true },
        { name: 'Workflow Automation', starter: false, professional: true, enterprise: true },
        { name: 'Equipment & Maintenance', starter: false, professional: true, enterprise: true },
        { name: 'Visual Gantt Scheduling', starter: false, professional: true, enterprise: true },
        { name: 'Advanced Reporting & Analytics', starter: false, professional: true, enterprise: true },
        { name: 'Multi-plant Operations', starter: false, professional: true, enterprise: true },
      ],
    },
    {
      category: 'Enterprise Features',
      features: [
        { name: 'White-labeling & Branding', starter: false, professional: false, enterprise: true },
        { name: 'SSO (SAML/OAuth)', starter: false, professional: false, enterprise: true },
        { name: 'Dedicated Instance', starter: false, professional: false, enterprise: true },
        { name: 'SAP Integration', starter: false, professional: false, enterprise: true },
        { name: 'API Access (unlimited)', starter: false, professional: true, enterprise: true },
        { name: 'Custom Integrations', starter: false, professional: false, enterprise: true },
      ],
    },
    {
      category: 'Support & SLA',
      features: [
        { name: 'Email Support', starter: true, professional: true, enterprise: true },
        { name: 'Priority Support (4-hour response)', starter: false, professional: true, enterprise: true },
        { name: 'Dedicated Success Manager', starter: false, professional: false, enterprise: true },
        { name: 'SLA Guarantee (99.9% uptime)', starter: false, professional: false, enterprise: true },
        { name: 'Onboarding & Training', starter: false, professional: true, enterprise: true },
        { name: 'Custom Development', starter: false, professional: false, enterprise: true },
      ],
    },
  ]

  return (
    <div className={className}>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-1/2">Features</TableHead>
              <TableHead className="text-center">Starter</TableHead>
              <TableHead className="text-center">Professional</TableHead>
              <TableHead className="text-center">Enterprise</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {featureCategories.map((category, categoryIndex) => (
              <>
                <TableRow key={`category-${categoryIndex}`} className="bg-slate-50">
                  <TableCell colSpan={4} className="font-semibold text-slate-900">
                    {category.category}
                  </TableCell>
                </TableRow>
                {category.features.map((feature, featureIndex) => (
                  <TableRow key={`${categoryIndex}-${featureIndex}`}>
                    <TableCell className="font-medium">{feature.name}</TableCell>
                    <TableCell className="text-center">
                      {feature.starter ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {feature.professional ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {feature.enterprise ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile-friendly cards view (shown on small screens) */}
      <div className="lg:hidden mt-8 space-y-6">
        {featureCategories.map((category, categoryIndex) => (
          <div key={`mobile-${categoryIndex}`}>
            <h3 className="mb-4 text-lg font-semibold text-slate-900">{category.category}</h3>
            <div className="space-y-4">
              {category.features.map((feature, featureIndex) => (
                <div key={`mobile-${categoryIndex}-${featureIndex}`} className="rounded-lg border p-4">
                  <div className="mb-3 font-medium text-slate-900">{feature.name}</div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="mb-1 text-xs text-slate-600">Starter</div>
                      {feature.starter ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </div>
                    <div className="text-center">
                      <div className="mb-1 text-xs text-slate-600">Professional</div>
                      {feature.professional ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </div>
                    <div className="text-center">
                      <div className="mb-1 text-xs text-slate-600">Enterprise</div>
                      {feature.enterprise ? (
                        <Check className="inline h-5 w-5 text-green-600" />
                      ) : (
                        <X className="inline h-5 w-5 text-slate-300" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
