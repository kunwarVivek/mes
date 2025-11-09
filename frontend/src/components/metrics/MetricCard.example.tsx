/**
 * MetricCard Usage Examples
 *
 * Demonstrates various configurations of the MetricCard component
 */
import { MetricCard } from './MetricCard'

export function MetricCardExamples() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-6">
      {/* OEE - Good Performance */}
      <MetricCard value={92.5} label="OEE" trend="up" target={90} unit="%" />

      {/* FPY - Warning State */}
      <MetricCard
        value={85.3}
        label="First Pass Yield"
        trend="down"
        target={95}
        unit="%"
      />

      {/* MTBF - Neutral Trend */}
      <MetricCard
        value={48.5}
        label="MTBF"
        trend="neutral"
        unit=" hrs"
      />

      {/* Production Count - No Trend */}
      <MetricCard value={1250} label="Units Produced" unit=" units" />

      {/* String Value - N/A */}
      <MetricCard value="N/A" label="Downtime" />

      {/* Zero Value */}
      <MetricCard value={0} label="Defects" unit=" units" />

      {/* Custom Styling */}
      <MetricCard
        value={99.8}
        label="Quality Rate"
        trend="up"
        unit="%"
        className="border-green-200"
      />
    </div>
  )
}
