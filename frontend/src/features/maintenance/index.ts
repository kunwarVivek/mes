/**
 * Maintenance Module
 *
 * Public exports for PM scheduling and downtime tracking
 */

// Types
export type * from './types/maintenance.types'

// Schemas
export * from './schemas/maintenance.schema'

// Services
export { maintenanceService } from './services/maintenance.service'

// Hooks
export { usePMSchedules, PM_SCHEDULES_QUERY_KEY } from './hooks/usePMSchedules'
export { usePMSchedule } from './hooks/usePMSchedule'
export {
  useCreatePMSchedule,
  useUpdatePMSchedule,
  useDeletePMSchedule,
} from './hooks/usePMScheduleMutations'
export { useDowntimeEvents, DOWNTIME_EVENTS_QUERY_KEY } from './hooks/useDowntimeEvents'

// Components
export { PMSchedulesTable } from './components/PMSchedulesTable'
export { PMScheduleForm } from './components/PMScheduleForm'
export { DowntimeTracker } from './components/DowntimeTracker'
