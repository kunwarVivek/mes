/**
 * RoleDashboard Usage Examples
 *
 * Demonstrates how to use the RoleDashboard component for different roles
 */
import { RoleDashboard } from './RoleDashboard'

// Example 1: Production Dashboard
export function ProductionDashboardExample() {
  return (
    <RoleDashboard
      role="production"
      metrics={{
        primary: {
          value: 87.5,
          label: 'OEE',
          trend: 'up',
          target: 90,
          unit: '%',
        },
        secondary: {
          value: 156,
          label: 'Work Orders Active',
          trend: 'neutral',
          target: 150,
        },
        tertiary: {
          value: 92.3,
          label: 'Machine Utilization',
          trend: 'up',
          target: 95,
          unit: '%',
        },
      }}
      chartData={[
        { name: 'Line 1', value: 85 },
        { name: 'Line 2', value: 92 },
        { name: 'Line 3', value: 88 },
        { name: 'Line 4', value: 95 },
      ]}
      trendData={[
        { name: 'Mon', value: 145 },
        { name: 'Tue', value: 152 },
        { name: 'Wed', value: 148 },
        { name: 'Thu', value: 156 },
        { name: 'Fri', value: 160 },
      ]}
    />
  )
}

// Example 2: Quality Dashboard
export function QualityDashboardExample() {
  return (
    <RoleDashboard
      role="quality"
      metrics={{
        primary: {
          value: 98.5,
          label: 'First Pass Yield',
          trend: 'up',
          target: 99,
          unit: '%',
        },
        secondary: {
          value: 1.2,
          label: 'Defect Rate',
          trend: 'down',
          target: 1.0,
          unit: '%',
        },
        tertiary: {
          value: 12,
          label: 'Open NCRs',
          trend: 'neutral',
          target: 10,
        },
      }}
      chartData={[
        { name: 'Visual', value: 45 },
        { name: 'Dimensional', value: 32 },
        { name: 'Functional', value: 18 },
        { name: 'Other', value: 5 },
      ]}
      trendData={[
        { name: 'Week 1', value: 8 },
        { name: 'Week 2', value: 12 },
        { name: 'Week 3', value: 10 },
        { name: 'Week 4', value: 12 },
      ]}
    />
  )
}

// Example 3: Maintenance Dashboard
export function MaintenanceDashboardExample() {
  return (
    <RoleDashboard
      role="maintenance"
      metrics={{
        primary: {
          value: 2.5,
          label: 'Average Downtime',
          trend: 'down',
          target: 2.0,
          unit: ' hrs',
        },
        secondary: {
          value: 48.2,
          label: 'MTBF',
          trend: 'up',
          target: 50,
          unit: ' hrs',
        },
        tertiary: {
          value: 94.5,
          label: 'PM Completion',
          trend: 'up',
          target: 95,
          unit: '%',
        },
      }}
      chartData={[
        { name: 'Operational', value: 18 },
        { name: 'Scheduled PM', value: 3 },
        { name: 'Under Repair', value: 2 },
        { name: 'Idle', value: 1 },
      ]}
      trendData={[
        { name: 'Mon', value: 4 },
        { name: 'Tue', value: 3 },
        { name: 'Wed', value: 5 },
        { name: 'Thu', value: 2 },
        { name: 'Fri', value: 3 },
      ]}
    />
  )
}

// Example 4: Planning Dashboard
export function PlanningDashboardExample() {
  return (
    <RoleDashboard
      role="planning"
      metrics={{
        primary: {
          value: 88.5,
          label: 'Schedule Adherence',
          trend: 'neutral',
          target: 90,
          unit: '%',
        },
        secondary: {
          value: 76.2,
          label: 'Capacity Utilization',
          trend: 'up',
          target: 80,
          unit: '%',
        },
        tertiary: {
          value: 42,
          label: 'Orders in Backlog',
          trend: 'down',
          target: 40,
        },
      }}
      chartData={[
        { name: 'Assembly', value: 82 },
        { name: 'Machining', value: 75 },
        { name: 'Welding', value: 68 },
        { name: 'Finishing', value: 90 },
      ]}
      trendData={[
        { name: 'Week 1', value: 48 },
        { name: 'Week 2', value: 45 },
        { name: 'Week 3', value: 43 },
        { name: 'Week 4', value: 42 },
      ]}
    />
  )
}
