/**
 * Equipment Module Exports
 *
 * Central export point for the Equipment/Machines module
 */

// Types
export type {
  Machine,
  MachineStatus,
  CreateMachineDTO,
  UpdateMachineDTO,
  MachineStatusUpdateDTO,
  MachineStatusHistory,
  MachineStatusUpdateResponse,
  OEEMetrics,
  MachineListResponse,
  MachineFilters,
} from './types/machine.types'

// Schemas
export {
  machineStatusSchema,
  createMachineSchema,
  updateMachineSchema,
  machineStatusUpdateSchema,
} from './schemas/machine.schema'

export type {
  CreateMachineFormData,
  UpdateMachineFormData,
  MachineStatusUpdateFormData,
} from './schemas/machine.schema'

// Services
export { machineService } from './services/machine.service'

// Hooks
export { useMachines, MACHINES_QUERY_KEY } from './hooks/useMachines'
export { useMachine, MACHINE_QUERY_KEY } from './hooks/useMachine'
export {
  useCreateMachine,
  useUpdateMachine,
  useDeleteMachine,
  useUpdateMachineStatus,
} from './hooks/useMachineMutations'
export { useMachineOEE, MACHINE_OEE_QUERY_KEY } from './hooks/useMachineOEE'

// Components
export { MachinesTable } from './components/MachinesTable'
export { MachineForm } from './components/MachineForm'
export { MachineStatusCard } from './components/MachineStatusCard'
export { OEEGauge } from './components/OEEGauge'
