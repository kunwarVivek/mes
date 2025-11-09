/**
 * Lane Hooks
 *
 * TanStack Query hooks for lane scheduling operations
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { lanesService } from '../services/lanes.service'
import type {
  LaneAssignmentCreateRequest,
  LaneAssignmentUpdateRequest,
} from '../types/lane.types'

// Query keys
export const LANES_QUERY_KEY = 'lanes'
export const LANE_ASSIGNMENTS_QUERY_KEY = 'lane-assignments'
export const LANE_CAPACITY_QUERY_KEY = 'lane-capacity'

/**
 * Fetch lanes list with optional plant filter
 */
export function useLanes(plantId?: number) {
  return useQuery({
    queryKey: [LANES_QUERY_KEY, { plant_id: plantId }],
    queryFn: () => lanesService.listLanes({ plant_id: plantId }),
  })
}

/**
 * Fetch single lane by ID
 */
export function useLane(laneId: number) {
  return useQuery({
    queryKey: [LANES_QUERY_KEY, laneId],
    queryFn: () => lanesService.getLane(laneId),
  })
}

/**
 * Fetch lane capacity for specific date
 */
export function useLaneCapacity(laneId: number, date: string) {
  return useQuery({
    queryKey: [LANE_CAPACITY_QUERY_KEY, laneId, date],
    queryFn: () => lanesService.getLaneCapacity(laneId, date),
  })
}

/**
 * Fetch lane assignments with filters
 */
export function useLaneAssignments(filters?: {
  lane_id?: number
  plant_id?: number
  start_date?: string
  end_date?: string
  status?: string
}) {
  return useQuery({
    queryKey: [LANE_ASSIGNMENTS_QUERY_KEY, filters],
    queryFn: () => lanesService.listAssignments(filters),
  })
}

/**
 * Create new lane assignment
 */
export function useCreateAssignment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: LaneAssignmentCreateRequest) =>
      lanesService.createAssignment(data),
    onSuccess: () => {
      // Invalidate assignments queries
      queryClient.invalidateQueries({ queryKey: [LANE_ASSIGNMENTS_QUERY_KEY] })
      // Invalidate capacity queries
      queryClient.invalidateQueries({ queryKey: [LANE_CAPACITY_QUERY_KEY] })
    },
  })
}

/**
 * Update existing lane assignment
 */
export function useUpdateAssignment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: LaneAssignmentUpdateRequest }) =>
      lanesService.updateAssignment(id, data),
    onSuccess: () => {
      // Invalidate assignments queries
      queryClient.invalidateQueries({ queryKey: [LANE_ASSIGNMENTS_QUERY_KEY] })
      // Invalidate capacity queries
      queryClient.invalidateQueries({ queryKey: [LANE_CAPACITY_QUERY_KEY] })
    },
  })
}

/**
 * Delete lane assignment
 */
export function useDeleteAssignment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => lanesService.deleteAssignment(id),
    onSuccess: () => {
      // Invalidate assignments queries
      queryClient.invalidateQueries({ queryKey: [LANE_ASSIGNMENTS_QUERY_KEY] })
      // Invalidate capacity queries
      queryClient.invalidateQueries({ queryKey: [LANE_CAPACITY_QUERY_KEY] })
    },
  })
}
