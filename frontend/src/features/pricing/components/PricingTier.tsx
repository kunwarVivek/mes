import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, X } from 'lucide-react'
import { Link } from '@tanstack/react-router'

/**
 * Pricing Tier Component
 *
 * Individual pricing tier card:
 * - Single Responsibility: Display single pricing tier
 * - Highlights popular tier
 * - Shows features with check/cross marks
 * - Clear CTA button
 */

export interface PricingFeature {
  name: string
  included: boolean
  highlight?: boolean
}

export interface PricingTierProps {
  name: string
  description: string
  price: number | 'custom'
  priceINR: number | 'custom'
  period: 'month' | 'year'
  isPopular?: boolean
  features: PricingFeature[]
  cta: {
    text: string
    href: string
  }
  limits: {
    users: string
    plants: string
    storage: string
  }
}

export function PricingTier({
  name,
  description,
  price,
  priceINR,
  period,
  isPopular,
  features,
  cta,
  limits
}: PricingTierProps) {
  const isCustom = price === 'custom'

  return (
    <Card className={`relative flex flex-col ${isPopular ? 'border-blue-600 shadow-lg ring-2 ring-blue-600' : ''}`}>
      {isPopular && (
        <div className="absolute -top-4 left-0 right-0 flex justify-center">
          <Badge className="bg-blue-600 px-4 py-1 text-sm font-semibold text-white">
            Most Popular
          </Badge>
        </div>
      )}

      <CardHeader className={isPopular ? 'pt-8' : ''}>
        <CardTitle className="text-2xl font-bold">{name}</CardTitle>
        <CardDescription className="text-base">{description}</CardDescription>
      </CardHeader>

      <CardContent className="flex-1">
        {/* Pricing */}
        <div className="mb-6">
          {isCustom ? (
            <div>
              <div className="text-4xl font-bold text-slate-900">Custom</div>
              <div className="mt-1 text-sm text-slate-600">Contact us for pricing</div>
            </div>
          ) : (
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-slate-900">
                  ${typeof price === 'number' ? price.toLocaleString() : price}
                </span>
                <span className="text-slate-600">/{period}</span>
              </div>
              <div className="mt-1 text-sm text-slate-600">
                {typeof priceINR === 'number' && `₹${priceINR.toLocaleString()}/month`}
              </div>
            </div>
          )}
        </div>

        {/* Limits */}
        <div className="mb-6 space-y-2 rounded-lg bg-slate-50 p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Users</span>
            <span className="font-semibold text-slate-900">{limits.users}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Plants</span>
            <span className="font-semibold text-slate-900">{limits.plants}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-600">Storage</span>
            <span className="font-semibold text-slate-900">{limits.storage}</span>
          </div>
        </div>

        {/* Features */}
        <ul className="space-y-3">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-3">
              {feature.included ? (
                <Check className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
              ) : (
                <X className="mt-0.5 h-5 w-5 shrink-0 text-slate-300" />
              )}
              <span className={`text-sm ${feature.included ? 'text-slate-700' : 'text-slate-400'}`}>
                {feature.name}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Link to={cta.href} className="w-full">
          <Button
            className="w-full"
            size="lg"
            variant={isPopular ? 'default' : 'outline'}
          >
            {cta.text}
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
