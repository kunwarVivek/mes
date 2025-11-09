/**
 * OEEGauge Component
 *
 * Visualization component for OEE metrics
 */
import './OEEGauge.css'
import type { OEEMetrics } from '../types/machine.types'

interface OEEGaugeProps {
  metrics: OEEMetrics
  compact?: boolean
  isLoading?: boolean
}

export function OEEGauge({ metrics, compact = false, isLoading = false }: OEEGaugeProps) {
  if (isLoading) {
    return <div data-testid="loading-skeleton">Loading...</div>
  }

  const formatPercentage = (value: number) => Math.round(value * 100)

  const getOEEStatus = (score: number) => {
    if (score >= 0.85) return 'Excellent'
    if (score >= 0.70) return 'Good'
    if (score >= 0.60) return 'Acceptable'
    return 'Poor'
  }

  const getOEEClass = (score: number) => {
    if (score >= 0.85) return 'oee-excellent'
    if (score >= 0.70) return 'oee-good'
    if (score >= 0.60) return 'oee-acceptable'
    return 'oee-poor'
  }

  const isLowMetric = (value: number) => value < 0.60

  return (
    <div
      data-testid="oee-gauge"
      className={`oee-gauge ${getOEEClass(metrics.oee_score)} ${compact ? 'compact' : ''}`}
    >
      <div className="oee-score">
        <div className="score-value">{formatPercentage(metrics.oee_score)}%</div>
        <div className="score-status">{getOEEStatus(metrics.oee_score)}</div>
      </div>

      {!compact && (
        <div className="oee-components">
          <div className="oee-component">
            <div className="component-label">Availability</div>
            <div
              className={`component-value ${isLowMetric(metrics.availability) ? 'low-metric' : ''}`}
            >
              {formatPercentage(metrics.availability)}%
            </div>
            <div
              data-testid="availability-bar"
              className={`component-bar ${isLowMetric(metrics.availability) ? 'low-metric' : ''}`}
              style={{ width: `${formatPercentage(metrics.availability)}%` }}
            />
          </div>

          <div className="oee-component">
            <div className="component-label">Performance</div>
            <div
              className={`component-value ${isLowMetric(metrics.performance) ? 'low-metric' : ''}`}
            >
              {formatPercentage(metrics.performance)}%
            </div>
            <div
              data-testid="performance-bar"
              className={`component-bar ${isLowMetric(metrics.performance) ? 'low-metric' : ''}`}
              style={{ width: `${formatPercentage(metrics.performance)}%` }}
            />
          </div>

          <div className="oee-component">
            <div className="component-label">Quality</div>
            <div
              className={`component-value ${isLowMetric(metrics.quality) ? 'low-metric' : ''}`}
            >
              {formatPercentage(metrics.quality)}%
            </div>
            <div
              data-testid="quality-bar"
              className={`component-bar ${isLowMetric(metrics.quality) ? 'low-metric' : ''}`}
              style={{ width: `${formatPercentage(metrics.quality)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
