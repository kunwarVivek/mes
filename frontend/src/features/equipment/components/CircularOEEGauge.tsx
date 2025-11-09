/**
 * CircularOEEGauge Component
 *
 * Circular gauge visualization for OEE metrics with color-coded display
 */

interface CircularOEEGaugeProps {
  value: number
  label: string
  size?: 'small' | 'medium' | 'large'
}

export function CircularOEEGauge({ value, label, size = 'medium' }: CircularOEEGaugeProps) {
  const sizeClasses = {
    small: 'w-24 h-24',
    medium: 'w-32 h-32',
    large: 'w-40 h-40'
  }

  const getColor = (value: number) => {
    if (value >= 85) return 'text-green-600'
    if (value >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const radius = size === 'small' ? 40 : size === 'medium' ? 52 : 64
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className={`relative ${sizeClasses[size]}`}>
        <svg className="transform -rotate-90" viewBox="0 0 140 140">
          {/* Background circle */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-gray-200"
          />
          {/* Progress circle */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={getColor(value)}
          />
        </svg>

        {/* Value text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`font-bold ${getColor(value)}`} data-testid="gauge-value">
            {value.toFixed(1)}%
          </span>
        </div>
      </div>

      <span className="mt-2 text-sm font-medium text-gray-700">{label}</span>
    </div>
  )
}
