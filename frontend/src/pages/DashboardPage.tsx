/**
 * DashboardPage Component
 *
 * Main dashboard with overview widgets and metrics:
 * - Single Responsibility: Dashboard overview
 * - Placeholder for future widgets
 * - Protected route (requires authentication)
 */

export const DashboardPage = () => {
  return (
    <div className="dashboard-page">
      <h1>Dashboard</h1>
      <p>Welcome to Unison ERP</p>
      <div className="dashboard-page__widgets">
        {/* Future widgets go here */}
      </div>
    </div>
  )
}

DashboardPage.displayName = 'DashboardPage'
