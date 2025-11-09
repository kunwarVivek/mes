/**
 * DashboardGrid Usage Examples
 *
 * This file demonstrates how to use the DashboardGrid component
 */
import { DashboardGrid } from './DashboardGrid'

// Example 1: Basic usage with default settings (3 columns, 1.5rem gap)
export function BasicExample() {
  return (
    <DashboardGrid>
      <div className="widget">Widget 1</div>
      <div className="widget">Widget 2</div>
      <div className="widget">Widget 3</div>
      <div className="widget">Widget 4</div>
      <div className="widget">Widget 5</div>
      <div className="widget">Widget 6</div>
    </DashboardGrid>
  )
}

// Example 2: Custom column count
export function CustomColumnsExample() {
  return (
    <DashboardGrid columns={4}>
      <div className="widget">Widget 1</div>
      <div className="widget">Widget 2</div>
      <div className="widget">Widget 3</div>
      <div className="widget">Widget 4</div>
    </DashboardGrid>
  )
}

// Example 3: Custom gap size
export function CustomGapExample() {
  return (
    <DashboardGrid gap={2}>
      <div className="widget">Widget 1</div>
      <div className="widget">Widget 2</div>
      <div className="widget">Widget 3</div>
    </DashboardGrid>
  )
}

// Example 4: With custom className for additional styling
export function CustomClassExample() {
  return (
    <DashboardGrid className="dashboard-main-grid">
      <div className="widget">Widget 1</div>
      <div className="widget">Widget 2</div>
      <div className="widget">Widget 3</div>
    </DashboardGrid>
  )
}

// Example 5: Real-world dashboard with mixed widgets
export function RealWorldExample() {
  return (
    <DashboardGrid columns={3} gap={1.5}>
      <div className="widget stats-card">
        <h3>Total Orders</h3>
        <p>1,234</p>
      </div>
      <div className="widget stats-card">
        <h3>Completed</h3>
        <p>987</p>
      </div>
      <div className="widget stats-card">
        <h3>In Progress</h3>
        <p>247</p>
      </div>
      <div className="widget chart-card" style={{ gridColumn: 'span 2' }}>
        <h3>Production Chart</h3>
        {/* Chart component */}
      </div>
      <div className="widget recent-activity">
        <h3>Recent Activity</h3>
        {/* Activity list */}
      </div>
    </DashboardGrid>
  )
}

// Example 6: Responsive behavior demonstration
// On desktop (>1024px): Uses custom column count (3)
// On tablet (641-1024px): Automatically becomes 2 columns
// On mobile (<=640px): Automatically becomes 1 column
export function ResponsiveExample() {
  return (
    <DashboardGrid columns={3} gap={1.5}>
      <div className="widget">Responsive Widget 1</div>
      <div className="widget">Responsive Widget 2</div>
      <div className="widget">Responsive Widget 3</div>
      <div className="widget">Responsive Widget 4</div>
      <div className="widget">Responsive Widget 5</div>
      <div className="widget">Responsive Widget 6</div>
    </DashboardGrid>
  )
}
