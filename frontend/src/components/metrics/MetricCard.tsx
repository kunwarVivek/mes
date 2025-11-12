import { Card } from '@/components/ui/card'

export interface MetricCardProps {
  value: number | string
  label: string
  trend?: 'up' | 'down' | 'neutral'
  target?: number
  unit?: string
  className?: string
}

/**
 * Validates numeric values for NaN and Infinity
 */
function isValidNumber(value: number): boolean {
  return !isNaN(value) && isFinite(value)
}

/**
 * Gets the trend icon for the given trend direction
 */
function getTrendIcon(trend: 'up' | 'down' | 'neutral'): string {
  const icons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  }
  return icons[trend]
}

/**
 * Gets the color class for the given trend direction
 */
function getTrendColor(trend: 'up' | 'down' | 'neutral'): string {
  const colors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  }
  return colors[trend]
}

/**
 * Gets the aria-label for the given trend direction
 */
function getTrendAriaLabel(trend: 'up' | 'down' | 'neutral'): string {
  const labels = {
    up: 'Trend: increasing',
    down: 'Trend: decreasing',
    neutral: 'Trend: stable',
  }
  return labels[trend]
}

export function MetricCard({
  value,
  label,
  trend,
  target,
  unit = '',
  className = '',
}: MetricCardProps) {
  // Validate and format numeric values
  const formattedValue =
    typeof value === 'number'
      ? isValidNumber(value)
        ? value.toFixed(1)
        : 'Invalid value'
      : value

  return (
    <Card className={className}>
      <div className="p-4">
        <p className="text-sm text-gray-600">{label}</p>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-3xl font-bold">
            {formattedValue}
            {unit}
          </span>
          {trend && (
            <span
              className={`text-xl ${getTrendColor(trend)}`}
              aria-label={getTrendAriaLabel(trend)}
              role="img"
            >
              {getTrendIcon(trend)}
            </span>
          )}
        </div>
        {target !== undefined && (
          <p className="text-xs text-gray-500 mt-1">
            Target: {target}
            {unit}
          </p>
        )}
      </div>
    </Card>
  )
}
