import './DashboardGrid.css'
import type { CSSProperties, ReactNode } from 'react'

export interface DashboardGridProps {
  /**
   * Dashboard widgets or content to display in grid
   */
  children: ReactNode
  /**
   * Number of columns in the grid (default: 3)
   * Responsive: 3 cols desktop, 2 tablet, 1 mobile
   */
  columns?: number
  /**
   * Gap size between grid items in rem units (default: 1.5)
   */
  gap?: number
  /**
   * Additional CSS classes
   */
  className?: string
}

/**
 * Responsive CSS Grid layout for dashboard widgets
 *
 * Features:
 * - Automatic responsive breakpoints (3 cols -> 2 cols -> 1 col)
 * - Configurable columns and gap
 * - Clean spacing with CSS Grid gap property
 */
export function DashboardGrid({
  children,
  columns = 3,
  gap = 1.5,
  className = ''
}: DashboardGridProps) {
  const gridStyle: CSSProperties = {
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: `${gap}rem`
  }

  return (
    <div
      className={`dashboard-grid ${className}`.trim()}
      style={gridStyle}
    >
      {children}
    </div>
  )
}
