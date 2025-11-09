/**
 * Shifts Module Exports
 */

// Types
export type {
  Shift,
  CreateShiftDTO,
  UpdateShiftDTO,
  ShiftListResponse,
  ShiftFilters,
  ShiftHandover,
  CreateShiftHandoverDTO,
  ShiftHandoverListResponse,
  ShiftHandoverFilters,
} from './types/shift.types'

// Services
export { shiftService } from './services/shift.service'

// Hooks
export { useShifts, SHIFTS_QUERY_KEY } from './hooks/useShifts'
export { useShift } from './hooks/useShift'
export {
  useCreateShift,
  useUpdateShift,
  useCreateHandover,
} from './hooks/useShiftMutations'

// Schemas
export {
  createShiftSchema,
  updateShiftSchema,
  createShiftHandoverSchema,
  type CreateShiftFormData,
  type UpdateShiftFormData,
  type CreateShiftHandoverFormData,
} from './schemas/shift.schema'

// Components
export { ShiftsTable, type ShiftsTableProps } from './components/ShiftsTable'
