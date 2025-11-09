import * as React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({
  title,
  value,
  unit,
  trend,
  trendValue,
  icon,
  className
}: MetricCardProps) {
  const trendIcons = {
    up: <TrendingUp className="h-4 w-4 text-green-600" />,
    down: <TrendingDown className="h-4 w-4 text-red-600" />,
    neutral: <Minus className="h-4 w-4 text-gray-600" />,
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value}{' '}
          {unit && (
            <span className="text-sm font-normal text-muted-foreground">{unit}</span>
          )}
        </div>
        {trend && trendValue && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            {trendIcons[trend]}
            <span>{trendValue}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
