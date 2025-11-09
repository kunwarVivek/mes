import {
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts'
import DOMPurify from 'dompurify'

export interface PieChartProps {
  data: Array<{ name: string; value: number }>
  height?: number
  colors?: string[]
  ariaLabel?: string
}

// Default material design color palette
const DEFAULT_COLORS = [
  '#1976d2',
  '#388e3c',
  '#d32f2f',
  '#f57c00',
  '#7b1fa2',
  '#0097a7',
  '#c2185b',
  '#303f9f',
]

/**
 * Validates that a number is finite and not NaN
 */
function isValidNumber(value: number): boolean {
  return !isNaN(value) && isFinite(value)
}

/**
 * PieChart component - Accessible, responsive pie chart wrapper
 * Uses Recharts library with sanitized data inputs
 */
export function PieChart({
  data,
  height = 300,
  colors = DEFAULT_COLORS,
  ariaLabel = 'Pie chart',
}: PieChartProps) {
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
        <RechartsPie accessibilityLayer aria-label={ariaLabel}>
          <Pie
            data={sanitizedData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            aria-label="Data distribution"
          >
            {sanitizedData.map((_entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[index % colors.length]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </RechartsPie>
      </ResponsiveContainer>
    </div>
  )
}
