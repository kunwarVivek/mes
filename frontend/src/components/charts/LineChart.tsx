import {
  ResponsiveContainer,
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import DOMPurify from 'dompurify'

export interface LineChartProps {
  data: Array<{ name: string; value: number }>
  height?: number
  color?: string
  ariaLabel?: string
}

/**
 * Validates that a number is finite and not NaN
 */
function isValidNumber(value: number): boolean {
  return !isNaN(value) && isFinite(value)
}

/**
 * LineChart component - Accessible, responsive line chart wrapper
 * Uses Recharts library with sanitized data inputs
 */
export function LineChart({
  data,
  height = 300,
  color = '#1976d2',
  ariaLabel = 'Line chart',
}: LineChartProps) {
  // Sanitize data to prevent XSS attacks using DOMPurify
  const sanitizedData = data.map((item) => ({
    name: DOMPurify.sanitize(String(item.name), { ALLOWED_TAGS: [] }),
    value: isValidNumber(Number(item.value)) ? Number(item.value) : 0,
  }))

  return (
    <div
      role="img"
      aria-label={ariaLabel}
      tabIndex={0}
      style={{ outline: 'none' }}
    >
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLine
          data={sanitizedData}
          accessibilityLayer
          aria-label={ariaLabel}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            aria-label="Data values"
          />
        </RechartsLine>
      </ResponsiveContainer>
    </div>
  )
}
