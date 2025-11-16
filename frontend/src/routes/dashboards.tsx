import { createRoute } from '@tanstack/react-router';
import { authenticatedRoute } from './_authenticated';
import { ExecutiveDashboard } from '@/features/dashboards/pages/ExecutiveDashboard';

/**
 * Executive Dashboard Route
 *
 * Manufacturing performance dashboard with KPIs:
 * - On-Time Delivery (OTD)
 * - First Pass Yield (FPY)
 * - Overall Equipment Effectiveness (OEE)
 * - NCR Pareto Analysis
 * - Downtime Breakdown
 */
export const dashboardsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/dashboards',
  component: ExecutiveDashboard,
});
