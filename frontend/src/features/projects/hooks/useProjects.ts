/**
 * useProjects Hooks
 *
 * TanStack Query hooks for Projects CRUD operations
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsService } from '../services/projects.service'
import { useAuthStore } from '../../../stores/auth.store'
import type {
  ProjectFilters,
  ProjectCreateRequest,
  ProjectUpdateRequest,
} from '../types/project.types'

export const PROJECTS_QUERY_KEY = 'projects'

/**
 * Hook to fetch projects list with optional filters
 */
export function useProjects(filters?: Omit<ProjectFilters, 'plant_id'>) {
  const currentPlant = useAuthStore((state) => state.currentPlant)

  return useQuery({
    queryKey: [PROJECTS_QUERY_KEY, currentPlant?.id, filters],
    queryFn: () =>
      projectsService.list({
        plant_id: currentPlant?.id,
        ...filters,
      }),
    enabled: !!currentPlant,
  })
}

/**
 * Hook to fetch a single project by ID
 */
export function useProject(id: number) {
  return useQuery({
    queryKey: [PROJECTS_QUERY_KEY, id],
    queryFn: () => projectsService.getById(id),
    enabled: !!id,
  })
}

/**
 * Hook to create a new project
 */
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectCreateRequest) => projectsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] })
    },
  })
}

/**
 * Hook to update an existing project
 */
export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProjectUpdateRequest }) =>
      projectsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] })
    },
  })
}

/**
 * Hook to delete a project
 */
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => projectsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [PROJECTS_QUERY_KEY] })
    },
  })
}
